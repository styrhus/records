"""Build the site and deliver it — the mechanical core of `records publish`.

Delivery is picked by params in the discovered hugo.yaml: publishTarget
pages-branch (force-push the built site to publishBranch on publishRemote)
or rsync (rsync -az --delete to publishDest). commit._deploy checks
deployCommand first, so `deployCommand: records publish` makes /cpd the
no-CI publish path; publish itself never commits or pushes source.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .config import find_hugo_configs

_TARGETS = ("pages-branch", "rsync")


def _run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")  # fail fast, never prompt
    return subprocess.run(argv, cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, env=env)


def _param(text: str, name: str, default: str = "") -> str:
    """First uncommented 'name: value' line, quotes and trailing comment stripped."""
    rx = re.compile(r"^\s*" + name + r":\s*(.*?)\s*(?:#.*)?$")
    for line in text.splitlines():
        m = rx.match(line)
        if m and m.group(1):
            return m.group(1).strip().strip('"').strip("'")
    return default


def _checkout_root(cfg: Path) -> Path:
    """The checkout holding hugo/: its parent, or grandparent when nested in tools/."""
    parent = cfg.parent.parent
    return parent.parent if parent.name == "tools" else parent


def _build(root: Path, outdir: Path) -> None:
    script = root / "bin" / "build.sh"
    if not script.is_file():
        raise RuntimeError(f"{script} not found — publish needs the checkout's build script")
    p = _run(["bash", str(script), str(outdir)], cwd=root)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip() or "build failed")


def _pages_branch(root: Path, outdir: Path, text: str, dry_run: bool) -> dict:
    branch = _param(text, "publishBranch", "pages")
    remote = _param(text, "publishRemote", "origin")
    p = _run(["git", "-C", str(root), "remote", "get-url", remote])
    if p.returncode != 0:
        raise RuntimeError(f"git remote {remote!r} not found in {root}")
    url = p.stdout.strip()
    result = {"remote": remote, "remote_url": url, "branch": branch, "dry_run": dry_run}
    if dry_run:
        result.update({"pushed": False,
                       "files": sum(1 for f in outdir.rglob("*") if f.is_file())})
        return result
    gitdir = outdir / ".git"
    shutil.rmtree(gitdir, ignore_errors=True)  # stateless across runs
    (outdir / ".nojekyll").touch()  # branch-served GitHub Pages runs Jekyll otherwise
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        for argv in (
            ["git", "-C", str(outdir), "init", "-q"],
            ["git", "-C", str(outdir), "add", "-A"],
            ["git", "-C", str(outdir), "-c", "user.name=records publish",
             "-c", "user.email=publish@invalid", "commit", "-q", "-m", f"publish {stamp}"],
            ["git", "-C", str(outdir), "push", "-q", "--force", url,
             f"HEAD:refs/heads/{branch}"],
        ):
            p = _run(argv)
            if p.returncode != 0:
                raise RuntimeError((p.stderr or p.stdout).strip() or "git failed")
    finally:
        shutil.rmtree(gitdir, ignore_errors=True)
    result["pushed"] = True
    return result


def _rsync(outdir: Path, text: str, dry_run: bool) -> dict:
    dest = _param(text, "publishDest")
    if not dest:
        raise RuntimeError("publishTarget: rsync needs params.publishDest in hugo.yaml")
    path = dest.split(":", 1)[1] if ":" in dest else dest
    if path.strip().rstrip("/") in ("", "~"):
        raise RuntimeError(f"refusing publishDest {dest!r} — --delete against a root/home dir")
    argv = ["rsync", "-az", "--delete"]
    if dry_run:
        argv += ["-n", "--itemize-changes"]
    argv += [str(outdir).rstrip("/") + "/", dest]
    p = _run(argv)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip() or "rsync failed")
    result = {"dest": dest, "synced": not dry_run, "dry_run": dry_run}
    if dry_run:
        result["changes"] = p.stdout.strip()
    return result


def publish(repo: Path, dry_run: bool = False, outdir: Path | None = None) -> dict:
    """Build via bin/build.sh, then deliver per publishTarget. Dry-run still builds."""
    configs = find_hugo_configs(Path(repo))
    if not configs:
        raise RuntimeError(f"no */hugo/hugo.yaml under {repo} — nothing to publish")
    cfg = configs[0]
    text = cfg.read_text(encoding="utf-8")
    target = _param(text, "publishTarget")
    if not target:
        raise RuntimeError(f"publishTarget unset — set it under params: in {cfg} "
                           "(pages-branch | rsync); with CI on a hosted forge, "
                           "pushing main already publishes")
    if target not in _TARGETS:
        raise RuntimeError(f"unknown publishTarget {target!r} (pages-branch | rsync)")
    root = _checkout_root(cfg).resolve()
    out = (Path(outdir) if outdir else root / "public").resolve()
    _build(root, out)
    result = {"repo": str(root), "target": target, "outdir": str(out), "built": True}
    if target == "pages-branch":
        result.update(_pages_branch(root, out, text, dry_run))
    else:
        result.update(_rsync(out, text, dry_run))
    return result
