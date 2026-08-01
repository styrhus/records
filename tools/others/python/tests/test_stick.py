from pathlib import Path

from recordkit import attach, stick


def _record(records_dir: Path, name: str, text: str = "---\ntitle: T\n---\n\nhello\n") -> Path:
    p = records_dir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_finds_a_flat_record(tmp_path):
    _record(tmp_path, "how-to.md")
    assert stick.find_record(tmp_path, "how-to") == [tmp_path / "how-to.md"]


def test_finds_a_record_in_a_tag_folder(tmp_path):
    _record(tmp_path, "linux/how-to.md")
    assert stick.find_record(tmp_path, "how-to") == [tmp_path / "linux" / "how-to.md"]


def test_slugifies_the_argument(tmp_path):
    _record(tmp_path, "how-to.md")
    assert stick.find_record(tmp_path, "How To") == [tmp_path / "how-to.md"]


def test_finds_a_leaf_bundle(tmp_path):
    """`records attach` makes <slug>/index.md; the URL is unchanged, so /stick must still find it."""
    _record(tmp_path, "how-to/index.md")
    assert stick.find_record(tmp_path, "how-to") == [tmp_path / "how-to" / "index.md"]


def test_a_bundle_directory_without_index_is_not_a_record(tmp_path):
    (tmp_path / "how-to").mkdir()
    assert stick.find_record(tmp_path, "how-to") == []


def test_ambiguity_survives_across_both_shapes(tmp_path):
    _record(tmp_path, "linux/how-to.md")
    _record(tmp_path, "notes/how-to/index.md")
    assert len(stick.find_record(tmp_path, "how-to")) == 2


def test_a_record_attached_to_stays_findable(tmp_path):
    """The real regression: attach converts the record, stick used to lose it."""
    records = tmp_path / "records"
    records.mkdir()
    rec = _record(records, "how-to.md")
    asset = tmp_path / "photo.png"
    asset.write_bytes(b"PNG")

    assert stick.find_record(records, "how-to") == [rec]
    attach.attach(rec, [asset])

    found = stick.find_record(records, "how-to")
    assert found == [records / "how-to" / "index.md"]
    assert stick.feature_file(found[0])["featured"] is True
    assert "featured: true" in found[0].read_text(encoding="utf-8")
