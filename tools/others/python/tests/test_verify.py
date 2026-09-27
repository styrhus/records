# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import subprocess
import zipfile
from datetime import datetime, timezone

import pytest

from recordkit import archive, verify

WHEN = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _no_git(monkeypatch):
    monkeypatch.setattr(archive, "_run", lambda argv, cwd=None:
                        subprocess.CompletedProcess(argv, 0, stdout="deadbeef\n", stderr=""))


def _repo(tmp_path, records=None):
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../../records\n", encoding="utf-8")
    rec = tmp_path / "records"
    rec.mkdir()
    for name, text in (records or {"a.md": "hello\n"}).items():
        p = rec / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    (tmp_path / "CURRENT").write_text("0.12.1 badstu-flue\n", encoding="utf-8")
    return tmp_path


def _rewrite(zip_path, changes):
    """Rebuild the zip applying {member: new bytes or None to drop} plus extras."""
    with zipfile.ZipFile(zip_path) as zf:
        keep = [(i, zf.read(i.filename)) for i in zf.infolist()]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for info, data in keep:
            if info.filename in changes:
                if changes[info.filename] is None:
                    continue
                data = changes[info.filename]
            zf.writestr(info, data)
        for name, data in changes.items():
            if name not in {i.filename for i, _ in keep} and data is not None:
                zf.writestr(name, data)


def test_clean_archive_verifies(tmp_path):
    repo = _repo(tmp_path, {"a.md": "one\n", "sub/b.md": "two\n"})
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    report = verify.verify_archive(out)
    assert report["ok"] is True and report["faults"] == []
    assert report["checked"] == 4  # two records, hugo.yaml, CURRENT
    assert report["created"] == "2026-08-01T12:00:00Z"


def test_corrupted_entry_is_named(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    _rewrite(out, {"records/a.md": b"tampered\n"})
    report = verify.verify_archive(out)
    assert report["ok"] is False
    fault = next(f for f in report["faults"] if f["kind"] == "checksum")
    assert fault["path"] == "records/a.md"
    assert fault["expected"] != fault["actual"]


def test_missing_entry_is_reported(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    _rewrite(out, {"records/a.md": None})
    report = verify.verify_archive(out)
    assert [f["kind"] for f in report["faults"]] == ["missing"]
    assert report["faults"][0]["path"] == "records/a.md"


def test_unexpected_extra_is_reported(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    _rewrite(out, {"records/smuggled.md": b"surprise\n"})
    report = verify.verify_archive(out)
    assert [f["kind"] for f in report["faults"]] == ["extra"]
    assert report["faults"][0]["path"] == "records/smuggled.md"


def test_absent_and_unreadable_archives(tmp_path):
    assert verify.verify_archive(tmp_path / "nope.zip")["faults"][0]["kind"] == "missing"
    junk = tmp_path / "junk.zip"
    junk.write_bytes(b"not a zip at all")
    assert verify.verify_archive(junk)["faults"][0]["kind"] == "unreadable"


def test_archive_without_a_manifest(tmp_path):
    bare = tmp_path / "bare.zip"
    with zipfile.ZipFile(bare, "w") as zf:
        zf.writestr("records/a.md", "hello\n")
    report = verify.verify_archive(bare)
    assert report["ok"] is False and report["faults"][0]["kind"] == "manifest"


def test_unparseable_manifest(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    _rewrite(out, {"manifest.json": b"{not json"})
    assert verify.verify_archive(out)["faults"][0]["kind"] == "manifest"


def test_manifest_and_readme_are_not_extras(tmp_path):
    """They cannot list their own checksums, so they must not read as unexpected either."""
    repo = _repo(tmp_path)
    out = tmp_path / "r.zip"
    archive.archive(repo, out=out, when=WHEN)
    with zipfile.ZipFile(out) as zf:
        assert "README.txt" in zf.namelist()
        assert not any(e["path"] == "README.txt"
                       for e in json.loads(zf.read("manifest.json"))["entries"])
    assert verify.verify_archive(out)["ok"] is True


def test_repo_with_intact_references(tmp_path):
    repo = _repo(tmp_path, {"a.md": "![x](photo.jpg)\n"})
    (repo / "records" / "photo.jpg").write_bytes(b"JPG")
    report = verify.verify_repo(repo)
    assert report["ok"] is True and report["checked"] == 1


def test_repo_broken_reference_names_the_record(tmp_path):
    repo = _repo(tmp_path, {"sub/a.md": "![x](moved.jpg)\n"})
    report = verify.verify_repo(repo)
    assert report["ok"] is False
    fault = report["faults"][0]
    assert fault["kind"] == "broken-reference"
    assert fault["path"] == "moved.jpg" and fault["record"] == "sub/a.md"


def test_repo_ignores_remote_and_absolute_targets(tmp_path):
    repo = _repo(tmp_path, {"a.md": "![x](https://e.example/x.png)\n![y](/logo.svg)\n"})
    report = verify.verify_repo(repo)
    assert report["ok"] is True and report["checked"] == 0


def test_repo_finds_bundle_assets(tmp_path):
    repo = _repo(tmp_path, {"2026-07-06_23-30/index.md": "![x](image.png)\n"})
    (repo / "records" / "2026-07-06_23-30" / "image.png").write_bytes(b"PNG")
    assert verify.verify_repo(repo)["ok"] is True


def test_repo_reference_follows_the_theme_key(tmp_path):
    repo = _repo(tmp_path, {"a.md": "![logo](logo.svg)\n"})
    (repo / "tools" / "hugo" / "hugo.yaml").write_text(
        "contentDir: ../../records\ntheme: Postkasse\n", encoding="utf-8")
    wrong = repo / "tools" / "hugo" / "themes" / "Fuglekasse" / "static"
    wrong.mkdir(parents=True)
    (wrong / "logo.svg").write_bytes(b"<svg/>")
    report = verify.verify_repo(repo)
    assert report["ok"] is False
    assert report["faults"][0]["kind"] == "broken-reference"
    right = repo / "tools" / "hugo" / "themes" / "Postkasse" / "static"
    right.mkdir(parents=True)
    (right / "logo.svg").write_bytes(b"<svg/>")
    assert verify.verify_repo(repo)["ok"] is True
