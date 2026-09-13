"""Build the site and deliver it — the mechanical core of `records publish`.

Delivery is picked by params in the discovered hugo.yaml: publishTarget
pages-branch (force-push the built site to publishBranch on publishRemote)
or rsync (rsync -az --delete to publishDest). pages-branch asks before the
force-push unless --yes, and refuses rather than assuming yes when stdin is
not a terminal. commit._deploy checks deployCommand first, so
`deployCommand: records publish --yes` makes /cpd the no-CI publish path —
without the flag it captures the question's output and waits forever;
publish itself never commits or pushes source.
"""

from __future__ import annotations

import os
import posixpath
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .config import checkout_root as _checkout_root
from .config import find_hugo_configs

_TARGETS = ("pages-branch", "rsync")

# `rsync --delete` erases everything at the destination that is not in the built
# site, so publishDest is judged before rsync is ever run. Two things shape the
# rules: a remote `user@host:/path` cannot be resolved here at all — the remote
# home, its symlinks and its environment are unknown — so it is judged as a
# string and nothing pretends otherwise; and the judgement happens before the
# --dry-run branch, so a dry run refuses exactly what a real run refuses.
_HOME_PARENTS = ("/home", "/Users", "/var/home", "/usr/home")  # Linux, macOS, ostree, BSD
_MIN_PARTS = 2  # /srv/www publishes, /srv does not: one level above a webroot is too much


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


def _split_dest(dest: str) -> tuple[str, bool]:
    """(path part, remote?) — `user@host:/path` and `host:path` are remote, a bare path is not."""
    head, sep, tail = dest.partition(":")
    return (tail, True) if sep else (head, False)


def _split_home(path: str) -> tuple[str, str]:
    """('~' or '~user', the rest) for a home-anchored path, ('', path) otherwise."""
    if not path.startswith("~"):
        return "", path
    head, sep, tail = path.partition("/")
    return head, (sep + tail) if sep else ""


def _home_verdict(path: str) -> str | None:
    """Why `path` is a home directory or the parent of all of them, or None.

    `_HOME_PARENTS` entries are not all one component deep (`/var/home`), so this
    compares whole prefixes rather than the first component.
    """
    for parent in _HOME_PARENTS:
        if path == parent:
            return f"{path} holds every user's home directory"
        if path.startswith(parent + "/") and "/" not in path[len(parent) + 1:]:
            return f"{path} is a user's home directory"
    return None


def _local_dest_problem(path: str) -> str | None:
    """The same judgement again with the filesystem consulted — symlinks and the real home.

    `~` is read as the home directory it names, which is the stricter reading: rsync
    runs no shell, so a literal `~/www` would only make a directory called `~` here.
    """
    try:
        expanded = Path(path).expanduser()
    except RuntimeError:
        return "names a home directory that does not exist on this machine"
    try:
        resolved = expanded.resolve()
    except OSError as e:
        return f"cannot be resolved ({e})"
    shown = str(resolved) + (f" (where {path} leads)" if resolved != expanded else "")
    parts = [p for p in resolved.parts if p != resolved.anchor]
    if len(parts) < _MIN_PARTS:
        return f"{shown} is the filesystem root or a top-level directory"
    try:
        home = Path.home().resolve()
    except (OSError, RuntimeError):
        home = None
    if home is not None and (resolved == home or resolved in home.parents):
        return f"{shown} is your home directory, or an ancestor of it"
    verdict = _home_verdict(str(resolved))
    return verdict.replace(str(resolved), shown, 1) if verdict else None


def publish_dest_problem(dest: str) -> str | None:
    """Why `dest` is unsafe for `rsync --delete`, or None when it is an acceptable webroot.

    Refused: an empty destination, a remote host with no path, the filesystem root, a
    top-level directory, a home directory or any ancestor of one, a path that climbs
    above its own anchor, an unexpanded `$VAR`, and — locally, where the filesystem can
    be read — anything that resolves through a symlink onto one of those.
    """
    raw = (dest or "").strip()
    if not raw:
        return "empty — --delete needs the webroot written out"
    path, remote = _split_dest(raw)
    path = path.strip()
    if not path:
        return "no path after the host — --delete would run in the remote login directory"
    if "$" in path:
        # rsync is handed argv, not a shell line, so the variable is never expanded:
        # what gets deleted is a directory literally named `$HOME`.
        return "carries an unexpanded variable — rsync runs no shell; write the directory out"

    home_prefix, rest = _split_home(path)
    if home_prefix:
        inside = posixpath.normpath(rest.lstrip("/")) if rest.strip("/") else "."
        if inside in (".", "..") or inside.startswith("../"):
            return f"{home_prefix} is a home directory — --delete would erase it"
        checked = f"{home_prefix}/{inside}"
    else:
        # posixpath.normpath keeps *exactly* two leading slashes — POSIX leaves `//`
        # implementation-defined, three or more collapse — and every check below reads
        # the string literally, so `//home/tb4` would slip past the home-directory rule
        # that refuses `/home/tb4`. Nothing here means anything different by `//`.
        checked = re.sub(r"^//+", "/", posixpath.normpath(path))
        if checked in ("", ".", "/"):
            return "is the filesystem root, or the directory publish is run from"
        if checked == ".." or checked.startswith("../"):
            return "climbs above the directory it starts in"
        if checked.startswith("/"):
            parts = [p for p in checked.split("/") if p]
            if len(parts) < _MIN_PARTS:
                return (f"/{parts[0]} is a top-level directory — "
                        "publish into a subdirectory of it, not into it")
            home = _home_verdict(checked)
            if home:
                return home
    if remote:
        return None  # the remote filesystem is out of reach; the string is all there is
    return _local_dest_problem(checked)


def check_publish_dest(dest: str) -> None:
    """Raise RuntimeError unless `dest` is safe to `rsync --delete` into."""
    why = publish_dest_problem(dest)
    if why:
        raise RuntimeError(f"refusing publishDest {dest!r} — {why}")


def _build(root: Path, outdir: Path) -> None:
    script = root / "bin" / "build.sh"
    if not script.is_file():
        raise RuntimeError(f"{script} not found — publish needs the checkout's build script")
    p = _run(["bash", str(script), str(outdir)], cwd=root)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip() or "build failed")


def ask(url: str, branch: str, files: int) -> bool:
    """Show what the force-push overwrites and ask. Non-interactive stdin is a no —
    never a silent yes, the same rule as redact.ask."""
    sys.stderr.write(
        f"about to force-push {files} file(s) to {branch!r} on {url}\n"
        f"  this replaces whatever that branch holds now — the old commit is not kept\n")
    if not sys.stdin.isatty():
        sys.stderr.write("stdin is not a terminal — pass --yes to publish without asking\n")
        return False
    sys.stderr.write(f"force-push to {branch}? [y/N] ")
    sys.stderr.flush()
    return sys.stdin.readline().strip().lower() in ("y", "yes")


def _pages_branch(root: Path, outdir: Path, text: str, dry_run: bool,
                  yes: bool = False, confirm=None) -> dict:
    branch = _param(text, "publishBranch", "pages")
    remote = _param(text, "publishRemote", "origin")
    p = _run(["git", "-C", str(root), "remote", "get-url", remote])
    if p.returncode != 0:
        raise RuntimeError(f"git remote {remote!r} not found in {root}")
    url = p.stdout.strip()
    result = {"remote": remote, "remote_url": url, "branch": branch, "dry_run": dry_run}
    files = sum(1 for f in outdir.rglob("*") if f.is_file())
    if dry_run:
        result.update({"pushed": False, "files": files})
        return result
    if not (yes or (confirm(url, branch, files) if confirm else ask(url, branch, files))):
        result.update({"pushed": False, "files": files, "cancelled": True})
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
    check_publish_dest(dest)  # before the dry-run branch: -n refuses what a real run refuses
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


def publish(repo: Path, dry_run: bool = False, outdir: Path | None = None,
            yes: bool = False, confirm=None) -> dict:
    """Build via bin/build.sh, then deliver per publishTarget. Dry-run still builds.

    pages-branch force-pushes, so it asks first unless --yes; rsync is unchanged.
    """
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
        result.update(_pages_branch(root, out, text, dry_run, yes=yes, confirm=confirm))
    else:
        result.update(_rsync(out, text, dry_run))
    return result
