"""Feature a record (/stick): locate it, add `featured: true`, drop any `draft:`."""

from __future__ import annotations

from pathlib import Path

from . import frontmatter, naming


def find_record(records_dir: Path, slug_or_name: str) -> list[Path]:
    """Slugify the argument and search the records tree for that filename (may return several)."""
    return sorted(Path(records_dir).rglob(naming.ensure_md(naming.slugify(slug_or_name))))


def feature_file(path: Path) -> dict:
    p = Path(path)
    p.write_text(frontmatter.feature(p.read_text(encoding="utf-8")), encoding="utf-8")
    return {"path": str(p), "featured": True}
