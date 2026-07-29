"""git commit/push and Hugo deploy — the mechanical core of /gc, /gcp, /cpd."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .config import find_hugo_configs

_DEPLOYCMD = re.compile(r"^\s*deployCommand:\s*(.*?)\s*(?:#.*)?$")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def has_changes(repo: Path) -> bool:
    return bool(_git(repo, "status", "--short").stdout.strip())


def commit(repo: Path, message: str | None, push: bool = False, deploy: bool = False) -> dict:
    """Stage + commit (message required when there are changes — no AI to author one), then
    optionally push and deploy. Mirrors /gc (commit), /gcp (+push), /cpd (+push +deploy)."""
    repo = Path(repo)
    result: dict = {"repo": str(repo), "committed": False, "pushed": False, "deployed": False}
    if has_changes(repo):
        if not message:
            raise ValueError("commit message required (no AI to author one): pass -m")
        add = _git(repo, "add", "-A")
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or "git add failed")
        cm = _git(repo, "commit", "-m", message)
        if cm.returncode != 0:
            raise RuntimeError(cm.stderr.strip() or cm.stdout.strip() or "git commit failed")
        result["committed"] = True
    else:
        result["note"] = "no changes to commit"
    if push:
        pr = _git(repo, "push")
        if pr.returncode != 0:
            raise RuntimeError(pr.stderr.strip() or "git push failed")
        result["pushed"] = True
    if deploy:
        result["deploy"] = _deploy(repo)
        result["deployed"] = bool(result["deploy"].get("ran"))
    return result


def _deploy(repo: Path) -> dict:
    """deployCommand first — so `deployCommand: records publish` beats the shipped
    workflow dirs and is the no-CI publish hook — then workflow presence, then none."""
    configs = find_hugo_configs(repo)
    if configs:
        for line in configs[0].read_text(encoding="utf-8").splitlines():
            m = _DEPLOYCMD.match(line)
            if m and m.group(1):
                cmd = m.group(1).strip().strip('"').strip("'")
                run = subprocess.run(cmd, shell=True, cwd=str(repo), capture_output=True, text=True)
                return {"method": "deployCommand", "command": cmd, "ran": True,
                        "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
    for wf in (".forgejo/workflows", ".github/workflows"):
        d = repo / wf
        if d.is_dir() and any(d.iterdir()):
            return {"method": "workflow", "ran": False,
                    "note": f"push triggers the {wf} workflow; nothing to run locally"}
    if (repo / ".gitlab-ci.yml").is_file():
        return {"method": "workflow", "ran": False,
                "note": "push triggers the .gitlab-ci.yml pipeline; nothing to run locally"}
    return {"method": None, "ran": False,
            "note": "no deploy method found (set params.deployCommand in hugo.yaml)"}
