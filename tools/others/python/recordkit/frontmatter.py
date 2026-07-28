"""Build the record frontmatter block byte-for-byte as record/all/me write it; minimal edits for /stick."""

from __future__ import annotations


def build(title: str, date_iso: str, tags: list[str] | None = None, draft: bool = False) -> str:
    """Frontmatter block: title, date, optional draft (before tags), optional tags. Trailing newline."""
    lines = ["---", f"title: {title}", f"date: {date_iso}"]
    if draft:
        lines.append("draft: true")
    if tags:
        lines.append("tags: [" + ", ".join(tags) + "]")
    lines.append("---")
    return "\n".join(lines) + "\n"


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
