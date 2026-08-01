---
title: postkasse — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, postkasse, status]
---

# 2 · postkasse — status

Road: **Seams** · [plan](ROADMAP.md) · [protocol](../README.md)

Partly walked — the cycle passed through `postkasse-flue` (the provider-agnostic release, tagged)
and `postkasse-beetle` before turning to badstu. The items below are what remained open.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | Ollama reaches Neovim | open | — | live `/record` turn in Neovim + fallback with Ollama stopped |
| 2 | beetle | Replies learn to stream | open | — | `python -m pytest tests/test_ollama.py` + visible streaming in both plugins |
| 3 | cricket | Voice skills become presets | open | — | `records ollama-chat --preset pirate --human "hello"` |
| 4 | moth | `/stick` checkout-aware + `test_stick.py` | open | — | `cd tools/others/python && python -m pytest` |
| 5 | tadpole | Both plugins walked against a real site | open | — | walkthrough log, 11 commands × 2 plugins |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- Do **1 · flue** before **2 · beetle** — streaming is cheaper to add to two existing call sites
  than to one existing and one missing.
- **3 · cricket** must say explicitly which voices stay AI-only and why; a voice that is more than a
  system prompt does not become a file.
- **5 · tadpole** clears the stale "Next Steps" list in `tools/others/README.md`. Deleting those
  lines is part of the item.
- The animal names here are already partly spent: `postkasse-flue` and `postkasse-beetle` have
  turned. Item numbering follows the pool for planning; it does not re-issue names.
- **Parallel-session collisions:** **4 · moth** and [schrank 3](../schrank/ROADMAP.md) both rewrite
  `recordkit/stick.py` — checkout-awareness and bundle-awareness in the same function. Do not run
  them concurrently. **1 · flue** shares `neovim/lua/records/init.lua` with
  [hundehus 3](../hundehus/ROADMAP.md).

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
