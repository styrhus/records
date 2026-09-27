# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Human vs Assistant token share of a conversation (/airtime) — no model, no tokenizer."""

from __future__ import annotations

from pathlib import Path

from .turns import split

CHARS_PER_TOKEN = 4  # the usual rough estimate; only the ratio matters


def estimate_tokens(text: str) -> int:
    """Rough token count: characters over four, rounded up; blank text is 0."""
    text = text.strip()
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN if text else 0


def measure(messages: list[dict]) -> dict:
    """Token share of role/content messages: counts, whole percents summing to 100, the /airtime line."""
    human = sum(estimate_tokens(m["content"]) for m in messages if m["role"] == "user")
    assistant = sum(estimate_tokens(m["content"]) for m in messages if m["role"] == "assistant")
    total = human + assistant
    human_pct = int(human * 100 / total + 0.5) if total else 0  # half-up, not banker's
    assistant_pct = 100 - human_pct if total else 0
    return {
        "human_tokens": human,
        "assistant_tokens": assistant,
        "human_pct": human_pct,
        "assistant_pct": assistant_pct,
        "turns": {
            "human": sum(1 for m in messages if m["role"] == "user"),
            "assistant": sum(1 for m in messages if m["role"] == "assistant"),
        },
        "line": f"Human: {human_pct}%, Assistant: {assistant_pct}%",
    }


def measure_file(path: Path) -> dict:
    """Measure a record's ## Human/## Assistant turns (signature lines already stripped by the parser)."""
    turns = split(Path(path).read_text(encoding="utf-8"))
    return {"file": str(path), **measure(turns)}


def measure_history(history: object) -> dict:
    """Measure an in-memory chat — the same {role, content} list ollama-chat takes."""
    if not isinstance(history, list) or not all(
        isinstance(m, dict) and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
        for m in history
    ):
        raise RuntimeError("invalid history")
    return measure(history)
