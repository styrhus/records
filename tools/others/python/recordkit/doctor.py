"""Diagnose a checkout and say what will fail — reporting only, never fixing.

Checks are grouped by subject (config, records, url, hugo, books, publish,
rsync, deploy, git, branch), each with a level (ok/warn/error) and a remedy.
Only build-stoppers are errors; git state never is, since CI checks out a
detached HEAD.

"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .config import find_hugo_configs, read_content_dir, read_theme, resolve_records_dir
from .publish import _TARGETS, _checkout_root, _param

_HUGO_MIN = (0, 158)  # the theme's site.Language.Locale needs it
_SKIP_RECORDS = {"_index.md", "LICENSE.md", "404.md"}
_DATE_FORMATS = ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                 "%Y-%m-%d", "%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M")
_HUGO_VERSION = re.compile(r"v(\d+)\.(\d+)")

_which = shutil.which  # monkeypatch seam, beside _run


def _run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True, text=True)


def _check(name: str, level: str, message: str, remedy: str = "") -> dict:
    return {"name": name, "level": level, "message": message, "remedy": remedy}


def resolve_url(text: str, env) -> tuple[str | None, str | None]:
    """The rung of bin/build.sh's URL ladder that wins here, and the URL it yields."""
    config_url = _param(text, "baseURL")
    if config_url:
        return "baseURL", config_url
    if env.get("BASE_URL"):
        return "BASE_URL", env["BASE_URL"]
    repo = env.get("GITHUB_REPOSITORY", "")
    owner, _, name = repo.partition("/")
    if env.get("PAGES_HOST") and repo:
        # git-pages convention: a repo literally named "pages" serves at the domain root.
        root = f"https://{owner}.{env['PAGES_HOST']}/"
        return "PAGES_HOST", root if name == "pages" else f"{root}{name}/"
    if repo and env.get("GITHUB_SERVER_URL", "").rstrip("/") == "https://codeberg.org":
        root = f"https://{owner}.codeberg.page/"
        return "codeberg", root if name == "pages" else f"{root}{name}/"
    if env.get("CI_PAGES_URL"):
        return "CI_PAGES_URL", env["CI_PAGES_URL"]
    return None, None


def _ci_workflows(root: Path) -> list[str]:
    """Provider shims present in the checkout — the reason an unset baseURL can still be fine."""
    found = []
    for rel in (".forgejo/workflows", ".github/workflows"):
        d = root / rel
        if d.is_dir() and any(d.iterdir()):
            found.append(rel)
    if (root / ".gitlab-ci.yml").is_file():
        found.append(".gitlab-ci.yml")
    return found


def _frontmatter(text: str) -> list[str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return []
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    return lines[1:close] if close else []


def _parseable_date(value: str) -> bool:
    value = value.strip().strip('"').strip("'")
    for fmt in _DATE_FORMATS:  # %z takes both 'Z' and '+01:00' since 3.7
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def _config_check(cfg: Path | None, records_dir: Path | None, repo: Path) -> dict:
    if cfg is None:
        return _check("config", "error", f"no */hugo/hugo.yaml under {repo}",
                      "every build and every skill resolves the site through it — "
                      "is this a records checkout?")
    if records_dir is None or not records_dir.is_dir():
        return _check("config", "error",
                      f"{cfg}: contentDir points at {records_dir}, which does not exist",
                      "fix contentDir in the site config, or create the directory — "
                      "the skills silently write to the wrong place otherwise")
    return _check("config", "ok", f"{cfg} → {records_dir}")


def _theme_check(cfg: Path) -> list[dict]:
    """An explicit theme: must name a directory under themes/ beside the config."""
    theme = read_theme(cfg, default="")
    if not theme:
        return []
    themes_dir = cfg.parent / "themes"
    if (themes_dir / theme).is_dir():
        return [_check("theme", "ok", f"{theme} → {themes_dir / theme}")]
    present = sorted(d.name for d in themes_dir.iterdir() if d.is_dir()) \
        if themes_dir.is_dir() else []
    remedy = ("themes present: " + ", ".join(present) + " — the name is case-sensitive"
              if present else f"create {themes_dir / theme}, or drop the theme: line")
    return [_check("theme", "error",
                   f"theme: {theme!r} has no directory under {themes_dir}", remedy)]


def _records_checks(records_dir: Path | None, text: str) -> list[dict]:
    if records_dir is None or not records_dir.is_dir():
        return []
    records = [f for f in sorted(records_dir.rglob("*.md")) if f.name not in _SKIP_RECORDS]
    bad_dates, reserved = [], []
    for f in records:
        for line in _frontmatter(f.read_text(encoding="utf-8", errors="replace")):
            key, sep, value = line.partition(":")
            if not sep:
                continue
            if key.strip() == "date" and not _parseable_date(value):
                bad_dates.append(f.name)
            elif key.strip() == "demo":
                reserved.append(f.name)
    out = []
    if bad_dates:
        out.append(_check("records", "error", "unparseable date: in " + ", ".join(bad_dates),
                          "Hugo stops the build on these — use 2026-07-06T23:22:00+01:00"))
    if reserved:
        out.append(_check("records", "warn", "reserved key demo: in " + ", ".join(reserved),
                          "demo: marks theme-shipped demo content; drop it from your records"))
    if out:
        return out
    if not records and _param(text, "demoMode").lower() != "true":
        return [_check("records", "warn", f"no records in {records_dir}",
                       "the site builds but is empty; params.demoMode shows the shipped demo")]
    return [_check("records", "ok", f"{len(records)} record(s) in {records_dir}")]


def _url_check(text: str, env, root: Path) -> dict:
    rung, url = resolve_url(text, env)
    if rung:
        return _check("url", "ok", f"{rung} → {url}")
    ci = _ci_workflows(root)
    if ci:
        return _check("url", "warn",
                      "no baseURL and no CI env — the URL is derived on push (" +
                      ", ".join(ci) + ")",
                      "local builds need BASE_URL=… bin/build.sh, or uncomment baseURL "
                      "in the site config")
    return _check("url", "error",
                  "no rung of the URL ladder resolves "
                  "(baseURL, BASE_URL, PAGES_HOST, Codeberg CI, CI_PAGES_URL)",
                  "uncomment baseURL in the site config, or pass BASE_URL — "
                  "bin/build.sh exits here")


def _hugo_check() -> dict:
    if not _which("hugo"):
        return _check("hugo", "error", "hugo not found on PATH",
                      "install it: https://gohugo.io/installation/")
    out = _run(["hugo", "version"]).stdout
    m = _HUGO_VERSION.search(out)
    if not m:
        return _check("hugo", "warn", f"unreadable hugo version: {out.strip()}")
    version = (int(m.group(1)), int(m.group(2)))
    if version < _HUGO_MIN:
        return _check("hugo", "error", f"hugo {version[0]}.{version[1]} is too old",
                      "the bundled themes need hugo ≥ 0.158 (site.Language.Locale)")
    return _check("hugo", "ok", f"hugo {version[0]}.{version[1]}")


def _books_check(text: str) -> list[dict]:
    wanted = [name for name in ("pdf", "epub", "booklet") if _param(text, name)]
    if not wanted:
        return []
    missing = []
    if not _which("pandoc"):
        missing.append("pandoc")
    if ("pdf" in wanted or "booklet" in wanted) and not _which("weasyprint"):
        missing.append("weasyprint")
    if "booklet" in wanted and _run([sys.executable, "-c", "import pypdf"]).returncode != 0:
        missing.append("pypdf")
    if missing:
        return [_check("books", "warn",
                       f"params {', '.join(wanted)} set but {', '.join(missing)} missing",
                       "bin/build.sh skip-notes the books and builds the site anyway")]
    return [_check("books", "ok", f"params {', '.join(wanted)}, toolchain complete")]


def _publish_checks(text: str, root: Path) -> list[dict]:
    target = _param(text, "publishTarget")
    deploy_cmd = _param(text, "deployCommand")
    ci = _ci_workflows(root)
    out = []
    if target and target not in _TARGETS:
        out.append(_check("publish", "error", f"unknown publishTarget {target!r}",
                          "known targets: " + " | ".join(_TARGETS)))
    elif target == "rsync":
        dest = _param(text, "publishDest")
        path = dest.split(":", 1)[1] if ":" in dest else dest
        if not dest:
            out.append(_check("publish", "error", "publishTarget: rsync without publishDest",
                              "set params.publishDest to the webroot to sync into"))
        elif path.strip().rstrip("/") in ("", "~"):
            out.append(_check("publish", "error", f"publishDest {dest!r} is a root/home dir",
                              "records publish refuses it — rsync --delete would wipe the host"))
        else:
            out.append(_check("publish", "ok", f"rsync → {dest}"))
        out.append(_check("rsync", "ok", "rsync found") if _which("rsync") else
                   _check("rsync", "warn", "publishTarget: rsync but rsync is not on PATH",
                          "install rsync, or switch publishTarget to pages-branch"))
    elif target == "pages-branch":
        remote = _param(text, "publishRemote", "origin")
        branch = _param(text, "publishBranch", "pages")
        remotes = _run(["git", "-C", str(root), "remote"]).stdout.split()
        if remote not in remotes:
            out.append(_check("publish", "warn",
                              f"publishRemote {remote!r} is not a remote of this checkout",
                              "set params.publishRemote, or add the remote"))
        else:
            out.append(_check("publish", "ok", f"pages-branch → {remote} {branch}"))
    elif ci:
        out.append(_check("publish", "ok", "CI publishes on push (" + ", ".join(ci) + ")"))
    elif deploy_cmd:
        out.append(_check("publish", "ok", f"deployCommand: {deploy_cmd}"))
    else:
        out.append(_check("publish", "warn",
                          "no publishTarget, no deployCommand, no CI workflow — "
                          "nothing publishes this site",
                          "set params.publishTarget for `records publish`, or keep a CI shim"))
    if deploy_cmd:
        first = deploy_cmd.split()[0]
        if "/" in first and not (root / first).exists():
            out.append(_check("deploy", "warn", f"deployCommand points at {first}, which is absent",
                              "/cpd runs it from the repo root after commit + push"))
        else:
            out.append(_check("deploy", "ok", f"deployCommand: {deploy_cmd}"))
    return out


def _git_checks(text: str, root: Path) -> list[dict]:
    head = _run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"])
    if head.returncode != 0:
        return [_check("git", "warn", f"{root} is not a git checkout",
                       "records are files in a repo — the forge links and /gc need one")]
    out = []
    remotes = _run(["git", "-C", str(root), "remote"]).stdout.split()
    if remotes:
        out.append(_check("git", "ok", "remotes: " + ", ".join(remotes)))
    else:
        out.append(_check("git", "warn", "no git remote", "nothing to push or publish to"))
    branch, repo_branch = head.stdout.strip(), _param(text, "repoBranch", "main")
    if branch == "HEAD":
        out.append(_check("branch", "warn", "detached HEAD",
                          f"raw record links resolve against repoBranch ({repo_branch})"))
    elif branch != repo_branch:
        out.append(_check("branch", "warn", f"on {branch!r}, repoBranch is {repo_branch!r}",
                          "raw links inside records point at repoBranch — set it, or switch"))
    else:
        out.append(_check("branch", "ok", branch))
    return out


def diagnose(repo: Path = Path("."), env=None) -> dict:
    """Every check, with counts. Reads only — the doctor never writes."""
    env = os.environ if env is None else env
    repo = Path(repo).resolve()
    configs = find_hugo_configs(repo)
    cfg = configs[0] if configs else None
    text = cfg.read_text(encoding="utf-8") if cfg else ""
    root = _checkout_root(cfg).resolve() if cfg else repo
    records_dir = ((cfg.parent / read_content_dir(cfg)).resolve() if cfg
                   else resolve_records_dir(repo))

    checks = [_config_check(cfg, records_dir, repo)]
    if cfg:
        checks += _theme_check(cfg)
    checks += _records_checks(records_dir, text)
    checks.append(_url_check(text, env, root))
    checks.append(_hugo_check())
    checks += _books_check(text)
    checks += _publish_checks(text, root)
    checks += _git_checks(text, root)

    errors = sum(1 for c in checks if c["level"] == "error")
    warnings = sum(1 for c in checks if c["level"] == "warn")
    return {"repo": str(root), "config": str(cfg) if cfg else None,
            "records_dir": str(records_dir), "checks": checks,
            "errors": errors, "warnings": warnings, "ok": errors == 0}


def render(result: dict) -> str:
    """The human-readable report; --json prints the dict instead."""
    lines = [f"records doctor — {result['repo']}", ""]
    for c in result["checks"]:
        lines.append(f"  {c['level']:<5}  {c['name']:<8}  {c['message']}")
        if c["remedy"]:
            lines.append(f"{'':<16}↳ {c['remedy']}")
    ok = len(result["checks"]) - result["errors"] - result["warnings"]
    warnings, errors = result["warnings"], result["errors"]
    lines += ["", f"  {ok} ok · {warnings} warning{'' if warnings == 1 else 's'}"
                  f" · {errors} error{'' if errors == 1 else 's'}"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="records doctor",
                                description="Report what will fail in this checkout.")
    p.add_argument("--repo", default=".")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)
    result = diagnose(Path(args.repo))
    print(json.dumps(result) if args.json else render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
