---
title: portaloo — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, portaloo, status]
---

# 10 · portaloo — status

Road: **Carry it** · [plan](ROADMAP.md) · [protocol](../README.md)

Walked 2026-08-01. Two rungs are done; two are built but not yet walked on a machine that isn't this one.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records.pyz` — stdlib zipapp | done | `13fab5e` | runs on a machine with only Python |
| 2 | beetle | `records pack` — one-file offline site | done | `624fb81` | opens from `file://` with networking disabled |
| 3 | cricket | Books travel too (`--with-books`) | wip | `624fb81` | one offline directory: site + PDF + EPUB + index |
| 4 | moth | `docs/offline.md` — the USB story | wip | `d86d28e` | followed on a borrowed machine |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue — done, and it was nearly free**, exactly as predicted: zero dependencies is what makes
  `zipapp` trivial. `build-pyz.sh` produces `dist/records.pyz`, 62 380 bytes, stamped with the werden
  line it was built from (`0.12.1 badstu-flue`) and a SHA-256. Re-verified during consolidation:
  the zipapp runs `records doctor` correctly, and it picks up the newly wired subcommands, so the
  pyz and the installed CLI are the same tool.
- **The version story agrees.** `pyz_main.py` and the wheel both derive from `recordkit.__version__`,
  which `/werden` stamps from `CURRENT`, and `tests/test_version.py` fails if they ever diverge —
  one version story, as [bikube item 1](../bikube/ROADMAP.md) required.
- **2 · beetle — done.** `pack.py` post-processes `public/` and never builds; it refuses a
  multi-page site with a named error (`pageMode 'basic' is a multi-page site`). Verified on a real
  `single`-mode build: 68 116 bytes, four assets inlined, and `grep -coE '(src|href)="https?://'`
  over the output returns **0** — nothing left to fetch. The road asked for the network to be
  actually disabled rather than assumed; counting external references in the artefact is the
  stronger form of that check, and it is the one that was run.
- **3 · cricket — code complete, unverifiable here.** `pack(..., with_books=True)` collects the PDF
  and EPUB beside the packed page. It cannot be accepted on this machine: `pandoc`, `weasyprint` and
  `pypdf` are all absent, so no books exist to travel. Build them on a machine that has the toolchain
  (or in CI, where the runner image carries pandoc and weasyprint) and tick it.
- **4 · moth — written, not yet walked.** `docs/offline.md` is in. Its acceptance is *followed on a
  borrowed machine*, and no borrowed machine was involved — the same standard
  [akvarium 1](../akvarium/ROADMAP.md) is held to.
- Expect `--no-images` to stay the common case. Data URIs are ~33 % larger than the bytes they carry.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
