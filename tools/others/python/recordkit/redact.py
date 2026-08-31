"""Rewrite one turn of a record in place, leaving a visible seam instead of a lie.

The seam is the point. A turn that has been redacted keeps its heading, its place in the
conversation and its signature line; only the text goes, replaced by `[redacted]` — a marker a
reader can see and ask about. Nothing here pretends the text was never written: git still has it,
and the command says so on every run.

Turn numbering is `turns.split`'s document order, 1-based — the same scheme `records card --turn`
uses and the same one `ollama.py` rebuilds history with. One scheme, not two: `locate()` reproduces
`split()`'s list exactly and only adds the line span each turn's content occupies.

Border: this never touches git. Removing the text from the working tree is all it claims to do.
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

from . import turns as turns_mod
from .attach import resolve_record

MARKER = "[redacted]"


def remains(path: Path) -> list[str]:
    """What a redaction does not reach. Printed every run; never suppressible."""
    return [
        f"git history still holds the original text — `git log -p -- {path}` shows it",
        "any clone, fork or mirror pulled before now still has the record in full",
        "the forge's own caches, search indexes and web archives are outside this repository",
        "the published site keeps the old page until the site is rebuilt and published",
    ]


def locate(text: str) -> list[dict]:
    """`turns.split`'s turns, each with the half-open line span its content occupies.

    Same order, same skipping of empty turns — the numbering scheme is shared, not reimplemented.
    """
    lines = text.split("\n")
    out: list[dict] = []
    head: tuple[str, str, str | None] | None = None
    start = 0

    def flush(end: int) -> None:
        nonlocal head
        if head is None:
            return
        role, label, name = head
        block = lines[start:end]
        filled = [j for j, ln in enumerate(block) if ln.strip()]
        head = None
        if not filled:
            return
        first, last = filled[0], filled[-1]
        model = None
        if role == "assistant":
            tail = block[last].strip() if last == first else block[last].rstrip()
            if tail.startswith("— "):  # trailing model signature — kept, never redacted
                model = tail[2:].strip()
                filled = filled[:-1]
                if not filled:
                    return
                first, last = filled[0], filled[-1]
        content = "\n".join(block[first:last + 1]).strip()
        if not content:
            return
        out.append({"role": role, "label": label, "name": name, "content": content,
                    "model": model, "start": start + first, "end": start + last + 1})

    for i, line in enumerate(lines):
        heading = turns_mod._heading(line.strip())
        if heading:
            flush(i)
            head, start = heading, i + 1
    flush(len(lines))
    return out


def pick(items: list[dict], turn: int) -> int:
    """1-based --turn over all turns in document order (card.py's rule)."""
    if not items:
        raise RuntimeError("the record has no Human/Assistant turns")
    if not 1 <= turn <= len(items):
        raise RuntimeError(f"--turn {turn} out of range: the record has {len(items)} turns")
    return turn - 1


def seam(replacement: str | None) -> list[str]:
    """The lines a redacted turn gets. `--remove` is the marker alone; a replacement keeps it too."""
    if replacement is None or not replacement.strip():
        return [MARKER]
    return [*replacement.rstrip("\n").split("\n"), "", MARKER]


def apply(text: str, turn: dict, replacement: str | None = None) -> str:
    """The record with one turn's content swapped for the seam; every other byte untouched."""
    lines = text.split("\n")
    return "\n".join(lines[:turn["start"]] + seam(replacement) + lines[turn["end"]:])


def diff(before: str, after: str, path: Path) -> str:
    """Unified diff of the one turn that changed — what --dry-run shows, and what the prompt shows."""
    return "".join(difflib.unified_diff(before.splitlines(keepends=True),
                                        after.splitlines(keepends=True),
                                        fromfile=f"a/{path}", tofile=f"b/{path}"))


def _show(text: str) -> None:
    if text:
        sys.stderr.write(text if text.endswith("\n") else text + "\n")


def _notice(path: Path) -> None:
    """The honesty line, on stderr, on every run. JSON on stdout stays machine-readable."""
    sys.stderr.write("redacted in the working tree only. What remains:\n")
    for line in remains(path):
        sys.stderr.write(f"  - {line}\n")


def ask(diff_text: str) -> bool:
    """Show the diff and ask. A non-interactive stdin is a no — never a silent yes."""
    _show(diff_text)
    if not sys.stdin.isatty():
        sys.stderr.write("stdin is not a terminal — pass --yes to redact without asking\n")
        return False
    sys.stderr.write("redact this turn? [y/N] ")
    sys.stderr.flush()
    return sys.stdin.readline().strip().lower() in ("y", "yes")


def redact(record: Path, turn: int, replace: str | None = None, remove: bool = False,
           dry_run: bool = False, yes: bool = False, confirm=None) -> dict:
    """Redact one turn. Shows the diff and asks unless --yes; writes nothing on --dry-run."""
    if (replace is None) == (not remove):
        raise RuntimeError("pass exactly one of --replace TEXT or --remove")
    path, _ = resolve_record(Path(record))
    before = path.read_text(encoding="utf-8")
    items = locate(before)
    target = items[pick(items, turn)]
    after = apply(before, target, replace)
    patch = diff(before, after, path)

    result = {"record": str(path), "turn": turn, "role": target["role"],
              "label": target["label"], "mode": "remove" if remove else "replace",
              "marker": MARKER, "diff": patch, "written": False, "dry_run": dry_run,
              "remains": remains(path)}
    if dry_run:
        _show(patch)
        _notice(path)
        return result
    if not (yes or (confirm(patch) if confirm else ask(patch))):
        result["cancelled"] = True
        return result
    path.write_text(after, encoding="utf-8")
    result["written"] = True
    _notice(path)
    return result
