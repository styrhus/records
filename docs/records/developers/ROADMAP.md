---
title: Roadmap
date: 2026-07-29T13:47:55+01:00
tags: [developers, roadmap]
---
<!-- werden: 0.2.2 postkasse-beetle -->

# Roadmap

## The question

*"Which road lies ahead of us to make **blyant records** at least as good as these other tools, and simply better?"* — asked by a dreamer, 2026-07-29, in front of this very file while it was still empty.

The answer has a shape: five roads, walked in order, each one a named werden step.

## Where we stand

`0.2.1 postkasse-flue`, the provider-agnostic release. One build path (`bin/build.sh`) behind every provider; forks publish with zero edits. An AI-free engine (`recordkit`, 102 tests) drives the mechanical commands from a VSCode sidebar, a Neovim split, or plain shell; Ollama brings the AI back, locally, when wanted.

And the sentence that sets our course: everyone's conversations are locked away in other people's apps. Nobody publishes them well. That is the whole gap we exist in.

## Seams — postkasse (0.2.x, now)

Finish what's begun before carrying it further. Each seam is one animal.

Ollama reaches Neovim — the CLI already does the HTTP, `handle_slash` just has to ask. Replies learn to stream, stdlib chunked reads in `recordkit/ollama.py`, surfaced in both plugins. The voice skills become system-prompt presets — deterministic prompt files, no model in the engine. `/stick` becomes checkout-aware like its siblings, and gets the first `test_stick.py`. And the CI stops fibbing politely: pypdf and rsync/openssh go into the hugo-runner image so the booklet stops being skipped, and the live-untested GitHub/GitLab shims get their smoke-repo rehearsal.

## Reach — bikube (0.3.x)

The hive the engine swarms out from. Shipping with known-unfinished seams would export the debt; that is why reach waits for seams.

`pipx install recordkit`, version derived from `CURRENT` so PyPI speaks werden. The VSCode extension goes to Open VSX first — Codeberg-first is a habit, not an accident — then the Marketplace; publisher `tb4` is already set. `records.nvim` becomes installable the lazy.nvim way. Emacs is named because the README already said it: the CLI is editor-agnostic, the pattern is straightforward. An animal, not a promise.

## Capture — suitcase (0.4.x)

Pack your conversations and carry them home. This is the road nobody else walks.

A new `recordkit/importer.py` behind `records import`, emitting through the existing `frontmatter.py` and `writer.py` so an imported record byte-matches a created one. Then one source per animal: Claude Code session transcripts (JSONL), ChatGPT export JSON, Claude export JSON, `llm` SQLite logs. Parsers stay stdlib — `json`, `sqlite3` — deterministic, tested beside the 102.

Packaged first, imported second: `records import` arrives inside an installable tool, not a cloned repo.

## Reading — kiste (0.5.x): theme Postkasse

A chest of records, opened for reading. Fuglekasse stays as it is — minimal is a feature with a fence, and the fence holds. Growth gets its own house: a second theme, **Postkasse**, wearing the name of the cycle that dreamed it.

Grown from Fuglekasse's flat shape, chosen by the one-line `theme:` key in `hugo.yaml`, `bin/build.sh` untouched. Inside Postkasse, and only there: site-wide search (JavaScript is allowed past this fence), backlinks between records computed at build time, and RSS done right — a feed template that strips the signature lines, flipping `disableKinds` knowingly in site config.

Reading follows capture on purpose: the richer site should launch with richer content.

## Android — akvarium (0.6.x)

Writing through the glass. A ladder, named but not solved.

The first rung can land any day as a docs minor: a record is just a Markdown file committed to a repo, so any phone git client or the Forgejo web editor already works — it only needs writing down. The second rung is a small PWA committing through the forge APIs. The third rung is *maybe* voice capture — and `voiceRecorded: true` marks, it never transcribes. Maybe means maybe.

## The order of things

Near is the rest of postkasse, minors only. Mid is bikube and suitcase. Far is kiste and akvarium.

| Road | Structure | First animals |
|---|---|---|
| Seams | postkasse (0.2.x, now) | beetle, cricket, moth, tadpole, snail |
| Reach | bikube (0.3.x) | flue: PyPI · beetle: Open VSX/Marketplace · cricket: records.nvim |
| Capture | suitcase (0.4.x) | flue: importer · beetle: Claude Code · cricket: ChatGPT · moth: llm logs |
| Reading | kiste (0.5.x) | flue: Postkasse skeleton · beetle: search · cricket: backlinks · moth: RSS |
| Android | akvarium (0.6.x) | flue: the phone doc · later rungs unnumbered |
| — | hundehus, schrank | left deliberately blank |

This table is desire, not contract. Names are claimed only when `/werden` actually turns; the epoch stays human-owned, hand-edited in `CURRENT`.

## What we will not build

No Windows — the build path is bash and stays bash. No voice-to-text engine. No federation, no comments platform, no accounts, no hosted service — a record is a file in your repo and the site is static; that is the product. No second build path. No growth in Fuglekasse. No dependencies in the engine — stdlib parsers, model-optional, mechanical output byte-matching AI output. No dates — the werden names are the schedule, and the mountain is climbed at walking pace. And no AI-drafted upstream contributions, ever — see [never-ever-ever-ai-slop.md](never-ever-ever-ai-slop.md), this file's older sibling.

Borders are a good thing.

## One closing line

We live in postkasse now; when the records are finally read the way they deserve, it will be a theme wearing this cycle's name that opens the lid.
