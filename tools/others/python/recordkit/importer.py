# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Turn exported conversations into records (`records import`).

One internal shape — a Conversation of Turns — is all any source parser produces; the emitting
happens here and only through create.py/writer.py, which is what keeps an imported record
byte-identical to one written by `records new` + `records append-turn`.

Identity: the frontmatter pair `source:` + `sourceId:`, written together and only when the parser
supplies an id. A record carrying that pair is never imported twice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import create, frontmatter, writer

HUMAN = "human"
ASSISTANT = "assistant"


@dataclass
class Turn:
    """One side of a conversation. `model` signs an assistant turn; human turns leave it None."""
    role: str
    text: str
    model: str | None = None


@dataclass
class Conversation:
    """What every parser produces and nothing else. `kind` is a parser-supplied label for the
    import summary (item 5 reports how each file was classified); it never reaches the record."""
    turns: list = field(default_factory=list)
    title: str = ""
    date: datetime | None = None
    source_id: str | None = None
    tags: list = field(default_factory=list)
    kind: str = ""


def parsers() -> dict:
    """The source registry, imported late so sources.py can build on this module's shape."""
    from . import sources
    return sources.PARSERS


def imported_ids(records_dir: Path, source: str) -> dict:
    """Every `sourceId` already under records_dir for this source, mapped to its record."""
    found: dict = {}
    for record in sorted(Path(records_dir).rglob("*.md")):
        try:
            meta = frontmatter.read(record.read_text(encoding="utf-8"))
        except OSError:
            continue
        if meta.get("source") == source and meta.get("sourceId"):
            found[meta["sourceId"]] = record
    return found


def emit(records_dir: Path, conv: Conversation, source: str = "", tags: list | None = None,
         name: str | None = None, dry_run: bool = False) -> dict:
    """Write one conversation as a record. Explicit `tags` override the parser's."""
    tags = tags if tags else list(conv.tags)
    when = conv.date or datetime.now()
    title = conv.title.strip()
    identity = {"source": source, "sourceId": conv.source_id} if source and conv.source_id else None

    if dry_run:
        path = create.target_path(records_dir, title, when, tags)
    else:
        path = Path(create.new_record(records_dir, tags=tags, title=title,
                                      when=when, extra=identity)["path"])
        for turn in conv.turns:
            if turn.role == ASSISTANT:
                writer.append_assistant(path, turn.text, model=turn.model)
            else:
                writer.append_human(path, turn.text, name=name)

    return {"path": str(path), "title": title or path.stem, "source_id": conv.source_id,
            "turns": len(conv.turns), "kind": conv.kind}


def run(source: str, path: Path, records_dir: Path, tags: list | None = None,
        name: str | None = None, dry_run: bool = False) -> dict:
    """Parse `path` with the named source and emit every conversation it yields."""
    registry = parsers()
    parser = registry.get(source)
    if parser is None:
        raise ValueError(f"unknown source: {source} (known: {', '.join(sorted(registry))})")

    seen = imported_ids(records_dir, source)
    written: list = []
    skipped: list = []
    for conv in parser(Path(path)):
        if conv.source_id and conv.source_id in seen:
            skipped.append({"source_id": conv.source_id, "record": str(seen[conv.source_id])})
            continue
        result = emit(records_dir, conv, source=source, tags=tags, name=name, dry_run=dry_run)
        if conv.source_id:
            seen[conv.source_id] = Path(result["path"])
        written.append(result)

    return {"source": source, "path": str(path), "records_dir": str(records_dir),
            "dry_run": dry_run, "written": written, "skipped": skipped,
            "count": {"written": len(written), "skipped": len(skipped)}}

