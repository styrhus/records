"""records booth — a room with a door: open, type, submit a turn, keep typing, close.

stdlib curses only. Buffer and Session hold the logic, so everything but the drawing
tests without a terminal. Records go through create.py and writer.py like every other
path, so what the booth writes is byte-identical to `records new` + `records append`.
"""
# TODO(cli.py): register the `booth` subparser — deferred while parallel road sessions run.

from __future__ import annotations

import curses
import locale
from pathlib import Path

from . import create, myname, ollama, writer
from .config import resolve_records_dir

HINT = "Enter newline · Ctrl-D send · Esc end"


class Buffer:
    """The draft being typed: lines and a cursor. No curses, no I/O."""

    def __init__(self, text: str = "") -> None:
        self.lines = text.split("\n") if text else [""]
        self.row = len(self.lines) - 1
        self.col = len(self.lines[self.row])

    def text(self) -> str:
        return "\n".join(self.lines)

    def clear(self) -> None:
        self.lines, self.row, self.col = [""], 0, 0

    def insert(self, ch: str) -> None:
        line = self.lines[self.row]
        self.lines[self.row] = line[:self.col] + ch + line[self.col:]
        self.col += len(ch)

    def newline(self) -> None:
        line = self.lines[self.row]
        self.lines[self.row:self.row + 1] = [line[:self.col], line[self.col:]]
        self.row, self.col = self.row + 1, 0

    def backspace(self) -> None:
        if self.col:
            line = self.lines[self.row]
            self.lines[self.row] = line[:self.col - 1] + line[self.col:]
            self.col -= 1
        elif self.row:
            prev = self.lines[self.row - 1]
            self.lines[self.row - 1] = prev + self.lines[self.row]
            del self.lines[self.row]
            self.row, self.col = self.row - 1, len(prev)

    def delete(self) -> None:
        line = self.lines[self.row]
        if self.col < len(line):
            self.lines[self.row] = line[:self.col] + line[self.col + 1:]
        elif self.row + 1 < len(self.lines):
            self.lines[self.row] = line + self.lines[self.row + 1]
            del self.lines[self.row + 1]

    def left(self) -> None:
        if self.col:
            self.col -= 1
        elif self.row:
            self.row, self.col = self.row - 1, len(self.lines[self.row - 1])

    def right(self) -> None:
        if self.col < len(self.lines[self.row]):
            self.col += 1
        elif self.row + 1 < len(self.lines):
            self.row, self.col = self.row + 1, 0

    def up(self) -> None:
        if self.row:
            self.row -= 1
            self.col = min(self.col, len(self.lines[self.row]))

    def down(self) -> None:
        if self.row + 1 < len(self.lines):
            self.row += 1
            self.col = min(self.col, len(self.lines[self.row]))

    def home(self) -> None:
        self.col = 0

    def end(self) -> None:
        self.col = len(self.lines[self.row])


class Session:
    """One booth session: where the record is, how many turns, and who answers."""

    def __init__(self, records_dir: Path | None = None, arguments: str = "",
                 draft: bool = False, file: Path | None = None,
                 endpoint: str | None = None, model: str | None = None,
                 timeout: float = ollama.DEFAULT_TIMEOUT, name: str | None = None) -> None:
        if bool(endpoint) != bool(model):
            raise RuntimeError("--endpoint and --model go together (or leave both out)")
        self.arguments, self.draft = arguments, draft
        self.endpoint, self.model, self.timeout = endpoint, model, timeout
        self.name = name
        self.turns = 0
        self.path = Path(file) if file else None
        self.records_dir = None
        if self.path is not None:
            if not self.path.is_file():
                raise RuntimeError(f"{self.path} not found — --file continues an existing record")
        else:
            self.records_dir = Path(records_dir) if records_dir else resolve_records_dir(Path("."))
            if not self.records_dir.is_dir():
                raise RuntimeError(f"no records directory at {self.records_dir} — run the booth "
                                   "from a records checkout, or pass --dir")

    @property
    def talks_back(self) -> bool:
        return bool(self.endpoint and self.model)

    def ensure_record(self) -> Path:
        """The record is created by the first submitted turn — an escaped booth leaves no file."""
        if self.path is None:
            created = create.new_record(self.records_dir, arguments=self.arguments,
                                        draft=self.draft)
            self.path = Path(created["path"])
        return self.path

    def _human_name(self) -> str | None:
        if self.name is None:
            self.name = myname.load() or ""
        return self.name or None

    def submit(self, text: str) -> dict:
        """Append one turn. The human's words land even when the model does not answer."""
        text = text.strip()
        if not text:
            return {"appended": False, "reply": None, "warning": None}
        path = self.ensure_record()
        if self.talks_back:
            try:
                answer = ollama.reply(path, self.endpoint, self.model, text,
                                      timeout=self.timeout, name=self._human_name())
                self.turns += 1
                return {"appended": True, "reply": answer["reply"], "warning": None}
            except RuntimeError as e:
                writer.append_user(path, text)  # a dead model never costs a sentence
                self.turns += 1
                return {"appended": True, "reply": None, "warning": str(e)}
        writer.append_user(path, text)
        self.turns += 1
        return {"appended": True, "reply": None, "warning": None}

    def transcript(self) -> str:
        """What has been written so far, frontmatter dropped — the booth's scrollback."""
        if self.path is None or not self.path.is_file():
            return ""
        text = self.path.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            _, _, rest = text[4:].partition("\n---\n")
            return rest.strip("\n")
        return text.strip("\n")


# ------------------------------------------------------------------ the screen

def _chunks(line: str, width: int) -> list:
    """Hard-wrap for display; fixed-width chunking keeps the cursor arithmetic exact."""
    return [line[i:i + width] for i in range(0, len(line), width)] or [""]


def _put(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    height, width = stdscr.getmaxyx()
    if 0 <= y < height:
        try:
            stdscr.addstr(y, x, text[:max(0, width - x - 1)], attr)
        except curses.error:  # the bottom-right cell always refuses
            pass


def _draw(stdscr, session: Session, buf: Buffer, status: str) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    text_width = max(1, width - 3)

    name = session.path.name if session.path else "(no record yet)"
    head = f" records booth · {name} · {session.turns} turns"
    if session.model:
        head += f" · {session.model}"
    _put(stdscr, 0, 0, head.ljust(width - 1), curses.A_REVERSE)

    rows = [r for line in buf.lines for r in _chunks(line, text_width)]
    input_height = min(max(len(rows) + 1, 3), max(3, height // 2))
    sep = height - 1 - input_height

    body = [r for line in session.transcript().splitlines() for r in _chunks(line, width - 2)]
    visible = body[-(sep - 1):] if sep > 1 else []
    for i, line in enumerate(visible):
        _put(stdscr, 1 + i, 1, line)

    _put(stdscr, sep, 0, "─" * (width - 1), curses.A_DIM)
    for i, line in enumerate(rows[-(input_height - 1):]):
        _put(stdscr, sep + 1 + i, 0, ("> " if i == 0 else "  ") + line)

    foot = f"{HINT}   {status}".strip()
    _put(stdscr, height - 1, 0, foot[:width - 1], curses.A_DIM)

    before = sum(len(_chunks(line, text_width)) for line in buf.lines[:buf.row])
    cy = sep + 1 + min(before + buf.col // text_width, input_height - 2)
    cx = 2 + buf.col % text_width
    try:
        stdscr.move(max(sep + 1, min(cy, height - 2)), min(cx, width - 1))
    except curses.error:
        pass
    stdscr.refresh()


def _loop(stdscr, session: Session) -> None:
    curses.curs_set(1)
    stdscr.keypad(True)
    if hasattr(curses, "set_escdelay"):
        curses.set_escdelay(25)  # a bare Esc should not wait for a sequence that never comes
    buf, status = Buffer(), ""

    while True:
        _draw(stdscr, session, buf, status)
        try:
            key = stdscr.get_wch()
        except curses.error:  # interrupted read (resize)
            continue
        except KeyboardInterrupt:
            return

        if isinstance(key, int):
            if key == curses.KEY_RESIZE:
                continue
            if key in (curses.KEY_BACKSPACE, 8, 127):
                buf.backspace()
            elif key == curses.KEY_DC:
                buf.delete()
            elif key == curses.KEY_LEFT:
                buf.left()
            elif key == curses.KEY_RIGHT:
                buf.right()
            elif key == curses.KEY_UP:
                buf.up()
            elif key == curses.KEY_DOWN:
                buf.down()
            elif key == curses.KEY_HOME:
                buf.home()
            elif key == curses.KEY_END:
                buf.end()
            elif key == curses.KEY_ENTER:
                buf.newline()
            continue

        if key == "\x04":  # Ctrl-D sends the turn
            text = buf.text().strip()
            if not text:
                continue
            if session.talks_back:
                _draw(stdscr, session, buf, f"waiting for {session.model}…")
            result = session.submit(text)
            buf.clear()
            warning = result["warning"]
            status = f"{warning} — your words were saved" if warning else ""
        elif key in ("\x1b", "\x03"):  # Esc ends the session, like /esc; Ctrl-C too
            return
        elif key in ("\n", "\r"):
            buf.newline()
        elif key in ("\x7f", "\b"):
            buf.backspace()
        elif key.isprintable() or key == "\t":
            buf.insert(key)


def run(records_dir: Path | None = None, arguments: str = "", draft: bool = False,
        file: Path | None = None, endpoint: str | None = None, model: str | None = None,
        timeout: float = ollama.DEFAULT_TIMEOUT, name: str | None = None) -> dict:
    """Open the booth. Everything that can fail without a terminal fails before curses starts."""
    session = Session(records_dir=records_dir, arguments=arguments, draft=draft, file=file,
                      endpoint=endpoint, model=model, timeout=timeout, name=name)
    locale.setlocale(locale.LC_ALL, "")  # multibyte input (æøå, ü) through get_wch
    try:
        curses.wrapper(_loop, session)
    except KeyboardInterrupt:
        pass
    return {"file": str(session.path) if session.path else None,
            "turns": session.turns, "model": session.model}
