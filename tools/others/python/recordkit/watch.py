"""Watch the records dir, rebuild through the one build path, and bark.

The dog: it notices and it reports. It never commits, never pushes, never
publishes — not behind a flag, not behind a config key. Polling, not inotify:
stdlib only, and a second of latency is cheaper than a dependency.

"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from .config import find_hugo_configs, read_content_dir, resolve_records_dir
from .publish import _checkout_root

_PRUNE = {"node_modules", "public"}
_NOTIFY_MODES = ("fail", "all", "none")

_which = shutil.which  # monkeypatch seam, beside _run


def _run(argv: list[str], cwd: Path | None = None, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True,
                          text=True, env=env)


def _stamp() -> str:
    return time.strftime("%H:%M:%S")


def snapshot(directory: Path) -> dict:
    """{relative path: (mtime, size)} for every file under `directory`; {} when it is gone."""
    directory = Path(directory)
    if not directory.is_dir():
        return {}
    out = {}
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in _PRUNE]
        for name in filenames:
            f = Path(dirpath) / name
            try:
                st = f.stat()
            except OSError:  # deleted between walk and stat
                continue
            out[f.relative_to(directory).as_posix()] = (st.st_mtime, st.st_size)
    return out


def diff(old: dict, new: dict) -> dict:
    return {"added": sorted(set(new) - set(old)),
            "changed": sorted(k for k in set(new) & set(old) if new[k] != old[k]),
            "removed": sorted(set(old) - set(new))}


def notify(title: str, body: str) -> bool:
    """Desktop bark via notify-send; silently no-op where there is none."""
    if not _which("notify-send"):
        return False
    try:
        _run(["notify-send", "--app-name=records", title, body])
    except OSError:
        return False
    return True


def build(root: Path, outdir: str | None = None, base_url: str | None = None) -> dict:
    """bin/build.sh — the one build path, never reimplemented and never bypassed."""
    script = Path(root) / "bin" / "build.sh"
    if not script.is_file():
        return {"ok": False, "output": f"{script} not found — the watcher builds through it"}
    argv = ["bash", str(script)] + ([str(outdir)] if outdir else [])
    env = dict(os.environ)
    if base_url:
        env["BASE_URL"] = base_url
    p = _run(argv, cwd=Path(root), env=env)
    return {"ok": p.returncode == 0, "output": (p.stderr or p.stdout).strip()}


def _bark(event: dict, notify_mode: str) -> None:
    if notify_mode == "none" or (notify_mode == "fail" and event["ok"]):
        return
    if event["ok"]:
        notify("records watch", f"rebuilt in {event['seconds']}s")
    else:
        first = (event["output"].splitlines() or [""])[0]
        notify("records watch", f"build failed: {first[:200]}")


def format_event(event: dict) -> str:
    if event["event"] == "missing":
        return f"{event['time']}  {event['message']}"
    counts = event["changed"]
    what = (f"{len(counts['added'])} added, {len(counts['changed'])} changed, "
            f"{len(counts['removed'])} removed")
    if event["ok"]:
        return f"{event['time']}  rebuilt in {event['seconds']}s — {what}"
    first = (event["output"].splitlines() or [""])[0]
    return f"{event['time']}  BUILD FAILED — {what}\n           {first}"


def watch(repo: Path = Path("."), interval: float = 1.0, once: bool = False,
          notify_mode: str = "fail", base_url: str | None = None,
          outdir: str | None = None, sleep=None, emit=None) -> dict:
    """Poll, debounce, rebuild, report. Ctrl-C leaves cleanly; nothing else is touched."""
    sleep = sleep or time.sleep
    emit = emit or (lambda event: None)
    repo = Path(repo).resolve()
    configs = find_hugo_configs(repo)
    cfg = configs[0] if configs else None
    root = _checkout_root(cfg).resolve() if cfg else repo
    records_dir = ((cfg.parent / read_content_dir(cfg)).resolve() if cfg
                   else resolve_records_dir(repo))

    state = snapshot(records_dir)
    missing = not records_dir.is_dir()
    builds = failures = 0
    try:
        while True:
            sleep(interval)
            if not records_dir.is_dir():
                if not missing:
                    missing = True
                    emit({"event": "missing", "ok": False, "time": _stamp(),
                          "message": f"{records_dir} is gone — still watching"})
                if once:
                    break
                continue
            if missing:  # came back: re-baseline rather than rebuild the whole dir
                missing, state = False, snapshot(records_dir)
            new = snapshot(records_dir)
            if new == state:
                if once:
                    break
                continue
            while True:  # debounce: an editor writing a file makes several events
                sleep(interval)
                newer = snapshot(records_dir)
                if newer == new:
                    break
                new = newer
            changed, state = diff(state, new), new
            started = time.monotonic()
            result = build(root, outdir=outdir, base_url=base_url)
            builds += 1
            failures += 0 if result["ok"] else 1
            event = {"event": "build", "ok": result["ok"], "changed": changed,
                     "output": result["output"], "time": _stamp(),
                     "seconds": round(time.monotonic() - started, 2)}
            emit(event)
            _bark(event, notify_mode)
            if once:
                break
    except KeyboardInterrupt:
        pass
    return {"records_dir": str(records_dir), "repo": str(root), "builds": builds,
            "failures": failures, "stopped": True}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="records watch",
                                description="Rebuild when a record changes. Never commits, "
                                            "never pushes, never publishes.")
    p.add_argument("--repo", default=".")
    p.add_argument("--interval", type=float, default=1.0, help="seconds between polls")
    p.add_argument("--once", action="store_true", help="one poll cycle, then exit")
    p.add_argument("--json", action="store_true", help="one JSON object per event")
    p.add_argument("--outdir", help="build destination (default: <repo>/public)")
    p.add_argument("--base-url", dest="base_url",
                   help="BASE_URL for the build when the site config leaves baseURL commented")
    p.add_argument("--notify", choices=_NOTIFY_MODES, default="fail",
                   help="desktop notifications (default: only on failure)")
    args = p.parse_args(argv)

    def emit(event):
        print(json.dumps(event) if args.json else format_event(event), flush=True)

    result = watch(Path(args.repo), interval=args.interval, once=args.once,
                   notify_mode=args.notify, base_url=args.base_url, outdir=args.outdir,
                   emit=emit)
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
