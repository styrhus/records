"""Smoke tests for the argparse wiring in `recordkit.cli` — one per subcommand.

`cli.py` is the one module every plugin goes through and the only one with no tests: the
modules under it are covered, the wiring between them is not. The bug class here is wiring,
not logic — a flag renamed on one side only, an argument passed positionally that the callee
now takes by keyword, a subcommand that parses and then reaches the wrong module. So each
test replaces the module function the command is supposed to reach, runs `cli.main(...)`,
and asserts three things: that function was called, with the arguments the CLI promises,
and the process exit code. Nothing below executes real work.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from recordkit import cli


class Spy:
    """Stands in for a module function: records how it was called, returns a fixed result."""

    def __init__(self, result=None):
        self.calls: list[tuple[tuple, dict]] = []
        self.result = {"ok": True} if result is None else result

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result

    @property
    def args(self) -> tuple:
        assert len(self.calls) == 1, f"expected exactly one call, got {len(self.calls)}"
        return self.calls[0][0]

    @property
    def kwargs(self) -> dict:
        assert len(self.calls) == 1, f"expected exactly one call, got {len(self.calls)}"
        return self.calls[0][1]


def run(capsys, argv: list[str]) -> tuple[int, dict]:
    """Run the CLI and return (exit code, the single JSON object it printed)."""
    code = cli.main(argv)
    out = capsys.readouterr().out
    return code, json.loads(out) if out.strip() else {}


@pytest.fixture
def no_saved_name(monkeypatch):
    """`--name` defaults to the saved /myname name, which would read the real filesystem."""
    monkeypatch.setattr(cli.myname, "load", lambda *a, **k: None)


# --- the JSON-on-stdout commands ---------------------------------------------

def test_new(capsys, monkeypatch):
    spy = Spy({"path": "r.md"})
    monkeypatch.setattr(cli.create, "new_record", spy)
    code, out = run(capsys, ["new", "#linux", "How", "to", "--dir", "/rec",
                             "--tags", "a, b", "--title", "T", "--draft"])
    assert (code, out) == (0, {"path": "r.md"})
    assert spy.args == (Path("/rec"),)
    assert spy.kwargs == {"arguments": "#linux How to", "draft": True,
                          "tags": ["a", "b"], "title": "T"}


def test_append(capsys, monkeypatch):
    spy = Spy()
    monkeypatch.setattr(cli.writer, "append_user", spy)
    code, out = run(capsys, ["append", "--file", "r.md", "--text", "hi"])
    assert (code, out) == (0, {"file": "r.md", "appended": True})
    assert spy.args == (Path("r.md"), "hi")


def test_append_reads_stdin_for_a_dash(capsys, monkeypatch):
    spy = Spy()
    monkeypatch.setattr(cli.writer, "append_user", spy)
    monkeypatch.setattr(cli.sys, "stdin", _Stdin("from stdin"))
    code, _ = run(capsys, ["append", "--file", "r.md", "--text", "-"])
    assert code == 0
    assert spy.args == (Path("r.md"), "from stdin")


def test_append_turn(capsys, monkeypatch):
    spy = Spy()
    monkeypatch.setattr(cli.writer, "append_turn", spy)
    code, out = run(capsys, ["append-turn", "--file", "r.md", "--human", "h",
                             "--assistant", "a", "--model", "m", "--name", "tb4"])
    assert (code, out) == (0, {"file": "r.md", "appended": True})
    assert spy.args == (Path("r.md"), "h", "a", "m")
    assert spy.kwargs == {"name": "tb4"}


def test_ollama_reply(capsys, monkeypatch, no_saved_name):
    spy = Spy({"reply": "hello", "appended": True})
    monkeypatch.setattr(cli.ollama, "reply", spy)
    code, out = run(capsys, ["ollama-reply", "--endpoint", "http://h:11434", "--model", "m",
                             "--file", "r.md", "--human", "h", "--timeout", "5"])
    assert (code, out) == (0, {"reply": "hello", "appended": True})
    assert spy.args == (Path("r.md"), "http://h:11434", "m", "h")
    assert spy.kwargs == {"timeout": 5.0, "context": None, "preset": None, "name": None}


def test_ollama_chat(capsys, monkeypatch):
    spy = Spy({"reply": "hello", "appended": False})
    monkeypatch.setattr(cli.ollama, "ephemeral_reply", spy)
    code, out = run(capsys, ["ollama-chat", "--endpoint", "http://h:11434", "--model", "m",
                             "--human", "h", "--history", '[{"role": "user", "content": "x"}]'])
    assert (code, out) == (0, {"reply": "hello", "appended": False})
    assert spy.args == ("http://h:11434", "m", "h", [{"role": "user", "content": "x"}])
    assert spy.kwargs == {"timeout": cli.ollama.DEFAULT_TIMEOUT, "context": None, "preset": None}


def test_stick(capsys, monkeypatch):
    spy = Spy({"path": "r.md", "featured": True})
    monkeypatch.setattr(cli.stick, "feature_file", spy)
    code, out = run(capsys, ["stick", "--file", "r.md"])
    assert (code, out) == (0, {"path": "r.md", "featured": True})
    assert spy.args == (Path("r.md"),)


def test_stick_by_slug(capsys, monkeypatch):
    monkeypatch.setattr(cli.stick, "find_record", Spy([Path("/rec/how-to.md")]))
    spy = Spy({"path": "/rec/how-to.md", "featured": True})
    monkeypatch.setattr(cli.stick, "feature_file", spy)
    code, _ = run(capsys, ["stick", "--slug", "how-to", "--dir", "/rec"])
    assert code == 0
    assert spy.args == (Path("/rec/how-to.md"),)


def test_commit(capsys, monkeypatch):
    spy = Spy({"committed": True})
    monkeypatch.setattr(cli.commit_mod, "commit", spy)
    code, out = run(capsys, ["commit", "-m", "msg", "--push", "--deploy", "--repo", "/r"])
    assert (code, out) == (0, {"committed": True})
    assert spy.args == (Path("/r"), "msg")
    assert spy.kwargs == {"push": True, "deploy": True}


def test_publish(capsys, monkeypatch):
    spy = Spy({"target": "pages-branch"})
    monkeypatch.setattr(cli.publish, "publish", spy)
    code, out = run(capsys, ["publish", "--repo", "/r", "--dry-run"])
    assert (code, out) == (0, {"target": "pages-branch"})
    assert spy.args == (Path("/r"),)
    assert spy.kwargs == {"dry_run": True}


def test_myname(capsys, monkeypatch):
    spy = Spy({"name": "tb4"})
    monkeypatch.setattr(cli.myname, "save", spy)
    code, out = run(capsys, ["myname", "tb4", "--memory-dir", "/mem"])
    assert (code, out) == (0, {"name": "tb4"})
    assert spy.args == ("tb4", Path("/mem"))


def test_mucke(capsys, monkeypatch):
    spy = Spy({"stamped": True})
    monkeypatch.setattr(cli.mucke, "stamp", spy)
    code, out = run(capsys, ["mucke", "--file", "r.md"])
    assert (code, out) == (0, {"stamped": True})
    assert spy.args == (Path("r.md"),)


def test_airtime_from_a_record(capsys, monkeypatch):
    spy = Spy({"line": "Human: 40%, Assistant: 60%"})
    monkeypatch.setattr(cli.airtime, "measure_file", spy)
    code, out = run(capsys, ["airtime", "--file", "r.md"])
    assert (code, out) == (0, {"line": "Human: 40%, Assistant: 60%"})
    assert spy.args == (Path("r.md"),)


def test_airtime_from_a_history(capsys, monkeypatch):
    spy = Spy({"line": "Human: 50%, Assistant: 50%"})
    monkeypatch.setattr(cli.airtime, "measure_history", spy)
    code, _ = run(capsys, ["airtime", "--history", '[{"role": "user", "content": "x"}]'])
    assert code == 0
    assert spy.args == ([{"role": "user", "content": "x"}],)


def test_werden(capsys, monkeypatch):
    spy = Spy({"new": "0.1.2 fuglekasse-beetle"})
    monkeypatch.setattr(cli.werden, "cycle", spy)
    code, out = run(capsys, ["werden", "postkasse", "--stamp", "--repo", "/r"])
    assert (code, out) == (0, {"new": "0.1.2 fuglekasse-beetle"})
    assert spy.args == (Path("/r"), "postkasse")
    assert spy.kwargs == {"stamp": True}


def test_config(capsys):
    code, out = run(capsys, ["config", "--dir", "/rec"])
    assert (code, out) == (0, {"records_dir": "/rec", "source": "--dir", "exists": False})


def test_import(capsys, monkeypatch):
    spy = Spy({"imported": 3})
    monkeypatch.setattr(cli.importer, "run", spy)
    code, out = run(capsys, ["import", "--source", "llm", "--path", "/e.json", "--dir", "/rec",
                             "--tags", "a,b", "--dry-run", "--name", "tb4"])
    assert (code, out) == (0, {"imported": 3})
    assert spy.args == ("llm", Path("/e.json"), Path("/rec"))
    assert spy.kwargs == {"tags": ["a", "b"], "name": "tb4", "dry_run": True}


def test_archive(capsys, monkeypatch):
    spy = Spy({"out": "records.zip"})
    monkeypatch.setattr(cli.archive_mod, "archive", spy)
    code, out = run(capsys, ["archive", "--repo", "/r", "--out", "a.zip", "--dry-run"])
    assert (code, out) == (0, {"out": "records.zip"})
    assert spy.args == (Path("/r"), Path("a.zip"))
    assert spy.kwargs == {"dry_run": True}


def test_verify_an_archive(capsys, monkeypatch):
    spy = Spy({"ok": True})
    monkeypatch.setattr(cli.verify, "verify_archive", spy)
    code, out = run(capsys, ["verify", "a.zip"])
    assert (code, out) == (0, {"ok": True})
    assert spy.args == (Path("a.zip"),)


def test_verify_a_checkout(capsys, monkeypatch):
    spy = Spy({"ok": True})
    monkeypatch.setattr(cli.verify, "verify_repo", spy)
    code, _ = run(capsys, ["verify", "--repo", "/r"])
    assert code == 0
    assert spy.args == (Path("/r"),)


def test_export(capsys, monkeypatch):
    spy = Spy({"written": 4})
    monkeypatch.setattr(cli.export_mod, "export", spy)
    code, out = run(capsys, ["export", "--repo", "/r", "--out", "/out", "--single"])
    assert (code, out) == (0, {"written": 4})
    assert spy.args == (Path("/r"), Path("/out"))
    assert spy.kwargs == {"single": True}


def test_attach(capsys, monkeypatch):
    spy = Spy({"bundle": True})
    monkeypatch.setattr(cli.attach, "attach", spy)
    code, out = run(capsys, ["attach", "r.md", "a.png", "b.png",
                             "--title", "T", "--append", "--dry-run"])
    assert (code, out) == (0, {"bundle": True})
    assert spy.args == (Path("r.md"), [Path("a.png"), Path("b.png")])
    assert spy.kwargs == {"title": "T", "append": True, "dry_run": True}


def test_pack(capsys, monkeypatch):
    spy = Spy({"out": "pack/index.html"})
    monkeypatch.setattr(cli.pack_mod, "pack", spy)
    code, out = run(capsys, ["pack", "--repo", "/r", "--out", "/o.html",
                             "--no-images", "--with-books", "--outdir", "/public"])
    assert (code, out) == (0, {"out": "pack/index.html"})
    assert spy.args == (Path("/r"), Path("/o.html"))
    assert spy.kwargs == {"images": False, "with_books": True, "outdir": Path("/public")}


def test_card(capsys, monkeypatch):
    spy = Spy({"out": "r-card.svg"})
    monkeypatch.setattr(cli.card, "build", spy)
    code, out = run(capsys, ["card", "r.md", "--turn", "2", "--out", "c.svg",
                             "--url", "https://x/", "--repo", "/r"])
    assert (code, out) == (0, {"out": "r-card.svg"})
    assert spy.args == (Path("r.md"),)
    assert spy.kwargs == {"turn": 2, "out": Path("c.svg"), "url": "https://x/", "repo": Path("/r")}


def test_booth(capsys, monkeypatch):
    spy = Spy({"path": "r.md"})
    monkeypatch.setattr(cli.booth, "run", spy)
    code, out = run(capsys, ["booth", "#linux", "How", "--dir", "/rec", "--draft",
                             "--file", "r.md", "--endpoint", "http://h:11434",
                             "--model", "m", "--timeout", "5", "--name", "tb4"])
    assert (code, out) == (0, {"path": "r.md"})
    assert spy.args == (Path("/rec"),)
    assert spy.kwargs == {"arguments": "#linux How", "draft": True, "file": Path("r.md"),
                          "endpoint": "http://h:11434", "model": "m", "timeout": 5.0,
                          "name": "tb4"}


def test_redact(capsys, monkeypatch):
    spy = Spy({"written": True})
    monkeypatch.setattr(cli.redact, "redact", spy)
    code, out = run(capsys, ["redact", "r.md", "--turn", "2", "--replace", "x", "--yes"])
    assert (code, out) == (0, {"written": True})
    assert spy.args == (Path("r.md"), 2)
    assert spy.kwargs == {"replace": "x", "remove": False, "dry_run": False, "yes": True}


def test_unpublish(capsys, monkeypatch):
    spy = Spy({"unpublished": True})
    monkeypatch.setattr(cli.unpublish, "unpublish", spy)
    code, out = run(capsys, ["unpublish", "how-to", "--tombstone", "--dir", "/rec", "--dry-run"])
    assert (code, out) == (0, {"unpublished": True})
    assert spy.args == ("how-to",)
    assert spy.kwargs == {"tombstone": True, "records_dir": Path("/rec"), "dry_run": True}


def test_unpublish_restore(capsys, monkeypatch):
    spy = Spy({"restored": True})
    monkeypatch.setattr(cli.unpublish, "restore", spy)
    code, _ = run(capsys, ["unpublish", "how-to", "--restore", "--dir", "/rec"])
    assert code == 0
    assert spy.args == ("how-to",)
    assert spy.kwargs == {"records_dir": Path("/rec"), "dry_run": False}


# --- the four that own their own output --------------------------------------
#
# `doctor`, `watch`, `scan` and `ignore` are intercepted before the main parser runs and handed
# their argv verbatim, because argparse.REMAINDER cannot carry leading options through a
# subparser. The wiring to check is exactly that: the right module, the rest of argv untouched
# (options included), and the module's own exit code returned rather than swallowed.

_PASSTHROUGH_CASES = [
    ("doctor", ["doctor", "--repo", "/r"], ["--repo", "/r"]),
    ("watch", ["watch", "--interval", "2"], ["--interval", "2"]),
    ("scan", ["scan", "--dir", "/rec"], ["--dir", "/rec"]),
    ("ignore", ["ignore", "--check"], ["--check"]),
]


@pytest.mark.parametrize("name, argv, rest", _PASSTHROUGH_CASES)
def test_passthrough_commands(capsys, monkeypatch, name, argv, rest):
    spy = Spy(0)
    monkeypatch.setattr(cli._PASSTHROUGH[name], "main", spy)
    assert cli.main(argv) == 0
    assert spy.args == (rest,)
    assert capsys.readouterr().out == ""      # they print for themselves, not through _emit


def test_passthrough_returns_the_modules_exit_code(monkeypatch):
    monkeypatch.setattr(cli._PASSTHROUGH["doctor"], "main", Spy(2))
    assert cli.main(["doctor"]) == 2


# --- the exit codes the CLI itself decides ------------------------------------

def test_stick_by_slug_not_found_is_an_error(capsys, monkeypatch):
    monkeypatch.setattr(cli.stick, "find_record", Spy([]))
    code, out = run(capsys, ["stick", "--slug", "nope", "--dir", "/rec"])
    assert (code, out) == (1, {"error": "not found", "slug": "nope"})


def test_stick_by_slug_ambiguous_is_an_error(capsys, monkeypatch):
    monkeypatch.setattr(cli.stick, "find_record", Spy([Path("/rec/a.md"), Path("/rec/b/a.md")]))
    code, out = run(capsys, ["stick", "--slug", "a", "--dir", "/rec"])
    assert code == 1
    assert out["error"] == "ambiguous"


def test_verify_failure_is_a_nonzero_exit(capsys, monkeypatch):
    monkeypatch.setattr(cli.verify, "verify_repo", Spy({"ok": False}))
    code, out = run(capsys, ["verify"])
    assert (code, out) == (1, {"ok": False})


def test_archive_check_is_silent_when_it_passes(capsys, monkeypatch):
    monkeypatch.setattr(cli.archive_mod, "check", Spy({"ok": True}))
    code, out = run(capsys, ["archive", "--check"])
    assert (code, out) == (0, {})             # cron mails what it prints


def test_archive_check_reports_when_it_fails(capsys, monkeypatch):
    monkeypatch.setattr(cli.archive_mod, "check", Spy({"ok": False}))
    code, out = run(capsys, ["archive", "--check"])
    assert (code, out) == (1, {"ok": False})


def test_a_declined_redact_is_not_success(capsys, monkeypatch):
    monkeypatch.setattr(cli.redact, "redact", Spy({"written": False}))
    code, out = run(capsys, ["redact", "r.md", "--turn", "1", "--remove"])
    assert (code, out) == (1, {"written": False})


def test_a_module_raising_becomes_json_and_exit_1(capsys, monkeypatch):
    def boom(*a, **k):
        raise ValueError("no such record")

    monkeypatch.setattr(cli.mucke, "stamp", boom)
    code, out = run(capsys, ["mucke", "--file", "r.md"])
    assert (code, out) == (1, {"error": "no such record"})


def test_no_subcommand_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main([])
    assert e.value.code == 2


class _Stdin:
    def __init__(self, text: str):
        self._text = text

    def read(self) -> str:
        return self._text


# --- the file is only "one smoke test per subcommand" while something checks it ------
#
# AGENTS.md asks for a row here whenever a subcommand is added. Nothing enforced that, so a
# 28th subcommand would have gone green with no test at all. This asks the parser itself what
# it accepts and fails naming whatever has no test, rather than trusting a count someone took
# by hand once.

def _registered_subcommands() -> set[str]:
    """Every command the CLI accepts, read off the parser rather than off a list kept by hand."""
    action = next(a for a in cli._build_parser()._actions
                  if isinstance(a, argparse._SubParsersAction))
    return set(action.choices) | set(cli._PASSTHROUGH)


def _tested_subcommands() -> set[str]:
    """Commands this module has a smoke test for: `test_<slug>`, `test_<slug>_…`, or a
    passthrough case. `-` in a subcommand is `_` in a test name (`append-turn`)."""
    names = {n for n in globals() if n.startswith("test_")}
    covered = {name for name, _argv, _rest in _PASSTHROUGH_CASES}
    for cmd in _registered_subcommands():
        stem = "test_" + cmd.replace("-", "_")
        if any(n == stem or n.startswith(stem + "_") for n in names):
            covered.add(cmd)
    return covered


def test_every_subcommand_has_a_smoke_test():
    missing = sorted(_registered_subcommands() - _tested_subcommands())
    assert not missing, (
        "subcommands with no smoke test in this file: " + ", ".join(missing)
        + " — add one per AGENTS.md, or a row to _PASSTHROUGH_CASES if it owns its output"
    )


def test_the_coverage_check_reads_the_parser_and_not_a_hardcoded_list():
    """Guards the guard: if `_registered_subcommands` stopped seeing the parser, the check
    above would pass vacuously. It must find the commands that are actually registered."""
    found = _registered_subcommands()
    assert len(found) >= 27, found
    assert {"new", "append-turn", "unpublish"} <= found       # ordinary subparsers
    assert set(cli._PASSTHROUGH) <= found                     # and the four passthroughs
