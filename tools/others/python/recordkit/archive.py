"""One self-contained bundle holding everything needed to rebuild — or simply to read — a records site.

The manifest is the point: written first, listing every entry with its size and SHA-256, so an
archive can be checked without unpacking it. Output is deterministic (fixed zip timestamps, sorted
entries), so archives of an unchanged tree are byte-identical and dedupe. The only varying input is
the manifest's `created` stamp — set SOURCE_DATE_EPOCH to pin it.

zipfile and hashlib, both stdlib. No compression library, no external checksum tool.

WIRING (deferred — parallel-session rule, see docs/records/developers/roadmap/README.md):

    ar = sub.add_parser("archive", help="bundle records, assets, config and a checksum manifest")
    ar.add_argument("--repo", default=".")
    ar.add_argument("--out", help="archive path; default ./records-<timestamp>.zip")
    ar.add_argument("--dry-run", action="store_true", help="list what would go in, and what would not")
    ar.add_argument("--check", action="store_true", help="cron mode: silent unless something is wrong")

    elif args.cmd == "archive":
        if args.check:
            report = archive.check(Path(args.repo), Path(args.out) if args.out else None)
            if not report["ok"]:
                _emit(report)
                return 1
            return 0                      # deliberate silence — cron mails what it prints
        _emit(archive.archive(Path(args.repo), Path(args.out) if args.out else None,
                              dry_run=args.dry_run))
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from . import config, naming, refs

SCHEMA = "records-archive/1"

_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)  # fixed: zip timestamps would otherwise break determinism
_FILE_MODE = 0o644 << 16
_MANIFEST = "manifest.json"
_README = "README.txt"

README_TEXT = """\
WHAT THIS IS
============

An archive of a conversation record collection — a "records" site.

Everything of value here is plain text. If the tools that made this are gone, the .md files under
records/ are still the content, and they are readable exactly as they are. Open them in any text
editor. Nothing needs to be installed, converted or run.


WHAT IS IN HERE
===============

manifest.json   A list of every file in this archive with its size and SHA-256 checksum, plus
                where it came from and when it was made. Read it first; it is plain JSON.
README.txt      This file.
records/        The conversations. One Markdown (.md) file per conversation, or a folder with an
                index.md when the conversation carries images or other attachments beside it.
static/         Images and other files that records point at but that were stored outside
                records/. Only files actually referenced are included.
hugo.yaml       The configuration of the site these records were published as. Kept for context;
                it is not needed to read anything.
CURRENT         One line naming the version of the project that made this archive.


HOW TO READ A RECORD
====================

A record is a conversation. It opens with a small block between two lines of three dashes:

    ---
    title: A conversation about bicycles
    date: 2026-07-06T23:22:00+01:00
    tags: [bicycles, repair]
    ---

That block is metadata — the title, when it happened, and any labels. Everything after it is the
conversation itself, which alternates between two kinds of heading:

    ## Human            what the person said (sometimes "## Human (name)")
    ## Assistant        what the AI assistant replied

The text under each heading is what was said, in full.

After an assistant's reply you may see a line beginning with an em dash:

    — mistral:latest

That is a signature. It names the AI model that produced the reply immediately above it. It is not
part of what was said. Older records may use "## User" instead of "## Human"; they mean the same
thing.

Images and attachments are referenced by their filename, like ![a photo](photo.jpg), and the file
sits in the same folder as the record that mentions it.


CHECKING THAT NOTHING HAS ROTTED
================================

Every entry in manifest.json carries the SHA-256 checksum of the file's contents. To check this
archive by hand after unpacking it, on any system with Python:

    python3 - <<'EOF'
    import hashlib, json, pathlib
    m = json.load(open("manifest.json"))
    for e in m["entries"]:
        p = pathlib.Path(e["path"])
        got = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
        if got != e["sha256"]:
            print("FAULT", e["path"], "missing" if got is None else "checksum mismatch")
    print("checked", len(m["entries"]), "files")
    EOF

Silence means everything matches.


THAT IS ALL
===========

There is no database, no index, no proprietary format, and nothing else to recover. The words are
the files.
"""


def _run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")  # fail fast, never prompt
    return subprocess.run(argv, cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, env=env)


def _git(root: Path, *args: str) -> str | None:
    """A git value, or None outside a checkout — provenance is nice to have, never required."""
    try:
        p = _run(["git", "-C", str(root), *args])
    except OSError:
        return None
    return p.stdout.strip() or None if p.returncode == 0 else None


def created_stamp(when: datetime | None = None) -> str:
    """UTC, second precision. SOURCE_DATE_EPOCH wins, which is what makes byte-identical runs possible."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.strip().isdigit():
        when = datetime.fromtimestamp(int(epoch.strip()), tz=timezone.utc)
    return (when or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_repo(repo: Path) -> tuple[Path, Path, Path | None]:
    """(checkout root, records dir, site config) for a --repo argument."""
    configs = config.find_hugo_configs(Path(repo))
    if configs:
        cfg = configs[0]
        return config.checkout_root(cfg).resolve(), config.resolve_records_dir(Path(repo)), cfg
    records_dir = config.resolve_records_dir(Path(repo))
    if not records_dir.is_dir():
        raise RuntimeError(f"no records directory found under {repo} — nothing to archive")
    return Path(repo).resolve(), records_dir, None


def _static_dirs(root: Path) -> list[Path]:
    """The site and theme static dirs, in the same order refs.resolve searches them."""
    root = Path(root)
    return [d for d in (root / "tools" / "hugo" / "static",
                        root / "tools" / "hugo" / "themes" / "Fuglekasse" / "static")
            if d.is_dir()]


def plan(root: Path, records_dir: Path, cfg: Path | None) -> tuple[list[tuple[str, Path]], list[dict]]:
    """(entries, excluded): what goes in the bundle, and what is left out with a reason each."""
    entries: list[tuple[str, Path]] = []
    excluded: list[dict] = []

    for f in sorted(p for p in records_dir.rglob("*") if p.is_file()):
        entries.append(("records/" + f.relative_to(records_dir).as_posix(), f))

    wanted: dict[Path, str] = {}
    for arc, src in list(entries):
        if not src.name.endswith(".md"):
            continue
        text = src.read_text(encoding="utf-8", errors="replace")
        for target in refs.asset_references(text):
            hit = refs.resolve(target, src, records_dir, root)
            if hit is None:
                excluded.append({"path": target, "reason": "not found",
                                 "referenced_by": arc})
            elif not _under(hit, records_dir):
                arcname = _static_arcname(hit, root)
                if arcname:
                    wanted[hit] = arcname
                else:
                    excluded.append({"path": str(hit), "reason": "outside the bundle",
                                     "referenced_by": arc})

    for src, arc in sorted(wanted.items(), key=lambda kv: kv[1]):
        entries.append((arc, src))

    for d in _static_dirs(root):
        for f in sorted(p for p in d.rglob("*") if p.is_file()):
            if f.resolve() not in wanted:
                excluded.append({"path": str(f.relative_to(root)), "reason": "unreferenced"})

    if cfg and cfg.is_file():
        entries.append(("hugo.yaml", cfg))
    current = root / "CURRENT"
    if current.is_file():
        entries.append(("CURRENT", current))

    payload = sorted(entries, key=lambda e: e[0])
    return payload, excluded


def _under(path: Path, parent: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(parent).resolve())
    except ValueError:
        return False
    return True


def _static_arcname(hit: Path, root: Path) -> str | None:
    for d in _static_dirs(root):
        if _under(hit, d):
            return "static/" + hit.resolve().relative_to(d.resolve()).as_posix()
    return None


def _sha256(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def _write(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    """Every entry gets the same fixed metadata; only the name and bytes differ."""
    info = zipfile.ZipInfo(arcname, date_time=_ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3  # posix, fixed — the default varies by platform
    info.external_attr = _FILE_MODE
    zf.writestr(info, data)


def default_out(root: Path, when: datetime | None = None) -> Path:
    """./records-<timestamp>.zip — the working directory, never inside the repo."""
    return Path.cwd() / f"records-{naming.now_stamp(when)}.zip"


def archive(repo: Path = Path("."), out: Path | None = None, dry_run: bool = False,
            when: datetime | None = None) -> dict:
    """Bundle the records tree, referenced assets, the site config and the cycle line."""
    root, records_dir, cfg = resolve_repo(Path(repo))
    if not records_dir.is_dir():
        raise RuntimeError(f"records directory {records_dir} does not exist — nothing to archive")
    entries, excluded = plan(root, records_dir, cfg)
    target = Path(out) if out else default_out(root, when)

    result = {"repo": str(root), "records_dir": str(records_dir), "out": str(target),
              "entries": len(entries), "excluded": excluded, "dry_run": dry_run}
    if dry_run:
        result["would_include"] = [arc for arc, _ in entries]
        result["written"] = False
        return result

    manifest = {
        "schema": SCHEMA,
        "created": created_stamp(when),
        "cycle": _read_cycle(root),
        "repo_url": _git(root, "remote", "get-url", "origin"),
        "commit": _git(root, "rev-parse", "HEAD"),
        "records_dir": records_dir.name,
        "entries": [],
    }
    for arc, src in entries:
        digest, size = _sha256(src)
        manifest["entries"].append({"path": arc, "size": size, "sha256": digest})

    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        _write(zf, _MANIFEST, json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        _write(zf, _README, README_TEXT.encode("utf-8"))
        for arc, src in entries:
            _write(zf, arc, Path(src).read_bytes())

    result.update({"written": True, "bytes": target.stat().st_size,
                   "created": manifest["created"], "commit": manifest["commit"]})
    return result


def _read_cycle(root: Path) -> str | None:
    current = Path(root) / "CURRENT"
    try:
        return current.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def newest_archive(directory: Path) -> Path | None:
    """The most recently modified records-*.zip in a directory — what --check falls back to."""
    found = sorted(Path(directory).glob("records-*.zip"), key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None


def check(repo: Path = Path("."), out: Path | None = None) -> dict:
    """Cron mode: verify an existing archive and the live checkout. Faults only, ok=False on any."""
    from . import verify

    root, records_dir, _ = resolve_repo(Path(repo))
    target = Path(out) if out else newest_archive(Path.cwd())
    faults: list[dict] = []
    checked = 0

    if target is None:
        faults.append({"kind": "no-archive", "path": str(Path.cwd()),
                       "detail": "no records-*.zip found; pass --out to name one"})
    else:
        report = verify.verify_archive(target)
        faults += report["faults"]
        checked += report["checked"]

    repo_report = verify.verify_repo(root)
    faults += repo_report["faults"]
    checked += repo_report["checked"]

    return {"ok": not faults, "faults": faults, "checked": checked,
            "archive": str(target) if target else None, "repo": str(root),
            "records_dir": str(records_dir)}
