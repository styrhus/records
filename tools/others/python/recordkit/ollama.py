"""Two-sided /record via a local Ollama model (stdlib urllib, /api/chat)."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from pathlib import Path

from .turns import parse_turns  # the record parser lives in turns.py; re-exported from here
from .writer import append_turn

DEFAULT_TIMEOUT = 120.0

MAX_FILE_BYTES = 65536
MAX_CONTEXT_BYTES = 262144
MAX_DIR_ENTRIES = 500
_DIR_IGNORE = {"node_modules", "__pycache__", ".git"}


def _file_block(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError:
        return f"### File: {path}\n(not found)"
    if b"\x00" in raw[:8192]:
        return f"### File: {path}\n(binary file — omitted)"
    text = raw[:MAX_FILE_BYTES].decode("utf-8", errors="replace")
    tail = "\n… (truncated at 64 KiB)" if len(raw) > MAX_FILE_BYTES else ""
    return f"### File: {path}\n```\n{text}{tail}\n```"


def _dir_block(path: Path) -> str:
    if not path.is_dir():
        return f"### Directory: {path}\n(not found)"
    entries = []
    for p in sorted(path.rglob("*")):
        rel = p.relative_to(path)
        if any(part.startswith(".") or part in _DIR_IGNORE for part in rel.parts):
            continue
        if p.is_file():
            entries.append(str(rel))
    lines = entries[:MAX_DIR_ENTRIES]
    if len(entries) > MAX_DIR_ENTRIES:
        lines.append(f"… ({len(entries) - MAX_DIR_ENTRIES} more)")
    return f"### Directory: {path}\n" + ("\n".join(lines) if lines else "(empty)")


def build_context(files: list[Path], dirs: list[Path]) -> str:
    """Model-only workspace context; soft-fails per attachment and is never written to the record."""
    blocks: list[str] = []
    total = 0
    for block in [_file_block(Path(f)) for f in files] + [_dir_block(Path(d)) for d in dirs]:
        if total + len(block) > MAX_CONTEXT_BYTES:
            blocks.append("… (context budget exceeded, remaining attachments omitted)")
            break
        blocks.append(block)
        total += len(block)
    if not blocks:
        return ""
    header = "The user attached workspace context (not part of the recorded conversation):"
    return header + "\n\n" + "\n\n".join(blocks)


def _http_post(url: str, payload: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat(endpoint: str, model: str, messages: list[dict], timeout: float = DEFAULT_TIMEOUT) -> str:
    endpoint = endpoint.rstrip("/")
    try:
        data = _http_post(f"{endpoint}/api/chat",
                          {"model": model, "messages": messages, "stream": False}, timeout)
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("error", "")
        except Exception:
            detail = e.reason
        raise RuntimeError(f"ollama HTTP {e.code}: {detail}") from e
    except (TimeoutError, socket.timeout) as e:
        raise RuntimeError(f"ollama timed out after {timeout:g}s") from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, (TimeoutError, socket.timeout)):
            raise RuntimeError(f"ollama timed out after {timeout:g}s") from e
        raise RuntimeError(f"ollama unreachable at {endpoint}: {e.reason}") from e
    content = data.get("message", {}).get("content") if isinstance(data, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("ollama returned a malformed response")
    return content.strip()


def ephemeral_reply(endpoint: str, model: str, human: str, history: list,
                    timeout: float = DEFAULT_TIMEOUT, context: str | None = None) -> dict:
    """Generate one reply from in-memory history; nothing is ever written to disk."""
    human = human.strip()
    if not human:
        raise RuntimeError("empty message")
    if not isinstance(history, list) or not all(
        isinstance(m, dict) and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
        for m in history
    ):
        raise RuntimeError("invalid history")
    messages = list(history)
    if context:
        # model-only: sent as a system message, like reply()
        messages.insert(0, {"role": "system", "content": context})
    messages.append({"role": "user", "content": human})
    assistant = chat(endpoint, model, messages, timeout)
    return {"model": model, "reply": assistant, "appended": False}


def reply(file: Path, endpoint: str, model: str, human: str,
          timeout: float = DEFAULT_TIMEOUT, context: str | None = None,
          name: str | None = None) -> dict:
    """Generate + append one signed turn; nothing is written when generation fails."""
    human = human.strip()
    if not human:
        raise RuntimeError("empty message")
    file = Path(file)
    messages = parse_turns(file.read_text(encoding="utf-8"))
    if context:
        # model-only: sent as a system message, never appended to the record
        messages.insert(0, {"role": "system", "content": context})
    messages.append({"role": "user", "content": human})
    assistant = chat(endpoint, model, messages, timeout)
    append_turn(file, human, assistant, model, name=name)
    return {"file": str(file), "model": model, "reply": assistant, "appended": True}
