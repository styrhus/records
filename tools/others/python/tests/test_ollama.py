# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

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


def test_parse_turns_named_human(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    writer.append_turn(f, "hi", "yo", "qwen2.5:14b", name="Ada Lovelace")
    turns = ollama.parse_turns(f.read_text())
    assert turns == [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]


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


def test_reply_with_preset_unreachable_still_appends_nothing(tmp_path):
    """The graceful no-model fallback, exercised with a preset set: this machine has no Ollama
    listening on 11434 (real connection refused, no mock), same contract as test_chat_unreachable —
    a preset changes the voice, never the failure behaviour. Nothing half-written reaches disk."""
    f = tmp_path / "r.md"
    f.write_text("head\n")
    preset = ollama.load_preset("pirate")
    with pytest.raises(RuntimeError, match="unreachable"):
        ollama.reply(f, "http://localhost:11434", "m", "hi", preset=preset, timeout=2.0)
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


def test_build_context_file_block(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("print('hi')\n")
    ctx = ollama.build_context([f], [])
    assert ctx.startswith("The user attached workspace context")
    assert f"### File: {f}\n```\nprint('hi')\n\n```" in ctx


def test_build_context_truncates_large_file(tmp_path):
    f = tmp_path / "big.txt"
    f.write_text("x" * (ollama.MAX_FILE_BYTES + 100))
    ctx = ollama.build_context([f], [])
    assert "… (truncated at 64 KiB)" in ctx
    assert len(ctx) < ollama.MAX_FILE_BYTES + 500


def test_build_context_binary_file(tmp_path):
    f = tmp_path / "blob.bin"
    f.write_bytes(b"\x00\x01\x02data")
    ctx = ollama.build_context([f], [])
    assert "(binary file — omitted)" in ctx
    assert "\x00" not in ctx


def test_build_context_missing_paths(tmp_path):
    ctx = ollama.build_context([tmp_path / "nope.txt"], [tmp_path / "nodir"])
    assert f"### File: {tmp_path / 'nope.txt'}\n(not found)" in ctx
    assert f"### Directory: {tmp_path / 'nodir'}\n(not found)" in ctx


def test_build_context_dir_listing(tmp_path):
    d = tmp_path / "src"
    (d / "sub").mkdir(parents=True)
    (d / "b.py").write_text("")
    (d / "sub" / "a.py").write_text("")
    (d / ".hidden").write_text("")
    (d / "node_modules").mkdir()
    (d / "node_modules" / "x.js").write_text("")
    ctx = ollama.build_context([], [d])
    assert f"### Directory: {d}\nb.py\nsub/a.py" in ctx
    assert ".hidden" not in ctx
    assert "node_modules" not in ctx


def test_build_context_empty():
    assert ollama.build_context([], []) == ""


def test_build_context_budget(tmp_path):
    files = []
    for i in range(6):
        f = tmp_path / f"f{i}.txt"
        f.write_text("y" * ollama.MAX_FILE_BYTES)
        files.append(f)
    ctx = ollama.build_context(files, [])
    assert "… (context budget exceeded, remaining attachments omitted)" in ctx
    assert len(ctx) < ollama.MAX_CONTEXT_BYTES + 1000


def test_reply_with_context_model_only(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    ollama.reply(f, "http://localhost:11434", "m", "hi", context="CTX")
    msgs = calls[0]["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": "CTX"}
    assert msgs[-1] == {"role": "user", "content": "hi"}
    # the record gets only the plain turn — context never touches the file
    assert "CTX" not in f.read_text()
    assert f.read_text().endswith("\n## Human\n\nhi\n\n## Assistant\n\nyo\n\n— m\n")


def test_reply_context_is_ephemeral(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    ollama.reply(f, "http://localhost:11434", "m", "first", context="CTX")
    ollama.reply(f, "http://localhost:11434", "m", "second")
    assert all(m["role"] != "system" for m in calls[1]["payload"]["messages"])


def test_ephemeral_reply_basic(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    r = ollama.ephemeral_reply("http://localhost:11434", "m:latest", "hi", [])
    assert r == {"model": "m:latest", "reply": "yo", "appended": False}
    assert calls[0]["payload"]["messages"] == [{"role": "user", "content": "hi"}]


def test_ephemeral_reply_with_history(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    history = [{"role": "user", "content": "first"}, {"role": "assistant", "content": "yo"}]
    ollama.ephemeral_reply("http://localhost:11434", "m", "second", history)
    assert [m["content"] for m in calls[0]["payload"]["messages"]] == ["first", "yo", "second"]
    # the caller's list is not mutated
    assert len(history) == 2


def test_ephemeral_reply_with_context(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    ollama.ephemeral_reply("http://localhost:11434", "m", "hi",
                           [{"role": "user", "content": "old"}], context="CTX")
    msgs = calls[0]["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": "CTX"}
    assert msgs[1] == {"role": "user", "content": "old"}
    assert msgs[-1] == {"role": "user", "content": "hi"}


def test_ephemeral_reply_empty_message():
    with pytest.raises(RuntimeError, match="empty message"):
        ollama.ephemeral_reply("http://localhost:11434", "m", "   ", [])


@pytest.mark.parametrize("history", [
    "not a list",
    [{"role": "system", "content": "x"}],
    [{"role": "user"}],
    [{"role": "user", "content": 42}],
    ["plain string"],
])
def test_ephemeral_reply_invalid_history(history):
    with pytest.raises(RuntimeError, match="invalid history"):
        ollama.ephemeral_reply("http://localhost:11434", "m", "hi", history)


def test_cli_ollama_chat_inline_history(monkeypatch, capsys):
    import json

    from recordkit import cli

    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    rc = cli.main(["ollama-chat", "--endpoint", "http://localhost:11434", "--model", "m",
                   "--human", "second",
                   "--history", '[{"role": "user", "content": "first"},'
                                ' {"role": "assistant", "content": "yo"}]'])
    assert rc == 0
    assert [m["content"] for m in calls[0]["payload"]["messages"]] == ["first", "yo", "second"]
    out = json.loads(capsys.readouterr().out)
    assert out == {"model": "m", "reply": "yo", "appended": False}


def test_cli_ollama_chat_history_stdin(monkeypatch):
    import io

    from recordkit import cli

    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    monkeypatch.setattr("sys.stdin", io.StringIO('[{"role": "user", "content": "first"}]'))
    rc = cli.main(["ollama-chat", "--endpoint", "http://localhost:11434", "--model", "m",
                   "--human", "hi", "--history", "-"])
    assert rc == 0
    assert [m["content"] for m in calls[0]["payload"]["messages"]] == ["first", "hi"]


def test_cli_ollama_chat_default_history(monkeypatch):
    from recordkit import cli

    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    rc = cli.main(["ollama-chat", "--endpoint", "http://localhost:11434", "--model", "m",
                   "--human", "hi"])
    assert rc == 0
    assert calls[0]["payload"]["messages"] == [{"role": "user", "content": "hi"}]


def test_cli_ollama_chat_bad_json(monkeypatch, capsys):
    import json

    from recordkit import cli

    monkeypatch.setattr(ollama, "_http_post", _mock_post([]))
    rc = cli.main(["ollama-chat", "--endpoint", "http://localhost:11434", "--model", "m",
                   "--human", "hi", "--history", "{nope"])
    assert rc == 1
    out = json.loads(capsys.readouterr().out)
    assert "invalid history JSON" in out["error"]


def test_cli_ollama_chat_context_flags(tmp_path, monkeypatch):
    from recordkit import cli

    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    src = tmp_path / "a.py"
    src.write_text("code\n")
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "m.py").write_text("")
    rc = cli.main(["ollama-chat", "--endpoint", "http://localhost:11434", "--model", "m",
                   "--human", "hi", "--context-file", str(src), "--context-dir", str(d)])
    assert rc == 0
    system = calls[0]["payload"]["messages"][0]
    assert system["role"] == "system"
    assert f"### File: {src}" in system["content"]
    assert f"### Directory: {d}" in system["content"]
    assert not list(tmp_path.glob("*.md"))


def test_cli_context_flags(tmp_path, monkeypatch):
    from recordkit import cli

    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    src = tmp_path / "a.py"
    src.write_text("code\n")
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "m.py").write_text("")
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    rc = cli.main(["ollama-reply", "--endpoint", "http://localhost:11434", "--model", "m",
                   "--file", str(f), "--human", "hi",
                   "--context-file", str(src), "--context-dir", str(d)])
    assert rc == 0
    system = calls[0]["payload"]["messages"][0]
    assert system["role"] == "system"
    assert f"### File: {src}" in system["content"]
    assert f"### Directory: {d}" in system["content"]


def test_load_preset_pirate():
    text = ollama.load_preset("pirate")
    assert "pirate" in text.lower()
    assert text == text.strip()  # no leading/trailing whitespace left in


def test_load_preset_poet():
    assert "poetic" in ollama.load_preset("poet").lower()


def test_load_preset_bff():
    assert "best friend" in ollama.load_preset("bff").lower()


def test_load_preset_unknown():
    with pytest.raises(RuntimeError, match="unknown preset"):
        ollama.load_preset("nope-not-a-voice")


@pytest.mark.parametrize("name", ["", "../pirate", "sub/pirate", ".", ".."])
def test_load_preset_rejects_path_traversal(name):
    with pytest.raises(RuntimeError, match="unknown preset"):
        ollama.load_preset(name)


def test_reply_with_preset_is_a_system_message(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    preset = ollama.load_preset("pirate")
    ollama.reply(f, "http://localhost:11434", "m", "hi", preset=preset)
    msgs = calls[0]["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": preset}
    assert msgs[-1] == {"role": "user", "content": "hi"}
    # the record gets only the plain turn — the preset never touches the file
    assert preset not in f.read_text()
    assert f.read_text().endswith("\n## Human\n\nhi\n\n## Assistant\n\nyo\n\n— m\n")


def test_reply_preset_precedes_context(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    ollama.reply(f, "http://localhost:11434", "m", "hi", preset="VOICE", context="CTX")
    msgs = calls[0]["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": "VOICE"}
    assert msgs[1] == {"role": "system", "content": "CTX"}
    assert msgs[-1] == {"role": "user", "content": "hi"}


def test_reply_preset_is_ephemeral(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    ollama.reply(f, "http://localhost:11434", "m", "first", preset="VOICE")
    ollama.reply(f, "http://localhost:11434", "m", "second")
    assert all(m["role"] != "system" for m in calls[1]["payload"]["messages"])


def test_ephemeral_reply_with_preset(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    preset = ollama.load_preset("poet")
    r = ollama.ephemeral_reply("http://localhost:11434", "m", "hi", [], preset=preset)
    assert r == {"model": "m", "reply": "yo", "appended": False}
    msgs = calls[0]["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": preset}
    assert msgs[-1] == {"role": "user", "content": "hi"}


def test_ephemeral_reply_preset_precedes_context(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    ollama.ephemeral_reply("http://localhost:11434", "m", "hi", [], preset="VOICE", context="CTX")
    msgs = calls[0]["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": "VOICE"}
    assert msgs[1] == {"role": "system", "content": "CTX"}


def test_ephemeral_reply_pirate_preset_payload_acceptance_equivalent(monkeypatch):
    """Exercises the assembled request payload for `records ollama-chat --preset pirate
    --human "hello"` (item 3's acceptance command). --preset is not yet wired into cli.py
    (see the reported diff), so this drives the same call cli.main() would make once it is:
    ollama.load_preset(name) -> ollama.ephemeral_reply(..., preset=text)."""
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls, content="Ahoy, matey!"))
    preset = ollama.load_preset("pirate")
    r = ollama.ephemeral_reply("http://localhost:11434", "m", "hello", [], preset=preset)
    assert r == {"model": "m", "reply": "Ahoy, matey!", "appended": False}
    assert calls[0]["payload"] == {
        "model": "m",
        "messages": [
            {"role": "system", "content": preset},
            {"role": "user", "content": "hello"},
        ],
        "stream": False,
    }


def _mock_stream(calls, chunks=None):
    """Line-delimited chunks, mirroring Ollama's /api/chat stream=true response."""
    if chunks is None:
        chunks = [{"message": {"content": "he"}, "done": False},
                  {"message": {"content": "llo"}, "done": False},
                  {"message": {"content": ""}, "done": True}]

    def post(url, payload, timeout):
        calls.append({"url": url, "payload": payload, "timeout": timeout})
        return iter(chunks)
    return post


def test_chat_stream_yields_tokens_and_assembles(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(calls))
    tokens = list(ollama.chat_stream("http://localhost:11434", "m",
                                     [{"role": "user", "content": "hi"}], 5.0))
    assert tokens == ["he", "llo"]
    assert calls[0]["url"] == "http://localhost:11434/api/chat"
    assert calls[0]["payload"] == {
        "model": "m",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": True,
    }


def test_chat_stream_skips_empty_content_chunks(monkeypatch):
    calls = []
    chunks = [{"message": {"content": ""}, "done": False},
             {"message": {"content": "ok"}, "done": False},
             {"done": True}]
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(calls, chunks))
    tokens = list(ollama.chat_stream("http://localhost:11434", "m",
                                     [{"role": "user", "content": "hi"}], 5.0))
    assert tokens == ["ok"]


def test_chat_stream_http_error(monkeypatch):
    def post(url, payload, timeout):
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
    monkeypatch.setattr(ollama, "_http_post_stream", post)
    with pytest.raises(RuntimeError, match="404"):
        list(ollama.chat_stream("http://localhost:11434", "nope",
                                [{"role": "user", "content": "hi"}], 5.0))


def test_chat_stream_timeout(monkeypatch):
    def post(url, payload, timeout):
        raise TimeoutError()
    monkeypatch.setattr(ollama, "_http_post_stream", post)
    with pytest.raises(RuntimeError, match="timed out"):
        list(ollama.chat_stream("http://localhost:11434", "m",
                                [{"role": "user", "content": "hi"}], 5.0))


def test_chat_stream_fault_mid_stream(monkeypatch):
    """A chunk arrives, then the connection drops — the caller still sees a RuntimeError."""
    def flaky():
        yield {"message": {"content": "he"}, "done": False}
        raise urllib.error.URLError("connection reset")

    def post(url, payload, timeout):
        return flaky()
    monkeypatch.setattr(ollama, "_http_post_stream", post)
    gen = ollama.chat_stream("http://localhost:11434", "m", [{"role": "user", "content": "hi"}], 5.0)
    assert next(gen) == "he"
    with pytest.raises(RuntimeError, match="unreachable"):
        next(gen)


def test_chat_stream_unreachable_real_connection(monkeypatch):
    """No mock: a real connection-refused/no-listener failure, same contract as
    test_chat_unreachable but exercised through the streaming path."""
    with pytest.raises(RuntimeError, match="unreachable|timed out"):
        list(ollama.chat_stream("http://localhost:1", "m", [{"role": "user", "content": "hi"}], 2.0))


def test_reply_stream_yields_then_appends_once(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    gen = ollama.reply_stream(f, "http://localhost:11434", "m:latest", "hi")
    tokens = list(gen)
    assert tokens == ["he", "llo"]
    # nothing appended until the generator is fully drained
    assert f.read_text().endswith("\n## Human\n\nhi\n\n## Assistant\n\nhello\n\n— m:latest\n")
    assert calls[0]["payload"] == {
        "model": "m:latest",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": True,
    }


def test_reply_stream_byte_identical_to_reply(tmp_path, monkeypatch):
    """The determinism border: streamed tokens joined + stripped must match the non-streaming
    write byte for byte."""
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls, content="hello"))
    f1 = tmp_path / "r1.md"
    f1.write_text("---\ntitle: X\n---\n")
    ollama.reply(f1, "http://localhost:11434", "m", "hi")

    stream_calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(stream_calls))
    f2 = tmp_path / "r2.md"
    f2.write_text("---\ntitle: X\n---\n")
    list(ollama.reply_stream(f2, "http://localhost:11434", "m", "hi"))

    assert f1.read_text() == f2.read_text()


def test_reply_stream_appends_nothing_before_drained(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(calls))
    f = tmp_path / "r.md"
    f.write_text("head\n")
    gen = ollama.reply_stream(f, "http://localhost:11434", "m", "hi")
    next(gen)  # pulls one token — the record must still be untouched
    assert f.read_text() == "head\n"


def test_reply_stream_fault_mid_stream_appends_nothing(tmp_path, monkeypatch):
    def flaky():
        yield {"message": {"content": "he"}, "done": False}
        raise urllib.error.URLError("connection reset")
    monkeypatch.setattr(ollama, "_http_post_stream", lambda url, payload, timeout: flaky())
    f = tmp_path / "r.md"
    f.write_text("head\n")
    gen = ollama.reply_stream(f, "http://localhost:11434", "m", "hi")
    next(gen)
    with pytest.raises(RuntimeError, match="unreachable"):
        next(gen)
    assert f.read_text() == "head\n"


def test_reply_stream_empty_message(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("")
    with pytest.raises(RuntimeError, match="empty message"):
        list(ollama.reply_stream(f, "http://localhost:11434", "m", "   "))


def test_reply_stream_unreachable_real_connection_appends_nothing(tmp_path):
    """Same graceful-fallback contract as test_chat_unreachable, through the streaming path and
    with no mock at all — a real refused/absent connection."""
    f = tmp_path / "r.md"
    f.write_text("head\n")
    with pytest.raises(RuntimeError, match="unreachable|timed out"):
        list(ollama.reply_stream(f, "http://localhost:1", "m", "hi", timeout=2.0))
    assert f.read_text() == "head\n"


def test_ephemeral_reply_stream_yields_and_returns_nothing_written(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(calls))
    tokens = list(ollama.ephemeral_reply_stream("http://localhost:11434", "m:latest", "hi", []))
    assert tokens == ["he", "llo"]
    assert calls[0]["payload"]["messages"] == [{"role": "user", "content": "hi"}]


def test_ephemeral_reply_stream_with_history_and_context(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(calls))
    history = [{"role": "user", "content": "first"}, {"role": "assistant", "content": "yo"}]
    list(ollama.ephemeral_reply_stream("http://localhost:11434", "m", "second", history,
                                       context="CTX"))
    msgs = calls[0]["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": "CTX"}
    assert [m["content"] for m in msgs[1:]] == ["first", "yo", "second"]
    # the caller's list is not mutated, same contract as ephemeral_reply()
    assert len(history) == 2


def test_ephemeral_reply_stream_with_preset(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(calls))
    preset = ollama.load_preset("pirate")
    list(ollama.ephemeral_reply_stream("http://localhost:11434", "m", "hi", [], preset=preset))
    msgs = calls[0]["payload"]["messages"]
    assert msgs[0] == {"role": "system", "content": preset}


def test_ephemeral_reply_stream_empty_message():
    with pytest.raises(RuntimeError, match="empty message"):
        list(ollama.ephemeral_reply_stream("http://localhost:11434", "m", "   ", []))


def test_ephemeral_reply_stream_invalid_history():
    with pytest.raises(RuntimeError, match="invalid history"):
        list(ollama.ephemeral_reply_stream("http://localhost:11434", "m", "hi", "not a list"))


def _drive(gen):
    """Fully consume a streaming generator, returning (tokens, stop_value) — the shape a CLI
    driver (or a plugin) uses to get both the live tokens and the final result dict."""
    tokens = []
    try:
        while True:
            tokens.append(next(gen))
    except StopIteration as stop:
        return tokens, stop.value


def test_reply_stream_return_value_matches_reply(tmp_path, monkeypatch):
    """The generator's `return` becomes StopIteration.value — this is what a cli.py --stream
    driver would emit as the final NDJSON line, and it must match reply()'s return exactly."""
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls, content="hello"))
    f1 = tmp_path / "r1.md"
    f1.write_text("---\ntitle: X\n---\n")
    expected = ollama.reply(f1, "http://localhost:11434", "m", "hi")

    stream_calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(stream_calls))
    f2 = tmp_path / "r2.md"
    f2.write_text("---\ntitle: X\n---\n")
    tokens, result = _drive(ollama.reply_stream(f2, "http://localhost:11434", "m", "hi"))
    assert tokens == ["he", "llo"]
    assert result == {**expected, "file": str(f2)}


def test_ephemeral_reply_stream_return_value_matches_ephemeral_reply(monkeypatch):
    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls, content="hello"))
    expected = ollama.ephemeral_reply("http://localhost:11434", "m", "hi", [])

    stream_calls = []
    monkeypatch.setattr(ollama, "_http_post_stream", _mock_stream(stream_calls))
    tokens, result = _drive(ollama.ephemeral_reply_stream("http://localhost:11434", "m", "hi", []))
    assert tokens == ["he", "llo"]
    assert result == expected


def test_ephemeral_reply_stream_malformed_empty_reply(monkeypatch):
    monkeypatch.setattr(ollama, "_http_post_stream",
                        lambda url, payload, timeout: iter([{"done": True}]))
    with pytest.raises(RuntimeError, match="malformed"):
        list(ollama.ephemeral_reply_stream("http://localhost:11434", "m", "hi", []))


def test_cli_no_context_flags(tmp_path, monkeypatch):
    from recordkit import cli

    calls = []
    monkeypatch.setattr(ollama, "_http_post", _mock_post(calls))
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    rc = cli.main(["ollama-reply", "--endpoint", "http://localhost:11434", "--model", "m",
                   "--file", str(f), "--human", "hi"])
    assert rc == 0
    assert calls[0]["payload"]["messages"] == [{"role": "user", "content": "hi"}]
