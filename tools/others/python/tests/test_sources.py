import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from recordkit import sources

FIXTURES = Path(__file__).parent / "fixtures"
SESSION = FIXTURES / "claude-code-session.jsonl"


def only(path):
    convs = list(sources.claude_code(Path(path)))
    assert len(convs) == 1
    return convs[0]


def test_claude_code_keeps_the_conversation_and_drops_the_trace():
    turns = only(SESSION).turns
    assert [(t.role, t.text) for t in turns] == [
        ("human", "make the icon right-aligned"),
        ("assistant", "Reading the skill file.\n\nDone — the icon now sits in a right-aligned div."),
        ("human", "thanks, ship it"),
    ]


def test_claude_code_drops_thinking_tool_and_image_blocks():
    body = "\n".join(t.text for t in only(SESSION).turns)
    assert "private reasoning" not in body
    assert "toolu_1" not in body and "description: stamp the track" not in body
    assert "iVBORw0KGgo=" not in body


def test_claude_code_drops_meta_and_sidechain_rows():
    body = "\n".join(t.text for t in only(SESSION).turns)
    assert "Base directory for this skill" not in body
    assert "subagent chatter" not in body


def test_claude_code_strips_command_and_ide_wrappers():
    body = "\n".join(t.text for t in only(SESSION).turns)
    assert "<ide_opened_file>" not in body and "SKILL.md in the IDE" not in body
    assert "/gcp" not in body and "Set model to" not in body


def test_claude_code_signs_assistant_turns_with_the_model():
    assistant = [t for t in only(SESSION).turns if t.role == "assistant"]
    assert [t.model for t in assistant] == ["claude-sonnet-5"]


def test_claude_code_title_comes_from_the_ai_title_row():
    assert only(SESSION).title == "Wrap the skill content"


def test_claude_code_session_id_is_the_source_id():
    assert only(SESSION).source_id == "sess-fixture"


def test_claude_code_date_is_the_first_timestamp_in_local_time():
    expected = datetime(2026, 7, 13, 22, 10, 49, 982000, tzinfo=timezone.utc).astimezone()
    assert only(SESSION).date == expected


def test_claude_code_title_falls_back_to_the_first_human_line(tmp_path):
    rows = [json.loads(ln) for ln in SESSION.read_text().splitlines()]
    f = tmp_path / "s.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows if r["type"] != "ai-title") + "\n")
    assert only(f).title == "make the icon right-aligned"


def test_claude_code_title_fallback_is_path_safe(tmp_path):
    f = tmp_path / "s.jsonl"
    f.write_text(json.dumps({"type": "user", "sessionId": "s", "timestamp": "2026-07-13T22:00:00Z",
                             "message": {"role": "user", "content": "fix src/foo.py please"}}) + "\n")
    assert "/" not in only(f).title


def test_claude_code_title_keeps_a_hash_now_that_build_quotes_it(tmp_path):
    f = tmp_path / "s.jsonl"
    f.write_text(json.dumps({"type": "user", "sessionId": "s", "timestamp": "2026-07-13T22:00:00Z",
                             "message": {"role": "user", "content": "fix the #tag bug"}}) + "\n")
    assert only(f).title == "fix the #tag bug"


def test_claude_code_reads_a_directory_of_sessions(tmp_path):
    (tmp_path / "a.jsonl").write_text(SESSION.read_text())
    (tmp_path / "b.jsonl").write_text(SESSION.read_text().replace("sess-fixture", "sess-other"))
    assert {c.source_id for c in sources.claude_code(tmp_path)} == {"sess-fixture", "sess-other"}


def test_claude_code_skips_a_session_with_no_conversation(tmp_path):
    f = tmp_path / "empty.jsonl"
    f.write_text(json.dumps({"type": "queue-operation", "sessionId": "s",
                             "timestamp": "2026-07-13T22:00:00Z"}) + "\n")
    assert list(sources.claude_code(f)) == []


def test_claude_code_bad_json_names_the_file_and_line(tmp_path):
    f = tmp_path / "broken.jsonl"
    f.write_text('{"type":"user"}\nnot json at all\n')
    with pytest.raises(ValueError) as e:
        list(sources.claude_code(f))
    assert "broken.jsonl" in str(e.value) and "line 2" in str(e.value)


def test_claude_code_drops_a_task_notification_and_its_nested_tags(tmp_path):
    f = tmp_path / "s.jsonl"
    f.write_text("\n".join(json.dumps(row) for row in [
        {"type": "user", "sessionId": "s", "timestamp": "2026-07-13T22:00:00Z",
         "message": {"role": "user", "content": "run the thing"}},
        {"type": "user", "sessionId": "s", "timestamp": "2026-07-13T22:01:00Z",
         "message": {"role": "user", "content":
                     "<task-notification>\n<task-id>t1</task-id>\n"
                     "<tool-use-id>toolu_01XMqxUigA1ptcCEboFKmQ6Z</tool-use-id>\n"
                     "<status>completed</status>\n</task-notification>"}},
    ]) + "\n")
    body = "\n".join(t.text for t in only(f).turns)
    assert body == "run the thing"


def test_claude_code_is_registered():
    assert sources.PARSERS["claude-code"] is sources.claude_code


# --- llm SQLite logs ---------------------------------------------------------------------------

LLM_SCHEMA = """
CREATE TABLE conversations (id TEXT PRIMARY KEY, name TEXT, model TEXT);
CREATE TABLE responses (id TEXT PRIMARY KEY, model TEXT, prompt TEXT, system TEXT,
                        response TEXT, conversation_id TEXT, datetime_utc TEXT);
"""


def llm_db(tmp_path, conversations=(("c1", "Booting a Pi"),), responses=(
        ("r1", "gpt-4o", "how do I flash it?", "Use rpi-imager.", "c1", "2026-07-13T22:10:00"),
        ("r2", "gpt-4o", "and the wifi?", "Put wpa_supplicant.conf on the boot partition.",
         "c1", "2026-07-13T22:12:00"))):
    db = tmp_path / "logs.db"
    con = sqlite3.connect(db)
    con.executescript(LLM_SCHEMA)
    con.executemany("INSERT INTO conversations (id, name) VALUES (?, ?)", conversations)
    con.executemany("INSERT INTO responses (id, model, prompt, response, conversation_id,"
                    " datetime_utc) VALUES (?, ?, ?, ?, ?, ?)", responses)
    con.commit()
    con.close()
    return db


def test_llm_pairs_each_prompt_with_its_response(tmp_path):
    convs = list(sources.llm(llm_db(tmp_path)))
    assert len(convs) == 1
    assert [(t.role, t.text) for t in convs[0].turns] == [
        ("human", "how do I flash it?"),
        ("assistant", "Use rpi-imager."),
        ("human", "and the wifi?"),
        ("assistant", "Put wpa_supplicant.conf on the boot partition."),
    ]


def test_llm_signs_assistant_turns_with_the_row_model(tmp_path):
    turns = list(sources.llm(llm_db(tmp_path)))[0].turns
    assert [t.model for t in turns if t.role == "assistant"] == ["gpt-4o", "gpt-4o"]


def test_llm_title_and_id_come_from_the_conversation(tmp_path):
    conv = list(sources.llm(llm_db(tmp_path)))[0]
    assert (conv.title, conv.source_id) == ("Booting a Pi", "c1")


def test_llm_title_falls_back_to_the_first_prompt(tmp_path):
    conv = list(sources.llm(llm_db(tmp_path, conversations=(("c1", None),))))[0]
    assert conv.title == "how do I flash it?"


def test_llm_date_is_utc_converted_to_local(tmp_path):
    expected = datetime(2026, 7, 13, 22, 10, tzinfo=timezone.utc).astimezone()
    assert list(sources.llm(llm_db(tmp_path)))[0].date == expected


def test_llm_orphan_response_becomes_its_own_conversation(tmp_path):
    db = llm_db(tmp_path, responses=(
        ("r1", "m", "grouped", "a", "c1", "2026-07-13T22:10:00"),
        ("r9", "m", "loose", "b", None, "2026-07-13T22:20:00")))
    assert sorted(c.source_id for c in sources.llm(db)) == ["c1", "r9"]


def test_llm_orders_turns_by_time_not_insertion(tmp_path):
    db = llm_db(tmp_path, responses=(
        ("r2", "m", "second", "b", "c1", "2026-07-13T22:20:00"),
        ("r1", "m", "first", "a", "c1", "2026-07-13T22:10:00")))
    assert [t.text for t in list(sources.llm(db))[0].turns] == ["first", "a", "second", "b"]


def test_llm_connection_refuses_writes(tmp_path):
    con = sources.llm_connect(llm_db(tmp_path))
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        con.execute("CREATE TABLE scribble (x TEXT)")


def test_llm_missing_table_is_named(tmp_path):
    db = tmp_path / "empty.db"
    sqlite3.connect(db).execute("CREATE TABLE conversations (id TEXT, name TEXT)")
    with pytest.raises(ValueError, match="responses"):
        list(sources.llm(db))


def test_llm_missing_column_is_named(tmp_path):
    db = tmp_path / "thin.db"
    con = sqlite3.connect(db)
    con.executescript("CREATE TABLE conversations (id TEXT, name TEXT);"
                      "CREATE TABLE responses (id TEXT, prompt TEXT);")
    con.close()
    with pytest.raises(ValueError, match="response"):
        list(sources.llm(db))


def test_llm_missing_file_is_named(tmp_path):
    with pytest.raises(ValueError, match="nowhere.db"):
        list(sources.llm(tmp_path / "nowhere.db"))


def test_llm_is_registered():
    assert sources.PARSERS["llm"] is sources.llm


# --- a directory of Markdown -------------------------------------------------------------------

def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def by_id(root):
    return {c.source_id: c for c in sources.markdown(root)}


def test_markdown_passes_frontmatter_through(tmp_path):
    write(tmp_path, "post.md", "---\ntitle: Old Post\ndate: 2019-03-04T05:06:07+02:00\n"
                               "tags: [linux, hw]\n---\n\nsome words\n")
    conv = by_id(tmp_path)["post.md"]
    assert conv.title == "Old Post"
    assert conv.tags == ["linux", "hw"]
    assert conv.date == datetime.fromisoformat("2019-03-04T05:06:07+02:00")


def test_markdown_unstructured_file_becomes_one_body_turn(tmp_path):
    write(tmp_path, "note.md", "just a note\n\nwith two paragraphs\n")
    conv = by_id(tmp_path)["note.md"]
    assert conv.kind == "body"
    assert [(t.role, t.text) for t in conv.turns] == [
        ("human", "just a note\n\nwith two paragraphs")]


def test_markdown_detects_turns_and_keeps_the_signature_model(tmp_path):
    write(tmp_path, "rec.md", "---\ntitle: T\n---\n\n## Human\n\nhi\n\n"
                              "## Assistant\n\nyo\n\n— qwen2.5:14b\n")
    conv = by_id(tmp_path)["rec.md"]
    assert conv.kind == "conversation"
    assert [(t.role, t.text, t.model) for t in conv.turns] == [
        ("human", "hi", None), ("assistant", "yo", "qwen2.5:14b")]


def test_markdown_title_from_the_first_heading(tmp_path):
    write(tmp_path, "x.md", "# A Real Heading\n\nwords\n")
    assert by_id(tmp_path)["x.md"].title == "A Real Heading"


def test_markdown_title_falls_back_to_the_filename_stem(tmp_path):
    write(tmp_path, "hello-world.md", "words with no heading\n")
    assert by_id(tmp_path)["hello-world.md"].title == "hello-world"


def test_markdown_date_from_a_timestamp_filename(tmp_path):
    write(tmp_path, "2026-07-06_23-22.md", "words\n")
    conv = by_id(tmp_path)["2026-07-06_23-22.md"]
    assert (conv.date.year, conv.date.month, conv.date.hour, conv.date.minute) == (2026, 7, 23, 22)


def test_markdown_date_falls_back_to_mtime(tmp_path):
    path = write(tmp_path, "plain.md", "words\n")
    os.utime(path, (1_500_000_000, 1_500_000_000))
    assert by_id(tmp_path)["plain.md"].date == datetime.fromtimestamp(1_500_000_000).astimezone()


def test_markdown_source_id_is_the_path_relative_to_the_root(tmp_path):
    write(tmp_path, "blog/2019/post.md", "words\n")
    assert "blog/2019/post.md" in by_id(tmp_path)


def test_markdown_skips_hugo_and_hidden_files(tmp_path):
    for name in ("_index.md", "404.md", "LICENSE.md", ".hidden/x.md", "node_modules/y.md"):
        write(tmp_path, name, "words\n")
    write(tmp_path, "keep.md", "words\n")
    assert list(by_id(tmp_path)) == ["keep.md"]


def test_markdown_accepts_a_single_file(tmp_path):
    path = write(tmp_path, "one.md", "words\n")
    assert [c.source_id for c in sources.markdown(path)] == ["one.md"]


def test_markdown_skips_an_empty_file(tmp_path):
    write(tmp_path, "blank.md", "---\ntitle: T\n---\n\n\n")
    assert by_id(tmp_path) == {}


def test_markdown_is_registered():
    assert sources.PARSERS["markdown"] is sources.markdown
