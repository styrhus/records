"""Resolve the records directory the way the record/all/me/cpd skills do."""

from __future__ import annotations

import re
from pathlib import Path

_PRUNE = {"node_modules"}
_DOCS_NAMES = ["docs", "doc", "documentation", "notes"]
_MAXDEPTH = 5
_CONTENTDIR = re.compile(r"^contentDir:\s*(.*?)\s*(?:#.*)?$")


def find_hugo_configs(start: Path) -> list[Path]:
    """All */hugo/hugo.yaml under `start` (maxdepth 5, dot-dirs and node_modules pruned), shallowest first."""
    start = Path(start)
    found: list[Path] = []

    def walk(d: Path, depth: int) -> None:
        try:
            entries = sorted(d.iterdir())
        except OSError:
            return
        for e in entries:
            edepth = depth + 1
            if e.is_dir():
                if edepth >= _MAXDEPTH or e.name.startswith(".") or e.name in _PRUNE:
                    continue
                walk(e, edepth)
            elif e.name == "hugo.yaml" and e.parent.name == "hugo" and edepth <= _MAXDEPTH:
                found.append(e)

    walk(start, 0)
    found.sort(key=lambda p: len(p.resolve().parts))
    return found


def checkout_root(hugo_yaml: Path) -> Path:
    """The checkout holding hugo/: its parent, or grandparent when nested in tools/."""
    parent = Path(hugo_yaml).parent.parent
    return parent.parent if parent.name == "tools" else parent


def read_content_dir(hugo_yaml: Path) -> str:
    """First `contentDir:` value in the config, or '../records' when the line is absent."""
    try:
        for line in Path(hugo_yaml).read_text(encoding="utf-8").splitlines():
            m = _CONTENTDIR.match(line)
            if m:
                return m.group(1).strip().strip('"').strip("'") or "../records"
    except OSError:
        pass
    return "../records"


def resolve_records_dir(start: Path = Path(".")) -> Path:
    """The records content directory, following the skills' priority order."""
    start = Path(start)
    configs = find_hugo_configs(start)
    if configs:
        hugo_yaml = configs[0]
        return (hugo_yaml.parent / read_content_dir(hugo_yaml)).resolve()
    if (start / "records").is_dir():
        return (start / "records").resolve()
    if (start / "docs").is_dir():
        return (start / "docs" / "records").resolve()
    for name in _DOCS_NAMES[1:]:
        if (start / name).is_dir():
            return (start / name / "records").resolve()
    children = sorted(c for c in start.iterdir() if c.is_dir() and not c.name.startswith(".")) \
        if start.is_dir() else []
    for name in _DOCS_NAMES:
        for child in children:
            if (child / name).is_dir():
                return (child / name / "records").resolve()
    return (start / "records").resolve()
