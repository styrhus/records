# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Create a new record file with frontmatter (the /record, /all, /me setup phase)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import frontmatter, naming


def target_path(records_dir: Path, title: str = "", when: datetime | None = None,
                tags: list[str] | None = None, bundle: bool = False) -> Path:
    """The path new_record would write to, computed without creating anything (import --dry-run).
    A bundle is a Hugo leaf page bundle — <slug>/index.md — so the record can carry files beside it;
    the URL is identical either way (:contentbasename resolves a bundle to its folder name)."""
    target_dir = Path(records_dir) / tags[0] if tags else Path(records_dir)
    stem = naming.slugify(title) if title.strip() else naming.now_stamp(when or datetime.now())
    if bundle:
        return naming.unique_path(target_dir, stem) / "index.md"
    return naming.unique_path(target_dir, naming.ensure_md(stem))


def new_record(records_dir: Path, arguments: str = "", draft: bool = False,
               tags: list[str] | None = None, title: str | None = None,
               when: datetime | None = None, extra: dict | None = None,
               bundle: bool = False) -> dict:
    """Route by first tag into a subfolder, name from the title (or the timestamp), write frontmatter.
    Explicit tags/title override anything parsed from `arguments`. `when` is the record's timestamp
    (imports carry the source's, not now); `extra` adds frontmatter lines after tags; `bundle`
    writes <slug>/index.md so the record can carry attachments."""
    parsed_tags, parsed_title = naming.extract_tags_title(arguments)
    tags = parsed_tags if tags is None else tags
    title = (parsed_title if title is None else title).strip()

    when = when or datetime.now()
    display_title = title if title else naming.now_stamp(when)

    path = target_path(records_dir, title, when, tags, bundle=bundle)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        frontmatter.build(display_title, naming.now_iso(when), tags=tags, draft=draft, extra=extra),
        encoding="utf-8",
    )
    return {"path": str(path), "title": display_title, "tags": tags, "draft": draft,
            "bundle": bundle}
