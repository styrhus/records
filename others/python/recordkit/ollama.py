"""Two-sided /record via a local Ollama model (stdlib urllib, /api/chat)."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from pathlib import Path

from .writer import append_turn

DEFAULT_TIMEOUT = 120.0

_HEADINGS = {"## Human": "user", "## User": "user", "## Assistant": "assistant"}


def parse_turns(text: str) -> list[dict]:
    """Rebuild the chat history from ## Human/## Assistant sections; signature lines stripped."""
    messages: list[dict] = []
    role: str | None = None
    lines: list[str] = []

    def flush() -> None:
        nonlocal role, lines
        if role is None:
            lines = []
            return
        content = "\n".join(lines).strip()
        if role == "assistant":
            body = content.rsplit("\n", 1)
            if body[-1].startswith("— "):  # trailing model signature
                content = body[0].strip() if len(body) > 1 else ""
        if content:
            messages.append({"role": role, "content": content})
        role, lines = None, []

    for line in text.splitlines():
        heading = _HEADINGS.get(line.strip())
        if heading:
            flush()
            role = heading
        else:
            lines.append(line)
    flush()
    return messages


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


def reply(file: Path, endpoint: str, model: str, human: str,
          timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Generate + append one signed turn; nothing is written when generation fails."""
    human = human.strip()
    if not human:
        raise RuntimeError("empty message")
    file = Path(file)
    messages = parse_turns(file.read_text(encoding="utf-8"))
    messages.append({"role": "user", "content": human})
    assistant = chat(endpoint, model, messages, timeout)
    append_turn(file, human, assistant, model)
    return {"file": str(file), "model": model, "reply": assistant, "appended": True}
