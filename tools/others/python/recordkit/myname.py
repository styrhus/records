"""Persist the user's name (/myname). Memory defaults to a gitignored .mem/ beside the records content."""

from __future__ import annotations

from pathlib import Path

from .config import resolve_records_dir

_NOTE = """---
name: user-name
description: The user's name
metadata:
  type: user
---

The user's name is {name}.
"""
_POINTER_PREFIX = "- [User's name](user-name.md)"
_POINTER = _POINTER_PREFIX + " — the user is {name}\n"


def default_memory_dir() -> Path:
    """Local, gitignored `.mem/` next to the records content — cross-platform, per-checkout."""
    return resolve_records_dir(Path(".")).parent / ".mem"


def save(name: str, memory_dir: Path | None = None) -> dict:
    name = name.strip()
    if not name:
        raise ValueError("name required")
    d = Path(memory_dir) if memory_dir else default_memory_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "user-name.md").write_text(_NOTE.format(name=name), encoding="utf-8")
    _upsert_pointer(d / "MEMORY.md", name)
    return {"name": name, "memory_dir": str(d)}


def _upsert_pointer(memory_md: Path, name: str) -> None:
    line = _POINTER.format(name=name)
    if not memory_md.exists():
        memory_md.write_text("# Memory index\n\n" + line, encoding="utf-8")
        return
    kept = [ln for ln in memory_md.read_text(encoding="utf-8").splitlines(keepends=True)
            if not ln.startswith(_POINTER_PREFIX)]
    if kept and not kept[-1].endswith("\n"):
        kept[-1] += "\n"
    kept.append(line)
    memory_md.write_text("".join(kept), encoding="utf-8")
