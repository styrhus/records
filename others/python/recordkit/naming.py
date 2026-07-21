"""Tag/title parsing, slugs, unique paths, timestamps — ported from the record/all/me setup."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_TAG_DROP = re.compile(r"[^a-z0-9-]")
_WS = re.compile(r"\s+")


def now_stamp(when: datetime | None = None) -> str:
    """Filename timestamp, matching `date +%Y-%m-%d_%H-%M`."""
    return (when or datetime.now()).strftime("%Y-%m-%d_%H-%M")


def now_iso(when: datetime | None = None) -> str:
    """Frontmatter date, matching `date -Iseconds` (local offset, second precision)."""
    return (when or datetime.now()).astimezone().isoformat(timespec="seconds")


def extract_tags_title(arguments: str) -> tuple[list[str], str]:
    """Split leading #tags from the title. Tags are the leading #word tokens only; the first
    token not starting with # ends the tag run, and the remainder is the title verbatim."""
    rest = (arguments or "").lstrip()
    tags: list[str] = []
    while rest.startswith("#"):
        m = re.match(r"(\S+)\s*(.*)", rest, re.DOTALL)
        token, rest = m.group(1), m.group(2)
        tag = _clean_tag(token)
        if tag:
            tags.append(tag)
    return tags, rest.rstrip()


def _clean_tag(token: str) -> str:
    """Strip the leading #, lowercase, drop any char that is not a letter, digit or hyphen."""
    return _TAG_DROP.sub("", token[1:].lower())


def slugify(title: str) -> str:
    """Lowercase and collapse whitespace runs into single hyphens (record/all/me/stick rule)."""
    return _WS.sub("-", title.strip().lower())


def ensure_md(name: str) -> str:
    return name if name.endswith(".md") else name + ".md"


def unique_path(directory: Path, filename: str) -> Path:
    """Never overwrite: append -1, -2, … before .md if the name is already taken."""
    stem, dot, ext = filename.rpartition(".")
    if not dot:
        stem, ext = filename, ""
    candidate = directory / filename
    n = 1
    while candidate.exists():
        candidate = directory / (f"{stem}-{n}.{ext}" if ext else f"{stem}-{n}")
        n += 1
    return candidate
