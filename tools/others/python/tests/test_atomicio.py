import os
import stat

import pytest

from recordkit.atomicio import atomic_write_text


def test_writes_the_new_content(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("before")
    atomic_write_text(f, "after")
    assert f.read_text() == "after"


def test_creates_a_new_file(tmp_path):
    f = tmp_path / "new.md"
    atomic_write_text(f, "hello")
    assert f.read_text() == "hello"


def test_no_leftover_temp_file(tmp_path):
    f = tmp_path / "r.md"
    atomic_write_text(f, "content")
    assert [p.name for p in tmp_path.iterdir()] == ["r.md"]


def test_preserves_permissions_of_existing_file(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("before")
    f.chmod(0o600)
    atomic_write_text(f, "after")
    assert stat.S_IMODE(f.stat().st_mode) == 0o600


def test_original_untouched_when_the_write_fails(tmp_path, monkeypatch):
    f = tmp_path / "r.md"
    f.write_text("original")

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(os, "fsync", boom)
    with pytest.raises(OSError):
        atomic_write_text(f, "new content")
    assert f.read_text() == "original"
    assert [p.name for p in tmp_path.iterdir()] == ["r.md"]  # no leftover temp file


def test_original_untouched_when_the_mode_copy_fails(tmp_path, monkeypatch):
    f = tmp_path / "r.md"
    f.write_text("original")

    def boom(*a, **k):
        raise OSError("no fchmod here")

    monkeypatch.setattr(os, "fchmod", boom)
    with pytest.raises(OSError):
        atomic_write_text(f, "new content")
    assert f.read_text() == "original"
    assert [p.name for p in tmp_path.iterdir()] == ["r.md"]  # no leftover temp file
