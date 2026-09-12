"""`.recordsignore` → the site config's ignoreFiles block.

The book side cannot be executed here (no pandoc, no lua interpreter), so `_book_lua_ignored`
below is a line-by-line transliteration of book.lua's `yamlListItems` + `regexToLua` + `ignored`.
It proves the generated block survives that reader and matches what it should; it does not prove
book.lua itself ran. The site side is proved for real by a hugo build — see the session report.
"""

import os
import re
import stat
from pathlib import Path

import pytest

from recordkit import ignore

CONFIG = """\
locale: en-no
title: blyant records

theme: Fuglekasse

# records/ is the single source of truth for content.
contentDir: ../../records

# Repo-root static/ holds your own assets.
staticDir: [static, ../../static]

params:
  greeting: Velkommen
"""


def _repo(tmp_path, config=CONFIG, ignorefile=None, records=()):
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text(config, encoding="utf-8")
    rec = tmp_path / "records"
    rec.mkdir(parents=True, exist_ok=True)
    for name in records:
        path = rec / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\ntitle: x\n---\n\n## Human\n\nhi\n", encoding="utf-8")
    if ignorefile is not None:
        (rec / ignore.IGNORE_FILE).write_text(ignorefile, encoding="utf-8")
    return tmp_path


def _config_text(tmp_path):
    return (tmp_path / "tools" / "hugo" / "hugo.yaml").read_text(encoding="utf-8")


# --- book.lua, transliterated -------------------------------------------------

def _book_lua_yaml_list_items(txt, key):
    """book.lua's yamlListItems: raw block-list reading, comments and blanks tolerated."""
    items, active = [], False
    for line in (txt + "\n").split("\n")[:-1]:
        if active:
            m = re.match(r"^\s*-\s*(.+)$", line)
            if m:
                item = m.group(1)
                dq = re.match(r'^"(.-)"'.replace(".-", ".*?"), item)
                sq = re.match(r"^'(.*?)'", item)
                if dq:
                    item = re.sub(r"\\(.)", r"\1", dq.group(1))
                elif sq:
                    item = sq.group(1).replace("''", "'")
                else:
                    item = re.sub(r"\s+#.*$", "", item).rstrip()
                if item:
                    items.append(item)
            elif not re.match(r"^\s*#", line) and not re.match(r"^\s*$", line):
                active = False
        if not active and re.match(r"^\s*" + key + r":\s*$", line):
            active = True
    return items


def _book_lua_regex_to_lua(regex):
    """book.lua's regexToLua: literals, \\-escapes, ^ and $ survive; everything else is escaped."""
    out, i = [], 0
    while i < len(regex):
        c = regex[i]
        if c == "\\":
            out.append("%" + regex[i + 1:i + 2])
            i += 2
        elif c in "^$" or re.match(r"[A-Za-z0-9/ ]", c):
            out.append(c)
            i += 1
        else:
            out.append("%" + c)
            i += 1
    return "".join(out)


def _lua_pattern_to_python(pattern):
    """The Lua patterns regexToLua can emit are all literal-plus-anchors — map them 1:1."""
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if c == "%":
            out.append(re.escape(pattern[i + 1]))
            i += 2
        elif c in "^$":
            out.append(c)
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "".join(out)


def _book_lua_ignored(config_text, rel):
    """book.lua's ignored(rel): unanchored find of each converted pattern."""
    for raw in _book_lua_yaml_list_items(config_text, "ignoreFiles"):
        lua = _book_lua_regex_to_lua(raw)
        if re.search(_lua_pattern_to_python(lua), rel):
            return True
    return False


def test_the_transliteration_agrees_with_the_module_on_plain_patterns():
    """Guard on the mirror itself: same answers as ignore.book_ignored for the shapes we emit."""
    config = "ignoreFiles:\n  - '^private/'\n  - '/private/'\n  - '\\.env$'\n"
    regexes = ["^private/", "/private/", r"\.env$"]
    for rel in ("private/a.md", "a/private/b.md", "notes.env", "keep.md", "myprivate/x.md"):
        assert _book_lua_ignored(config, rel) == ignore.book_ignored(rel, regexes), rel


# --- translation --------------------------------------------------------------

@pytest.mark.parametrize("pattern,regexes", [
    ("private/", ["^private/", "/private/"]),
    ("secret.md", [r"^secret\.md$", r"/secret\.md$"]),
    ("notes/draft.md", [r"^notes/draft\.md$", r"/notes/draft\.md$"]),
    ("*.env", [r"\.env$"]),
    ("*-scratch.md", [r"-scratch\.md$"]),        # - is literal in RE2 and in book.lua's subset
    ("re: ^work/.*\\.md$", [r"^work/.*\.md$"]),
])
def test_translate(pattern, regexes):
    assert ignore.translate(pattern) == regexes


@pytest.mark.parametrize("pattern,because", [
    ("!keep.md", "negation"),
    ("/private/", "absolute paths"),
    ("a*b.md", "only supported at the start"),
    ("draft?.md", "single-character wildcards"),
    ("[ab].md", "character classes"),
    ("*", "everything"),
    ("re:", "empty"),
])
def test_unsupported_patterns_say_why(pattern, because):
    with pytest.raises(ignore.PatternError) as e:
        ignore.translate(pattern)
    assert because in str(e.value)


def test_problems_are_collected_not_raised(tmp_path):
    repo = _repo(tmp_path, ignorefile="private/\n!keep.md\n/rooted/\n")
    result = ignore.sync(repo)
    assert result["ok"] is False
    assert [p["line"] for p in result["problems"]] == [2, 3]
    assert _config_text(tmp_path) == CONFIG        # nothing written on a bad file


# --- both matchers agree ------------------------------------------------------

def test_emitted_regexes_hide_the_file_from_hugo_and_from_the_book(tmp_path):
    repo = _repo(tmp_path, ignorefile="private/\nnotes.md\n*.env\n",
                 records=("keep.md", "private/leak.md", "deep/private/leak.md",
                          "notes.md", "deep/notes.md"))
    result = ignore.sync(repo)
    assert result["ok"] is True
    records = tmp_path / "records"
    config = _config_text(tmp_path)
    for rel, want in [("keep.md", False), ("private/leak.md", True),
                      ("deep/private/leak.md", True), ("notes.md", True),
                      ("deep/notes.md", True)]:
        abs_path = str((records / rel).resolve())
        assert ignore.hugo_ignored(abs_path, result["regexes"]) is want, f"hugo {rel}"
        assert _book_lua_ignored(config, rel) is want, f"book {rel}"
    assert result["disagree"] == []
    assert sorted(result["ignored"]) == ["deep/notes.md", "deep/private/leak.md",
                                         "notes.md", "private/leak.md"]


def test_a_similar_name_is_not_caught(tmp_path):
    repo = _repo(tmp_path, ignorefile="notes.md\nprivate/\n",
                 records=("my-notes.md", "notes.md.bak.md", "myprivate/a.md"))
    result = ignore.sync(repo)
    assert result["ignored"] == []
    config = _config_text(tmp_path)
    for rel in ("my-notes.md", "notes.md.bak.md", "myprivate/a.md"):
        assert _book_lua_ignored(config, rel) is False


# --- the generated block ------------------------------------------------------

def test_block_lands_after_contentdir_and_is_idempotent(tmp_path):
    repo = _repo(tmp_path, ignorefile="private/\n")
    ignore.sync(repo)
    text = _config_text(tmp_path)
    assert "# records-ignore:begin" in text and "# records-ignore:end" in text
    assert text.index("contentDir:") < text.index("ignoreFiles:") < text.index("staticDir:")
    assert "\nignoreFiles:\n" in text          # key alone on its line: book.lua needs that
    # a comment block documents the key below it — the insert goes above it, not between
    assert "# Repo-root static/ holds your own assets.\nstaticDir:" in text
    second = ignore.sync(repo)
    assert second["drift"] is False and second["written"] is False
    assert _config_text(tmp_path) == text


def test_check_reports_drift_without_writing(tmp_path):
    repo = _repo(tmp_path, ignorefile="private/\n")
    result = ignore.sync(repo, check=True)
    assert result["ok"] is False and result["drift"] is True
    assert result["written"] is False
    assert _config_text(tmp_path) == CONFIG
    ignore.sync(repo)
    assert ignore.sync(repo, check=True)["ok"] is True


def test_removing_every_pattern_removes_the_block(tmp_path):
    repo = _repo(tmp_path, ignorefile="private/\n")
    ignore.sync(repo)
    (tmp_path / "records" / ignore.IGNORE_FILE).write_text("# nothing here\n", encoding="utf-8")
    ignore.sync(repo)
    text = _config_text(tmp_path)
    assert "ignoreFiles" not in text
    assert "contentDir: ../../records" in text and "staticDir:" in text


def test_no_ignore_file_at_all_is_a_no_op(tmp_path):
    repo = _repo(tmp_path)
    result = ignore.sync(repo)
    assert result["ok"] is True and result["drift"] is False
    assert _config_text(tmp_path) == CONFIG


def test_comments_and_blank_lines_are_skipped(tmp_path):
    repo = _repo(tmp_path, ignorefile="# private stuff\n\nprivate/\n\n  # trailing note\n")
    result = ignore.sync(repo)
    assert result["patterns"] == ["private/"]


def test_duplicate_regexes_are_emitted_once(tmp_path):
    repo = _repo(tmp_path, ignorefile="private/\nprivate/\n")
    assert ignore.sync(repo)["regexes"] == ["^private/", "/private/"]


# --- existing ignoreFiles behaviour is unchanged ------------------------------

HAND = CONFIG.replace("staticDir:", "ignoreFiles:\n  - '\\.bak$'\n\nstaticDir:")


def test_a_hand_written_block_is_refused_not_clobbered(tmp_path):
    repo = _repo(tmp_path, config=HAND, ignorefile="private/\n")
    result = ignore.sync(repo)
    assert result["ok"] is False
    assert "--adopt" in result["problems"][0]["problem"]
    assert _config_text(tmp_path) == HAND


def test_adopt_moves_hand_written_patterns_into_the_ignore_file(tmp_path):
    repo = _repo(tmp_path, config=HAND, ignorefile="private/\n",
                 records=("keep.md", "old.bak", "private/x.md"))
    result = ignore.sync(repo, adopt=True)
    assert result["ok"] is True
    assert result["adopted"] == [r"\.bak$"]
    assert r"\.bak$" in result["regexes"]
    assert "re: \\.bak$" in (tmp_path / "records" / ignore.IGNORE_FILE).read_text(encoding="utf-8")
    text = _config_text(tmp_path)
    assert text.count("ignoreFiles:") == 1
    assert _book_lua_ignored(text, "old.bak") is True       # the old behaviour still holds
    assert ignore.sync(repo, check=True)["ok"] is True      # and it settles


# --- the command --------------------------------------------------------------

def test_main_exit_codes(tmp_path, capsys):
    repo = _repo(tmp_path, ignorefile="private/\n", records=("private/x.md",))
    assert ignore.main(["--repo", str(repo), "--check"]) == 1
    assert "drift" in capsys.readouterr().out
    assert ignore.main(["--repo", str(repo)]) == 0
    out = capsys.readouterr().out
    assert "excluded private/x.md" in out and "written" in out
    assert ignore.main(["--repo", str(repo), "--check"]) == 0


# --- both rewrites are atomic -------------------------------------------------

def _break_the_swap(monkeypatch, name):
    """Fail `os.replace` for one target only; --adopt rewrites the ignore file and the
    config in the same run, so each has to hold on its own."""
    real = os.replace

    def guard(src, dst, *a, **k):
        if Path(dst).name == name:
            raise OSError("swap failed")
        return real(src, dst, *a, **k)

    monkeypatch.setattr(os, "replace", guard)


def test_the_config_survives_a_failed_write(tmp_path, monkeypatch):
    """The site config is hand-written YAML around a generated block — losing it to a
    truncate loses the user's own settings, not just the block."""
    repo = _repo(tmp_path, ignorefile="private/\n", records=("keep.md", "private/x.md"))
    _break_the_swap(monkeypatch, "hugo.yaml")
    with pytest.raises(OSError):
        ignore.sync(repo)
    assert _config_text(tmp_path) == CONFIG
    assert sorted(p.name for p in (tmp_path / "tools" / "hugo").iterdir()) == ["hugo.yaml"]


def test_the_ignore_file_survives_a_failed_write(tmp_path, monkeypatch):
    """--adopt prepends to whatever the user already wrote in .recordsignore."""
    repo = _repo(tmp_path, config=HAND, ignorefile="private/\n", records=("old.bak",))
    _break_the_swap(monkeypatch, ignore.IGNORE_FILE)
    with pytest.raises(OSError):
        ignore.sync(repo, adopt=True)
    ignore_path = tmp_path / "records" / ignore.IGNORE_FILE
    assert ignore_path.read_text(encoding="utf-8") == "private/\n"
    assert _config_text(tmp_path) == HAND      # the config write comes after; it never ran


def test_the_config_keeps_its_permissions(tmp_path):
    repo = _repo(tmp_path, ignorefile="private/\n", records=("keep.md", "private/x.md"))
    cfg = tmp_path / "tools" / "hugo" / "hugo.yaml"
    cfg.chmod(0o640)
    assert ignore.sync(repo)["ok"] is True
    assert stat.S_IMODE(cfg.stat().st_mode) == 0o640
    assert "ignoreFiles:" in cfg.read_text(encoding="utf-8")
