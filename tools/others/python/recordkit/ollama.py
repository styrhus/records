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

PRESETS_DIR = Path(__file__).parent / "presets"


def load_preset(name: str) -> str:
    """A voice preset's system-prompt text — deterministic, no model involved in the lookup.
    One plain-text file per voice; `name` may not contain a path separator."""
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise RuntimeError(f"unknown preset: {name!r}")
    path = PRESETS_DIR / f"{name}.txt"
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as e:
        raise RuntimeError(f"unknown preset: {name}") from e


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


def _http_post_stream(url: str, payload: dict, timeout: float):
    """Yield each parsed line of Ollama's line-delimited JSON stream. Opens the connection
    eagerly (a refused connection raises here, at the first `next()`, same as `_http_post`)."""
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=timeout)

    def _lines():
        with resp:
            for raw in resp:
                line = raw.strip()
                if line:
                    yield json.loads(line.decode("utf-8"))
    return _lines()


def _translate_http_errors(e: BaseException, endpoint: str, timeout: float) -> RuntimeError:
    """Shared with chat()/chat_stream(): both wrap the same urllib error shapes the same way."""
    if isinstance(e, urllib.error.HTTPError):
        try:
            detail = json.loads(e.read().decode("utf-8")).get("error", "")
        except Exception:
            detail = e.reason
        return RuntimeError(f"ollama HTTP {e.code}: {detail}")
    if isinstance(e, (TimeoutError, socket.timeout)):
        return RuntimeError(f"ollama timed out after {timeout:g}s")
    if isinstance(e, urllib.error.URLError):
        if isinstance(e.reason, (TimeoutError, socket.timeout)):
            return RuntimeError(f"ollama timed out after {timeout:g}s")
        return RuntimeError(f"ollama unreachable at {endpoint}: {e.reason}")
    return RuntimeError(str(e))


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


def chat_stream(endpoint: str, model: str, messages: list[dict], timeout: float = DEFAULT_TIMEOUT):
    """Same request as chat(), `stream: true` — yields each content token as it arrives instead
    of waiting for the full reply. Raises the same RuntimeErrors as chat(), on the first `next()`
    for a connection failure, or on any later one for a fault mid-stream."""
    endpoint = endpoint.rstrip("/")
    try:
        for obj in _http_post_stream(f"{endpoint}/api/chat",
                                     {"model": model, "messages": messages, "stream": True}, timeout):
            content = obj.get("message", {}).get("content") if isinstance(obj, dict) else None
            if content:
                yield content
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as e:
        raise _translate_http_errors(e, endpoint, timeout) from e


def ephemeral_reply(endpoint: str, model: str, human: str, history: list,
                    timeout: float = DEFAULT_TIMEOUT, context: str | None = None,
                    preset: str | None = None) -> dict:
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
    if preset:
        # the voice, ahead of any workspace context — same slot, composed alongside it
        messages.insert(0, {"role": "system", "content": preset})
    messages.append({"role": "user", "content": human})
    assistant = chat(endpoint, model, messages, timeout)
    return {"model": model, "reply": assistant, "appended": False}


def ephemeral_reply_stream(endpoint: str, model: str, human: str, history: list,
                           timeout: float = DEFAULT_TIMEOUT, context: str | None = None,
                           preset: str | None = None):
    """Streaming twin of ephemeral_reply(): yields each token; nothing is ever written to disk.
    Raises "empty message" / "invalid history" up front, before any request is made, same as the
    non-streaming path — a generator only runs its body once iterated, so callers still see these
    on the first `next()`, not the call itself."""
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
        messages.insert(0, {"role": "system", "content": context})
    if preset:
        messages.insert(0, {"role": "system", "content": preset})
    messages.append({"role": "user", "content": human})
    chunks: list[str] = []
    for token in chat_stream(endpoint, model, messages, timeout):
        chunks.append(token)
        yield token
    assistant = "".join(chunks).strip()
    if not assistant:
        raise RuntimeError("ollama returned a malformed response")
    # a generator's `return value` becomes StopIteration.value — the caller drives this generator
    # to completion (e.g. `result = yield from ...` or catching StopIteration) to get the same
    # {"model", "reply", "appended": False} shape ephemeral_reply() returns directly.
    return {"model": model, "reply": assistant, "appended": False}


def reply(file: Path, endpoint: str, model: str, human: str,
          timeout: float = DEFAULT_TIMEOUT, context: str | None = None,
          name: str | None = None, preset: str | None = None) -> dict:
    """Generate + append one signed turn; nothing is written when generation fails."""
    human = human.strip()
    if not human:
        raise RuntimeError("empty message")
    file = Path(file)
    messages = parse_turns(file.read_text(encoding="utf-8"))
    if context:
        # model-only: sent as a system message, never appended to the record
        messages.insert(0, {"role": "system", "content": context})
    if preset:
        # the voice, ahead of any workspace context — same slot, composed alongside it;
        # never appended to the record either, same as context
        messages.insert(0, {"role": "system", "content": preset})
    messages.append({"role": "user", "content": human})
    assistant = chat(endpoint, model, messages, timeout)
    append_turn(file, human, assistant, model, name=name)
    return {"file": str(file), "model": model, "reply": assistant, "appended": True}


def reply_stream(file: Path, endpoint: str, model: str, human: str,
                 timeout: float = DEFAULT_TIMEOUT, context: str | None = None,
                 name: str | None = None, preset: str | None = None):
    """Streaming twin of reply(): yields each token as it arrives; the signed turn is appended
    only once, after the stream completes — a caller that stops early, or a fault mid-stream,
    reaches append_turn never, so a half-written turn never lands on disk (same contract as
    reply()). The joined, stripped tokens are byte-identical to what reply() would have written."""
    human = human.strip()
    if not human:
        raise RuntimeError("empty message")
    file = Path(file)
    messages = parse_turns(file.read_text(encoding="utf-8"))
    if context:
        messages.insert(0, {"role": "system", "content": context})
    if preset:
        messages.insert(0, {"role": "system", "content": preset})
    messages.append({"role": "user", "content": human})
    chunks: list[str] = []
    for token in chat_stream(endpoint, model, messages, timeout):
        chunks.append(token)
        yield token
    assistant = "".join(chunks).strip()
    if not assistant:
        raise RuntimeError("ollama returned a malformed response")
    append_turn(file, human, assistant, model, name=name)
    # see ephemeral_reply_stream()'s note: this becomes StopIteration.value for the caller
    return {"file": str(file), "model": model, "reply": assistant, "appended": True}
