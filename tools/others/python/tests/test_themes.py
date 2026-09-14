"""Layer A of the theme tests: the contract between the two themes, as files.

No Hugo, no build, no skip — ``pathlib`` and ``hashlib``. AGENTS.md states
this contract in prose and it has already drifted once (``head-meta.html``),
so it is checked here instead of remembered.

The identical list is **named**, not a blanket rule over everything shared:
``repo-link.html`` differs by exactly one byte on purpose (the theme's own
name in its ``warnf``), and a blanket rule would accuse it wrongly.
"""

import hashlib

import pytest

from conftest import THEMES, THEMES_DIR, normalise

# Shared layout files that must stay byte-identical across both themes.
# AGENTS.md names the first five; 404.html measures identical too.
IDENTICAL = (
    "404.html",
    "_markup/render-codeblock-assistant.html",
    "_partials/comment-link.html",
    "_partials/head-extra.html",
    "_partials/lang-badge.html",
    "_partials/static-url.html",
)

# The partial contract: Postkasse "mirrors Fuglekasse's partial contract … so
# every documented param behaves the same" (AGENTS.md). These names must
# resolve in both themes, however each theme implements them.
CONTRACT = (
    "_partials/record.html",
    "_partials/repo-link.html",
    "_partials/comment-link.html",
    "_partials/static-url.html",
    "_partials/lang-badge.html",
    "_partials/head-extra.html",
)

# Shared paths that are allowed to differ, each with the reason. Anything
# shared that is in neither this list nor IDENTICAL is new, and the test says
# so — a shared file has to be classified on purpose, not by omission.
MAY_DIFFER = {
    "_partials/head-meta.html": "Postkasse carries the params.ogCards block",
    "_partials/record.html": "Postkasse delegates to its own strip/resolve/rewrite partials",
    "_partials/repo-link.html": "one byte: the theme's own name in the warnf",
    "baseof.html": "Fuglekasse inlines all CSS; Postkasse has an assets pipeline",
    "home.html": "Postkasse's home page carries search, backlinks and reading chrome",
    "page.html": "Postkasse's record page carries its own chrome",
}


def _layouts(theme):
    return THEMES_DIR / theme / "layouts"


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _shared_paths():
    per_theme = []
    for theme in THEMES:
        root = _layouts(theme)
        per_theme.append({str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()})
    return sorted(set.intersection(*per_theme))


@pytest.mark.parametrize("name", IDENTICAL)
def test_shared_partial_is_byte_identical_in_both_themes(name):
    digests = {}
    for theme in THEMES:
        path = _layouts(theme) / name
        assert path.is_file(), f"{theme} has no {name}"
        digests[theme] = _digest(path)
    assert len(set(digests.values())) == 1, (
        f"{name} has drifted between the themes: {digests} — "
        "copy one over the other, or move it to MAY_DIFFER with the reason")


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("name", CONTRACT)
def test_partial_contract_exists_in_both_themes(theme, name):
    assert (_layouts(theme) / name).is_file(), (
        f"{theme} is missing {name} — the documented partial contract "
        "(AGENTS.md) is what lets one hugo.yaml drive either theme")


def test_every_shared_layout_is_classified():
    """The guard's own guard: no shared file may be silently unclassified.

    Without this, adding a shared layout to both themes and forgetting it
    here would look exactly like passing.
    """
    known = set(IDENTICAL) | set(MAY_DIFFER)
    unclassified = [p for p in _shared_paths() if p not in known]
    assert not unclassified, (
        "shared layout files in neither IDENTICAL nor MAY_DIFFER: "
        f"{unclassified} — add each to one list, with a reason if it may differ")


def test_the_identical_list_is_not_vacuous():
    """Both lists must name files that actually exist, in both themes."""
    shared = set(_shared_paths())
    assert IDENTICAL, "IDENTICAL is empty — the test above would pass on nothing"
    missing = [p for p in set(IDENTICAL) | set(MAY_DIFFER) if p not in shared]
    assert not missing, f"listed but not shared by both themes any more: {missing}"


@pytest.mark.parametrize("name", sorted(MAY_DIFFER))
def test_a_file_listed_as_differing_really_differs(name):
    """The other direction: a file that converged should leave MAY_DIFFER.

    Otherwise the list grows into a graveyard of stale exemptions, and a real
    drift can hide behind one.
    """
    digests = {theme: _digest(_layouts(theme) / name) for theme in THEMES}
    assert len(set(digests.values())) > 1, (
        f"{name} is byte-identical in both themes now — move it from "
        f"MAY_DIFFER ({MAY_DIFFER[name]}) to IDENTICAL")


def test_repo_link_differs_only_by_the_theme_name():
    """The one-byte exemption, pinned to its reason rather than to a number."""
    lines = {theme: (_layouts(theme) / "_partials" / "repo-link.html")
             .read_text(encoding="utf-8").splitlines() for theme in THEMES}
    a, b = (lines[theme] for theme in THEMES)
    assert len(a) == len(b)
    differing = [(x, y) for x, y in zip(a, b) if x != y]
    assert len(differing) == 1, f"repo-link.html now differs on {len(differing)} lines"
    x, y = differing[0]
    for theme in THEMES:
        assert theme in (x if theme == THEMES[0] else y)
    assert x.replace(THEMES[0], "") == y.replace(THEMES[1], "")


def test_normalise_collapses_whitespace_between_tags_only():
    """The golden apparatus's one normalisation, checked without a build."""
    assert normalise("<p>a</p>\n  <p>b</p>") == "<p>a</p><p>b</p>"
    assert normalise("  <p>a b</p>  ") == "<p>a b</p>"
    assert normalise("<p>a  b</p>") == "<p>a  b</p>"
