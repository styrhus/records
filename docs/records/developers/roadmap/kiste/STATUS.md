---
title: kiste — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, kiste, status]
---

# 5 · kiste — status

Road: **Reading** · [plan](ROADMAP.md) · [protocol](../README.md)

The rooms are furnished: 3–6 walked 2026-08-31 in one session against real hugo builds of a
four-record fixture in all four pageModes, Fuglekasse byte-identical throughout.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | Postkasse theme skeleton | done | `032c102` | `theme: Postkasse` builds clean; Fuglekasse output unchanged |
| 2 | beetle | Site-wide search | open | — | query over 1 000 records + index size reported |
| 3 | cricket | Backlinks computed at build | done | Claude Opus 5, 2026-08-31 | three records link a fourth by two link shapes; all three listed under it, forge rewrite intact |
| 4 | moth | RSS with signatures stripped | done | Claude Opus 5, 2026-08-31 | feed parses (minidom), 4 items, 0 `— model` lines — Hugo's embedded feed leaked 4 on the same fixture |
| 5 | tadpole | Reading chrome (time, sticky nav, keys) | done | Claude Opus 5, 2026-08-31 | each param off by default, mode-warned, markup absent when off |
| 6 | snail | Attachments render (hooks, video, audio, PDF) | done | Claude Opus 5, 2026-08-31 | image + PDF + video + audio correct in all four pageModes, including the single-mode relative-path bug |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue is done and 2–5 are now unblocked.** `tools/hugo/themes/Postkasse/` ships with an
  assets pipeline (`assets/css`, `assets/js`), the mirrored partial contract
  (`record.html`, `repo-link.html`, `comment-link.html`, `asset-url.html`, `static-url.html`,
  `lang-badge.html`) and its own README. Both halves of the acceptance were re-run during
  consolidation: `theme: Postkasse` builds 14 pages with **no WARN and no ERROR** lines, and the
  default Fuglekasse build is untouched.
- **The skeleton is deliberately only a skeleton.** Its README says so in as many words — search,
  build-time backlinks, RSS and reading chrome are "planned on top of that foundation". Nothing in
  items 2–5 has been started; do not read the theme's existence as a head start on them.
- **1 · flue also unblocked [booth item 4](../booth/ROADMAP.md)** (cards as Open Graph images), which
  was waiting on exactly this. `card.py` already renders at the Open Graph size.
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

## Walked (2026-08-31, items 3–6)

- **3 · cricket**: `backlinks-map.html` builds the graph once (`partialCached`) from
  `.RawContent` — before the forge rewrite, as warned — scanning both markdown links and raw
  `href=` in unsafe HTML, normalising `records/x.md`, `../x.md`, `/x/` and `x/index.md` to one
  node. `params.showBacklinks` defaults true; rendered on record pages and `single` cards
  (`#slug` anchors there), deliberately absent from `single-flowing`, which shows no per-record
  metadata. Not scanned: reference-style definitions and autolinks.
- **4 · moth**: the signature rule moved from `record.html` into `_partials/strip-signatures.html`
  — one regex pair, two callers — still fed by `data/models.json`. The feed carries **full
  content** (a summary of a conversation is its opening exchange out of context), with attachment
  and record links resolved and made absolute. Enabling it stays a knowing site-config edit:
  Hugo ignores root keys in theme configs, so the commented `disableKinds` alternative sits in
  `hugo.yaml`/`one-page.yaml`. Leaving RSS enabled under Fuglekasse publishes Hugo's embedded
  feed, signatures and all.
- **5 · tadpole**: four independent params, all default false — `showReadingTime`, `stickyNav`
  (single-flowing only; invisible without JS), `permalinkButton` (plain anchor without JS, copy
  button with), `keyNav` (`j`/`n`, `k`/`p`). With all off, every build is warning-free and none of
  the markup is emitted.
- **6 · snail**: `render-image.html`/`render-link.html` resolve through `.Page.Resources`, so
  URLs are site-root-absolute and survive the one-page modes — the confirmed 404 is fixed in all
  four. Video/audio get players, PDFs a typed, sized download link; `srcset` at 480/960/1440
  (`responsiveImages`, default true). Raw `<img>`/`<a>` HTML is rewritten **by resource name**
  (mirroring `book.lua`'s intent without its blind regex) in `resolve-attachments.html`. Still
  open, precisely: raw HTML pointing outside the record's own resources, `srcset=`/`poster=`/
  unquoted attributes, `<source>` without `src=`; and a captioned image must stand on its own
  line (goldmark's paragraph wrapping can't be turned off theme-side). Books unchanged and
  untested — pandoc is absent here.
- **A bug found on the way**: `record.html`'s forge rewrite regex matched *any* href containing
  `records/`, which mangled every attachment URL on a site served under such a base path.
  Postkasse's copy (now `_partials/rewrite-record-links.html`, shared with the feed) matches
  relative paths only. **Fuglekasse keeps the loose regex** — it has no render hooks, so the bug
  only bites raw HTML there; if the fix is genuinely universal it should be argued in the open,
  per the border above.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
