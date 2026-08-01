"""Put a file into a record — the ergonomics of the leaf-bundle convention.

Converting a flat `<slug>.md` into `<slug>/index.md` and copying a file beside it is a four-step
dance by hand, and nobody does a four-step dance twice. This does the whole move in one call and
leaves the record's URL unchanged, because Hugo resolves a leaf bundle to its folder name.

The source file is copied, never moved: what you attached stays where it was.

"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import naming, writer

_IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp"}
_VIDEO = {".mp4", ".webm", ".ogv", ".mov", ".m4v"}
_AUDIO = {".mp3", ".ogg", ".oga", ".wav", ".flac", ".m4a", ".opus"}


def resolve_record(record: Path) -> tuple[Path, bool]:
    """(the record's .md path, is it already a bundle). Accepts a flat file, a bundle or a folder."""
    p = Path(record)
    if p.is_dir():
        index = p / "index.md"
        if not index.is_file():
            raise RuntimeError(f"{p} is a directory without an index.md — not a record")
        return index, True
    if p.name == "index.md":
        if not p.is_file():
            raise RuntimeError(f"{p} does not exist")
        return p, True
    if not p.is_file():
        raise RuntimeError(f"{p} does not exist")
    if p.suffix != ".md":
        raise RuntimeError(f"{p} is not a Markdown record")
    return p, False


def markdown_for(name: str, title: str | None = None) -> str:
    """The line to paste: images inline, video and audio as players, anything else as a link."""
    suffix = Path(name).suffix.lower()
    label = title or Path(name).stem.replace("-", " ")
    if suffix in _IMAGE:
        return f"![{label}]({name})"
    if suffix in _VIDEO:
        return f'<video src="{name}" controls></video>'
    if suffix in _AUDIO:
        return f'<audio src="{name}" controls></audio>'
    return f"[{label}]({name})"


def _bundle_dir(record: Path) -> Path:
    """Where a flat record becomes a bundle: <slug>/ beside <slug>.md."""
    return record.parent / record.stem


def convert(record: Path, dry_run: bool = False) -> Path:
    """Flat `<slug>.md` → `<slug>/index.md`, bytes untouched. Returns the new record path."""
    target_dir = _bundle_dir(record)
    if target_dir.exists():
        raise RuntimeError(f"cannot convert {record}: {target_dir} already exists")
    index = target_dir / "index.md"
    if dry_run:
        return index
    target_dir.mkdir(parents=True)
    record.replace(index)  # rename: the record's bytes are never rewritten
    return index


def attach(record: Path, files: list[Path], title: str | None = None,
           append: bool = False, dry_run: bool = False) -> dict:
    """Convert the record to a bundle if needed, copy the files in, return the Markdown to paste."""
    src_record, is_bundle = resolve_record(record)
    sources = [Path(f) for f in files]
    for f in sources:
        if not f.is_file():
            raise RuntimeError(f"{f} does not exist — nothing to attach")

    converted = not is_bundle
    index = convert(src_record, dry_run) if converted else src_record
    bundle = index.parent

    attached = []
    taken: set[str] = set()
    for f in sources:
        name = naming.slug_filename(f.name)
        dest = _free_path(bundle, name, taken, dry_run)
        taken.add(dest.name)
        if not dry_run:
            shutil.copy2(f, dest)  # copy, never move — the source stays where it was
        attached.append({"source": str(f), "path": str(dest), "name": dest.name,
                         "markdown": markdown_for(dest.name, title)})

    block = "\n\n".join(a["markdown"] for a in attached)
    if append and not dry_run:
        writer.append_block(index, block)

    return {"record": str(index), "bundle": str(bundle), "converted": converted,
            "was_bundle": is_bundle, "attached": attached, "markdown": block,
            "appended": bool(append and not dry_run), "dry_run": dry_run}


def _free_path(bundle: Path, name: str, taken: set[str], dry_run: bool) -> Path:
    """naming.unique_path, plus the names claimed earlier in this same call (dry runs create nothing)."""
    candidate = naming.unique_path(bundle, name)
    if candidate.name not in taken:
        return candidate
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    n = 1
    while True:
        alt = f"{stem}-{n}.{ext}" if ext else f"{stem}-{n}"
        if alt not in taken and not (bundle / alt).exists():
            return bundle / alt
        n += 1
