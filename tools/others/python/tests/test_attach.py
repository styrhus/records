from pathlib import Path

import pytest

from recordkit import attach, create, naming


def _record(tmp_path, name="2026-07-06_23-30.md", text="---\ntitle: T\n---\n\nhello\n"):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _file(tmp_path, name, data=b"DATA"):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    p = src / name
    p.write_bytes(data)
    return p


def test_slug_filename_hygiene():
    assert naming.slug_filename("My Photo.JPG") == "my-photo.jpg"
    assert naming.slug_filename("wéird!! name.PDF") == "wird-name.pdf"
    assert naming.slug_filename("noext") == "noext"
    assert naming.slug_filename("!!!.png") == "file.png"


def test_flat_record_converts_to_a_bundle(tmp_path):
    record = _record(tmp_path)
    before = record.read_bytes()
    result = attach.attach(record, [_file(tmp_path, "shot.png")])

    assert result["converted"] is True
    index = tmp_path / "2026-07-06_23-30" / "index.md"
    assert index.is_file() and not record.exists()
    assert index.read_bytes() == before  # the record's bytes are never rewritten
    assert (tmp_path / "2026-07-06_23-30" / "shot.png").read_bytes() == b"DATA"


def test_url_slug_is_unchanged_by_conversion(tmp_path):
    """The bundle folder carries the old filename's stem, so :contentbasename gives the same URL."""
    record = _record(tmp_path)
    result = attach.attach(record, [_file(tmp_path, "a.png")])
    assert Path(result["bundle"]).name == "2026-07-06_23-30"


def test_second_attach_reuses_the_existing_bundle(tmp_path):
    record = _record(tmp_path)
    attach.attach(record, [_file(tmp_path, "a.png")])
    index = tmp_path / "2026-07-06_23-30" / "index.md"
    result = attach.attach(index, [_file(tmp_path, "b.pdf")])
    assert result["converted"] is False and result["was_bundle"] is True
    assert (tmp_path / "2026-07-06_23-30" / "b.pdf").is_file()


def test_bundle_folder_argument_is_accepted(tmp_path):
    record = _record(tmp_path)
    attach.attach(record, [_file(tmp_path, "a.png")])
    result = attach.attach(tmp_path / "2026-07-06_23-30", [_file(tmp_path, "c.txt")])
    assert result["converted"] is False


def test_three_file_types_in_one_command(tmp_path):
    record = _record(tmp_path)
    files = [_file(tmp_path, "photo.png"), _file(tmp_path, "paper.pdf"),
             _file(tmp_path, "clip.mp4")]
    result = attach.attach(record, files, append=True)

    names = [a["name"] for a in result["attached"]]
    assert names == ["photo.png", "paper.pdf", "clip.mp4"]
    markdown = result["markdown"]
    assert "![photo](photo.png)" in markdown
    assert "[paper](paper.pdf)" in markdown
    assert '<video src="clip.mp4" controls></video>' in markdown
    assert markdown in Path(result["record"]).read_text()


def test_source_is_copied_never_moved(tmp_path):
    record = _record(tmp_path)
    src = _file(tmp_path, "keepme.png")
    attach.attach(record, [src])
    assert src.is_file()


def test_never_overwrites(tmp_path):
    record = _record(tmp_path)
    attach.attach(record, [_file(tmp_path, "a.png")])
    index = tmp_path / "2026-07-06_23-30" / "index.md"
    other = tmp_path / "other"
    other.mkdir()
    (other / "a.png").write_bytes(b"SECOND")
    result = attach.attach(index, [other / "a.png"])
    assert result["attached"][0]["name"] == "a-1.png"
    assert (tmp_path / "2026-07-06_23-30" / "a.png").read_bytes() == b"DATA"


def test_two_identical_names_in_one_call(tmp_path):
    record = _record(tmp_path)
    a, b = _file(tmp_path, "x.png", b"1"), tmp_path / "other" / "x.png"
    b.parent.mkdir()
    b.write_bytes(b"2")
    result = attach.attach(record, [a, b])
    assert [x["name"] for x in result["attached"]] == ["x.png", "x-1.png"]


def test_dry_run_changes_nothing(tmp_path):
    record = _record(tmp_path)
    result = attach.attach(record, [_file(tmp_path, "a.png")], dry_run=True)
    assert result["converted"] is True and result["dry_run"] is True
    assert record.is_file()  # not converted
    assert not (tmp_path / "2026-07-06_23-30").exists()
    assert result["attached"][0]["markdown"] == "![a](a.png)"


def test_missing_source_is_an_error(tmp_path):
    record = _record(tmp_path)
    with pytest.raises(RuntimeError, match="nothing to attach"):
        attach.attach(record, [tmp_path / "nope.png"])
    assert record.is_file()  # refused before converting


def test_conversion_refuses_to_clobber_an_existing_folder(tmp_path):
    record = _record(tmp_path)
    (tmp_path / "2026-07-06_23-30").mkdir()
    with pytest.raises(RuntimeError, match="already exists"):
        attach.attach(record, [_file(tmp_path, "a.png")])


def test_title_overrides_the_label(tmp_path):
    record = _record(tmp_path)
    result = attach.attach(record, [_file(tmp_path, "a.png")], title="The whiteboard")
    assert result["attached"][0]["markdown"] == "![The whiteboard](a.png)"


def test_markdown_for_by_type():
    assert attach.markdown_for("a.jpg") == "![a](a.jpg)"
    assert attach.markdown_for("a.mp3") == '<audio src="a.mp3" controls></audio>'
    assert attach.markdown_for("a.tar.gz") == "[a.tar](a.tar.gz)"


def test_bundle_records_created_by_create(tmp_path):
    result = create.new_record(tmp_path, title="Whiteboard Session", bundle=True)
    path = Path(result["path"])
    assert path == tmp_path / "whiteboard-session" / "index.md"
    assert result["bundle"] is True
    assert path.read_text().startswith("---\ntitle: Whiteboard Session\n")


def test_flat_creation_is_unchanged(tmp_path):
    result = create.new_record(tmp_path, title="Whiteboard Session")
    assert Path(result["path"]) == tmp_path / "whiteboard-session.md"
    assert result["bundle"] is False


def test_bundle_folders_get_unique_names(tmp_path):
    a = create.new_record(tmp_path, title="Dup", bundle=True)
    b = create.new_record(tmp_path, title="Dup", bundle=True)
    assert Path(a["path"]).parent.name == "dup"
    assert Path(b["path"]).parent.name == "dup-1"


def test_bundle_inside_a_tag_folder(tmp_path):
    result = create.new_record(tmp_path, arguments="#linux Kernel Notes", bundle=True)
    assert Path(result["path"]) == tmp_path / "linux" / "kernel-notes" / "index.md"
