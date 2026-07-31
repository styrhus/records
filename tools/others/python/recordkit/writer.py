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


def append_turn(file: Path, human: str, assistant: str, model: str, name: str | None = None) -> None:
    """Ollama-backed /record — a full Human/Assistant turn signed with the model tag.
    A name (from /myname) heads the human side as `## Human (name)`."""
    heading = f"## Human ({name})" if name else "## Human"
    append_block(file, f"{heading}\n\n{human}\n\n## Assistant\n\n{assistant}\n\n— {model}")
