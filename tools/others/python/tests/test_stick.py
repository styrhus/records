import os
import stat
from pathlib import Path

import pytest

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


def test_find_record_in_checkout_resolves_via_hugo_config(tmp_path):
    """/record, /all, /me, /cpd all resolve the records dir from a nested hugo.yaml's contentDir —
    /stick must land on the exact same directory, not the caller's $PWD."""
    hugo = tmp_path / "project" / "site" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../records\n")
    records = tmp_path / "project" / "site" / "records"
    rec = _record(records, "how-to.md")

    # `start` stands in for the caller's cwd — a parent workspace above the records checkout.
    assert stick.find_record_in_checkout(tmp_path, "how-to") == [rec]


def test_find_record_in_checkout_from_a_parent_project_workspace(tmp_path):
    """The acceptance shape: run from a parent project directory that merely contains the
    records checkout somewhere below it, same as /record's discovery walk."""
    nested = tmp_path / "workspace" / "notes-clone"
    hugo = nested / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../../records\n")
    records = nested / "records"
    rec = _record(records, "linux/how-to.md")

    assert stick.find_record_in_checkout(tmp_path / "workspace", "how-to") == [rec]


def test_find_record_in_checkout_falls_back_to_records_dir(tmp_path):
    """No hugo.yaml found anywhere below `start` → the same `records/` fallback config.py uses."""
    rec = _record(tmp_path / "records", "how-to.md")
    assert stick.find_record_in_checkout(tmp_path, "how-to") == [rec]


def test_find_record_in_checkout_ambiguous_stays_explicit(tmp_path):
    hugo = tmp_path / "hugo"
    hugo.mkdir()
    (hugo / "hugo.yaml").write_text("contentDir: ../records\n")
    records = tmp_path / "records"
    _record(records, "linux/how-to.md")
    _record(records, "notes/how-to/index.md")
    assert len(stick.find_record_in_checkout(tmp_path, "how-to")) == 2


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


# --- the rewrite is atomic ----------------------------------------------------

def _break_the_swap(monkeypatch, name):
    """Fail `os.replace` for one target only, so the rest of a run behaves normally."""
    real = os.replace

    def guard(src, dst, *a, **k):
        if Path(dst).name == name:
            raise OSError("swap failed")
        return real(src, dst, *a, **k)

    monkeypatch.setattr(os, "replace", guard)


def test_featuring_leaves_the_record_whole_when_the_write_fails(tmp_path, monkeypatch):
    """The record is the user's own conversation — a failed rewrite must lose none of it."""
    p = _record(tmp_path, "how-to.md")
    before = p.read_text(encoding="utf-8")
    _break_the_swap(monkeypatch, "how-to.md")
    with pytest.raises(OSError):
        stick.feature_file(p)
    assert p.read_text(encoding="utf-8") == before
    assert [q.name for q in tmp_path.iterdir()] == ["how-to.md"]  # no leftover temp file


def test_featuring_keeps_the_record_permissions(tmp_path):
    p = _record(tmp_path, "how-to.md")
    p.chmod(0o640)
    stick.feature_file(p)
    assert stat.S_IMODE(p.stat().st_mode) == 0o640
    assert "featured: true" in p.read_text(encoding="utf-8")
