from datetime import datetime
from pathlib import Path

import pytest

from recordkit import create, importer, writer


def conv(**kw):
    kw.setdefault("turns", [importer.Turn("human", "hi"),
                            importer.Turn("assistant", "yo", model="qwen2.5:14b")])
    return importer.Conversation(**kw)


def date_of(record: Path) -> datetime:
    line = next(ln for ln in record.read_text().splitlines() if ln.startswith("date: "))
    return datetime.fromisoformat(line[len("date: "):])


def test_imported_record_is_byte_identical_to_created(tmp_path):
    made = Path(create.new_record(tmp_path / "created", title="Byte Match")["path"])
    writer.append_turn(made, "hi", "yo", "qwen2.5:14b")

    out = importer.emit(tmp_path / "imported", conv(title="Byte Match", date=date_of(made)))
    assert Path(out["path"]).read_text() == made.read_text()


def test_source_and_source_id_land_in_frontmatter(tmp_path):
    out = importer.emit(tmp_path, conv(title="T", source_id="sess-1"), source="claude-code")
    assert "\nsource: claude-code\nsourceId: sess-1\n---\n" in Path(out["path"]).read_text()


def test_no_source_id_means_no_identity_keys(tmp_path):
    out = importer.emit(tmp_path, conv(title="T"), source="claude-code")
    assert "source:" not in Path(out["path"]).read_text()


def test_title_falls_back_to_the_source_timestamp(tmp_path):
    when = datetime(2019, 3, 4, 5, 6, 7).astimezone()
    out = importer.emit(tmp_path, conv(date=when))
    assert Path(out["path"]).name == "2019-03-04_05-06.md"


def test_tags_route_into_the_first_tag_folder(tmp_path):
    out = importer.emit(tmp_path, conv(title="T", tags=["chatgpt", "old"]))
    assert Path(out["path"]) == tmp_path / "chatgpt" / "t.md"


def test_explicit_tags_override_the_parser(tmp_path):
    out = importer.emit(tmp_path, conv(title="T", tags=["parsed"]), tags=["forced"])
    assert Path(out["path"]).parent == tmp_path / "forced"


def test_lone_human_turn_gets_no_assistant_section(tmp_path):
    out = importer.emit(tmp_path, conv(title="T", turns=[importer.Turn("human", "alone")]))
    assert Path(out["path"]).read_text().endswith("---\n\n## Human\n\nalone\n")


def test_consecutive_assistant_turns_each_get_a_section(tmp_path):
    turns = [importer.Turn("assistant", "one", model="m"), importer.Turn("assistant", "two")]
    body = Path(importer.emit(tmp_path, conv(title="T", turns=turns))["path"]).read_text()
    assert body.endswith("## Assistant\n\none\n\n— m\n\n## Assistant\n\ntwo\n")


def test_human_name_heads_the_turn(tmp_path):
    out = importer.emit(tmp_path, conv(title="T"), name="Ada")
    assert "## Human (Ada)\n" in Path(out["path"]).read_text()


def test_dry_run_writes_nothing_but_names_the_target(tmp_path):
    out = importer.emit(tmp_path, conv(title="T"), dry_run=True)
    assert Path(out["path"]) == tmp_path / "t.md"
    assert not (tmp_path / "t.md").exists()


def test_imported_ids_finds_the_pair(tmp_path):
    importer.emit(tmp_path, conv(title="A", source_id="one"), source="llm")
    importer.emit(tmp_path, conv(title="B", source_id="two"), source="other")
    assert set(importer.imported_ids(tmp_path, "llm")) == {"one"}


def test_run_skips_conversations_already_imported(tmp_path, monkeypatch):
    convs = [conv(title="A", source_id="one"), conv(title="B", source_id="two")]
    monkeypatch.setitem(importer.parsers(), "fake", lambda p: iter(convs))

    first = importer.run("fake", tmp_path / "src", tmp_path / "rec")
    second = importer.run("fake", tmp_path / "src", tmp_path / "rec")
    assert first["count"] == {"written": 2, "skipped": 0}
    assert second["count"] == {"written": 0, "skipped": 2}


def test_run_dry_run_leaves_the_records_dir_empty(tmp_path, monkeypatch):
    monkeypatch.setitem(importer.parsers(), "fake", lambda p: iter([conv(title="A", source_id="one")]))
    out = importer.run("fake", tmp_path / "src", tmp_path / "rec", dry_run=True)
    assert out["count"]["written"] == 1
    assert not (tmp_path / "rec").exists()


def test_run_deduplicates_within_a_single_batch(tmp_path, monkeypatch):
    twice = [conv(title="A", source_id="same"), conv(title="A", source_id="same")]
    monkeypatch.setitem(importer.parsers(), "fake", lambda p: iter(twice))
    assert importer.run("fake", tmp_path / "s", tmp_path / "r")["count"] == {"written": 1, "skipped": 1}


def test_unknown_source_error_names_the_known_ones(tmp_path):
    with pytest.raises(ValueError) as e:
        importer.run("nope", tmp_path, tmp_path)
    assert "nope" in str(e.value) and "claude-code" in str(e.value)
