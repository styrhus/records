# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Stamp the MPRIS now-playing track into a file (/mucke)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .writer import append_block

_DIV = (
    '<div style="text-align:right">'
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
    'style="vertical-align:-2px" aria-hidden="true">'
    '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/>'
    '<circle cx="18" cy="16" r="3"/></svg> {title} • {artist}</div>'
)


def _playerctl(field: str) -> str:
    try:
        r = subprocess.run(["playerctl", "metadata", field], capture_output=True, text=True)
    except FileNotFoundError:
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def now_playing() -> tuple[str, str] | None:
    """(title, artist) of the current track, or None when nothing is playing."""
    title = _playerctl("title")
    if not title:
        return None
    return title, _playerctl("artist")


def stamp(file: Path) -> dict:
    np = now_playing()
    if np is None:
        raise RuntimeError("nothing playing")
    title, artist = np
    append_block(Path(file), _DIV.format(title=title, artist=artist))
    return {"file": str(file), "title": title, "artist": artist}
