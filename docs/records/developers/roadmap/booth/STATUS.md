---
title: booth — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, booth, status]
---

# 9 · booth — status

Road: **The booth** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked. New road, defined 2026-08-01.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records card` — a turn as SVG | open | — | card opened in a browser, palette matches the site |
| 2 | beetle | `records booth` — stdlib curses composer | open | — | record byte-identical to `records new` + `append` |
| 3 | cricket | The booth talks back (Ollama) | open | — | two-sided session + user-only fallback with Ollama stopped |
| 4 | moth | Cards as Open Graph images (Postkasse) | blocked | — | link-preview tool shows the record's card |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **4 · moth is blocked on [kiste item 1](../kiste/ROADMAP.md)** — Open Graph images are theme work
  and Fuglekasse does not grow. It waits for the Postkasse theme.
- **3 · cricket** reuses `ollama.reply` directly. Do not write a second Ollama path; the sidebar's
  code is the reference implementation.
- Streaming in the booth is nicer if [postkasse item 2](../postkasse/ROADMAP.md) has landed, but is
  not a blocker — a spinner is acceptable.
- **1 · flue**: SVG only. PNG conversion would mean a dependency, and anyone can convert an SVG.
  Text metrics without a font library are approximate; pick a monospace assumption and accept the
  imprecision rather than reaching for a library.
- **2 · beetle**: keep the logic separable from `curses` so it can be tested without a terminal.
- The booth must work with nothing installed but Python. No model, no config, no plugin.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
