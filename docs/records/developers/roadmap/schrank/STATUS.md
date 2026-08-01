---
title: schrank — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, schrank, status]
---

# 8 · schrank — status

Road: **Preservation** · [plan](ROADMAP.md) · [protocol](../README.md)

Walked end to end, 2026-08-01, across three commits. All six items are in.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records archive` — bundle + manifest + README.txt | done | `825363e` | unpack in an empty dir, all checksums verified |
| 2 | beetle | `records verify` — archives and live checkouts | done | `825363e` | corrupted archive rejected, broken image reference reported |
| 3 | cricket | Attachments: leaf page bundles + tooling agrees | done | `8a1ae70` | image + PDF + video render on site, PDF and EPUB; flat records untouched |
| 4 | moth | Plain-text export | done | `50690a8` | whole corpus read end to end in `less` |
| 5 | tadpole | Integrity over time (`--check`, rotation) | done | `825363e` | `--check` running from cron |
| 6 | snail | `records attach` | done | `8a1ae70` | flat record converted + 3 file types attached in one command |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **Determinism held** — fixed zip timestamps, sorted entries, `SOURCE_DATE_EPOCH` pinning the
  manifest stamp, so an unchanged tree archives byte-identically and dedupes.
- **3 · cricket's third breakage was missed, and is now fixed.** The item named three:
  `book.lua`'s `"index"` base name (fixed in `8a1ae70`), `create.py`'s bundle mode (fixed in
  `8a1ae70`), and **`stick.py`'s `find_record` missing `<slug>/index.md` — which was not**.
  The result was two shipped commands contradicting each other: `records attach` converted a record
  to a bundle and `records stick` could then no longer find it (`{"error": "not found"}`).
  `find_record` now matches both shapes, with `tests/test_stick.py` covering the regression
  end to end (attach, then stick, on the same record).
- **The rendering half is still not here** — see [kiste item 6](../kiste/ROADMAP.md), which remains
  open. In single and single-flowing modes every record renders on `/`, so a relative `image.png`
  404s. That is a theme fix and it has not been made.
- **Parallel-session collision, still live:** [postkasse 4](../postkasse/ROADMAP.md) also rewrites
  `find_record`, for checkout-awareness. That function now carries the bundle fix and a test file;
  whoever takes postkasse 4 extends both rather than replacing them.
- Two roads deferred to this decision: [suitcase item 3](../suitcase/ROADMAP.md) (export
  attachments) and [akvarium item 3](../akvarium/ROADMAP.md) (audio, which answered *no*).
- No git-annex, no LFS, no external store — the border held.
- No git-annex, no LFS, no external store. If it does not fit in a git repo, the honest answer is
  that it does not belong in one.
- **4 · moth** is the item that has to survive this project's own disappearance. If the export needs
  this repo to make sense, it failed.

## What landed

`recordkit/archive.py` (13 tests), `verify.py` (12), `export.py` (12), `attach.py` (18) and the
shared reference scanner `refs.py` (11) — all five now registered in `cli.py`, which they were not
when the road's commits were written.

Re-verified during consolidation, against this checkout: `records archive` wrote a 13-entry bundle;
`records verify <archive>` recomputed every checksum clean; `records verify` over the checkout found
no broken references; `records archive --check` printed **nothing** and exited 0, which is item 5
working as designed — cron mails what a job prints, so a healthy run must say nothing. `records
export --single` collapsed the 10-record corpus into one text file. `records attach` converted a
flat record to `<slug>/index.md`, copied a PNG and a PDF beside it, and appended a figure and a link.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
