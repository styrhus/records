"""Find and resolve the local files a record points at — the one scanner archive/verify/export share.

Only asset references count: Markdown images and raw `src=` attributes (records are
`unsafe: true`, so raw HTML in a record is real markup). Markdown *links* are deliberately
excluded — `[see](2026-07-06_23-21)` is a valid site URL, not a file, and flagging it would
make `records verify` cry wolf.

Resolution mirrors book.lua's resolveLocal: record dir, records root, site static, theme static.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from .config import DEFAULT_THEME

TARGET = r"\(\s*(?:<([^>]*)>|([^)\s]+))[^)]*\)"  # the <angle> form may hold spaces
MD_IMAGE = re.compile(r"!\[[^\]]*\]" + TARGET)
SRC_ATTR = re.compile(r"""<(?:img|video|audio|source|embed)\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']""",
                       re.IGNORECASE)
MD_LINK = re.compile(r"(?<!!)\[([^\]]*)\]" + TARGET)
_ABSOLUTE = ("http://", "https://", "//", "data:", "mailto:", "#", "/")


def is_local(target: str) -> bool:
    """A reference resolvable to a file beside the record — not a URL, anchor or site-absolute path."""
    t = (target or "").strip()
    return bool(t) and not t.lower().startswith(_ABSOLUTE)


def asset_references(text: str) -> list[str]:
    """Local image/media targets in a record, in document order, deduplicated."""
    seen: dict[str, None] = {}
    for m in MD_IMAGE.finditer(text):
        t = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
        if is_local(t):
            seen.setdefault(t, None)
    for target in SRC_ATTR.findall(text):
        t = target.strip()
        if is_local(t):
            seen.setdefault(t, None)
    return list(seen)


def links(text: str) -> list[tuple[str, str]]:
    """(label, target) for every Markdown link — used by the plain-text export, not by verify."""
    return [(m.group(1), (m.group(2) if m.group(2) is not None else m.group(3)).strip())
            for m in MD_LINK.finditer(text)]


def search_dirs(record: Path, records_dir: Path, root: Path | None = None,
                theme: str = DEFAULT_THEME) -> list[Path]:
    """Where a relative reference is looked for, in book.lua's order."""
    dirs = [Path(record).parent, Path(records_dir)]
    if root:
        dirs += [Path(root) / "tools" / "hugo" / "static",
                 Path(root) / "tools" / "hugo" / "themes" / theme / "static"]
    return dirs


def resolve(target: str, record: Path, records_dir: Path, root: Path | None = None,
            theme: str = DEFAULT_THEME) -> Path | None:
    """The first existing file for a local reference, or None when nothing matches."""
    candidate = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not candidate:
        return None
    for d in search_dirs(record, records_dir, root, theme):
        p = d / candidate
        if p.is_file():
            return p.resolve()
    return None
