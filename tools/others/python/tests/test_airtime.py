# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
import json

import pytest

from recordkit import airtime, cli

RECORD = """---
date: 2026-08-18T10:00:00+02:00
tags: [test]
---

## Human

Say hi in one word.

## Assistant

Hi!

— some-model

## Human (Ada)

And in two words?

## Assistant

Hello there.

— some-model
"""


def test_estimate_tokens_rounds_up_and_ignores_blank():
    assert airtime.estimate_tokens("") == 0
    assert airtime.estimate_tokens("   \n") == 0
    assert airtime.estimate_tokens("abcd") == 1
    assert airtime.estimate_tokens("abcde") == 2
    assert airtime.estimate_tokens("  abcd  ") == 1


def test_measure_file_counts_both_sides_without_signatures(tmp_path):
    f = tmp_path / "r.md"
    f.write_text(RECORD)
    r = airtime.measure_file(f)
    assert r["file"] == str(f)
    # named Human turns (## Human (Ada)) count as human
    assert r["human_tokens"] == (airtime.estimate_tokens("Say hi in one word.")
                                 + airtime.estimate_tokens("And in two words?"))
    # the "— some-model" signature lines are not counted
    assert r["assistant_tokens"] == (airtime.estimate_tokens("Hi!")
                                     + airtime.estimate_tokens("Hello there."))
    assert r["turns"] == {"human": 2, "assistant": 2}
    assert r["human_pct"] + r["assistant_pct"] == 100
    assert r["line"] == f"Human: {r['human_pct']}%, Assistant: {r['assistant_pct']}%"


def test_measure_percents_are_whole_and_sum_to_100():
    r = airtime.measure([{"role": "user", "content": "abcd"},
                         {"role": "assistant", "content": "abcdefgh"}])
    assert (r["human_tokens"], r["assistant_tokens"]) == (1, 2)
    assert (r["human_pct"], r["assistant_pct"]) == (33, 67)
    assert r["line"] == "Human: 33%, Assistant: 67%"


def test_measure_rounds_half_up():
    # 1 vs 7 → 12.5% → 13; the assistant side is derived so the pair still sums to 100
    r = airtime.measure([{"role": "user", "content": "abcd"},
                         {"role": "assistant", "content": "a" * 28}])
    assert (r["human_pct"], r["assistant_pct"]) == (13, 87)


def test_measure_empty_is_zero_zero(tmp_path):
    assert airtime.measure([])["line"] == "Human: 0%, Assistant: 0%"
    f = tmp_path / "empty.md"
    f.write_text("---\ndate: 2026-08-18T10:00:00+02:00\n---\n\nno turns here\n")
    r = airtime.measure_file(f)
    assert (r["human_tokens"], r["assistant_tokens"], r["human_pct"], r["assistant_pct"]) == (0, 0, 0, 0)


@pytest.mark.parametrize("history", ["nope", [{"role": "system", "content": "x"}],
                                     [{"role": "user"}], [{"role": "user", "content": 1}]])
def test_measure_history_invalid(history):
    with pytest.raises(RuntimeError, match="invalid history"):
        airtime.measure_history(history)


def test_cli_airtime_file(tmp_path, capsys):
    f = tmp_path / "r.md"
    f.write_text(RECORD)
    assert cli.main(["airtime", "--file", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["file"] == str(f)
    assert out["line"].startswith("Human: ") and out["human_pct"] + out["assistant_pct"] == 100


def test_cli_airtime_history_inline(capsys):
    assert cli.main(["airtime", "--history",
                     '[{"role": "user", "content": "abcd"}, {"role": "assistant", "content": "abcdefgh"}]']) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["line"] == "Human: 33%, Assistant: 67%"
    assert "file" not in out


def test_cli_airtime_history_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("[]"))
    assert cli.main(["airtime", "--history", "-"]) == 0
    assert json.loads(capsys.readouterr().out)["line"] == "Human: 0%, Assistant: 0%"


def test_cli_airtime_bad_json(capsys):
    assert cli.main(["airtime", "--history", "{nope"]) == 1
    assert "invalid history JSON" in json.loads(capsys.readouterr().out)["error"]


def test_cli_airtime_needs_exactly_one_source(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["airtime"])
    with pytest.raises(SystemExit):
        cli.main(["airtime", "--file", str(tmp_path / "r.md"), "--history", "[]"])
