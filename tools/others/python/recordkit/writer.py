"""Append helpers matching the record/all/me heredoc pattern (leading blank line, then content)."""

from __future__ import annotations

from pathlib import Path


def append_block(file: Path, text: str) -> None:
    """Append a leading blank line, the text, and a trailing newline — as the skills' heredoc does."""
    with Path(file).open("a", encoding="utf-8") as f:
        f.write("\n" + text + "\n")


def append_user(file: Path, message: str) -> None:
    """/all, /me, no-AI /record — the user's message verbatim, blank-line separated."""
    append_block(file, message)


def append_turn(file: Path, human: str, assistant: str, model: str) -> None:
    """Ollama-backed /record — a full Human/Assistant turn signed with the model tag."""
    append_block(file, f"## Human\n\n{human}\n\n## Assistant\n\n{assistant}\n\n— {model}")
