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
   *In parallel mode this step belongs to the human — see [running several sessions at
   once](#running-several-sessions-at-once).*
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
project's living docs are load-bearing: `AGENTS.md` (the tracked agent-instructions file;
`CLAUDE.md` symlinks to it), `tools/others/README.md`, the theme README. If an item changes a
config key, a command, an ordering rule or a build step, updating the matching prose is part of the
item, not a follow-up.

Nothing is done because it looks done. If the acceptance check could not be run, the item stays
`wip` and the reason goes in the notes.

## Running several sessions at once

The roads are open, not queued, so several sessions can run in parallel. Not naively, though —
three things bite.

### One workspace per session

Two sessions in the same checkout stomp each other regardless of which files they touch: each sees
the other's half-finished edits, tests run against a mixed tree, and `git status` shows everyone's
work at once. Give each session its own worktree:

```bash
git worktree add ../records-hundehus
git worktree add ../records-schrank
```

The project's instructions (`AGENTS.md`) are tracked, so every fresh worktree has them. `.mem/` is
gitignored — copy it in if the session needs the local memory.

### The human assigns; the table is the ledger

The claim step above assumes everyone can see the same `STATUS.md`. In separate worktrees each
session has its own copy, so claims are invisible to the others and two sessions will happily take
the same item.

**In parallel mode, assign items up front and keep the `STATUS.md` rows yourself.** Sessions read
their road, do their item, and report; they do not claim. A session told to work alone in the main
checkout still claims normally.

### Defer the `cli.py` registration

`recordkit/cli.py` is the one genuine chokepoint — seven roads add a subparser to the same function.
The conflict is trivial but universal.

**A session adding a command writes its module and leaves a one-line `TODO` where the subparser
would go, rather than editing `cli.py`.** Wiring them all up afterwards is a single small pass with
no conflicts at all. The same applies to the shared prose: if several sessions are running, they
note what `AGENTS.md` and `tools/others/README.md` need rather than editing those files.

### What does not parallelize

- **Items with a stated dependency.** Each `STATUS.md` names them in its notes — `schrank 3` before
  `kiste 6`, `kiste 1` before `booth 4`, `bikube 1` before `portaloo 1`, `suitcase 1` before the
  rest of its road.
- **Two items on the same file.** Beyond `cli.py`, the known pairs are `recordkit/stick.py`
  (`postkasse 4` and `schrank 3` change the same function for different reasons), the Neovim plugin
  (`postkasse 1` and `hundehus 3`), and the CI shims (`badstu 2` and `hundehus 4`).
- **`badstu 4`, the audit.** It reads and corrects the whole repo by definition. Run it alone.

Items that create new files and touch nothing shared are the ones to fan out on. Anything under
`docs/` is free.

## Which model walks it

Each road in the [roadmap's at-a-glance table](../ROADMAP.md#the-eleven-at-a-glance) carries a
recommended model. The assignment is simple:

- **sonnet** is the fan-out default. Roadmap items are deliberately session-sized, with named files,
  an acceptance check and a border — exactly the well-specified work Sonnet handles at near-Opus
  quality, and parallel sessions multiply whatever a model costs.
- **opus** for the three roads where judgment outweighs typing: *kiste* (a second theme designed
  from scratch — search, backlinks, RSS all have wrong-but-plausible shapes), *utedo* (redact,
  unpublish, scrub — destructive and irreversible, where a subtle mistake is a lie in the record),
  and *badstu* (the whole-repo audit and CI truth-checking, which is judgment about everything at
  once).
- **haiku** for no road. Every road touches multiple files or writes tested code; the savings are
  not worth the re-runs.
- **fable** for no road either. Nothing here needs the top tier, and its cost cuts directly against
  fanning out. If any single item earns it, it is `badstu`'s audit — which runs alone anyway.

A recommendation is a default, not a rule: a human running one session on a hard item can always
step up a tier.

## The borders

Every road inherits the project's borders, listed in full at the bottom of the
[roadmap](../ROADMAP.md). The three that bite most often while implementing:

- **The engine takes no dependencies.** `recordkit` is stdlib-only, and stays that way. If an item
  seems to need a library, it needs a smaller design instead.
- **There is one build path.** `bin/build.sh` is it. Nothing gets a second one.
- **Fuglekasse does not grow.** New display features live in a new theme, not in the minimal one.

## Stewardship

Coordination of these roads is stewarded by the **assistant** (the Forgejo
user of that name). Development happens in the assistant's sidestream copy of
this repository; finished work arrives here as merge requests, reviewed and
merged by the human — merges are never the assistant's. The assistant may
delegate items to other agents and models; whoever the hands, the protocol
above still governs: claims in STATUS, evidence before assertions, borders
respected. Conversation about the roads is welcome in this repository's
issue tracker.

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
