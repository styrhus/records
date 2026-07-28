"""Advance the werden development cycle (/werden) — bump, derive number, stamp the docs."""

from __future__ import annotations

import os
import re
from json import loads
from pathlib import Path

_MARKER = re.compile(r"<!-- werden:[^>]*-->")
_FASE = re.compile(r"^> Fase — .*$", re.MULTILINE)

_SKIP_DIRS = {".git", "node_modules", "public", ".mem"}
# Dirs holding the marker as literal text (this mirror, the skill), repo-relative.
_SKIP_REL = ("tools/others/python", ".ai/skills/werden", ".claude/skills/werden")


def _pools(repo: Path) -> tuple[list[str], list[str]]:
    naming = repo / "tools" / "others" / "naming"
    animals = loads((naming / "dyr.json").read_text(encoding="utf-8"))
    structures = loads((naming / "strukturer.json").read_text(encoding="utf-8"))
    return animals, structures


def _read_state(state: Path) -> tuple[str, str]:
    """Return (number, name); legacy name-only CURRENT yields an empty number."""
    if not state.is_file():
        return "", ""
    parts = state.read_text(encoding="utf-8").split()
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return ("", parts[0]) if parts else ("", "")


def _stamp_docs(repo: Path, line: str) -> list[str]:
    """Rewrite every existing marker under repo; returns the touched repo-relative paths."""
    updated = []
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            f = Path(dirpath) / name
            rel = f.relative_to(repo).as_posix()
            if any(rel == s or rel.startswith(s + "/") for s in _SKIP_REL):
                continue
            try:
                raw = f.read_bytes()
            except OSError:
                continue
            if b"\0" in raw[:8192] or b"<!-- werden:" not in raw:
                continue
            text = raw.decode("utf-8", errors="surrogateescape")
            f.write_text(_MARKER.sub(line, text), encoding="utf-8", errors="surrogateescape")
            updated.append(rel)
    return sorted(updated)


def cycle(repo: Path, structure: str | None = None, stamp: bool = False) -> dict:
    """Mirror of .ai/skills/werden/werden.sh — same modes, same state file, same stamping."""
    repo = Path(repo)
    animals, structures = _pools(repo)
    state = repo / "CURRENT"
    old_num, old = _read_state(state)

    warnings = []
    epoch = old_num.split(".", 1)[0]
    if not epoch.isdigit():
        if old_num:
            warnings.append(f"epoch '{old_num}' not numeric; using 0")
        epoch = "0"

    if stamp:
        if not old:
            raise ValueError("--stamp needs an existing cycle in CURRENT, found none")
        struct, _, animal = old.rpartition("-")
    elif structure:
        struct, animal = structure, animals[0]
        if struct not in structures:
            warnings.append(f"'{struct}' is not in strukturer.json (using it anyway)")
    elif not old:
        struct, animal = structures[0], animals[0]
    else:
        struct, _, cur = old.rpartition("-")
        if cur not in animals:
            raise ValueError(f"current animal '{cur}' not found in dyr.json")
        idx = animals.index(cur) + 1
        if idx >= len(animals):
            raise ValueError(f"already at the last animal ('{cur}'); "
                             "pass a new structure name to start a new cycle")
        animal = animals[idx]

    new = f"{struct}-{animal}"
    maj = structures.index(struct) + 1 if struct in structures else 0
    num = f"{epoch}.{maj}.{animals.index(animal) + 1}"
    state.write_text(f"{num} {new}\n", encoding="utf-8")

    updated = _stamp_docs(repo, f"<!-- werden: {num} {new} -->")

    readme = repo / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    fase_line = bool(_FASE.search(text))
    if fase_line:
        readme.write_text(_FASE.sub(f"> Fase — {num} {new}", text), encoding="utf-8")

    result = {"old": f"{old_num} {old}".strip(), "new": f"{num} {new}",
              "state": str(state), "markers_updated": updated,
              "fase_line": fase_line, "stamp_only": stamp}
    if warnings:
        result["warnings"] = warnings
    return result
