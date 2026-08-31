"""Feature a record (/stick): locate it, add `featured: true`, drop any `draft:`."""

from __future__ import annotations

from pathlib import Path

from . import frontmatter, naming
from .config import resolve_records_dir


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


def find_record_in_checkout(start: Path, slug_or_name: str) -> list[Path]:
    """Checkout-aware find_record: resolve the records dir the way /record, /all, /me and /cpd
    do — from `start` (the caller's cwd), not an assumed $PWD-relative `records/` — then search it.
    Same fallback a caller gets for free by passing `records_dir=None` to booth/myname/doctor/watch."""
    return find_record(resolve_records_dir(Path(start)), slug_or_name)


def feature_file(path: Path) -> dict:
    p = Path(path)
    p.write_text(frontmatter.feature(p.read_text(encoding="utf-8")), encoding="utf-8")
    return {"path": str(p), "featured": True}
