# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Source parsers for `records import` — every one yields importer.Conversation and writes nothing.

Kept strictly apart from the emitting in importer.py: a parser reads the user's file (read-only,
stdlib only, no network) and hands back the internal shape. Add a source by writing a function
here and registering it in PARSERS.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import frontmatter
from .importer import ASSISTANT, HUMAN, Conversation, Turn

TITLE_LIMIT = 72

# Wrappers Claude Code puts around machinery in a user turn; a real message can follow one.
_CC_NOISE = ("local-command-caveat", "local-command-stdout", "local-command-stderr",
             "command-name", "command-message", "command-args", "system-reminder",
             "ide_opened_file", "ide_selection", "task-notification")
_CC_NOISE_RE = re.compile(r"<(%s)>.*?</\1>" % "|".join(_CC_NOISE), re.DOTALL)
_TITLE_UNSAFE = re.compile(r"[\\/\x00-\x1f]+")


def _clean_title(text: str, limit: int = TITLE_LIMIT) -> str:
    """A title from arbitrary source text: first line, path-safe, truncated on a word boundary.
    ' #' used to be stripped here too, as a workaround for frontmatter.build writing it unquoted;
    build() now quotes it (frontmatter.quote), so a parser-derived '#' survives into the title."""
    first = next((ln for ln in (text or "").splitlines() if ln.strip()), "")
    line = " ".join(_TITLE_UNSAFE.sub("-", first).split()).strip("-. ")
    if len(line) <= limit:
        return line
    return line[:limit].rsplit(" ", 1)[0] or line[:limit]


def _when(stamp: str | None, assume_utc: bool = False) -> datetime | None:
    """An export timestamp (ISO 8601, UTC 'Z' allowed) as a local-zone datetime.
    `assume_utc` is for sources that store UTC without an offset, like llm's `datetime_utc`."""
    if not stamp:
        return None
    text = str(stamp).strip().replace("Z", "+00:00")
    for candidate in (text, re.sub(r"\.\d+", "", text)):
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if parsed.tzinfo is None and assume_utc:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone() if parsed.tzinfo else parsed
    return None


def _coalesce(turns: list) -> list:
    """Merge consecutive same-role turns — tool traffic between two assistant texts is dropped,
    not a turn boundary."""
    merged: list = []
    for turn in turns:
        if merged and merged[-1].role == turn.role:
            merged[-1].text = f"{merged[-1].text}\n\n{turn.text}"
            merged[-1].model = merged[-1].model or turn.model
        else:
            merged.append(turn)
    return merged


# --- Claude Code session transcripts (JSONL) ---------------------------------------------------

def _cc_text(message: dict, role: str) -> str:
    """The human/assistant prose of one row — text blocks only, no thinking, tools or images."""
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    else:
        return ""
    if role == HUMAN:
        text = _CC_NOISE_RE.sub("", text)
    return text.strip()


def _cc_rows(file: Path) -> list:
    """Every JSON object in the file, with a clear error naming the line that failed."""
    rows = []
    with Path(file).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{Path(file).name}: line {number} is not JSON ({e.msg})") from e
    return rows


def _cc_session(file: Path) -> Conversation | None:
    """One session file as a conversation, or None when it holds no human/assistant prose."""
    rows = _cc_rows(file)
    turns: list = []
    title = ""
    for row in rows:
        if row.get("type") == "ai-title" and row.get("aiTitle"):
            title = str(row["aiTitle"])  # refined as the session runs; the last one wins
        if row.get("type") not in ("user", "assistant") or row.get("isMeta") or row.get("isSidechain"):
            continue
        role = HUMAN if row["type"] == "user" else ASSISTANT
        text = _cc_text(row.get("message") or {}, role)
        if text:
            turns.append(Turn(role, text, model=(row.get("message") or {}).get("model")))

    turns = _coalesce(turns)
    if not turns:
        return None
    first_human = next((t.text for t in turns if t.role == HUMAN), "")
    return Conversation(
        turns=turns,
        title=_clean_title(title or first_human),
        date=next((_when(r.get("timestamp")) for r in rows if r.get("timestamp")), None),
        source_id=next((r["sessionId"] for r in rows if r.get("sessionId")), Path(file).stem),
        kind="claude-code session",
    )


def claude_code(path: Path):
    """Claude Code JSONL transcripts — one session file, or a directory of them."""
    path = Path(path)
    files = sorted(path.rglob("*.jsonl")) if path.is_dir() else [path]
    for file in files:
        conversation = _cc_session(file)
        if conversation:
            yield conversation


# --- llm SQLite logs ---------------------------------------------------------------------------

_LLM_COLUMNS = {"conversations": ("id", "name"),
                "responses": ("id", "model", "prompt", "response", "conversation_id",
                              "datetime_utc")}


def llm_connect(path: Path):
    """Open an llm log read-only — the user's history is never written to."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"no llm log at {path}")
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def _llm_check(con) -> None:
    """Fail with the missing table or column named, rather than a traceback from the query."""
    for table, columns in _LLM_COLUMNS.items():
        present = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
        if not present:
            raise ValueError(f"not an llm log: no `{table}` table")
        missing = [c for c in columns if c not in present]
        if missing:
            raise ValueError(f"not an llm log: `{table}` is missing {', '.join(missing)}")


def llm(path: Path):
    """Simon Willison's `llm` history — one conversation per conversation id, prompt/response pairs."""
    con = llm_connect(path)
    try:
        _llm_check(con)
        rows = con.execute(
            "SELECT r.id, r.model, r.prompt, r.response, r.conversation_id, r.datetime_utc, c.name"
            "  FROM responses r LEFT JOIN conversations c ON c.id = r.conversation_id"
            " ORDER BY COALESCE(r.conversation_id, r.id), COALESCE(r.datetime_utc, ''), r.id"
        ).fetchall()
    finally:
        con.close()

    current: Conversation | None = None
    key = None
    for row_id, model, prompt, response, conversation_id, stamp, name in rows:
        row_key = conversation_id or row_id
        if row_key != key:
            if current:
                yield current
            key, current = row_key, Conversation(source_id=row_key, title=_clean_title(name or ""),
                                                 date=_when(stamp, assume_utc=True), kind="llm log")
        if prompt:
            current.turns.append(Turn(HUMAN, prompt.strip()))
        if response:
            current.turns.append(Turn(ASSISTANT, response.strip(), model=model))
        if not current.title and prompt:
            current.title = _clean_title(prompt)
    if current:
        yield current


# --- a directory of Markdown -------------------------------------------------------------------

_MD_SKIP_NAMES = {"_index.md", "404.md", "LICENSE.md"}
_MD_SKIP_DIRS = {"node_modules"}
_MD_STAMPS = (("%Y-%m-%d_%H-%M", 16), ("%Y-%m-%d", 10))


def _md_wanted(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts if path != root else ()
    return (path.name not in _MD_SKIP_NAMES
            and not any(p.startswith(".") or p in _MD_SKIP_DIRS for p in parts[:-1]))


def _md_tags(raw: str) -> list:
    """`tags: [a, b]` as records write it. Multi-line YAML lists are not read — stdlib only."""
    raw = (raw or "").strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [t.strip().strip("\"'") for t in raw[1:-1].split(",") if t.strip()]
    return [raw.strip("\"'")] if raw else []


def _md_date(path: Path, raw: str | None) -> datetime:
    """Frontmatter date, else a timestamp filename, else the file's mtime."""
    stated = _when(raw)
    if stated:
        return stated
    for layout, width in _MD_STAMPS:
        try:
            return datetime.strptime(path.stem[:width], layout).astimezone()
        except ValueError:
            continue
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone()


def _md_turns(text: str) -> tuple:
    """(turns, kind) — a record's Human/Assistant sections, or the whole body as one human turn."""
    from .turns import split

    found = [Turn(HUMAN if t["role"] == "user" else ASSISTANT, t["content"], model=t["model"])
             for t in split(text)]
    if found:
        return found, "conversation"
    return ([Turn(HUMAN, text.strip())] if text.strip() else []), "body"


def markdown(path: Path):
    """A tree of Markdown — notes, an old blog, records in another flavour. Turn detection is
    best-effort: a file without Human/Assistant headings stays one body, never a guessed dialogue."""
    path = Path(path)
    root = path if path.is_dir() else path.parent
    files = sorted(f for f in path.rglob("*.md") if _md_wanted(f, root)) if path.is_dir() else [path]

    for file in files:
        text = file.read_text(encoding="utf-8")
        meta = frontmatter.read(text)
        content = frontmatter.body(text)
        turns, kind = _md_turns(content)
        if not turns:
            continue
        heading = next((ln[2:] for ln in content.splitlines() if ln.startswith("# ")), "")
        yield Conversation(
            turns=turns,
            title=_clean_title(meta.get("title") or heading or file.stem),
            date=_md_date(file, meta.get("date")),
            source_id=file.relative_to(root).as_posix(),
            tags=_md_tags(meta.get("tags", "")),
            kind=kind,
        )


PARSERS: dict = {
    "claude-code": claude_code,
    "llm": llm,
    "markdown": markdown,
}
