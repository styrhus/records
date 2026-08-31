---
title: booth — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, booth, status]
---

# 9 · booth — status

Road: **The booth** · [plan](ROADMAP.md) · [protocol](../README.md)

Three of four walked, 2026-08-01. Item 4 was unblocked the same day by kiste 1 landing.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records card` — a turn as SVG | done | `a5c6e82` | card opened in a browser, palette matches the site |
| 2 | beetle | `records booth` — stdlib curses composer | done | `a3dd0ce` | record byte-identical to `records new` + `append` |
| 3 | cricket | The booth talks back (Ollama) | done | `a3dd0ce` | two-sided session + user-only fallback with Ollama stopped |
| 4 | moth | Cards as Open Graph images (Postkasse) | done | Claude Sonnet 5, 2026-08-31 | scratch Postkasse build: `ogCards` on → per-record `og:image` at `/cards/<slug>.svg` (1200×630, site palette); off → site-level fallback; python3 masked → clean skip; Fuglekasse → no-op |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **4 · moth is no longer blocked.** It waited on [kiste item 1](../kiste/ROADMAP.md), which landed
  in `032c102` — the Postkasse theme exists, so the Open Graph work has a house to live in. The
  border stands: this belongs to Postkasse, not Fuglekasse. `card.py` already renders at 1200×630,
  the Open Graph size, precisely so this item can reuse it unchanged.
- **4 · moth walked 2026-08-31.** `bin/build.sh` gains a step gated on `params.ogCards` *and*
  `theme: Postkasse` (Fuglekasse no-ops — the border held; the one-page modes no-op too, since no
  per-record page exists to carry the tag) that runs `records card` unchanged per record into
  `public/cards/`, skip-noting when python3/recordkit is absent, pandoc-style. Postkasse's
  `head-meta.html` emits the per-record `og:image` by `ContentBaseName` — the same basename the
  card default and the `:contentbasename` permalink already share. Two honest caveats: SVG
  og:images render in Slack/Discord but not on many crawlers (a rasterizer would be a dependency,
  and PNG conversion is explicitly not `card.py`'s job); and the tag is emitted whenever the
  param is set, even if generation was skipped — the same precedent as the Get PDF link, which
  trusts `params.pdf` without checking pandoc produced the file. The acceptance's live
  link-preview check waits on a published site.
- **The wiring the road left behind is done.** All three landed commands were written but never
  registered in `cli.py` (the parallel-session deferral rule). `records card` and `records booth` are
  now real subcommands — verified, not assumed.
- **3 · cricket** reused `ollama.reply` directly, as required — no second Ollama path was written.
  `Session.submit` appends the human's words first and falls back to a user-only turn when the model
  is unreachable ("a dead model never costs a sentence"), covered by
  `test_a_dead_model_never_costs_a_sentence` and `test_two_sided_session_over_real_http_then_fallback`.
- Streaming in the booth is still nicer if [postkasse item 2](../postkasse/ROADMAP.md) lands; the
  booth ships with a busy state instead, which the road allowed.
- **1 · flue** stayed SVG-only, as the border required — no PNG conversion, no font library, a
  monospace advance assumption for text metrics.
- **2 · beetle**: `Buffer` and `Session` hold the logic and `curses` only draws, so 17 of the road's
  tests run with no terminal at all.
- The booth works with nothing installed but Python. No model, no config, no plugin.

## What landed

`recordkit/card.py` (23 tests) and `recordkit/booth.py` (17 tests). Cards read the site's own
palette out of `hugo.yaml`, so a fork's colours carry into its cards. Records written in the booth go
through `create.py` and `writer.py` like every other path, which is what makes the byte-identity
claim true by construction rather than by comparison.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
