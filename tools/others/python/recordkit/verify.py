"""Read an archive back, or a live checkout, and report rot.

An archive nobody has ever opened is a hope, not a backup. `verify_archive` recomputes every
checksum against the manifest; `verify_repo` asks the everyday question instead — does every
relative image reference in every record still resolve to a file that exists? A moved image is a
broken image on the site and a missing figure in the PDF, silently, today.

An early plan asked for a --json flag. There is none: the CLI emits JSON on stdout for every command
by design (cli._emit), so `records verify` is already machine-readable.

"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from . import config, refs

_SKIP = ("manifest.json", "README.txt")


def _fault(kind: str, path: str, detail: str, **extra) -> dict:
    return {"kind": kind, "path": path, "detail": detail, **extra}


def verify_archive(archive: Path) -> dict:
    """Recompute every entry's SHA-256 against the manifest; report mismatches, gaps and extras."""
    archive = Path(archive)
    if not archive.is_file():
        return {"ok": False, "checked": 0, "archive": str(archive),
                "faults": [_fault("missing", str(archive), "archive file does not exist")]}

    faults: list[dict] = []
    try:
        zf = zipfile.ZipFile(archive)
    except zipfile.BadZipFile as e:
        return {"ok": False, "checked": 0, "archive": str(archive),
                "faults": [_fault("unreadable", str(archive), f"not a readable zip: {e}")]}

    with zf:
        try:
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            entries = manifest["entries"]
        except (KeyError, ValueError, UnicodeDecodeError) as e:
            return {"ok": False, "checked": 0, "archive": str(archive),
                    "faults": [_fault("manifest", "manifest.json",
                                      f"absent or unreadable: {e}")]}

        present = {n for n in zf.namelist() if n not in _SKIP}
        checked = 0
        for entry in entries:
            name = entry["path"]
            if name not in present:
                faults.append(_fault("missing", name, "listed in the manifest, absent from the archive"))
                continue
            present.discard(name)
            try:
                data = zf.read(name)
            except (zipfile.BadZipFile, RuntimeError) as e:
                faults.append(_fault("unreadable", name, str(e)))
                continue
            checked += 1
            digest = hashlib.sha256(data).hexdigest()
            if digest != entry["sha256"]:
                faults.append(_fault("checksum", name, "contents do not match the manifest",
                                     expected=entry["sha256"], actual=digest))
            elif len(data) != entry["size"]:
                faults.append(_fault("size", name, "size does not match the manifest",
                                     expected=entry["size"], actual=len(data)))

        for name in sorted(present):
            faults.append(_fault("extra", name, "in the archive, absent from the manifest"))

    return {"ok": not faults, "checked": checked, "archive": str(archive),
            "created": manifest.get("created"), "commit": manifest.get("commit"),
            "faults": faults}


def verify_repo(repo: Path = Path(".")) -> dict:
    """Every local image/media reference in every record, resolved the way the site resolves it."""
    from . import archive as archive_mod

    root, records_dir, cfg = archive_mod.resolve_repo(Path(repo))
    theme = config.read_theme(cfg) if cfg else config.DEFAULT_THEME
    faults: list[dict] = []
    checked = 0

    for record in sorted(records_dir.rglob("*.md")):
        text = record.read_text(encoding="utf-8", errors="replace")
        for target in refs.asset_references(text):
            checked += 1
            if refs.resolve(target, record, records_dir, root, theme) is None:
                faults.append(_fault("broken-reference", target,
                                     "no file of that name beside the record, in the records "
                                     "root, or in a static directory",
                                     record=str(record.relative_to(records_dir))))

    return {"ok": not faults, "checked": checked, "repo": str(root),
            "records_dir": str(records_dir), "faults": faults}
