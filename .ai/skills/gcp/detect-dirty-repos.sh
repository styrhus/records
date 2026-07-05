#!/usr/bin/env bash
# Print the git status + diff of every dirty repo open in the current editor
# window, so the commit skill can author messages and commit in ONE shot.
#
# Repo discovery, in priority order:
#   1. The Claude Code IDE lock files (~/.claude/ide/<port>.lock) — the editor's
#      own list of open folders (workspaceFolders). We filter to LIVE windows by
#      checking which lock ports have a listening socket (pid is the shared
#      VSCode main process and stale locks accumulate, so neither is reliable),
#      then pick the lock whose folders contain $PWD.
#   2. Fallback: a VSCode .code-workspace file in $PWD or up to 3 parent dirs.
#   3. $PWD is always included.
#
# This logic lives in a standalone script (not inline in the SKILL.md `!`
# injection) on purpose: Claude Code's shell-injection permission checker
# statically analyzes the injected command, and it cannot parse heredocs or
# embedded Python. Keeping the injection a single script call lets it be
# allow-listed cleanly while the complexity stays here.
set -u

PWD_REAL=$(realpath "$PWD")
export PWD_REAL

python3 <<'EOF'
import glob
import json
import os
import subprocess

PWD_REAL = os.environ["PWD_REAL"]
HOME = os.path.expanduser("~")
DIFF_CAP = 400  # max diff lines per repo before falling back to --stat


def listening_ports():
    """Set of TCP ports in LISTEN state, from /proc (Linux, no ss/lsof dep)."""
    ports = set()
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as fh:
                next(fh)  # header
                for line in fh:
                    parts = line.split()
                    if len(parts) < 4 or parts[3] != "0A":  # 0A = TCP_LISTEN
                        continue
                    ports.add(int(parts[1].split(":")[1], 16))
        except (OSError, ValueError, StopIteration):
            continue
    return ports


def folders_from_ide():
    """workspaceFolders of the live IDE window whose folders contain $PWD."""
    live = listening_ports()
    best = None          # (match_len, folders)
    for lock in glob.glob(os.path.join(HOME, ".claude", "ide", "*.lock")):
        stem = os.path.splitext(os.path.basename(lock))[0]
        try:
            port = int(stem)
        except ValueError:
            continue
        if port not in live:
            continue
        try:
            with open(lock) as fh:
                folders = json.load(fh).get("workspaceFolders", [])
        except (OSError, ValueError):
            continue
        for f in folders:
            fr = os.path.realpath(f)
            if PWD_REAL == fr or PWD_REAL.startswith(fr + os.sep):
                if best is None or len(fr) > best[0]:
                    best = (len(fr), folders)
    return best[1] if best else []


def folders_from_workspace_file():
    """folders[] of a .code-workspace in $PWD or up to 3 parent dirs."""
    d = PWD_REAL
    ws_file = None
    for _ in range(4):
        hits = glob.glob(os.path.join(d, "*.code-workspace"))
        if hits:
            ws_file = hits[0]
            break
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    if not ws_file:
        return []
    try:
        with open(ws_file) as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    ws_dir = os.path.dirname(ws_file)
    out = []
    for f in data.get("folders", []):
        p = f.get("path", "")
        if not os.path.isabs(p):
            p = os.path.join(ws_dir, p)
        out.append(p)
    return out


def resolve_folders():
    folders = folders_from_ide() or folders_from_workspace_file()
    resolved, seen = [], set()
    for f in [PWD_REAL] + folders:
        fr = os.path.realpath(f)
        if fr not in seen:
            seen.add(fr)
            resolved.append(fr)
    return resolved


def git(path, *args):
    return subprocess.run(
        ["git", "-C", path, *args], capture_output=True, text=True
    )


def is_repo(path):
    return git(path, "rev-parse", "--git-dir").returncode == 0


def emit(path):
    if not os.path.isdir(path) or not is_repo(path):
        return False
    status = git(path, "status", "--short").stdout
    if not status.strip():
        return False
    print(f"=== {path} ===")
    print(status.rstrip())
    print("--- diff (git diff HEAD) ---")
    diff = git(path, "--no-pager", "diff", "HEAD").stdout
    lines = diff.splitlines()
    if len(lines) > DIFF_CAP or "Binary files" in diff:
        print(git(path, "--no-pager", "diff", "HEAD", "--stat").stdout.rstrip())
        print("(diff truncated — see --stat above)")
    else:
        print(diff.rstrip())
    print()
    return True


any_dirty = False
for path in resolve_folders():
    if emit(path):
        any_dirty = True

if not any_dirty:
    print("(no changes in any open repo)")
EOF
