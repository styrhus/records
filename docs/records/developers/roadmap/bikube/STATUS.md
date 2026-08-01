---
title: bikube — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, bikube, status]
---

# 3 · bikube — status

Road: **Reach** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `pipx install recordkit`, version from `CURRENT` | open | — | clean-container `pipx install` + `records new` |
| 2 | beetle | Open VSX, then Marketplace | open | — | install by name in clean VSCodium |
| 3 | cricket | `records.nvim` installable (lazy.nvim) | open | — | lazy spec in clean Neovim, `:Records` opens |
| 4 | moth | Emacs plugin | open | — | record created from Emacs |
| 5 | tadpole | One install story: `docs/install.md` | open | — | zero-to-record by following one page |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **Preferred after postkasse.** Publishing with open seams exports the debt. Not a hard lock — the
  human may say go early.
- **1 · flue** is the gate for 2, 3 and 4: every plugin's install instructions end at "and you need
  the CLI". Do it first.
- Open VSX **before** the Marketplace. Codeberg-first is deliberate.
- Four stale `.vsix` builds sit in `tools/others/vscode/`. Item 2 decides: keep as artefacts or
  gitignore. Do not leave it ambiguous.
- **4 · moth** may ship mechanical-only. Ollama in Emacs is optional and can wait for its own animal.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
