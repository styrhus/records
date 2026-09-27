# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

import json

import pytest

from recordkit import scan


def _records(tmp_path, **files):
    """A records dir with the given name → contents."""
    rec = tmp_path / "records"
    rec.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        path = rec / name.replace("__", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return rec


def _rules(result):
    return {f["rule"] for f in result["findings"]}


def _record(body):
    return "---\ntitle: One\ndate: 2026-07-06T23:22:00+01:00\n---\n\n## Human\n\n" + body + "\n"


# --- the acceptance check: a planted secret is found --------------------------

PLANTED = "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


def test_planted_secret_is_found(tmp_path):
    _records(tmp_path,
             **{"2026-07-06_23-22.md": _record(f"here is the token: {PLANTED}"),
                "2026-07-07_10-00.md": _record("no secrets in this one, just prose")})
    result = scan.scan(tmp_path / "records")
    assert result["ok"] is False
    assert result["errors"] == 1
    finding = result["findings"][0]
    assert finding["rule"] == "token-prefix"
    assert finding["path"] == "2026-07-06_23-22.md"
    assert finding["line"] == 8      # front matter, blank, ## Human, blank, the body
    assert "rotate" in finding["remedy"]


def test_the_secret_is_never_printed_back(tmp_path):
    """A report that quotes the key has made another copy of it."""
    _records(tmp_path, **{"a.md": _record(PLANTED)})
    result = scan.scan(tmp_path / "records")
    text = scan.render(result) + json.dumps(result)
    assert PLANTED not in text
    assert PLANTED[:4] in text
    assert str(len(PLANTED)) in text


def test_clean_tree_is_ok_but_says_it_is_a_heuristic(tmp_path):
    _records(tmp_path, **{"a.md": _record("a conversation about gardening")})
    result = scan.scan(tmp_path / "records")
    assert result["ok"] is True
    assert result["findings"] == []
    assert "Heuristic" in scan.render(result)
    assert "not a promise" in scan.render(result)


# --- the rule families --------------------------------------------------------

@pytest.mark.parametrize("rule,text", [
    ("private-key", "-----BEGIN OPENSSH PRIVATE KEY-----"),
    ("private-key", "-----BEGIN RSA PRIVATE KEY-----"),
    ("token-prefix", "sk-ant-api03-" + "x" * 40),
    ("token-prefix", "AKIAIOSFODNN7EXAMPLE"),
    ("token-prefix", "glpat-" + "aB3" * 8),
    ("token-prefix", "xoxb-123456789012-abcdefghijkl"),
    ("jwt", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92"),
    ("url-credentials", "clone https://tb4:hunter2swordfish@git.example.org/x.git"),
    ("env-line", "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCY"),
    ("env-line", "export DATABASE_PASSWORD=correct-horse-battery"),
])
def test_named_shapes(rule, text):
    findings = scan.scan_text(text)
    assert rule in {f["rule"] for f in findings}


@pytest.mark.parametrize("text", [
    "the commit is 6f1a4c2b9e8d7f3a5c1b2d4e6f8a0c2e4d6b8f0a",     # a git sha
    "sha256: " + "0123456789abcdef" * 4,                          # a checksum
    "https://example.org/a/perfectly/ordinary/long/url/path/here",
    "a sentence that happens to run on for quite a long while indeed",
    "1234567890.1234567890.1234567890.1234",
])
def test_quiet_on_things_that_are_not_secrets(text):
    assert scan.scan_text(text) == []


def test_high_entropy_string_is_a_warning_not_an_error():
    findings = scan.scan_text("token = qX7vT2mKp9RzL4wYqX6cHjF8sD3gA5eU1oIiPl0Z")
    assert [f["rule"] for f in findings] == ["high-entropy"]
    assert findings[0]["level"] == "warn"


@pytest.mark.parametrize("text", [
    "background: var(--vscode-textCodeBlock-background);",          # an identifier path
    "see [the roadmap](../../../docs/records/developers/roadmap/kiste/ROADMAP.md)",
    'let $abc := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop0123456789-._~"',
    "https://open.spotify.com/playlist/4O49cydRwgT8wBITSY2Zgn0000000",
])
def test_the_entropy_heuristic_leaves_ordinary_code_alone(text):
    """Every one of these was a false positive on a real sweep of this repo."""
    assert scan.scan_text(text) == []


def test_named_rule_wins_over_entropy_on_the_same_span():
    """One finding per secret, not two — the named rule already said it."""
    findings = scan.scan_text(f"key: {PLANTED}")
    assert [f["rule"] for f in findings] == ["token-prefix"]


def test_the_more_specific_rule_wins_between_named_rules():
    """A token inside an .env line is one finding, named by its issuer."""
    findings = scan.scan_text(f"GITHUB_TOKEN={PLANTED}")
    assert [f["rule"] for f in findings] == ["token-prefix"]


def test_two_secrets_on_one_line_are_two_findings():
    findings = scan.scan_text(f"{PLANTED} and AKIAIOSFODNN7EXAMPLE")
    assert [f["rule"] for f in findings] == ["token-prefix", "token-prefix"]


def test_entropy_of_a_uniform_string_is_zero():
    assert scan._entropy("aaaaaaaa") == 0.0
    assert scan._entropy("") == 0.0
    assert scan._entropy("ab") == pytest.approx(1.0)


# --- what it reads ------------------------------------------------------------

def test_scans_attachments_not_only_markdown(tmp_path):
    """A pasted .env lands beside a record as a file, not as a transcript."""
    _records(tmp_path, **{"a.md": _record("see the attached env"),
                          "a__config.env": "API_TOKEN=s3cr3t-value-here\n"})
    result = scan.scan(tmp_path / "records")
    assert [f["path"] for f in result["findings"]] == ["a/config.env"]


def test_binary_files_are_skipped(tmp_path):
    rec = _records(tmp_path, **{"a.md": _record("hi")})
    (rec / "photo.png").write_bytes(b"\x89PNG\x00\x00" + PLANTED.encode())
    result = scan.scan(tmp_path / "records")
    assert result["skipped"] == 1
    assert result["findings"] == []


def test_dot_directories_are_not_walked(tmp_path):
    rec = _records(tmp_path, **{"a.md": _record("hi")})
    (rec / ".git").mkdir()
    (rec / ".git" / "config").write_text(PLANTED, encoding="utf-8")
    assert scan.scan(rec)["ok"] is True


def test_ignored_and_draft_records_are_still_scanned(tmp_path):
    """Neither keeps a file out of git, and git is what leaks."""
    _records(tmp_path, **{".recordsignore": "private/\n",
                          "private__leak.md": _record(PLANTED),
                          "d.md": "---\ndraft: true\n---\n\n" + PLANTED + "\n"})
    result = scan.scan(tmp_path / "records")
    assert sorted(f["path"] for f in result["findings"]) == ["d.md", "private/leak.md"]


def test_a_single_file_can_be_scanned(tmp_path):
    rec = _records(tmp_path, **{"a.md": _record(PLANTED), "b.md": _record("clean")})
    assert scan.scan(rec / "b.md")["ok"] is True
    assert scan.scan(rec / "a.md")["errors"] == 1


def test_a_checkout_resolves_to_its_records_dir(tmp_path):
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../../records\n", encoding="utf-8")
    _records(tmp_path, **{"a.md": _record(PLANTED)})
    result = scan.scan(tmp_path)
    assert result["root"] == str((tmp_path / "records").resolve())
    assert result["errors"] == 1


# --- the command --------------------------------------------------------------

def test_main_exit_codes_and_json(tmp_path, capsys):
    _records(tmp_path, **{"a.md": _record(PLANTED)})
    assert scan.main([str(tmp_path / "records"), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["errors"] == 1
    _records(tmp_path, **{"a.md": _record("clean")})
    assert scan.main([str(tmp_path / "records")]) == 0
    assert "nothing matched" in capsys.readouterr().out
