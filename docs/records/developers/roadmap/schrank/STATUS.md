---
title: schrank — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, schrank, status]
---

# 8 · schrank — status

Road: **Preservation** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked. New road, defined 2026-08-01.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records archive` — bundle + manifest + README.txt | open | — | unpack in an empty dir, all checksums verified |
| 2 | beetle | `records verify` — archives and live checkouts | open | — | corrupted archive rejected, broken image reference reported |
| 3 | cricket | Attachments: leaf page bundles + tooling agrees | open | — | image + PDF + video render on site, PDF and EPUB; flat records untouched |
| 4 | moth | Plain-text export | open | — | whole corpus read end to end in `less` |
| 5 | tadpole | Integrity over time (`--check`, rotation) | open | — | `--check` running from cron |
| 6 | snail | `records attach` | open | — | flat record converted + 3 file types attached in one command |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue gates 2.** Verify reads what archive writes; the manifest format is decided in item 1.
- **Determinism is a requirement, not a nicety** — fixed zip timestamps, sorted entries. Archives
  that differ byte-wise for identical input cannot be diffed or deduplicated.
- **3 · cricket — the convention is decided: Hugo leaf page bundles.** Verified on Hugo 0.164
  against the real config and theme: any file type publishes verbatim, URLs are byte-identical to
  the flat form (`:contentbasename`), chapters and tag folders survive, the `cascade` never touches
  bundles. Do not re-litigate the layout; implement it.
  - Three known breakages to fix as part of the item: `book.lua:293` derives `"index"` as the base
    name, `stick.py`'s `find_record` misses `<slug>/index.md`, and `create.py` needs a bundle mode.
  - Two roads defer to this decision: [suitcase item 3](../suitcase/ROADMAP.md) (export
    attachments) and [akvarium item 3](../akvarium/ROADMAP.md) (audio).
  - The rendering half is **not here** — see [kiste item 6](../kiste/ROADMAP.md). In single and
    single-flowing modes every record renders on `/`, so a relative `image.png` 404s. Theme fix.
- **6 · snail depends on 3.** `records attach` is the ergonomics of the convention; the convention
  has to exist first. It is also what makes the VSCode `@` picker's two meanings (model context vs.
  recorded attachment) finally distinct.
- No git-annex, no LFS, no external store. If it does not fit in a git repo, the honest answer is
  that it does not belong in one.
- **4 · moth** is the item that has to survive this project's own disappearance. If the export needs
  this repo to make sense, it failed.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
