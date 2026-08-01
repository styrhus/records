---
title: hundehus — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, hundehus, status]
---

# 7 · hundehus — status

Road: **The watch** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked. New road, defined 2026-08-01.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records doctor` — checkout diagnostics | open | — | run against this repo + a broken scratch checkout |
| 2 | beetle | `records watch` — polling rebuild watcher | open | — | one rebuild per save; survives a broken build |
| 3 | cricket | The bark — notifications + editor status | open | — | one notification per failure; no-op without `notify-send` |
| 4 | moth | Doctor as an optional CI pre-flight | open | — | misconfigured fork fails with a named fault; passes with recordkit absent |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue is the highest-value item on this road** and probably the highest-value unwritten
  command in the project. It can be picked up cold, today, with no dependencies.
- Do 1 before 2 — the watcher's value is mostly in surfacing what the doctor already knows.
- **The defining border:** nothing here commits, pushes or publishes. Not behind a flag, not behind
  a config key. If an implementation seems to want that, it has misread the road.
- Polling, not inotify. Stdlib only — a second of latency is fine, a dependency is not.
- `recordkit/mucke.py` is the existing precedent for optional desktop integration (D-Bus, degrades
  silently). Follow its shape in item 3.
- **4 · moth** must keep the shims working with no Python present, the same way `bin/build.sh`
  skip-notes a missing pandoc.
- **Parallel-session collisions:** **3 · cricket** shares `neovim/lua/records/init.lua` with
  [postkasse 1](../postkasse/ROADMAP.md); **4 · moth** shares the CI shims with
  [badstu 2](../badstu/ROADMAP.md).

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
