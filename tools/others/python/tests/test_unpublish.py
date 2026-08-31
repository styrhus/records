import re

import pytest

from recordkit import frontmatter, unpublish

RECORD = """---
title: A conversation about bicycles
date: 2026-07-06T23:22:58+02:00
tags: [bicycles]
---

## Human

How do I true a wheel?

## Assistant

Spoke by spoke.

— mistral:latest
"""


def _record(tmp_path, text=RECORD, name="bicycles.md"):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


# book.lua's own rule, transcribed: it splits the frontmatter with the same fence pattern and
# drops the record when `draft` is true. pandoc is not installed here, so this is how the
# mechanism gets tested against the book build's behaviour.
_FENCE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$", re.S)


def book_lua_skips(text: str) -> bool:
    """True when tools/pandoc/book.lua would leave this file out of the PDF/EPUB/booklet."""
    m = _FENCE.match(text)
    if not m:
        return False
    for line in m.group(1).split("\n"):
        key, sep, value = line.partition(":")
        if sep and key.strip() == "draft":
            return value.strip().lower() == "true"
    return False


def hugo_skips(text: str) -> bool:
    """Hugo's default: drafts are not built (bin/build.sh never passes -D/--buildDrafts)."""
    return frontmatter.read(text).get("draft") == "true"


# ------------------------------------------------------------------ the mechanism

def test_unpublish_drafts_the_record(tmp_path):
    p = _record(tmp_path)
    out = unpublish.unpublish(p, when=None)
    text = p.read_text(encoding="utf-8")
    assert out["written"] is True and out["draft"] is True
    assert "draft: true" in text
    assert frontmatter.read(text)["unpublished"] == out["unpublished"]


def test_the_drafted_record_leaves_the_site_and_the_books(tmp_path):
    """One mechanism: the same flat `draft: true` both Hugo and book.lua already honour."""
    p = _record(tmp_path)
    assert not hugo_skips(p.read_text(encoding="utf-8"))
    assert not book_lua_skips(p.read_text(encoding="utf-8"))
    unpublish.unpublish(p)
    assert hugo_skips(p.read_text(encoding="utf-8"))
    assert book_lua_skips(p.read_text(encoding="utf-8"))


def test_the_draft_line_is_the_one_the_engine_already_writes(tmp_path):
    """Byte-identical to `records new --draft`, so nothing downstream meets a second spelling."""
    assert unpublish.DRAFT_LINE in frontmatter.build("t", "2026-01-01", draft=True).split("\n")
    p = _record(tmp_path)
    unpublish.unpublish(p)
    assert unpublish.DRAFT_LINE in p.read_text(encoding="utf-8").split("\n")


def test_the_body_is_preserved_byte_for_byte(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p)
    assert frontmatter.body(p.read_text(encoding="utf-8")) == frontmatter.body(RECORD)


def test_restore_is_byte_exact(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p)
    out = unpublish.restore(p)
    assert out["restored"] is True and out["from_stash"] is False
    assert p.read_text(encoding="utf-8") == RECORD


def test_restore_puts_it_back_on_the_site(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p)
    unpublish.restore(p)
    assert not hugo_skips(p.read_text(encoding="utf-8"))
    assert not book_lua_skips(p.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ the tombstone

def test_tombstone_takes_the_url_and_the_record_moves_aside(tmp_path):
    p = _record(tmp_path)
    out = unpublish.unpublish(p, tombstone=True)
    stash = tmp_path / "bicycles.withdrawn.md"
    assert out["stash"] == str(stash) and stash.is_file()
    # the URL comes from the filename (permalinks /:contentbasename/), so the stub keeps it
    assert p.name == "bicycles.md"
    meta = frontmatter.read(p.read_text(encoding="utf-8"))
    assert meta["title"] == "Withdrawn" and meta["tombstone"] == "true"
    assert meta["date"] == "2026-07-06T23:22:58+02:00"  # keeps its place in the ordering


def test_the_tombstone_carries_none_of_the_conversation(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p, tombstone=True)
    stub = p.read_text(encoding="utf-8")
    for gone in ("How do I true a wheel?", "Spoke by spoke.", "## Human", "## Assistant",
                 "A conversation about bicycles", "mistral:latest"):
        assert gone not in stub


def test_the_tombstone_renders_and_the_stash_does_not(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p, tombstone=True)
    stub = p.read_text(encoding="utf-8")
    stash = (tmp_path / "bicycles.withdrawn.md").read_text(encoding="utf-8")
    assert not hugo_skips(stub) and not book_lua_skips(stub)
    assert hugo_skips(stash) and book_lua_skips(stash)


def test_the_tombstone_says_what_remains(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p, tombstone=True)
    stub = p.read_text(encoding="utf-8")
    assert "Nothing has been erased" in stub
    assert "git history" in stub


def test_restore_from_the_stash_is_byte_exact(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p, tombstone=True)
    out = unpublish.restore(p)
    assert out["from_stash"] is True
    assert p.read_text(encoding="utf-8") == RECORD
    assert not (tmp_path / "bicycles.withdrawn.md").exists()


def test_the_stash_is_refused_when_one_is_already_there(tmp_path):
    p = _record(tmp_path)
    (tmp_path / "bicycles.withdrawn.md").write_text("mine", encoding="utf-8")
    with pytest.raises(RuntimeError, match="already exists"):
        unpublish.unpublish(p, tombstone=True)
    assert p.read_text(encoding="utf-8") == RECORD


# ------------------------------------------------------------------ record shapes

def test_a_leaf_bundle_unpublishes_and_restores(tmp_path):
    _record(tmp_path, name="bicycles/index.md")
    out = unpublish.unpublish(tmp_path / "bicycles", tombstone=True)
    index = tmp_path / "bicycles" / "index.md"
    assert out["record"] == str(index) and out["slug"] == "bicycles"
    assert (tmp_path / "bicycles" / "index.withdrawn.md").is_file()
    unpublish.restore(index)
    assert index.read_text(encoding="utf-8") == RECORD
    assert not (tmp_path / "bicycles" / "index.withdrawn.md").exists()


def test_a_slug_resolves_under_the_records_dir(tmp_path):
    records = tmp_path / "records"
    _record(records, name="linux/bicycles.md")
    out = unpublish.unpublish("Bicycles", records_dir=records)
    assert out["record"] == str(records / "linux" / "bicycles.md")
    unpublish.restore("bicycles", records_dir=records)
    assert (records / "linux" / "bicycles.md").read_text(encoding="utf-8") == RECORD


def test_an_ambiguous_slug_is_refused(tmp_path):
    records = tmp_path / "records"
    _record(records, name="linux/bicycles.md")
    _record(records, name="notes/bicycles/index.md")
    with pytest.raises(RuntimeError, match="ambiguous"):
        unpublish.unpublish("bicycles", records_dir=records)


# ------------------------------------------------------------------ refusals

def test_a_hand_written_draft_is_refused(tmp_path):
    """Restoring it would publish something that was never published."""
    p = _record(tmp_path, text=RECORD.replace("tags:", "draft: true\ntags:"))
    with pytest.raises(RuntimeError, match="already a draft"):
        unpublish.unpublish(p)


def test_unpublishing_twice_is_refused(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p)
    with pytest.raises(RuntimeError, match="already unpublished"):
        unpublish.unpublish(p)


def test_restoring_something_it_did_not_unpublish_is_refused(tmp_path):
    p = _record(tmp_path)
    with pytest.raises(RuntimeError, match="did not unpublish it"):
        unpublish.restore(p)


def test_a_file_without_frontmatter_is_refused(tmp_path):
    p = _record(tmp_path, text="just prose\n")
    with pytest.raises(RuntimeError, match="no frontmatter"):
        unpublish.unpublish(p)


def test_a_missing_record_is_refused(tmp_path):
    with pytest.raises(RuntimeError, match="does not exist"):
        unpublish.unpublish(tmp_path / "nope.md")


# ------------------------------------------------------------------ honesty

def test_dry_run_writes_nothing(tmp_path):
    p = _record(tmp_path)
    out = unpublish.unpublish(p, tombstone=True, dry_run=True)
    assert out["written"] is False
    assert p.read_text(encoding="utf-8") == RECORD
    assert not (tmp_path / "bicycles.withdrawn.md").exists()


def test_dry_run_restore_writes_nothing(tmp_path):
    p = _record(tmp_path)
    unpublish.unpublish(p)
    after = p.read_text(encoding="utf-8")
    out = unpublish.restore(p, dry_run=True)
    assert out["written"] is False and p.read_text(encoding="utf-8") == after


def test_the_result_never_claims_erasure(tmp_path):
    p = _record(tmp_path)
    out = unpublish.unpublish(p)
    joined = " ".join(out["remains"]).lower()
    assert "git history" in joined
    assert "fork" in joined and "cache" in joined
    assert "pages-branch" in " ".join(out["next"])
    assert "--restore" in " ".join(out["next"])


def test_nothing_here_touches_git(tmp_path):
    import inspect
    assert "subprocess" not in inspect.getsource(unpublish)
