---
title: utedo — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, utedo, status]
---

# 11 · utedo — status

Road: **What must leave** · [plan](ROADMAP.md) · [protocol](../README.md)

Walked 2026-08-31, in one parallel-session pass. 4 of 5 done; item 3 waits on a human review.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `records redact` — rewrite a turn, leave a seam | done | Claude Opus 5, 2026-08-31 | `pytest tests/test_redact.py -q` → 26 passed; redacted record renders with `[redacted]`, output states git retains the original |
| 2 | beetle | `records unpublish` + `--restore` | done | Claude Opus 5, 2026-08-31 | `pytest tests/test_unpublish.py -q` → 24 passed; gone from a rebuilt site and from a real force-pushed pages branch after a clean publish, then restored |
| 3 | cricket | Secret in a transcript: `docs/oops.md` + `records scan` | wip | Claude Opus 5, 2026-08-31 | planted `ghp_…` found (1 error, exit 1; `pytest tests/test_scan.py` → 34 passed); procedure awaiting review by someone who has done a history rewrite |
| 4 | moth | `.recordsignore` over existing `ignoreFiles` | done | Claude Opus 5, 2026-08-31 | ignored record absent from a real `hugo` build (page gone, out of the sitemap, no text match in `public/`); book side by transliteration of `book.lua`'s reader — `pytest tests/test_ignore.py` → 26 passed |
| 5 | tadpole | `docs/other-people.md` — consent, written down | done | Claude Opus 5, 2026-08-31 | page exists, ~100 lines, no defined terms or obligations |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **The border that defines this road: never rewrite git history automatically.** Not behind a flag,
  not with a confirmation prompt. Item 3 explains `git filter-repo`; the human runs it.
- **Never claim erasure.** Every removal path must state what remains — git history, forks, forge
  caches, whatever is already indexed. A tool that implies the past is gone is worse than no tool.
- **1 · flue**: turn numbering must match what `recordkit/ollama.py` already uses when rebuilding
  history from `## Human` / `## Assistant` sections. One scheme, not two.
- **2 · beetle**: verify rather than assume that `publish --target pages-branch` (single force-push)
  and `book.lua`'s draft skipping already drop an unpublished record. Both look right; neither has
  been tested for this.
- **4 · moth** is a friendlier front end to Hugo's `ignoreFiles`, which `book.lua` already re-reads
  and matches. Reuse that path — do not build a second exclusion mechanism.
- **3 · cricket**'s most important line is not code: *rotate the credential first.* A history
  rewrite is cleanup; rotation is the fix.

## Walked (2026-08-31)

- **1 · flue**: `redact.locate()` is `turns.split()` plus line spans — checked equal on all 42
  record-shaped files in `docs/`, so the numbering is genuinely one scheme. `--replace` keeps the
  `[redacted]` marker as well as the replacement text: a substitution is still a visible seam.
  Default is show-the-diff-and-ask; a non-tty stdin is a no. The module contains no `subprocess`
  and no `filter-repo` — a test asserts it.
- **2 · beetle**: `draft: true` chosen over `build.render/list: never` — the `build.*` keys are
  nested, and `book.lua` (line 339) and `frontmatter.read` are both flat-key readers, so the books
  would have kept the record. **The pages-branch assumption did not hold as written**: Hugo does
  not clean its destination (`Cleaned │ 0`) and `records publish` force-pushes `public/` as it
  finds it, so an unpublished record's page was still on the branch after the next publish; it left
  only after `rm -rf public`. The command's `next` output now leads with that step. Follow-ups for
  whoever wants them: a deliberate decision on `--cleanDestinationDir` in `bin/build.sh` (it also
  affects renames and deletions, and deletes anything Hugo did not generate), and `records stick`
  on an unpublished record (`frontmatter.feature()` strips `draft:` but leaves `unpublished:` —
  refuse, or clear both). `book.lua`'s draft skipping is verified by reading plus a transcribed
  unit test; pandoc was absent, so no book was actually built.
- **3 · cricket**: matches are masked (`ghp_… (40 chars)`) — a report that quotes the secret has
  made a second copy of it. False-positive tuning was done against this repo's 257 real files: a
  first sweep found 35, four deterministic tightenings brought it to 0 outside the planted
  fixtures, each with a regression test. `.recordsignore` and `draft: true` are deliberately not
  honoured — neither keeps a file out of git, and git is what leaks.
- **4 · moth**: implemented as a *translator* onto `ignoreFiles` — `bin/build.sh`, `book.lua` and
  the themes are unchanged. Hugo matches `ignoreFiles` against **absolute** paths and `book.lua`
  against **records-relative** ones (both verified), so one rule usually emits two regexes, each
  inert for the other matcher, all inside `regexToLua`'s subset. A hand-written `ignoreFiles` is
  refused, never clobbered (`--adopt` migrates it). `records ignore` is a sync step; `--check`
  exits non-zero on drift and belongs in CI. Worth one confirming `tools/pandoc/build.sh` run
  wherever pandoc lives.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
