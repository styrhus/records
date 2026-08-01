---
title: How a road is walked
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap]
---

# How a road is walked

The [roadmap](../ROADMAP.md) names eleven roads. This folder holds one directory per road, and each
directory holds two files:

- **`ROADMAP.md`** — the elaborate plan. Written for someone who has read nothing else.
- **`STATUS.md`** — the handoff table. One row per item, claimed by editing the row.

An item is one session's work. Roads are open, not queued: whoever arrives with time picks any item
whose `State` is `open` and whose dependencies are `done`.

## Picking up an item

1. **Claim it.** In the road's `STATUS.md`, set the item's `State` to `wip` and put something in
   `Owner` — a handle, a model name, a date. An unclaimed `wip` row older than a session is fair game.
2. **Read the sibling `ROADMAP.md`.** The item section names the files, the command, and the border
   it must not cross. Read it before the code.
3. **Do the work.** Test-first where there are tests to write; the engine has them, the templates
   don't.
4. **Make the `Verify` command pass.** It is in the table. Paste its real output into the session —
   evidence before assertions, always.
5. **Tick it.** `State` → `done`. Add a one-line note if the shape changed from the plan.
6. **Leave the commit alone.** Commits belong to the human, via `/gc`. Report what changed and stop.

## What "done" means

An item is done when its acceptance check passes *and* the docs that describe it are true. This
project's living docs are load-bearing: `CLAUDE.local.md` (and its tracked mirror
`CLAUDE.local.md.example.md`), `tools/others/README.md`, the theme README. If an item changes a
config key, a command, an ordering rule or a build step, updating the matching prose is part of the
item, not a follow-up.

Nothing is done because it looks done. If the acceptance check could not be run, the item stays
`wip` and the reason goes in the notes.

## The borders

Every road inherits the project's borders, listed in full at the bottom of the
[roadmap](../ROADMAP.md). The three that bite most often while implementing:

- **The engine takes no dependencies.** `recordkit` is stdlib-only, and stays that way. If an item
  seems to need a library, it needs a smaller design instead.
- **There is one build path.** `bin/build.sh` is it. Nothing gets a second one.
- **Fuglekasse does not grow.** New display features live in a new theme, not in the minimal one.

## When a road finishes

When every item in a road's `STATUS.md` reads `done`, the road is walked. Turning the cycle is the
human's call, not an agent's: `/werden <next-structure>` claims the next name, and the werden marker
propagates itself. Agents never run `/werden`.

## Item numbering

A road's items are numbered by the animal pool in [dyr.json](../../../../tools/others/naming/dyr.json)
— item 1 is `flue`, item 2 `beetle`, item 3 `cricket`, and so on. This is not decoration: when the
item lands and the cycle turns, the animal is the name the cycle actually takes. Item 4 of *bikube*
is `bikube-moth` when it ships.

Roads themselves are numbered by
[strukturer.json](../../../../tools/others/naming/strukturer.json) — `postkasse` is 2, `badstu` is 12.
The full scheme is documented in [tools/others/naming/README.md](../../../../tools/others/naming/README.md).
