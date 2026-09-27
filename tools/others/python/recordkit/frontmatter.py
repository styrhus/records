# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Build the record frontmatter block byte-for-byte as record/all/me write it; minimal edits for /stick."""

from __future__ import annotations

import re

# A YAML plain scalar may not open with an indicator, nor hold ': '. Titles come from people and
# from imports, so both cases are real: `Chapter 1: Beginnings`, `@readme.md#30-43`.
_YAML_INDICATORS = "-?:,[]{}#&*!|>'\"%@`"


def quote(value: str) -> str:
    """A YAML scalar: bare when it can be, double-quoted when a plain scalar would not parse.
    A ' #' inside a value opens a comment mid-scalar — the reader keeps everything before it and
    silently drops the rest — so it quotes too, wherever it falls, not just at the start."""
    text = str(value)
    if (not text or text[0] in _YAML_INDICATORS or text.endswith(":")
            or ": " in text or " #" in text or text.strip() != text):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def unquote(value: str) -> str:
    """The inverse of quote() for the simple scalars this module writes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        return re.sub(r"\\(.)", r"\1", inner) if value[0] == '"' else inner
    return value


def build(title: str, date_iso: str, tags: list[str] | None = None, draft: bool = False,
          extra: dict | None = None) -> str:
    """Frontmatter block: title, date, optional draft (before tags), optional tags, then any
    extra `key: value` lines (the importer's source/sourceId pair). Trailing newline."""
    lines = ["---", f"title: {quote(title)}", f"date: {date_iso}"]
    if draft:
        lines.append("draft: true")
    if tags:
        lines.append("tags: [" + ", ".join(tags) + "]")
    lines.extend(f"{k}: {quote(v)}" for k, v in (extra or {}).items())
    lines.append("---")
    return "\n".join(lines) + "\n"


def read(text: str) -> dict:
    """Top-level `key: value` lines of the frontmatter block, quoted scalars unquoted.
    Not a YAML parser — nested keys and multi-line values are skipped, by design (stdlib only)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep and key and not key[0].isspace():
            out[key.strip()] = unquote(value.strip())
    return out


def body(text: str) -> str:
    """Everything after the frontmatter block; the whole text when there is no block."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    return text if close is None else "\n".join(lines[close + 1:])


def feature(text: str) -> str:
    """Add `featured: true` (if absent) and drop any `draft: true` line, inside the frontmatter block.
    The body after the block is preserved byte-for-byte."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("no frontmatter block")
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if close is None:
        raise ValueError("unterminated frontmatter")
    block = [ln for ln in lines[1:close] if ln.strip() != "draft: true"]
    if not any(ln.strip().startswith("featured:") for ln in block):
        block.append("featured: true")
    return "\n".join(["---", *block, "---", *lines[close + 1:]])
