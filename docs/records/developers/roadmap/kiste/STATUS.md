---
title: kiste — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, kiste, status]
---

# 5 · kiste — status

Road: **Reading** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | Postkasse theme skeleton | open | — | `theme: Postkasse` builds clean; Fuglekasse output unchanged |
| 2 | beetle | Site-wide search | open | — | query over 1 000 records + index size reported |
| 3 | cricket | Backlinks computed at build | open | — | two records link a third, both listed under it |
| 4 | moth | RSS with signatures stripped | open | — | validated feed, no `— model` lines |
| 5 | tadpole | Reading chrome (time, sticky nav, keys) | open | — | each feature switchable off independently |
| 6 | snail | Attachments render (hooks, video, audio, PDF) | open | — | image + PDF + video correct in all four pageModes |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue gates 2–5.** They all live inside the new theme.
- **Preferred after suitcase** — search over eleven records is a demo, search over an imported
  archive is the feature.
- **2 · beetle** should reuse badstu item 6's synthetic corpus rather than generating its own.
- **3 · cricket** must run on source text, *before* `record.html` rewrites relative `records/` links
  to forge raw URLs. Get this wrong and the graph is silently empty.
- **6 · snail pairs with [schrank item 3](../schrank/ROADMAP.md)** — schrank decides where
  attachments live (leaf page bundles, already verified), kiste makes them render. It carries a
  confirmed bug: in `single`/`single-flowing` every record renders on `/`, so a relative
  `image.png` 404s. Render hooks fix all four render spots with one file. Raw `<img>` from
  `unsafe: true` content bypasses hooks — mirror `book.lua`'s regex workaround or document the gap.
- The one border that will be tested repeatedly on this road: **Fuglekasse does not grow.** Every
  feature here belongs to Postkasse — including the render hook that fixes the attachment path bug.
  If something seems genuinely universal, argue it separately — do not slip it in.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
