import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from recordkit import archive


def _repo(tmp_path, records=None):
    """A minimal checkout: tools/hugo/hugo.yaml, a records tree, a CURRENT line."""
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../../records\n", encoding="utf-8")
    rec = tmp_path / "records"
    rec.mkdir()
    for name, text in (records or {"a.md": "---\ntitle: A\n---\n\nhello\n"}).items():
        p = rec / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    (tmp_path / "CURRENT").write_text("0.12.1 badstu-flue\n", encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def _no_git(monkeypatch):
    """Provenance is nice to have; tests never shell out for it."""
    monkeypatch.setattr(archive, "_run", lambda argv, cwd=None:
                        subprocess.CompletedProcess(argv, 0, stdout="deadbeef\n", stderr=""))


WHEN = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_bundle_layout_and_manifest(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "out" / "r.zip"
    result = archive.archive(repo, out=out, when=WHEN)
    assert result["written"] is True

    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        assert names[0] == "manifest.json" and names[1] == "README.txt"
        assert "records/a.md" in names and "hugo.yaml" in names and "CURRENT" in names
        manifest = json.loads(zf.read("manifest.json"))

    assert manifest["schema"] == archive.SCHEMA
    assert manifest["created"] == "2026-08-01T12:00:00Z"
    assert manifest["cycle"] == "0.12.1 badstu-flue"
    body = "---\ntitle: A\n---\n\nhello\n"
    entry = next(e for e in manifest["entries"] if e["path"] == "records/a.md")
    assert entry["size"] == len(body)
    assert entry["sha256"] == hashlib.sha256(body.encode()).hexdigest()


def test_manifest_checksums_match_the_files(tmp_path):
    repo = _repo(tmp_path, {"a.md": "one\n", "sub/b.md": "two\n"})
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    with zipfile.ZipFile(out) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        for e in manifest["entries"]:
            assert hashlib.sha256(zf.read(e["path"])).hexdigest() == e["sha256"]
    assert len(manifest["entries"]) == 4  # two records, hugo.yaml, CURRENT


def test_deterministic_bytes(tmp_path):
    repo = _repo(tmp_path)
    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    archive.archive(repo, out=a, when=WHEN)
    archive.archive(repo, out=b, when=WHEN)
    assert a.read_bytes() == b.read_bytes()


def test_source_date_epoch_pins_created(tmp_path, monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1000000000")
    repo = _repo(tmp_path)
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    with zipfile.ZipFile(out) as zf:
        assert json.loads(zf.read("manifest.json"))["created"] == "2001-09-09T01:46:40Z"


def test_zip_entries_carry_fixed_metadata(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    with zipfile.ZipFile(out) as zf:
        for info in zf.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.create_system == 3


def test_referenced_asset_outside_records_is_included(tmp_path):
    repo = _repo(tmp_path, {"a.md": "![logo](logo.svg)\n"})
    static = repo / "tools" / "hugo" / "themes" / "Fuglekasse" / "static"
    static.mkdir(parents=True)
    (static / "logo.svg").write_bytes(b"<svg/>")
    (static / "unused.svg").write_bytes(b"<svg/>")
    out = tmp_path / "r.zip"
    result = archive.archive(repo, out=out, when=WHEN)
    with zipfile.ZipFile(out) as zf:
        assert "static/logo.svg" in zf.namelist()
        assert "static/unused.svg" not in zf.namelist()
    assert any(e["reason"] == "unreferenced" and e["path"].endswith("unused.svg")
               for e in result["excluded"])


def test_bundle_assets_ride_along_with_the_records_tree(tmp_path):
    repo = _repo(tmp_path, {"2026-07-06_23-30/index.md": "![x](image.png)\n"})
    (repo / "records" / "2026-07-06_23-30" / "image.png").write_bytes(b"PNG")
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    with zipfile.ZipFile(out) as zf:
        assert "records/2026-07-06_23-30/image.png" in zf.namelist()


def test_dry_run_writes_nothing_and_explains_exclusions(tmp_path):
    repo = _repo(tmp_path, {"a.md": "![gone](missing.png)\n"})
    out = tmp_path / "r.zip"
    result = archive.archive(repo, out=out, dry_run=True, when=WHEN)
    assert result["written"] is False and not out.exists()
    assert "records/a.md" in result["would_include"]
    assert result["excluded"] == [{"path": "missing.png", "reason": "not found",
                                   "referenced_by": "records/a.md"}]


def test_missing_records_dir_is_an_error(tmp_path):
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../../records\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="nothing to archive"):
        archive.archive(tmp_path, out=tmp_path / "r.zip")


def test_default_out_lands_in_the_working_directory(tmp_path):
    assert archive.default_out(tmp_path, WHEN).parent == Path.cwd()
    assert archive.default_out(tmp_path, WHEN).name.startswith("records-")


def test_check_is_clean_for_a_fresh_archive(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "records-x.zip"
    archive.archive(repo, out=out, when=WHEN)
    report = archive.check(repo, out=out)
    assert report["ok"] is True and report["faults"] == []


def test_check_reports_a_corrupted_archive_and_a_broken_reference(tmp_path):
    repo = _repo(tmp_path, {"a.md": "![gone](missing.png)\n"})
    out = tmp_path / "records-x.zip"
    archive.archive(repo, out=out, when=WHEN)
    _corrupt(out, "records/a.md")
    report = archive.check(repo, out=out)
    assert report["ok"] is False
    kinds = {f["kind"] for f in report["faults"]}
    assert "checksum" in kinds and "broken-reference" in kinds


def test_check_without_an_archive_says_so(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    report = archive.check(repo)
    assert report["ok"] is False
    assert report["faults"][0]["kind"] == "no-archive"


def _corrupt(zip_path: Path, member: str) -> None:
    """Rewrite one member with different bytes, leaving the manifest untouched."""
    with zipfile.ZipFile(zip_path) as zf:
        keep = [(i, zf.read(i.filename)) for i in zf.infolist()]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for info, data in keep:
            zf.writestr(info, b"tampered\n" if info.filename == member else data)
