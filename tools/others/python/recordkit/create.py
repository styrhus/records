"""Create a new record file with frontmatter (the /record, /all, /me setup phase)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import frontmatter, naming


def new_record(records_dir: Path, arguments: str = "", draft: bool = False,
               tags: list[str] | None = None, title: str | None = None) -> dict:
    """Route by first tag into a subfolder, name from the title (or the timestamp), write frontmatter.
    Explicit tags/title override anything parsed from `arguments`."""
    parsed_tags, parsed_title = naming.extract_tags_title(arguments)
    tags = parsed_tags if tags is None else tags
    title = (parsed_title if title is None else title).strip()

    when = datetime.now()
    target_dir = Path(records_dir) / tags[0] if tags else Path(records_dir)

    if title:
        filename = naming.ensure_md(naming.slugify(title))
        display_title = title
    else:
        display_title = naming.now_stamp(when)
        filename = f"{display_title}.md"

    target_dir.mkdir(parents=True, exist_ok=True)
    path = naming.unique_path(target_dir, filename)
    path.write_text(
        frontmatter.build(display_title, naming.now_iso(when), tags=tags, draft=draft),
        encoding="utf-8",
    )
    return {"path": str(path), "title": display_title, "tags": tags, "draft": draft}
