---
title: suitcase — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, suitcase, status]
---

# 4 · suitcase — status

Road: **Capture** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | The importer core (`recordkit/importer.py`) | open | — | `diff` of imported vs. created record returns nothing |
| 2 | beetle | Claude Code JSONL transcripts | open | — | real session imported, `hugo` builds warning-free |
| 3 | cricket | ChatGPT + Claude export JSON | open | — | 20+ conversations imported, idempotent on re-run |
| 4 | moth | `llm` SQLite logs | open | — | count matches a `SELECT` on the same file |
| 5 | tadpole | Directory of Markdown | open | — | classification summary per file |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue gates everything else.** Do not write a source parser before the core exists; the whole
  point is that parsers never touch the writing path.
- **Preferred after bikube** — `records import` should arrive inside an installable tool, not a
  cloned repo. Not a hard lock.
- The idempotency rule (a source id in frontmatter) is decided in item 1 and inherited by 2–5. If
  item 1 chose differently, say so here.
- **3 · cricket** needs real export files to confirm shapes. Vendor formats drift; do not write the
  parser from memory or from documentation alone.
- Attachments and images in exports are deferred to [schrank](../schrank/ROADMAP.md). Note them in
  the record, do not invent a storage scheme here.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
