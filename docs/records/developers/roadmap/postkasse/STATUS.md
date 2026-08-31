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
| 1 | flue | Ollama reaches Neovim | wip | Claude Sonnet 5, 2026-08-31 | code + fallback done, mirroring the VSCode session semantics; the live Neovim + Ollama run is pending — neither exists on the walking box |
| 2 | beetle | Replies learn to stream | wip | Claude Sonnet 5, 2026-08-31 | `pytest tests/test_ollama.py` → 72 passed, streamed write byte-identical to the non-streaming one; plugin streaming is opt-in (`stream` / `records.stream`) and visually unverified |
| 3 | cricket | Voice skills become presets | wip | Claude Sonnet 5, 2026-08-31 | preset loading, composition and fallback proven by tests (`pytest tests/test_ollama.py` green); the live acceptance run waits on a reachable Ollama |
| 4 | moth | `/stick` checkout-aware + `test_stick.py` | done | Claude Sonnet 5, 2026-08-31 | `cd tools/others/python && python -m pytest` → 570 passed |
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
- **4 · moth — half its ground is already taken.** [schrank 3](../schrank/ROADMAP.md) landed, and
  with it `find_record` became bundle-aware and gained the `tests/test_stick.py` this item was going
  to create (7 tests, covering both record shapes and the attach→stick regression). What remains for
  this item is the part schrank did not touch: **checkout-awareness**, making `/stick` resolve its
  records dir the way `/record`, `/all`, `/me` and `/cpd` already do instead of assuming `$PWD`.
  Extend the existing function and test file; do not replace them.
- **Parallel-session collisions:** **1 · flue** shares `neovim/lua/records/init.lua` with
  [hundehus 3](../hundehus/ROADMAP.md), which is still open — coordinate before touching it.
- **3 · cricket, walked 2026-08-31:** `/pirate`, `/poet` and `/bff` became
  `recordkit/presets/*.txt` — each SKILL.md was already a static persona with no tool use, so a
  fixed system prompt is lossless, and the skills now point at the preset files instead of
  restating them. **`/eq` stays AI-only**: its cap-your-reply-to-my-token-length rule is a live
  per-turn self-measurement, not a tone — a local model that silently fails it has no way to be
  caught by the engine. `/werden`'s verse also stays AI-only: it must name the specific old→new
  cycle at the moment of turning, which is runtime state, not fixed prompt text. The preset rides
  the existing system-message slot ahead of `--context-*`, is never written to the record, and the
  row stays `wip` only for the live Ollama run.
- **1 · flue + 2 · beetle, walked 2026-08-31 (code side):** Neovim's `/record` now asks
  `records ollama-reply` asynchronously (`jobstart`, 0.9 floor — not `vim.system`), captures
  `{endpoint, model}` once per recording like the VSCode sidebar, and on any failure appends the
  human's words through the mechanical path with a warning — never lost, relying on the engine's
  tested guarantee that a failed generation touches nothing. Idle lines chat ephemerally via
  `ollama-chat`. Streaming: `ollama.py` gained `reply_stream`/`ephemeral_reply_stream` (final
  joined text asserted byte-identical to the non-streaming write; mid-stream faults append
  nothing, including a real no-mock connection-refused case), surfaced as `--stream` NDJSON on
  both CLI commands; both plugins render tokens behind an **off-by-default** `stream` setting.
  Both rows stay `wip` for the live half only: no Neovim, no VSCode, no Ollama on the walking box.
- **4 · moth, walked 2026-08-31:** the surprise was that `cli.py`'s `stick` handler has resolved
  the records dir via `config.resolve_records_dir` since 2026-07-21 — the real `$PWD`-scoping
  lived in the `/stick` skill's hardcoded `find records …`, now replaced with the same discovery
  block its siblings carry. `stick.py` gained `find_record_in_checkout` (engine-level, testable);
  `test_stick.py` extended 7 → 11 tests, schrank 3's work intact.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
