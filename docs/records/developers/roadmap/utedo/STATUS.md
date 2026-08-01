---
title: utedo — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, utedo, status]
---

# 11 · utedo — status

Road: **What must leave** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked. New road, defined 2026-08-01.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records redact` — rewrite a turn, leave a seam | open | — | redacted record renders; output states git retains the original |
| 2 | beetle | `records unpublish` + `--restore` | open | — | gone from site, books and pages branch; then restored |
| 3 | cricket | Secret in a transcript: `docs/oops.md` + `records scan` | open | — | planted test secret found; procedure reviewed |
| 4 | moth | `.recordsignore` over existing `ignoreFiles` | open | — | ignored file absent from site, PDF and EPUB |
| 5 | tadpole | `docs/other-people.md` — consent, written down | open | — | page exists, short, not a ToS |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **The border that defines this road: never rewrite git history automatically.** Not behind a flag,
  not with a confirmation prompt. Item 3 explains `git filter-repo`; the human runs it.
- **Never claim erasure.** Every removal path must state what remains — git history, forks, forge
  caches, whatever is already indexed. A tool that implies the past is gone is worse than no tool.
- **1 · flue**: turn numbering must match what `recordkit/ollama.py` already uses when rebuilding
  history from `## Human` / `## Assistant` sections. One scheme, not two.
- **2 · beetle**: verify rather than assume that `publish --target pages-branch` (single force-push)
  and `book.lua`'s draft skipping already drop an unpublished record. Both look right; neither has
  been tested for this.
- **4 · moth** is a friendlier front end to Hugo's `ignoreFiles`, which `book.lua` already re-reads
  and matches. Reuse that path — do not build a second exclusion mechanism.
- **3 · cricket**'s most important line is not code: *rotate the credential first.* A history
  rewrite is cleanup; rotation is the fix.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
