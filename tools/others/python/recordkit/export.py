"""The last resort: the whole corpus as plain text that needs no tooling at all.

Markdown is already readable, but not *only* readable — it has syntax that means something else
when rendered, and a reader in twenty years should not have to know which. So headings become
labelled turns, links carry their URL inline, images say what they were, code fences become indented
blocks, and emphasis markers go away.

If this output needs this repo to make sense, it has failed.

WIRING (deferred — parallel-session rule, see docs/records/developers/roadmap/README.md):

    ex = sub.add_parser("export", help="write the whole corpus as plain text")
    ex.add_argument("--repo", default=".")
    ex.add_argument("--format", default="text", choices=["text"])
    ex.add_argument("--out", required=True, help="directory for the tree, or the file with --single")
    ex.add_argument("--single", action="store_true", help="one concatenated file with a contents list")

    elif args.cmd == "export":
        _emit(export.export(Path(args.repo), Path(args.out), single=args.single))
"""

from __future__ import annotations

import re
from pathlib import Path

from . import frontmatter, refs

_RULE = "=" * 76
_THIN = "-" * 76

_TURN = re.compile(r"^##\s+(Human|User|Assistant)\b\s*(?:\(([^)]*)\))?\s*$", re.IGNORECASE)
_SIGNATURE = re.compile(r"^—\s*(.+)$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_EMPHASIS = re.compile(r"(\*\*|__|\*|_|`)")
_BULLET = re.compile(r"^(\s*)[-*+]\s+")
_STAMP = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})")


def record_date(path: Path, meta: dict) -> str:
    """The site's rule: `date:` frontmatter is authoritative, the filename timestamp is the fallback."""
    value = (meta.get("date") or "").strip().strip('"').strip("'")
    if value:
        return value
    m = _STAMP.search(Path(path).stem if Path(path).stem != "index" else Path(path).parent.name)
    return f"{m.group(1)} {m.group(2)}:{m.group(3)}" if m else ""


def _sort_key(entry: dict) -> str:
    return entry["date"] or "0000"


def _inline(text: str) -> str:
    """Links keep their URL, images say what they were, emphasis markers go."""
    def image(m):
        target = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
        return f"[image: {target}]"

    def link(m):
        label = m.group(1).strip()
        target = (m.group(2) if m.group(2) is not None else m.group(3)).strip()
        if not label:
            return f"<{target}>"
        return label if target.startswith("#") else f"{label} <{target}>"

    text = refs.MD_IMAGE.sub(image, text)
    text = refs.MD_LINK.sub(link, text)
    return _EMPHASIS.sub("", text)


def plain_body(body: str) -> str:
    """A record's turns as labelled plain text — the heart of the format."""
    out: list[str] = []
    in_fence = False

    def push(line: str) -> None:
        """Runs of blank lines collapse to one — the source's spacing is Markdown's, not a reader's."""
        if line.strip() or (out and out[-1].strip()):
            out.append(line)

    for line in body.split("\n"):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            out.append("    " + line)
            continue
        turn = _TURN.match(line)
        if turn:
            who = turn.group(1).capitalize()
            who = "Human" if who.lower() == "user" else who
            speaker = f"{who} ({turn.group(2)})" if turn.group(2) else who
            if out and out[-1].strip():
                out.append("")
            out += [_THIN, f"{speaker.upper()} SAID:", _THIN, ""]
            continue
        sig = _SIGNATURE.match(line.strip())
        if sig:
            push(f"[written by the AI model: {sig.group(1).strip()}]")
            continue
        heading = _HEADING.match(line)
        if heading:
            push(_inline(heading.group(2)).upper())
            continue
        push(_BULLET.sub(r"\1  * ", _inline(line)))  # bullets last: _inline strips '*'
    return "\n".join(out).strip("\n")


def render(path: Path, text: str, meta: dict, date: str) -> str:
    """One record: a plain header block, then the conversation."""
    title = (meta.get("title") or Path(path).stem).strip().strip('"').strip("'")
    header = [_RULE, title, _RULE, ""]
    if date:
        header.append(f"Date:  {date}")
    tags = (meta.get("tags") or "").strip().strip("[]")
    if tags:
        header.append(f"Tags:  {tags}")
    header.append(f"File:  {path}")
    header.append("")
    return "\n".join(header) + "\n" + plain_body(frontmatter.body(text)) + "\n"


def collect(records_dir: Path) -> list[dict]:
    """Every non-draft record, oldest first — the order the site reads them in."""
    entries = []
    for f in sorted(records_dir.rglob("*.md")):
        stem = f.stem
        if stem in ("_index", "LICENSE", "404"):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        meta = frontmatter.read(text)
        if (meta.get("draft") or "").strip().lower() == "true":
            continue
        rel = f.relative_to(records_dir)
        name = rel.parent.name if stem == "index" and rel.parent.name else stem
        entries.append({"path": f, "rel": rel.as_posix(), "name": name, "text": text,
                        "meta": meta, "date": record_date(f, meta)})
    entries.sort(key=_sort_key)
    return entries


def export(repo: Path = Path("."), out: Path = Path("export"), single: bool = False) -> dict:
    """Write the corpus as a text tree, or as one concatenated file with a contents list."""
    from . import archive as archive_mod

    _root, records_dir, _cfg = archive_mod.resolve_repo(Path(repo))
    entries = collect(records_dir)
    out = Path(out)
    written: list[str] = []

    if single:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_single_document(entries), encoding="utf-8")
        written.append(str(out))
    else:
        for e in entries:
            target = out / Path(e["rel"]).with_suffix(".txt")
            if Path(e["rel"]).name == "index.md":
                target = out / Path(e["rel"]).parent.with_suffix(".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render(e["rel"], e["text"], e["meta"], e["date"]), encoding="utf-8")
            written.append(str(target))

    return {"records_dir": str(records_dir), "out": str(out), "single": single,
            "records": len(entries), "written": len(written), "files": written}


def _single_document(entries: list[dict]) -> str:
    parts = [_RULE, "A COLLECTION OF CONVERSATIONS", _RULE, "",
             "Plain text. Nothing needs to be installed to read this file.",
             "Each conversation below is introduced by a line of = signs, and alternates",
             "between what a person said and what an AI assistant replied. A line reading",
             "'[written by the AI model: ...]' names the model that produced the reply above",
             "it; it is not part of what was said.", "",
             f"{len(entries)} conversations, oldest first.", "", "CONTENTS", _THIN]
    for i, e in enumerate(entries, 1):
        title = (e["meta"].get("title") or e["name"]).strip().strip('"').strip("'")
        parts.append(f"{i:4}. {title}" + (f"   ({e['date']})" if e["date"] else ""))
    parts += ["", ""]
    for i, e in enumerate(entries, 1):
        parts.append(render(e["rel"], e["text"], e["meta"], e["date"]))
        parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n"
