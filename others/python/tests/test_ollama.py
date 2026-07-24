import urllib.error

import pytest

from recordkit import ollama, writer


def _mock_post(calls, content="yo"):
    def post(url, payload, timeout):
        calls.append({"url": url, "payload": payload, "timeout": timeout})
        return {"message": {"role": "assistant", "content": content}, "done": True}
    return post


def test_parse_turns_round_trip(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    writer.append_turn(f, "hi", "yo", "qwen2.5:14b")
    writer.append_turn(f, "more", "sure", "qwen2.5:14b")
    turns = ollama.parse_turns(f.read_text())
    assert turns == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "yo"},
        {"role": "user", "content": "more"},
        {"role": "assistant", "content": "sure"},
    ]


def test_parse_turns_ignores_plain_blocks(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    writer.append_user(f, "just a note")
    writer.append_turn(f, "hi", "yo", "m")
    turns = ollama.parse_turns(f.read_text())
    assert turns == [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]


def test_reply_appends_and_returns(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    r = ollama.reply(f, "http://localhost:11434", "m:latest", "hi")
    assert r == {"file": str(f), "model": "m:latest", "reply": "yo", "appended": True}
    assert f.read_text().endswith("\n## Human\n\nhi\n\n## Assistant\n\nyo\n\n— m:latest\n")
    assert calls[0]["url"] == "http://localhost:11434/api/chat"
    assert calls[0]["payload"] == {
        "model": "m:latest",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False,
    }


def test_reply_multi_turn_context(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    ollama.reply(f, "http://localhost:11434", "m", "first")
    ollama.reply(f, "http://localhost:11434", "m", "second")
    assert [m["content"] for m in calls[1]["payload"]["messages"]] == ["first", "yo", "second"]


def test_reply_empty_message(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("")
    with pytest.raises(RuntimeError, match="empty message"):
        ollama.reply(f, "http://localhost:11434", "m", "   ")


def test_chat_unreachable(tmp_path, monkeypatch):
    def post(url, payload, timeout):
        raise urllib.error.URLError("connection refused")
    monkeypatch.setattr(ollama, "_http_post", post)
    f = tmp_path / "r.md"
    f.write_text("head\n")
    with pytest.raises(RuntimeError, match="unreachable"):
        ollama.reply(f, "http://localhost:1", "m", "hi")
    assert f.read_text() == "head\n"


def test_chat_http_error(monkeypatch):
    def post(url, payload, timeout):
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
    monkeypatch.setattr(ollama, "_http_post", post)
    with pytest.raises(RuntimeError, match="404"):
        ollama.chat("http://localhost:11434", "nope", [{"role": "user", "content": "hi"}], 5.0)


def test_chat_timeout(monkeypatch):
    def post(url, payload, timeout):
        raise TimeoutError()
    monkeypatch.setattr(ollama, "_http_post", post)
    with pytest.raises(RuntimeError, match="timed out"):
        ollama.chat("http://localhost:11434", "m", [{"role": "user", "content": "hi"}], 5.0)


def test_chat_malformed_response(monkeypatch):
    monkeypatch.setattr(ollama, "_http_post", lambda url, payload, timeout: {"done": True})
    with pytest.raises(RuntimeError, match="malformed"):
        ollama.chat("http://localhost:11434", "m", [{"role": "user", "content": "hi"}], 5.0)


def test_endpoint_trailing_slash(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    ollama.chat("http://localhost:11434/", "m", [{"role": "user", "content": "hi"}], 5.0)
    assert calls[0]["url"] == "http://localhost:11434/api/chat"
