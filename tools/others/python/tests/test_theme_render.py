"""Layer B of the theme tests: what the themes actually render.

Needs a real Hugo (``requires_hugo``); skips without one, and fails instead
of skipping under ``RECORDS_REQUIRE_HUGO=1``. See ``conftest.py``.

The assertions are about *properties* of the output — a signature is gone, a
turn landed in the right section, a relative link became a forge link — not
about bytes. Properties survive a palette change, a ``/werden`` bump and most
Hugo minor releases; a byte blob does not. The golden apparatus exists in
``conftest.py`` for the first case a property honestly cannot express; there
are no samples yet.
"""

import pytest

from conftest import THEMES, main_of

TURNS = """## Human

Look at [the other one](records/second.md).

## Assistant

Answered.

— claude
"""

TWO_RECORDS = [
    dict(name="first", title="First", date="2026-01-01T10:00:00+01:00",
         body=TURNS, language="nb"),
    dict(name="second", title="Second", date="2026-01-02T10:00:00+01:00",
         body="## Human\n\nAnd again.\n\n## Assistant\n\nAgain.\n"),
]


@pytest.fixture(params=THEMES)
def built(request, hugo_site):
    """The same two-record site, once per theme."""
    return request.param, hugo_site(TWO_RECORDS, theme=request.param)


def test_no_empty_section_precedes_the_first_turn(built):
    """record.html opens a wrapper the first turn's rewrite closes at once.

    Left alone that emits ``<section></section>`` before every record — the
    blemish this wave removed before any golden sample could freeze it.
    """
    theme, public = built
    for slug in ("first", "second"):
        main = main_of(public / slug / "index.html")
        assert "<section></section>" not in main, f"{theme}/{slug}"
        assert main.count("<section") == main.count("</section>"), f"{theme}/{slug}"


def test_a_record_without_turns_keeps_the_plain_wrapper(hugo_site):
    """The other side of that fix: no turn heading, so nothing to trim."""
    public = hugo_site([dict(name="plain", title="Plain",
                             date="2026-01-03T10:00:00+01:00",
                             body="Just a paragraph, no turn headings.\n")])
    main = main_of(public / "plain" / "index.html")
    assert "<section><p>Just a paragraph" in main.replace("\n", "")
    assert "<section></section>" not in main


def test_the_signature_line_never_reaches_the_output(built):
    """``— claude`` is stripped by record.html — the reason RSS is off by
    default under Fuglekasse, and the point of strip-signatures.html."""
    theme, public = built
    main = main_of(public / "first" / "index.html")
    assert "claude" not in main, f"{theme}: signature survived into <main>"
    assert "Answered." in main, f"{theme}: the turn's own text went missing too"


def test_turns_land_in_their_own_sections(built):
    theme, public = built
    main = main_of(public / "first" / "index.html")
    assert '<section class="user"><h2 id="human">' in main, theme
    assert '<section class="assistant"><h2>' in main, theme


def test_a_relative_record_link_becomes_a_raw_forge_link(built):
    """``records/second.md`` in a turn points at the repo, not at the site."""
    theme, public = built
    main = main_of(public / "first" / "index.html")
    assert 'href="https://example.test/owner/repo/raw/branch/main/records/second.md"' in main, theme
    assert 'href="records/second.md"' not in main, theme


def test_the_lang_badge_follows_the_language_param(built):
    """``language: nb`` shows the badge; a record without one shows none."""
    theme, public = built
    with_lang = main_of(public / "first" / "index.html")
    without = main_of(public / "second" / "index.html")
    assert 'class="record-lang"' in with_lang, theme
    assert "> nb</span>" in with_lang, theme
    assert 'class="record-lang"' not in without, theme


def test_single_flowing_publishes_one_page_and_no_record_pages(hugo_site):
    """The one-page overlay: every record is on ``/``, so the per-record
    pages are orphans and one-page.yaml stops Hugo writing them."""
    public = hugo_site(TWO_RECORDS, params="  pageMode: single-flowing\n", one_page=True)
    assert (public / "index.html").is_file()
    assert not (public / "first" / "index.html").exists()
    assert not (public / "sitemap.xml").exists()
    index = main_of(public / "index.html")
    assert "Answered." in index and "Again." in index
    assert "<section></section>" not in index
