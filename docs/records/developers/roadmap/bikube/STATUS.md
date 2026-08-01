---
title: bikube — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, bikube, status]
---

# 3 · bikube — status

Road: **Reach** · [plan](ROADMAP.md) · [protocol](../README.md)

Walked 2026-08-01, except the two uploads.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `pipx install recordkit`, version from `CURRENT` | wip | opus, 2026-08-01 | clean-container `pipx install` + `records new` |
| 2 | beetle | Open VSX, then Marketplace | wip | opus, 2026-08-01 | install by name in clean VSCodium |
| 3 | cricket | `records.nvim` installable (lazy.nvim) | done | opus, 2026-08-01 | lazy spec in clean Neovim, `:Records` opens |
| 4 | moth | Emacs plugin | done | opus, 2026-08-01 | record created from Emacs |
| 5 | tadpole | One install story: `docs/install.md` | done | opus, 2026-08-01 | zero-to-record by following one page |

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

## What actually happened

**1 · flue — `wip`, and only because of the upload.** The packaging is finished and evidenced:
`pyproject.toml` takes its version from `recordkit.__version__`, `/werden` stamps that from `CURRENT`
(both the bash script and the recordkit mirror), and `tests/test_version.py` fails if the two ever
disagree. `records --version` exists. Wheel and sdist build clean — `recordkit/` and nothing from
`tools/`. `pipx install` of the wheel in a `python:3.12-slim` container, then a real `records config`,
`records new "#test Container check"` and `records append` against a fixture checkout, all correct.
The acceptance check names `pipx install recordkit`, which needs the human's PyPI token. The
runbook is in `tools/others/README.md` § Releasing. `recordkit` was free on PyPI as of 2026-08-01.

**The version story got a rule.** Roads are open, not queued, so the structure does not climb
monotonically — `badstu` (12) → `bikube` (3) derives `0.3.1`, lower than `0.12.1`, and PyPI would
keep serving the older release. **When the structure steps down the pool, the human bumps the epoch
in `CURRENT` before releasing.** Written up in `tools/others/naming/README.md`.

**2 · beetle — `wip`, same reason.** `.vscodeignore` did not exclude `*.vsix`, so the four stale
builds in the folder would have shipped *inside* the next package; fixed, and the question is
settled: `.vsix` files are build artefacts — gitignored (they already were, twice), never committed,
never packaged, deleted locally. `package.json` gained keywords, homepage, bugs and a gallery
banner at 0.6.0, with the missing 0.5.0 CHANGELOG entry restored. The README now stands alone on a
registry page — a reader arriving from Open VSX has no repo context — and says
`pipx install recordkit`, as does the extension's own missing-CLI panel. `vsce ls` lists 12 files
(package.json, README, LICENSE, CHANGELOG, four `out/*.js`, two media assets), 21.6 KB. Namespace
registration and publish need the human's Open VSX and Marketplace tokens.

**3 · cricket — `done`, and it needed more than layout.** The plugin could not open at all:
`add_line` and `on_submit` were declared `local` *after* `M.open` referenced them, so those
references resolved to nil globals. `run_cli` concatenated argv into a shell string, which made
`/record #linux Title` a shell comment. `records myname` takes a positional name, so `/myname` had
never worked. `/mucke` stamped the chat buffer's own path. All fixed, plus `plugin/records.lua`
(`:Records` without `setup()`) and `doc/records.txt` (`:help records`). Verified with a real
lazy.nvim `{ dir = …, cmd = "Records" }` spec in a clean Neovim 0.10.4 container: cold start,
`:Records`, record written to `records/test/via-lazy.nvim.md`.

Distribution shape, decided: **a subdirectory spec, not a mirror repo.** A mirror needs syncing and
nothing here syncs itself. The layout is already what a plugin repo needs, so a mirror stays cheap
to add if the friction ever proves real.

**4 · moth — `done`, mechanical only.** `tools/others/emacs/records.el`, one file, no dependencies
beyond Emacs 27.1, `call-process` to the CLI, the same eleven-command slash registry as the other
two. Verified in Emacs 30.1: byte-compiles with no warnings; `/config`, `/all #test From Emacs`, a
plain appended line and `/esc` all correct against a fixture checkout. `records-ollama-endpoint` is
declared and reserved — Ollama in Emacs can wait for its own animal.

**5 · tadpole — `done`.** `docs/install.md` is the one page: CLI, then VS Code / Neovim / Emacs /
Claude Code, then the shared command table, then **one** section saying Ollama is optional. The three
plugin READMEs shrank to what-this-does plus a link; `tools/others/README.md` § Quick Start does the
same and gained the release runbooks; the root README links the page. The only surviving
`pipx install ./tools/others/python` is the deliberate from-a-clone fallback on that page.

**Left for the human:** the two uploads, and `/werden` — agents never turn the cycle.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
