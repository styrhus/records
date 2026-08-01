import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from recordkit import booth, create, ollama, writer


# ---------------------------------------------------------------- the draft buffer

def test_buffer_types_and_edits():
    b = booth.Buffer()
    for ch in "hei":
        b.insert(ch)
    b.newline()
    for ch in "du":
        b.insert(ch)
    assert b.text() == "hei\ndu"
    b.backspace()
    assert b.text() == "hei\nd"


def test_buffer_backspace_joins_lines():
    b = booth.Buffer("one\ntwo")
    b.home()
    b.backspace()
    assert (b.text(), b.row, b.col) == ("onetwo", 0, 3)


def test_buffer_delete_and_movement():
    b = booth.Buffer("abc")
    b.home()
    b.delete()
    assert b.text() == "bc"
    b.end()
    b.left()
    b.insert("X")
    assert b.text() == "bXc"


def test_buffer_up_down_clamp_the_column():
    b = booth.Buffer("short\nlonger line")
    b.end()
    b.up()
    assert (b.row, b.col) == (0, 5)
    b.down()
    assert (b.row, b.col) == (1, 5)


def test_buffer_takes_the_characters_norwegian_and_german_use():
    b = booth.Buffer()
    for ch in "blåbærsyltetøy über":
        b.insert(ch)
    assert b.text() == "blåbærsyltetøy über"
    b.backspace()
    assert b.text() == "blåbærsyltetøy übe"


def test_display_chunks_are_exact():
    assert booth._chunks("abcdef", 4) == ["abcd", "ef"]
    assert booth._chunks("", 4) == [""]


# ---------------------------------------------------------------- the session

def test_no_record_until_the_first_turn_is_submitted(tmp_path):
    s = booth.Session(records_dir=tmp_path)
    assert s.path is None
    assert list(tmp_path.iterdir()) == []
    s.submit("   ")  # nothing but whitespace stays nothing
    assert s.path is None


def test_submit_creates_then_appends(tmp_path):
    s = booth.Session(records_dir=tmp_path, arguments="#booth A Title")
    s.submit("first")
    created = s.path
    assert created == tmp_path / "booth" / "a-title.md"
    s.submit("second")
    assert s.path == created and s.turns == 2
    assert created.read_text(encoding="utf-8").endswith("\nfirst\n\nsecond\n")


def test_booth_output_is_byte_identical_to_new_plus_append(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()

    s = booth.Session(records_dir=a, arguments="Byte Check")
    s.submit("hei\n\nandre avsnitt")
    s.submit("tredje")

    reference = Path(create.new_record(b, arguments="Byte Check")["path"])
    writer.append_user(reference, "hei\n\nandre avsnitt")
    writer.append_user(reference, "tredje")

    def normalise(p):
        return "\n".join(ln for ln in p.read_text(encoding="utf-8").splitlines()
                         if not ln.startswith("date: "))

    assert s.path.name == reference.name
    assert normalise(s.path) == normalise(reference)


def test_file_continues_an_existing_record(tmp_path):
    existing = Path(create.new_record(tmp_path, arguments="Existing")["path"])
    before = sorted(p.name for p in tmp_path.iterdir())
    s = booth.Session(file=existing)
    s.submit("added")
    assert sorted(p.name for p in tmp_path.iterdir()) == before
    assert existing.read_text(encoding="utf-8").endswith("\nadded\n")


def test_missing_records_dir_fails_before_the_terminal(tmp_path):
    with pytest.raises(RuntimeError, match="no records directory"):
        booth.Session(records_dir=tmp_path / "nope")


def test_missing_file_fails(tmp_path):
    with pytest.raises(RuntimeError, match="not found"):
        booth.Session(file=tmp_path / "nope.md")


def test_endpoint_and_model_go_together(tmp_path):
    with pytest.raises(RuntimeError, match="go together"):
        booth.Session(records_dir=tmp_path, endpoint="http://localhost:11434")
    with pytest.raises(RuntimeError, match="go together"):
        booth.Session(records_dir=tmp_path, model="m:latest")


def test_transcript_drops_the_frontmatter(tmp_path):
    s = booth.Session(records_dir=tmp_path, arguments="T")
    s.submit("visible")
    assert s.transcript() == "visible"


# ---------------------------------------------------------------- the model half

def test_model_turn_is_written_signed(tmp_path, monkeypatch):
    monkeypatch.setattr(ollama, "_http_post",
                        lambda url, payload, timeout: {"message": {"content": "yo"}})
    s = booth.Session(records_dir=tmp_path, arguments="Talk",
                      endpoint="http://localhost:11434", model="m:latest", name="Ada")
    result = s.submit("hi")
    assert result == {"appended": True, "reply": "yo", "warning": None}
    assert s.path.read_text(encoding="utf-8").endswith(
        "\n## Human (Ada)\n\nhi\n\n## Assistant\n\nyo\n\n— m:latest\n")


def test_a_dead_model_never_costs_a_sentence(tmp_path, monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("ollama unreachable at http://localhost:11434: refused")

    monkeypatch.setattr(ollama, "chat", boom)
    s = booth.Session(records_dir=tmp_path, arguments="Talk",
                      endpoint="http://localhost:11434", model="m:latest")
    result = s.submit("words worth keeping")
    assert result["appended"] is True and result["reply"] is None
    assert "unreachable" in result["warning"]
    assert s.path.read_text(encoding="utf-8").endswith("\nwords worth keeping\n")
    assert "## Assistant" not in s.path.read_text(encoding="utf-8")


class _StubOllama(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        reply = "stub heard: " + body["messages"][-1]["content"]
        payload = json.dumps({"message": {"role": "assistant", "content": reply}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture
def stub_ollama():
    server = HTTPServer(("127.0.0.1", 0), _StubOllama)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server, f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_two_sided_session_over_real_http_then_fallback(tmp_path, stub_ollama):
    server, endpoint = stub_ollama
    s = booth.Session(records_dir=tmp_path, arguments="Stub", endpoint=endpoint,
                      model="stub:latest", timeout=5)
    first = s.submit("hallo")
    assert first["reply"] == "stub heard: hallo"

    server.shutdown()  # the model goes away mid-session
    server.server_close()
    second = s.submit("still writing")
    assert second["appended"] is True and second["reply"] is None and second["warning"]

    text = s.path.read_text(encoding="utf-8")
    assert "## Human\n\nhallo\n\n## Assistant\n\nstub heard: hallo\n\n— stub:latest" in text
    assert text.endswith("\nstill writing\n")
