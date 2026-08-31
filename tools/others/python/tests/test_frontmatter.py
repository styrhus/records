import pytest

from recordkit import frontmatter


def test_build_basic():
    assert frontmatter.build("T", "2026-07-21T14:35:00+02:00") == (
        "---\ntitle: T\ndate: 2026-07-21T14:35:00+02:00\n---\n")


def test_build_with_tags():
    assert frontmatter.build("T", "D", tags=["linux", "hw"]) == (
        "---\ntitle: T\ndate: D\ntags: [linux, hw]\n---\n")


def test_build_draft_before_tags():
    assert frontmatter.build("T", "D", tags=["a"], draft=True) == (
        "---\ntitle: T\ndate: D\ndraft: true\ntags: [a]\n---\n")


def test_build_extra_keys_after_tags():
    assert frontmatter.build("T", "D", tags=["a"], extra={"source": "llm", "sourceId": "01x"}) == (
        "---\ntitle: T\ndate: D\ntags: [a]\nsource: llm\nsourceId: 01x\n---\n")


def test_build_empty_extra_changes_nothing():
    assert frontmatter.build("T", "D", extra={}) == frontmatter.build("T", "D")


def test_build_quotes_a_title_yaml_cannot_start_with():
    assert frontmatter.build("@readme.md#30-43", "D") == (
        '---\ntitle: "@readme.md#30-43"\ndate: D\n---\n')


def test_build_quotes_a_title_holding_a_colon():
    assert frontmatter.build("Chapter 1: Beginnings", "D") == (
        '---\ntitle: "Chapter 1: Beginnings"\ndate: D\n---\n')


def test_build_quotes_a_title_with_a_mid_string_space_hash():
    assert frontmatter.build("Title #b", "D") == (
        '---\ntitle: "Title #b"\ndate: D\n---\n')


def test_build_escapes_quotes_inside_a_quoted_title():
    assert 'title: "\\"quoted\\" start"\n' in frontmatter.build('"quoted" start', "D")


def test_build_leaves_an_ordinary_title_bare():
    assert "title: A plain title\n" in frontmatter.build("A plain title", "D")
    assert 'title: He said "hi"\n' in frontmatter.build('He said "hi"', "D")


def test_build_quotes_extra_values_that_need_it():
    assert 'sourceId: "@odd"\n' in frontmatter.build("T", "D", extra={"sourceId": "@odd"})


@pytest.mark.parametrize("title", [
    "@readme.md#30-43 fix this", "`backtick", "*star", "|pipe", ">gt", "%percent",
    "[bracket", "{brace", '"quote', "'apostrophe", "Chapter 1: Beginnings", "trailing colon:",
    'He said "hi" and \\ left', "A plain title", "2026-07-06_23-22",
    "Title #b", "Ticket #42 done", "trailing hash #",
])
def test_title_survives_a_build_read_round_trip(title):
    assert frontmatter.read(frontmatter.build(title, "D"))["title"] == title


def test_read_returns_raw_values():
    assert frontmatter.read("---\ntitle: T\ntags: [a, b]\n---\n\nbody\n") == {
        "title": "T", "tags": "[a, b]"}


def test_read_without_a_block_is_empty():
    assert frontmatter.read("no frontmatter here\n") == {}


def test_read_stops_at_the_closing_fence():
    assert "body" not in frontmatter.read("---\ntitle: T\n---\nbody: not frontmatter\n")


def test_body_drops_the_block():
    assert frontmatter.body("---\ntitle: T\n---\n\nhello\n") == "\nhello\n"


def test_body_without_a_block_is_the_whole_text():
    assert frontmatter.body("hello\n") == "hello\n"


def test_feature_adds_featured_and_unsets_draft():
    out = frontmatter.feature("---\ntitle: T\ndate: D\ndraft: true\n---\n\nbody\n")
    assert "draft: true" not in out
    assert "featured: true" in out
    assert out.endswith("\nbody\n")


def test_feature_is_idempotent():
    out = frontmatter.feature("---\ntitle: T\nfeatured: true\n---\nbody\n")
    assert out.count("featured: true") == 1
