---
title: Roadmap
date: 2026-07-29T13:47:55+01:00
tags: [developers, roadmap]
---
<!-- werden: 0.12.3 badstu-cricket -->

# Roadmap

## The question

*"Which road lies ahead of us to make **blyant records** at least as good as these other tools, and simply better?"* — asked by a dreamer, 2026-07-29, in front of this very file while it was still empty.

The answer has a shape: eleven roads, from the mailbox to the sauna, each one a named werden step.

## Where we stand

`CURRENT` reads **`0.12.3 badstu-cricket`** — the road under our feet.

Behind it the roads are no longer unwalked. They are still not a queue: the werden major is a
position in the name pool, not a percentage of anything, and a road is claimed by whoever arrives
with time for it. Walk them in the order that suits the week.

Where each one stands, as of 2026-08-31 — the day the agent-workable remainder was walked in one
parallel-session sweep:

| Road | Walked | Left |
|------|--------|------|
| 2 · postkasse | 1 of 5, 3 more code-complete | the live halves — a real Neovim with a real Ollama for items 1–3 — and the walkthrough |
| 3 · bikube | 3 of 5 | two uploads, both needing the human's tokens (PyPI, Open VSX) |
| 4 · suitcase | 4 of 5 | ChatGPT + Claude export JSON, blocked for want of a real export file |
| 5 · kiste | **6 of 6** | — |
| 6 · akvarium | 1 of 3 | two rungs waiting on a real phone |
| 7 · hundehus | 3 of 4 | the bark's live run in a real editor |
| 8 · schrank | **6 of 6** | — |
| 9 · booth | **4 of 4** | — |
| 10 · portaloo | 2 of 4 | books travelling (gated on badstu 3), and the USB story walked on a borrowed machine |
| 11 · utedo | 4 of 5 | the oops procedure's review by someone who has done a history rewrite |
| 12 · badstu | 4 of 6 | CI truth (a toggle only the human holds), the runner image, and item 5's browser half |

What is already built: one build path (`bin/build.sh`) behind every provider, forks publishing with
zero edits, an AI-free engine (`recordkit` 0.12.3, 595 tests) driving the mechanical commands from a
VSCode sidebar, a Neovim split, an Emacs buffer, or plain shell — and Ollama bringing the AI back,
locally, when wanted. Twenty-seven CLI commands now, fourteen of them from the roads above.

And the sentence that sets the course: everyone's conversations are locked away in other people's
apps, and nobody publishes them well. That is the whole gap we exist in.

## How to walk one

Each road has a folder. The folder holds the elaborate plan and a handoff table where items are
claimed one at a time. The protocol is one page: [how a road is walked](roadmap/README.md).

Several sessions can run at once — one worktree each, items assigned up front, and the shared files
left alone until the end. That has its own rules, on the same page:
[running several sessions at once](roadmap/README.md#running-several-sessions-at-once).

Agents pick up items. Humans turn the cycle.

---

## 12 · badstu — Steam <small>(now)</small>

The sauna: heat, sweat, cold water, and the room where people talk without titles. Two things
happen here at once. The project gets **help** — this roadmap, the folders below it, a handoff
protocol so many hands can work without collision. And the project gets **honest** — the untested
provider shims actually exercised, the silently-skipped booklet unskipped, every claim in every
README checked against the code that is supposed to back it.

What survives the heat is what the project really is.

→ [plan](roadmap/badstu/ROADMAP.md) · [status](roadmap/badstu/STATUS.md)

## 2 · postkasse — Seams

Finish what's begun before carrying it further. Ollama reaches Neovim — the CLI already does the
HTTP, `handle_slash` just has to ask. Replies learn to stream. The voice skills become system-prompt
presets, deterministic files, no model in the engine. `/stick` becomes checkout-aware like its
siblings, and gets the first `test_stick.py`.

→ [plan](roadmap/postkasse/ROADMAP.md) · [status](roadmap/postkasse/STATUS.md)

## 3 · bikube — Reach

The hive the engine swarms out from. `pipx install recordkit`, version derived from `CURRENT` so
PyPI speaks werden. The VSCode extension to Open VSX first — Codeberg-first is a habit, not an
accident — then the Marketplace. `records.nvim` installable the lazy.nvim way. Emacs because the
CLI is editor-agnostic and the pattern is straightforward.

→ [plan](roadmap/bikube/ROADMAP.md) · [status](roadmap/bikube/STATUS.md)

## 4 · suitcase — Capture

Pack your conversations and carry them home. This is the road nobody else walks. A
`recordkit/importer.py` behind `records import`, emitting through the existing `frontmatter.py` and
`writer.py` so an imported record byte-matches a created one. Then one source per animal: Claude
Code session transcripts, ChatGPT export JSON, Claude export JSON, `llm` SQLite logs. Parsers stay
stdlib — `json`, `sqlite3` — deterministic, tested beside the rest.

→ [plan](roadmap/suitcase/ROADMAP.md) · [status](roadmap/suitcase/STATUS.md)

## 5 · kiste — Reading

A chest of records, opened for reading. Fuglekasse stays as it is — minimal is a feature with a
fence, and the fence holds. Growth gets its own house: a second theme, **Postkasse**, wearing the
name of the cycle that dreamed it. Inside it, and only there: site-wide search, backlinks computed
at build time, RSS done right — a feed that strips the signature lines — and attachments that
render as what they are: photos as figures, video as video, a PDF as something you can take.

→ [plan](roadmap/kiste/ROADMAP.md) · [status](roadmap/kiste/STATUS.md)

## 6 · akvarium — Android

Writing through the glass. A ladder, named but not solved. The first rung is a docs minor: a record
is a Markdown file committed to a repo, so any phone git client or the Forgejo web editor already
works — it only needs writing down. The second rung is a small PWA committing through the forge
APIs. The third is *maybe* voice capture — and `voiceRecorded: true` marks, it never transcribes.
Maybe means maybe.

→ [plan](roadmap/akvarium/ROADMAP.md) · [status](roadmap/akvarium/STATUS.md)

## 7 · hundehus — The watch

The doghouse is where the loyal thing sleeps, outside, watching the door. `records watch` is a small
stdlib process that notices a record change, rebuilds, and barks — never commits, never publishes,
never decides. Beside it `records doctor` sniffs a checkout and says what is wrong: missing
`baseURL`, absent pandoc, a `deployCommand` pointing nowhere, a records dir the config can't find.

A dog is useful because it has no opinions.

→ [plan](roadmap/hundehus/ROADMAP.md) · [status](roadmap/hundehus/STATUS.md)

## 8 · schrank — Preservation

A cupboard is where things wait without spoiling. Everything here assumes the tools are gone:
`records archive` writes one self-contained bundle — records, images, config, a manifest with
checksums — using nothing but `zipfile` and `hashlib`. `records verify` reads it back and reports
rot. And the plain-text emergency export that outlives Hugo, pandoc, this repo, and us.

Attachments get a home here too, and it isn't git-annex: a record that carries files becomes a Hugo
leaf page bundle, `index.md` with the photo, the video, the PDF sitting beside it, published at the
same URL the flat record had. `records attach` does the move. Everything you attached is a file in
your repo, next to the words it belongs to.

Publishing is about reach. This road is about the other thing.

→ [plan](roadmap/schrank/ROADMAP.md) · [status](roadmap/schrank/STATUS.md)

## 9 · booth — The booth

Two booths, one road. The **recording booth**: `records booth`, a distraction-free composing screen
in stdlib `curses` — one box, one conversation, no model required, the whole ceremony of writing a
record reduced to a room with a door. The **photo booth**: `records card`, turning a single turn
into a shareable SVG quote card drawn from the site's own palette, no dependencies, no service, just
a file you can post anywhere.

A booth is small on purpose. You step in, something is captured, you step out.

→ [plan](roadmap/booth/ROADMAP.md) · [status](roadmap/booth/STATUS.md)

## 10 · portaloo — Carry it

The whole facility, carried. Two deliverables that both mean *needs nothing installed*:
`records.pyz`, the engine as a single-file stdlib `zipapp` that runs on any Python; and
`records pack`, the entire site collapsed into one self-contained HTML file — CSS inlined, images
data-URI'd — that opens from `file://`, works on a USB stick, and survives an airplane.

Not glamorous. Extremely useful. Both true of a portaloo.

→ [plan](roadmap/portaloo/ROADMAP.md) · [status](roadmap/portaloo/STATUS.md)

## 11 · utedo — What must leave

The outhouse: the smallest useful building, standing apart, dealing with what has to go. Every
publishing tool pretends this road doesn't exist. `records redact` rewrites a turn in place and
leaves a visible seam rather than a lie. `records unpublish` pulls a record out of the site, the
pages branch and the books, leaving a tombstone. A secret-scrub path for the day a key lands in a
transcript, with honest guidance about what git history does and doesn't forget.

Publishing without a way back is a trap. This is the way back.

→ [plan](roadmap/utedo/ROADMAP.md) · [status](roadmap/utedo/STATUS.md)

---

## The eleven, at a glance

| # | Structure | Road | Model | First items |
|---|---|---|---|---|
| 2 | postkasse | Seams | sonnet | flue: Ollama in Neovim · beetle: streaming · cricket: voice presets · moth: `/stick` |
| 3 | bikube | Reach | sonnet | flue: PyPI · beetle: Open VSX · cricket: lazy.nvim · moth: Emacs |
| 4 | suitcase | Capture | sonnet | flue: importer core · beetle: Claude Code · cricket: ChatGPT · moth: `llm` logs |
| 5 | kiste | Reading | opus | flue: Postkasse skeleton · beetle: search · cricket: backlinks · moth: RSS · snail: attachments render |
| 6 | akvarium | Android | sonnet | flue: the phone doc · beetle: PWA · cricket: *maybe* voice |
| 7 | hundehus | The watch | sonnet | flue: `records doctor` · beetle: `records watch` · cricket: the bark |
| 8 | schrank | Preservation | sonnet | flue: `records archive` · beetle: `records verify` · cricket: attachments as page bundles · snail: `records attach` |
| 9 | booth | The booth | sonnet | flue: `records card` · beetle: the curses booth · cricket: booth + Ollama |
| 10 | portaloo | Carry it | sonnet | flue: `records.pyz` · beetle: `records pack` · cricket: offline books |
| 11 | utedo | What must leave | opus | flue: `records redact` · beetle: `records unpublish` · cricket: scrub |
| 12 | badstu | Steam <small>(now)</small> | opus | flue: this roadmap · beetle: CI truth · cricket: runner image · moth: the audit |

The `Model` column is the recommended Claude model for a session walking that road — the reasoning
lives in [how a road is walked](roadmap/README.md#which-model-walks-it).

This table is desire, not contract. Names are claimed only when `/werden` actually turns; the epoch
stays human-owned, hand-edited in `CURRENT`.

## What we will not build

No Windows — the build path is bash and stays bash. No voice-to-text engine. No federation, no
comments platform, no accounts, no hosted service — a record is a file in your repo and the site is
static; that is the product. No second build path. No growth in Fuglekasse. No dependencies in the
engine — stdlib parsers, model-optional, mechanical output byte-matching AI output. No dates — the
werden names are the schedule, and the mountain is climbed at walking pace. And no AI-drafted
upstream contributions, ever — see [never-ever-ever-ai-slop.md](never-ever-ever-ai-slop.md), this
file's older sibling.

Borders are a good thing.

## One closing line

Eleven roads, and none of them leads away from the same small idea: your words, your repo, your
site. We are in the sauna now — and what walks out of the heat still has to fit in a mailbox.
