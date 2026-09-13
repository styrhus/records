"""Resolve the records directory the way the record/all/me/cpd skills do."""

from __future__ import annotations

import re
from pathlib import Path

_PRUNE = {"node_modules"}
_DOCS_NAMES = ["docs", "doc", "documentation", "notes"]
_MAXDEPTH = 5
_CONTENTDIR = re.compile(r"^contentDir:\s*(.*?)\s*(?:#.*)?$")
DEFAULT_THEME = "Fuglekasse"  # book.lua's fallback — keep in sync
_THEME = re.compile(r"^theme:\s*(.*?)\s*(?:#.*)?$")


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


def read_theme(hugo_yaml: Path, default: str = DEFAULT_THEME) -> str:
    """First `theme:` value in the config, or `default` when the line is absent."""
    try:
        for line in Path(hugo_yaml).read_text(encoding="utf-8").splitlines():
            m = _THEME.match(line)
            if m:
                return m.group(1).strip().strip('"').strip("'") or default
    except OSError:
        pass
    return default


def discover_records_dir(start: Path = Path(".")) -> tuple[Path, bool]:
    """(records content directory, discovered?) — the skills' priority order, and whether
    anything in the checkout actually pointed at the answer.

    Every rung but the last is a discovery: a site config's contentDir, or a directory that
    is there on disk. The last rung is an assumption — `<start>/records`, the conventional
    name, returned whether or not it exists. It has to stay, because it is also the right
    answer for a fresh clone where the directory has not been created yet and `records new`
    is about to create it. What it must not do is look like a finding, which is what the
    second element is for: callers that need certainty can ask, and `records config` and
    `records doctor` say which of the two answers they are giving.
    """
    start = Path(start)
    configs = find_hugo_configs(start)
    if configs:
        hugo_yaml = configs[0]
        return (hugo_yaml.parent / read_content_dir(hugo_yaml)).resolve(), True
    if (start / "records").is_dir():
        return (start / "records").resolve(), True
    if (start / "docs").is_dir():
        return (start / "docs" / "records").resolve(), True
    for name in _DOCS_NAMES[1:]:
        if (start / name).is_dir():
            return (start / name / "records").resolve(), True
    children = sorted(c for c in start.iterdir() if c.is_dir() and not c.name.startswith(".")) \
        if start.is_dir() else []
    for name in _DOCS_NAMES:
        for child in children:
            if (child / name).is_dir():
                return (child / name / "records").resolve(), True
    return (start / "records").resolve(), False


def resolve_records_dir(start: Path = Path(".")) -> Path:
    """The records content directory, following the skills' priority order.

    Answers without saying whether it found the directory or assumed it —
    `discover_records_dir` is the one to use when that difference matters.
    """
    return discover_records_dir(start)[0]
