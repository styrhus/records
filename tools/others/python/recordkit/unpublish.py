# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pull a record out of the published world without pretending it never existed.

One mechanism, not two: `draft: true` in the record's own frontmatter. Hugo skips drafts by
default (`bin/build.sh` never passes -D) and `tools/pandoc/book.lua` skips them too — it reads each
record's frontmatter and drops anything whose `draft` is true, so the PDF, EPUB and booklet lose the
record for free. `build.list: never` plus `build.render: never` would work for Hugo alone, but they
are nested keys: book.lua does not read them, and neither does this engine's frontmatter reader.
The flat key is the one both sides already honour, and it is visible in a diff.

A second flat key, `unpublished: <timestamp>`, marks who did it, so `--restore` can tell an
unpublished record from a draft someone wrote by hand. A record that is already a draft is refused
rather than silently swallowed — restoring it would publish something that never was published.

`--tombstone` puts a stub at the old URL: the tombstone takes over the record's filename (the URL
comes from the filename, via permalinks `/:contentbasename/`) and the record itself moves next to it
as `<name>.withdrawn.md`, still carrying `draft: true`. Same one mechanism, still reversible.

Border: nothing here touches git, and nothing here claims erasure. Every path reports what remains.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import frontmatter, naming
from .atomicio import atomic_write_text
from .attach import resolve_record
from .stick import find_record

DRAFT_LINE = "draft: true"
MARK = "unpublished"
TOMBSTONE_KEY = "tombstone"
TOMBSTONE_TITLE = "Withdrawn"
STASH_INFIX = ".withdrawn"

TOMBSTONE_BODY = """\
A record was published at this address and has been withdrawn on {date}.

Nothing has been erased. The conversation is still in this repository's git history, in every
clone and fork made before now, and in whatever caches and archives already hold a copy.
"""


def remains(path: Path) -> list[str]:
    """What unpublishing does not reach. Part of every result; never suppressible."""
    return [
        f"git history keeps every version of this record — `git log -p -- {path}` still shows it",
        "any clone, fork or mirror made before now still has it in full",
        "the forge's own caches, search indexes and web archives are outside this repository",
        "the live site and the pages branch carry it until the next build and publish",
    ]


# bin/build.sh passes --cleanDestinationDir, so a rebuild drops the record's old page from the
# output dir; a hand-run `hugo` does not clean, so the advice names the script, not hugo.
NEXT = [
    "bin/build.sh — rebuild the site and the books; it cleans the output dir, "
    "so the record's old page leaves with it (a plain `hugo` run does not clean)",
    "records publish — deliver; publishTarget pages-branch force-pushes one commit built "
    "from that output dir, so the page leaves the branch with it",
    "records unpublish <record> --restore — put it back",
]


# ------------------------------------------------------------------ frontmatter

def _split(text: str) -> tuple[list[str], list[str]]:
    """(frontmatter lines without the fences, everything after). Raises when there is no block."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise RuntimeError("no frontmatter block — not a record this can unpublish")
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if close is None:
        raise RuntimeError("unterminated frontmatter")
    return lines[1:close], lines[close + 1:]


def _join(block: list[str], rest: list[str]) -> str:
    return "\n".join(["---", *block, "---", *rest])


def _clean(block: list[str]) -> list[str]:
    """Drop the two keys this module owns, so marking is idempotent and unmarking is complete."""
    return [ln for ln in block
            if ln.strip() != DRAFT_LINE and not ln.strip().startswith(MARK + ":")]


def mark(text: str, stamp: str) -> str:
    """Add `draft: true` and `unpublished: <stamp>`. The body is preserved byte-for-byte."""
    block, rest = _split(text)
    return _join([*_clean(block), DRAFT_LINE, f"{MARK}: {stamp}"], rest)


def unmark(text: str) -> str:
    """The inverse: both keys gone, the body preserved byte-for-byte."""
    block, rest = _split(text)
    return _join(_clean(block), rest)


def is_unpublished(text: str) -> bool:
    meta = frontmatter.read(text)
    return bool(meta.get(MARK)) and meta.get("draft") == "true"


def tombstone_text(original: str, stamp: str) -> str:
    """The stub that takes the record's place: the old date, no old title, no old words."""
    meta = frontmatter.read(original)
    date = meta.get("date") or stamp
    head = frontmatter.build(TOMBSTONE_TITLE, date,
                             extra={TOMBSTONE_KEY: "true", MARK: stamp})
    return head + "\n" + TOMBSTONE_BODY.format(date=stamp[:10])


# ------------------------------------------------------------------ paths

def stash_path(record: Path) -> Path:
    """`how-to.md` → `how-to.withdrawn.md`; a bundle's `index.md` → `index.withdrawn.md` beside it."""
    record = Path(record)
    return record.with_name(record.stem + STASH_INFIX + record.suffix)


def resolve(record: str | Path, records_dir: Path | None = None) -> Path:
    """A path to the record, or — when nothing is there — a slug looked up under the records dir."""
    p = Path(record)
    if p.exists():
        return resolve_record(p)[0]
    if records_dir is None:
        raise RuntimeError(f"{record} does not exist")
    matches = find_record(Path(records_dir), str(record))
    if not matches:
        raise RuntimeError(f"no record named {record!r} under {records_dir}")
    if len(matches) > 1:
        raise RuntimeError(f"{record!r} is ambiguous: {', '.join(str(m) for m in matches)}")
    return matches[0]


# ------------------------------------------------------------------ commands

def unpublish(record: str | Path, tombstone: bool = False, records_dir: Path | None = None,
              dry_run: bool = False, when: datetime | None = None) -> dict:
    """Draft the record out of the site and the books, optionally leaving a stub at its URL."""
    path = resolve(record, records_dir)
    text = path.read_text(encoding="utf-8")
    meta = frontmatter.read(text)
    if meta.get(MARK):
        raise RuntimeError(f"{path} is already unpublished ({MARK}: {meta[MARK]})")
    if meta.get("draft") == "true":
        raise RuntimeError(f"{path} is already a draft — it is not published, so there is "
                           "nothing to unpublish")
    stamp = naming.now_iso(when)
    marked = mark(text, stamp)
    stash = stash_path(path) if tombstone else None

    result = {"record": str(path), "slug": path.parent.name if path.name == "index.md"
              else path.stem, "unpublished": stamp, "draft": True,
              "tombstone": bool(tombstone), "stash": str(stash) if stash else None,
              "dry_run": dry_run, "written": False,
              "remains": remains(path), "next": NEXT}
    if dry_run:
        return result
    if tombstone:
        if stash.exists():
            raise RuntimeError(f"{stash} already exists — refusing to overwrite it")
        atomic_write_text(stash, marked)
        atomic_write_text(path, tombstone_text(text, stamp))
    else:
        atomic_write_text(path, marked)
    result["written"] = True
    return result


def restore(record: str | Path, records_dir: Path | None = None, dry_run: bool = False) -> dict:
    """Put an unpublished record back: the stash returns over its tombstone, the keys come off."""
    path = resolve(record, records_dir)
    text = path.read_text(encoding="utf-8")
    stash = stash_path(path)

    if stash.is_file():
        stashed = stash.read_text(encoding="utf-8")
        if not frontmatter.read(stashed).get(MARK):
            raise RuntimeError(f"{stash} carries no {MARK}: marker — refusing to restore it")
        source, from_stash = stashed, True
    else:
        if not frontmatter.read(text).get(MARK):
            raise RuntimeError(f"{path} carries no {MARK}: marker — "
                               "`records unpublish` did not unpublish it")
        source, from_stash = text, False

    restored = unmark(source)
    result = {"record": str(path), "restored": True, "from_stash": from_stash,
              "stash": str(stash) if from_stash else None, "dry_run": dry_run,
              "written": False,
              "next": ["bin/build.sh — rebuild the site and the books with it back",
                       "records publish — deliver"]}
    if dry_run:
        result["restored"] = False
        return result
    atomic_write_text(path, restored)
    if from_stash:
        stash.unlink()
    result["written"] = True
    return result
