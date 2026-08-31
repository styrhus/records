import pytest

from recordkit import redact, turns

RECORD = """---
title: A conversation about bicycles
date: 2026-07-06T23:22:58+02:00
tags: [bicycles]
---

## Human (Ada)

My key is hunter2, please remember it.

## Assistant

Noted: hunter2.

Anything else?

— claude-opus-4-8

## User

Nothing else.

## Assistant

Goodbye.

— mistral:latest
"""


def _record(tmp_path, text=RECORD, name="bicycles.md"):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _yes(_diff):
    return True


def _no(_diff):
    return False


# ------------------------------------------------------------------ numbering

def test_locate_reproduces_the_one_numbering_scheme():
    """locate() must be turns.split() plus spans — ollama.py and card.py count the same turns."""
    located = redact.locate(RECORD)
    split = turns.split(RECORD)
    assert [(t["role"], t["content"], t["model"], t["label"], t["name"]) for t in located] == \
           [(t["role"], t["content"], t["model"], t["label"], t["name"]) for t in split]


@pytest.mark.parametrize("text", [
    "## Human\n\nhi\n",
    "## Assistant\n\n— model\n",                      # signature only: no content, no turn
    "## Human\n\n## Assistant\n\nreply\n\n— m\n",     # empty human turn is skipped by split()
    "---\nt: 1\n---\n\n## User\n\na\n\n## Assistant\n\nb\n",
    "## Assistant\n\nline\n\nmore\n\n— a:b\n",
    "no headings at all\n",
])
def test_locate_matches_split_on_awkward_shapes(text):
    assert [(t["role"], t["content"], t["model"]) for t in redact.locate(text)] == \
           [(t["role"], t["content"], t["model"]) for t in turns.split(text)]


def test_turn_numbering_is_the_history_index(tmp_path):
    """--turn N addresses the same turn ollama.py would send as history[N-1]."""
    history = turns.parse_turns(RECORD)
    assert history[1]["content"].startswith("Noted: hunter2.")
    p = _record(tmp_path)
    out = redact.redact(p, turn=2, remove=True, yes=True)
    assert out["role"] == "assistant"
    assert "Noted: hunter2." not in p.read_text(encoding="utf-8")


# ------------------------------------------------------------------ the seam

def test_remove_leaves_the_marker_and_keeps_the_shape(tmp_path):
    p = _record(tmp_path)
    redact.redact(p, turn=1, remove=True, yes=True)
    text = p.read_text(encoding="utf-8")
    assert "My key is hunter2" not in text
    assert "## Human (Ada)\n\n[redacted]\n" in text
    assert text.startswith("---\ntitle: A conversation about bicycles\n")


def test_the_conversation_still_reads_after_a_redaction(tmp_path):
    p = _record(tmp_path)
    before = turns.split(RECORD)
    redact.redact(p, turn=1, remove=True, yes=True)
    after = turns.split(p.read_text(encoding="utf-8"))
    assert len(after) == len(before)
    assert [t["role"] for t in after] == [t["role"] for t in before]
    assert [t["label"] for t in after] == [t["label"] for t in before]
    assert after[0]["content"] == redact.MARKER


def test_the_model_signature_survives(tmp_path):
    p = _record(tmp_path)
    redact.redact(p, turn=2, remove=True, yes=True)
    text = p.read_text(encoding="utf-8")
    assert "— claude-opus-4-8" in text
    assert turns.split(text)[1]["model"] == "claude-opus-4-8"
    assert turns.split(text)[1]["content"] == redact.MARKER


def test_replace_keeps_the_seam_visible(tmp_path):
    p = _record(tmp_path)
    redact.redact(p, turn=1, replace="My key is [a password], please remember it.", yes=True)
    text = p.read_text(encoding="utf-8")
    assert "My key is hunter2" not in text
    assert "My key is [a password], please remember it.\n\n[redacted]\n" in text


def test_only_the_named_turn_changes(tmp_path):
    p = _record(tmp_path)
    redact.redact(p, turn=2, remove=True, yes=True)
    text = p.read_text(encoding="utf-8")
    for kept in ("My key is hunter2, please remember it.", "Nothing else.", "Goodbye.",
                 "— mistral:latest", "tags: [bicycles]"):
        assert kept in text


def test_redacting_a_multi_paragraph_turn_takes_all_of_it(tmp_path):
    p = _record(tmp_path)
    redact.redact(p, turn=2, remove=True, yes=True)
    text = p.read_text(encoding="utf-8")
    assert "Anything else?" not in text


def test_a_bundle_record_is_addressable_by_its_folder(tmp_path):
    _record(tmp_path, name="bicycles/index.md")
    out = redact.redact(tmp_path / "bicycles", turn=1, remove=True, yes=True)
    assert out["record"] == str(tmp_path / "bicycles" / "index.md")
    assert "My key is hunter2" not in (tmp_path / "bicycles" / "index.md").read_text(encoding="utf-8")


# ------------------------------------------------------------------ asking first

def test_dry_run_writes_nothing_and_shows_the_diff(tmp_path):
    p = _record(tmp_path)
    out = redact.redact(p, turn=1, remove=True, dry_run=True)
    assert p.read_text(encoding="utf-8") == RECORD
    assert out["written"] is False
    assert "-My key is hunter2, please remember it." in out["diff"]
    assert "+[redacted]" in out["diff"]


def test_a_declined_confirmation_writes_nothing(tmp_path):
    p = _record(tmp_path)
    out = redact.redact(p, turn=1, remove=True, confirm=_no)
    assert p.read_text(encoding="utf-8") == RECORD
    assert out["written"] is False and out["cancelled"] is True


def test_confirmation_sees_the_diff(tmp_path):
    seen = []
    _record(tmp_path)
    redact.redact(tmp_path / "bicycles.md", turn=1, remove=True,
                  confirm=lambda d: seen.append(d) or True)
    assert seen and "hunter2" in seen[0]


def test_an_accepted_confirmation_writes(tmp_path):
    p = _record(tmp_path)
    assert redact.redact(p, turn=1, remove=True, confirm=_yes)["written"] is True


# ------------------------------------------------------------------ honesty

def test_every_result_states_what_remains(tmp_path):
    p = _record(tmp_path)
    for out in (redact.redact(p, turn=1, remove=True, dry_run=True),
                redact.redact(p, turn=1, remove=True, confirm=_no),
                redact.redact(p, turn=1, remove=True, yes=True)):
        assert any("git history" in line for line in out["remains"])
        assert any("fork" in line or "mirror" in line for line in out["remains"])


def test_the_notice_reaches_stderr_on_every_write(tmp_path, capsys):
    p = _record(tmp_path)
    redact.redact(p, turn=1, remove=True, yes=True)
    err = capsys.readouterr().err
    assert "git history still holds the original text" in err
    assert "working tree only" in err


def test_nothing_here_touches_git(tmp_path):
    """The border: redact never rewrites history. It writes one file and says so."""
    import inspect
    source = inspect.getsource(redact)
    assert "subprocess" not in source and "filter-repo" not in source


# ------------------------------------------------------------------ refusals

def test_turn_out_of_range(tmp_path):
    p = _record(tmp_path)
    with pytest.raises(RuntimeError, match="out of range"):
        redact.redact(p, turn=99, remove=True, yes=True)


def test_needs_exactly_one_of_replace_or_remove(tmp_path):
    p = _record(tmp_path)
    with pytest.raises(RuntimeError, match="exactly one"):
        redact.redact(p, turn=1, yes=True)
    with pytest.raises(RuntimeError, match="exactly one"):
        redact.redact(p, turn=1, replace="x", remove=True, yes=True)


def test_a_record_without_turns(tmp_path):
    p = _record(tmp_path, text="---\ntitle: t\n---\n\njust prose\n")
    with pytest.raises(RuntimeError, match="no Human/Assistant turns"):
        redact.redact(p, turn=1, remove=True, yes=True)


def test_a_missing_record(tmp_path):
    with pytest.raises(RuntimeError):
        redact.redact(tmp_path / "nope.md", turn=1, remove=True, yes=True)
