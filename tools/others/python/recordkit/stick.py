"""Feature a record (/stick): locate it, add `featured: true`, drop any `draft:`."""

from __future__ import annotations

from pathlib import Path

from . import frontmatter, naming


def find_record(records_dir: Path, slug_or_name: str) -> list[Path]:
    """Slugify the argument and search the records tree for that record (may return several).

    A record is either `<slug>.md` or a leaf bundle's `<slug>/index.md` — `records attach` turns the
    first into the second, and the URL does not change, so neither should what /stick can find.
    """
    root = Path(records_dir)
    slug = naming.slugify(slug_or_name)
    flat = root.rglob(naming.ensure_md(slug))
    bundled = (d / "index.md" for d in root.rglob(slug) if d.is_dir())
    return sorted(p for p in (*flat, *bundled) if p.is_file())


def feature_file(path: Path) -> dict:
    p = Path(path)
    p.write_text(frontmatter.feature(p.read_text(encoding="utf-8")), encoding="utf-8")
    return {"path": str(p), "featured": True}
