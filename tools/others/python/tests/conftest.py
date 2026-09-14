"""Shared fixtures.

Everything in tests/ runs without Hugo except the theme *render* tests, which
need a real one. The rule for "new enough" is imported from ``recordkit.doctor``
rather than restated, so the repo keeps one Hugo version rule and not two.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from recordkit import doctor


def _repo_root() -> Path:
    """The checkout this test file lives in — found, not counted in ``..``."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "tools" / "hugo" / "themes").is_dir():
            return parent
    raise RuntimeError("no tools/hugo/themes above " + str(Path(__file__).resolve()))


REPO_ROOT = _repo_root()
THEMES_DIR = REPO_ROOT / "tools" / "hugo" / "themes"
GOLDEN_DIR = Path(__file__).parent / "golden"
THEMES = ("Fuglekasse", "Postkasse")


def pytest_addoption(parser):
    parser.addoption("--update-golden", action="store_true", default=False,
                     help="rewrite tests/golden/*.html from this run instead of comparing")


def hugo_problem():
    """None when a usable hugo is on PATH, else a sentence saying why not.

    Same check ``records doctor`` runs: ``doctor._HUGO_VERSION`` against
    ``doctor._HUGO_MIN``.
    """
    wanted = "{}.{}".format(*doctor._HUGO_MIN)
    exe = shutil.which("hugo")
    if not exe:
        return f"no hugo on PATH — the bundled themes need hugo >= {wanted}"
    out = subprocess.run([exe, "version"], capture_output=True, text=True).stdout
    m = doctor._HUGO_VERSION.search(out)
    if not m:
        return f"unreadable hugo version {out.strip()!r} — the themes need hugo >= {wanted}"
    found = (int(m.group(1)), int(m.group(2)))
    if found < doctor._HUGO_MIN:
        return f"hugo {found[0]}.{found[1]} is too old — the themes need hugo >= {wanted}"
    return None


@pytest.fixture(scope="session")
def requires_hugo():
    """Path to a hugo that can build the themes; skips the test without one.

    ``RECORDS_REQUIRE_HUGO=1`` turns that skip into a failure — so whoever
    builds a job that *has* Hugo finds out immediately if these tests are
    quietly skipping in it anyway. Same idea as
    ``test_every_subcommand_has_a_smoke_test``: guard the guard.
    """
    problem = hugo_problem()
    if problem:
        if os.environ.get("RECORDS_REQUIRE_HUGO") == "1":
            pytest.fail(f"RECORDS_REQUIRE_HUGO=1, but {problem}")
        pytest.skip(problem)
    return shutil.which("hugo")


@pytest.fixture(scope="session")
def hugo_version(requires_hugo):
    """``0.166`` — the version that produced this run's output."""
    out = subprocess.run([requires_hugo, "version"], capture_output=True, text=True).stdout
    m = doctor._HUGO_VERSION.search(out)
    return f"{int(m.group(1))}.{int(m.group(2))}"


RECORD = """---
title: {title}
date: {date}
{extra}---

{body}
"""


def write_record(records_dir: Path, name, title, date, body, **frontmatter):
    extra = "".join(f"{k}: {v}\n" for k, v in frontmatter.items())
    path = records_dir / f"{name}.md"
    path.write_text(RECORD.format(title=title, date=date, extra=extra, body=body),
                    encoding="utf-8")
    return path


BASE_CONFIG = """locale: en-no
title: throwaway
theme: {theme}
contentDir: ../../records
staticDir: [static, ../../static]
dataDir: ../../data
disableHugoGeneratorInject: true
module:
  mounts:
    - source: ../../CURRENT
      target: assets/CURRENT
timeZone: Europe/Oslo
permalinks:
  page:
    /: /:contentbasename/
markup:
  goldmark:
    renderer:
      unsafe: true
disableKinds: [taxonomy, term, rss]
params:
  repoURL: https://example.test/owner/repo
  demoMode: false
{params}"""


@pytest.fixture
def hugo_site(requires_hugo, tmp_path):
    """Builds a throwaway site in ``tmp_path`` and returns its ``public/``.

    The tree mirrors a real checkout (``records/`` beside ``tools/hugo/``,
    the repo's own ``data/`` and ``CURRENT``) because that is the shape the
    themes are written against; only the themes themselves are borrowed from
    the checkout, via ``--themesDir``.
    """
    def build(records, *, theme="Fuglekasse", params="", one_page=False, name="site"):
        root = tmp_path / name
        (root / "records").mkdir(parents=True)
        (root / "static").mkdir()
        (root / "tools" / "hugo").mkdir(parents=True)
        shutil.copytree(REPO_ROOT / "data", root / "data")
        shutil.copy(REPO_ROOT / "CURRENT", root / "CURRENT")
        (root / "tools" / "hugo" / "hugo.yaml").write_text(
            BASE_CONFIG.format(theme=theme, params=params), encoding="utf-8")

        config = "hugo.yaml"
        if one_page:
            shutil.copy(REPO_ROOT / "tools" / "hugo" / "one-page.yaml",
                        root / "tools" / "hugo" / "one-page.yaml")
            config = "hugo.yaml,one-page.yaml"

        for record in records:
            write_record(root / "records", **record)

        out = root / "public"
        done = subprocess.run(
            [requires_hugo, "--source", str(root / "tools" / "hugo"),
             "--themesDir", str(THEMES_DIR), "--config", config,
             "--destination", str(out), "--cleanDestinationDir"],
            capture_output=True, text=True)
        assert done.returncode == 0, done.stdout + done.stderr
        return out
    return build


_MAIN = re.compile(r"<main\b[^>]*>(.*?)</main>", re.S)
_BETWEEN_TAGS = re.compile(r">\s+<")


def main_of(path: Path) -> str:
    """The ``<main>`` of a built page, inner HTML only.

    The cut is deliberate: most of ``baseof.html`` is inline CSS/JS (and
    Postkasse fingerprints its stylesheet), so a whole-page comparison goes
    red on every palette line while ``<main>`` — the part the record
    templates actually produce — stays stable.
    """
    m = _MAIN.search(path.read_text(encoding="utf-8"))
    assert m, f"no <main> in {path}"
    return m.group(1)


def normalise(html: str) -> str:
    """The one normalisation golden samples get: whitespace between tags.

    Template indentation is not part of the contract; the tags, their order
    and their attributes are.
    """
    return _BETWEEN_TAGS.sub("><", html).strip()


@pytest.fixture
def assert_golden(request, hugo_version):
    """Compare HTML against ``tests/golden/<name>.html``.

    There are **no** samples yet, on purpose: a property assertion that says
    what it means beats a byte blob that only says "something changed". This
    exists so the first case that genuinely needs a blob has somewhere to put
    it — write it with ``pytest --update-golden``, read the diff, commit it.
    Every sample carries the producing Hugo version in its first line, so a
    diff after a Hugo bump says so instead of leaving you guessing.
    """
    def check(name, html):
        path = GOLDEN_DIR / f"{name}.html"
        body = (f"<!-- hugo {hugo_version} · regenerate: pytest --update-golden -->\n"
                + normalise(html) + "\n")
        if request.config.getoption("--update-golden"):
            GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            pytest.skip(f"golden sample written: {path.name}")
        if not path.exists():
            pytest.fail(f"no golden sample {path.name} — create it with pytest --update-golden")
        assert path.read_text(encoding="utf-8") == body
    return check
