# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Write a whole file's replacement text without a truncate-then-write window.

`Path.write_text` opens the target in truncating mode first and writes the new content after —
if the process dies, the disk fills, or anything else interrupts it in between, the file is left
empty or half-written and the previous content is already gone. `redact` and `unpublish` rewrite a
person's own conversation record in place (that is the whole point of both), so this is the one
place in the engine where a plain write is a real way to lose a user's data. `atomic_write_text`
writes to a temp file beside the target and swaps it in with a single `os.replace` — on every
platform this project targets, that swap either lands in full or not at all; the target is never
observed half-written, and a failure before the swap leaves the original file untouched.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8",
                      errors: str | None = None) -> None:
    """Replace `path`'s content with `text`, atomically. Leaves `path` untouched on any failure.

    `errors` is passed straight to the encoder, for the one caller that rewrites documents which
    may hold undecodable bytes (`werden._stamp_docs`, `surrogateescape`). The default is `None`,
    which is the encoder's own default — strict — so every other caller is unaffected.
    """
    path = Path(path)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        # fdopen takes ownership of fd straight away, so nothing below can leak it.
        with os.fdopen(fd, "w", encoding=encoding, errors=errors) as f:
            # mkstemp makes the temp file 0600 regardless of umask; match the replaced file's
            # mode (or the platform default when there isn't one yet) so redact/unpublish don't
            # quietly tighten permissions on every rewrite.
            try:
                mode = path.stat().st_mode & 0o777
            except OSError:
                mode = 0o666 & ~_umask()
            os.fchmod(f.fileno(), mode)
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)  # single filesystem-level swap — atomic on POSIX and Windows
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _umask() -> int:
    """The process umask, read without side effects (os.umask has none but must set to read)."""
    current = os.umask(0)
    os.umask(current)
    return current
