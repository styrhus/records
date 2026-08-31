---
title: hundehus — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, hundehus, status]
---

# 7 · hundehus — status

Road: **The watch** · [plan](ROADMAP.md) · [protocol](../README.md)

Half walked, 2026-08-01. The dog is awake; it does not yet bark in an editor, and it has not gone to CI.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records doctor` — checkout diagnostics | done | `72a7396` | run against this repo + a broken scratch checkout |
| 2 | beetle | `records watch` — polling rebuild watcher | done | `72a7396` | one rebuild per save; survives a broken build |
| 3 | cricket | The bark — notifications + editor status | open | — | one notification per failure; no-op without `notify-send` |
| 4 | moth | Doctor as an optional CI pre-flight | done | Claude Sonnet 5, 2026-08-31 | misconfigured scratch checkout fails the step (3 errors, exit 1) under `-eo pipefail`; passes with python3 masked (skip note, exit 0); this repo: 7 ok · 1 warning · 0 errors |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **3 · cricket is half-built already, and the built half is not the hard half.** `watch.py` carries
  `notify()` — freedesktop `notify-send` when present, a silent no-op when not — and a `--notify
  {fail,all,none}` flag defaulting to `fail`, which satisfies the desktop side of the acceptance.
  What is missing is the **editor surfacing** the item actually names: watcher status in the VSCode
  sidebar (the dim `status` class exists) and a Neovim status function. Whoever takes this touches
  `tools/others/vscode/src/` and `neovim/lua/records/init.lua`, not `watch.py`.
- **4 · moth walked 2026-08-31.** All three shims run `records doctor` in-place
  (`PYTHONPATH=tools/others/python python3 -m recordkit doctor`, no install step) before the
  build, guarded by `command -v python3` plus a directory check so a fork without Python
  skip-notes and passes — the pandoc pattern. The step fails on errors only: doctor's own exit
  code is already warnings-tolerant (`ok = errors == 0`), so a fork whose only finding is the
  derived-on-push `baseURL` warning still deploys. Plain text output, not `--json` — the readable
  fault-plus-remedy rendering is the point of a CI log. The three real CI backends were not
  exercised live (that is [badstu 2](../badstu/ROADMAP.md)'s toggle); verification is each step
  body reproduced under matching `set -eo pipefail` semantics.
- **The defining border held.** Neither command commits, pushes or publishes — not behind a flag,
  not behind a config key. Polling, not inotify; stdlib only.
- **Parallel-session collisions still stand:** **3 · cricket** shares
  `neovim/lua/records/init.lua` with [postkasse 1](../postkasse/ROADMAP.md); **4 · moth** shares the
  CI shims with [badstu 2](../badstu/ROADMAP.md).

## What landed

`recordkit/doctor.py` (42 tests) and `recordkit/watch.py` (20 tests), both now registered in
`cli.py`. They are the CLI's two exceptions to JSON-on-stdout: each owns its flags and its
human-readable rendering, so `records doctor` and `records watch` hand straight through to the
module's own `main()`, `--json` included.

Both halves of item 1's acceptance were re-run during consolidation. Against this repo: `6 ok · 1
warning · 0 errors`, the warning being the uncommented `baseURL` that CI derives on push. Against a
deliberately broken scratch checkout — bad `contentDir`, no URL rung, `publishTarget: rsync` with no
`publishDest`, an unparseable `date:` — `2 ok · 2 warnings · 3 errors`, each fault named with its
remedy. That is the item working.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
