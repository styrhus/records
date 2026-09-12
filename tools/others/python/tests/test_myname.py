import os
import stat
from pathlib import Path

import pytest

from recordkit import myname


def test_save_writes_note_and_pointer(tmp_path):
    r = myname.save("Ada Lovelace", memory_dir=tmp_path)
    assert r == {"name": "Ada Lovelace", "memory_dir": str(tmp_path)}
    assert "The user's name is Ada Lovelace." in (tmp_path / "user-name.md").read_text()
    assert (tmp_path / "MEMORY.md").read_text().count("user-name.md") == 1


def test_save_pointer_is_idempotent(tmp_path):
    myname.save("Ada", memory_dir=tmp_path)
    myname.save("Grace", memory_dir=tmp_path)
    ptr = (tmp_path / "MEMORY.md").read_text()
    assert ptr.count("[User's name](user-name.md)") == 1
    assert "the user is Grace" in ptr


def test_empty_name_rejected(tmp_path):
    with pytest.raises(ValueError):
        myname.save("   ", memory_dir=tmp_path)


def test_load_roundtrip(tmp_path):
    myname.save("Ada Lovelace", memory_dir=tmp_path)
    assert myname.load(memory_dir=tmp_path) == "Ada Lovelace"


def test_load_missing_returns_none(tmp_path):
    assert myname.load(memory_dir=tmp_path) is None


# --- the pointer rewrite is atomic --------------------------------------------
#
# `_upsert_pointer` reads `.mem/MEMORY.md`, drops its own line and writes every other line
# back. Those other lines are the user's — memories `/myname` never wrote. A truncate-then-write
# that dies in the middle takes them with it, which is the gap 1 class.

def _break_the_swap(monkeypatch, name):
    """Fail `os.replace` for one target only, so the rest of a run behaves normally."""
    real = os.replace

    def guard(src, dst, *a, **k):
        if Path(dst).name == name:
            raise OSError("swap failed")
        return real(src, dst, *a, **k)

    monkeypatch.setattr(os, "replace", guard)


def test_the_index_survives_a_failed_pointer_write(tmp_path, monkeypatch):
    myname.save("Ada", memory_dir=tmp_path)
    index = tmp_path / "MEMORY.md"
    index.write_text(index.read_text(encoding="utf-8") + "- [Other](other.md) — not ours\n",
                     encoding="utf-8")
    before = index.read_text(encoding="utf-8")

    _break_the_swap(monkeypatch, "MEMORY.md")
    with pytest.raises(OSError):
        myname.save("Grace", memory_dir=tmp_path)

    assert index.read_text(encoding="utf-8") == before
    assert sorted(q.name for q in tmp_path.iterdir()) == ["MEMORY.md", "user-name.md"]  # no temp


def test_upserting_keeps_the_index_permissions(tmp_path):
    myname.save("Ada", memory_dir=tmp_path)
    index = tmp_path / "MEMORY.md"
    index.chmod(0o640)
    myname.save("Grace", memory_dir=tmp_path)
    assert stat.S_IMODE(index.stat().st_mode) == 0o640
    assert "the user is Grace" in index.read_text(encoding="utf-8")
