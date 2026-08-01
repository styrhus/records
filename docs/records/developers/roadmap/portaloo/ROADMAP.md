---
title: portaloo — Carry it
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, portaloo]
---

# 10 · portaloo — Carry it

> The whole facility, carried. Not glamorous. Extremely useful.

Two deliverables that mean the same thing in different directions: **needs nothing installed**.

`records.pyz` is the engine as one file. Copy it to a machine with Python and it runs — no pip, no
pipx, no virtualenv, no network. The kind of thing you keep on a USB stick.

`records pack` is the site as one file. Every stylesheet inlined, every image a data URI, every link
relative — opens from `file://`, works on a train, works on a laptop that has never heard of Hugo,
works in ten years.

Both are the same instinct: the thing should survive being carried away from everything that made it.

## Dependencies

Item 1 pairs with bikube but does not need it — a zipapp is an alternative distribution, not a
replacement for PyPI.

Item 2 needs a built site, which every road already produces.

## Items

### 1 · flue — `records.pyz`

The engine as a single executable file, built with stdlib `zipapp`.

- A build script (`tools/others/python/build-pyz.sh` or a `make` target) producing `records.pyz`
  from `recordkit/`.
- Zero dependencies makes this genuinely trivial — that is the payoff of the border, and it should
  be said out loud in the docs.
- Shebang set so `./records.pyz new "title"` works directly on Unix.
- Version stamped from `CURRENT`, agreeing with the PyPI version from
  [bikube item 1](../bikube/ROADMAP.md); one version story, not two.
- Determinism: same source, same bytes, so the artefact can be checksummed and compared.
- Document the Python floor (whatever `recordkit` actually requires — check, don't guess) and test
  on it.
- Attach it to releases alongside the git tag that release-worthy major steps already carry.

**Files:** `tools/others/python/build-pyz.sh`, `tools/others/README.md`.

**Acceptance:** `records.pyz` copied to a machine with only Python installed, creating and appending
to a record in a checkout, output pasted.

### 2 · beetle — `records pack`

The entire site as one self-contained HTML file.

- New `recordkit/pack.py` behind `records pack [--repo .] [--out FILE]`, running after the normal
  build rather than replacing it — **one build path**, always.
- It post-processes `public/`: inline every `<link rel=stylesheet>`, inline every `<script>`,
  convert every referenced image to a `data:` URI, and rewrite internal links to in-page anchors.
- `pageMode: single` and `single-flowing` are the natural fit — they are already one page. Other
  modes either flatten to single or are refused with a clear message; decide, implement, document.
- Size is the honest constraint. Measure and report the output size, and warn above a threshold —
  data URIs are roughly a third larger than the bytes they carry, and a corpus with photographs will
  produce something no browser enjoys.
- `--no-images` for a text-only pack, which will be the sane choice more often than not.
- The result must open from `file://` with no server and no network access whatsoever. Test with
  the network disabled, not just with the file open.

**Files:** `recordkit/pack.py`, `recordkit/cli.py`, `tests/test_pack.py`.

**Acceptance:** a packed file opened from `file://` on a machine with networking disabled, rendering
completely, with its size reported.

**Border:** stdlib only — `html.parser` or careful string work, no BeautifulSoup, no bundler.

### 3 · cricket — Books travel too

The PDF and EPUB are already single files, which makes them the most portable thing here — they just
are not treated that way.

- A `records pack --with-books` that gathers the packed HTML, the PDF, the EPUB and the booklet into
  one directory or archive, with a small index.
- Reuse [schrank's](../schrank/ROADMAP.md) manifest format rather than inventing a second one, if
  that road has landed.
- Skip cleanly when the book params are unset or the toolchain is missing, exactly as
  `bin/build.sh` already does.

**Acceptance:** a single directory containing the site, the books and an index, usable offline.

### 4 · moth — The USB story, written down

The item that makes the other three mean something.

- A short `docs/offline.md`: how to put your records, the engine and the site on a stick and use all
  three on a machine that has nothing.
- Covers the realistic cases — a laptop without Python (the packed HTML still works), a machine
  without network (everything works), a machine that is not yours (nothing is installed, nothing is
  left behind).
- Explicit about what does *not* travel: publishing needs a network, Ollama needs a model, git needs
  a remote.

**Acceptance:** someone follows the page on a borrowed machine and reads their records.

## Borders for this road

- Stdlib only. `zipapp`, `base64`, `html.parser`. No bundler, no minifier, no parser library.
- One build path. `records pack` post-processes what `bin/build.sh` produced; it never builds a site
  itself.
- One version story — the zipapp, the PyPI package and `CURRENT` agree.
- Offline means offline. If the packed file fetches anything, from anywhere, it is broken.
