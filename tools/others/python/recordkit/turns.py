"""Split a record into its Human/Assistant turns — the one parser for the record format."""

from __future__ import annotations

import re

_HEADINGS = {"## Human": "user", "## User": "user", "## Assistant": "assistant"}
_NAMED_HUMAN = re.compile(r"^## (?:Human|User) \((.+)\)$")


def _heading(line: str) -> tuple[str, str, str | None] | None:
    """(role, label, name) for a turn heading; named turns (## Human (Ada)) are user turns too."""
    role = _HEADINGS.get(line)
    if role:
        return role, line[3:], None
    m = _NAMED_HUMAN.match(line)
    return ("user", line[3:], m.group(1)) if m else None


def split(text: str) -> list[dict]:
    """Turns in document order: role, heading label, name, content, and the signature's model tag."""
    turns: list[dict] = []
    head: tuple[str, str, str | None] | None = None
    lines: list[str] = []

    def flush() -> None:
        nonlocal head, lines
        if head is None:
            lines = []
            return
        role, label, name = head
        content, model = "\n".join(lines).strip(), None
        if role == "assistant":
            body = content.rsplit("\n", 1)
            if body[-1].startswith("— "):  # trailing model signature
                model = body[-1][2:].strip()
                content = body[0].strip() if len(body) > 1 else ""
        if content:
            turns.append({"role": role, "label": label, "name": name,
                          "content": content, "model": model})
        head, lines = None, []

    for line in text.splitlines():
        heading = _heading(line.strip())
        if heading:
            flush()
            head = heading
        else:
            lines.append(line)
    flush()
    return turns


def parse_turns(text: str) -> list[dict]:
    """Chat history for the Ollama API: role + content only, signature lines stripped."""
    return [{"role": t["role"], "content": t["content"]} for t in split(text)]
