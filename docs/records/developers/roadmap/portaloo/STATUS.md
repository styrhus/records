---
title: portaloo — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, portaloo, status]
---

# 10 · portaloo — status

Road: **Carry it** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked. New road, defined 2026-08-01.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records.pyz` — stdlib zipapp | open | — | runs on a machine with only Python |
| 2 | beetle | `records pack` — one-file offline site | open | — | opens from `file://` with networking disabled |
| 3 | cricket | Books travel too (`--with-books`) | open | — | one offline directory: site + PDF + EPUB + index |
| 4 | moth | `docs/offline.md` — the USB story | open | — | followed on a borrowed machine |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue is nearly free** — zero dependencies is exactly what makes `zipapp` trivial. It is the
  payoff of the engine's defining border, and the docs should say so.
- Version must agree with [bikube item 1](../bikube/ROADMAP.md) and `CURRENT`. One version story,
  not two. If bikube has not landed, derive from `CURRENT` and note it here.
- **2 · beetle** must post-process `public/`, never build a site itself. One build path.
- Test the pack with the **network actually disabled**, not just by opening the file. A missed
  external reference is invisible on a connected machine and fatal on a train.
- Expect `--no-images` to be the common case. Data URIs are ~33 % larger than the bytes they carry.
- **3 · cricket** should reuse [schrank's](../schrank/ROADMAP.md) manifest format if that road has
  landed, rather than inventing a second one.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
