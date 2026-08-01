---
title: utedo — What must leave
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, utedo]
---

# 11 · utedo — What must leave

> The outhouse: the smallest useful building, standing apart, dealing with what has to go.

Every publishing tool pretends this road does not exist. You get a beautiful path in and no path
back — and then someone publishes a conversation containing a name that should not be there, or an
API key, or a sentence about a person who did not consent to being in it.

Publishing without a way back is a trap. This road is the way back, and it is the reason to be
careful about the promises it makes: git remembers, and any tool claiming otherwise is lying.

So the deal here is honesty. Remove what can be removed. Say precisely what remains. Never imply the
past has been erased when it has only been amended.

## Dependencies

None. Every item is self-contained.

Item 1 is the most-used, item 3 is the most urgent when it is urgent.

## Items

### 1 · flue — `records redact`

Rewrite a turn in place, and leave a visible seam rather than a lie.

- New `recordkit/redact.py` behind
  `records redact <record> --turn N [--replace TEXT | --remove]`.
- The record keeps its shape: the turn stays, the conversation still reads, the removed text is
  replaced by a marker that is honest about what happened — `[redacted]` and nothing more clever.
- Turn numbering matches whatever `ollama.py` already uses when it rebuilds history from `## Human` /
  `## Assistant` sections. One numbering scheme, not two.
- `--dry-run` shows the diff before anything is written. Default to showing it and asking, given
  what this command does.
- The site rebuilds and the redaction is gone from the published page. **Git history still has it**,
  and the command says so, every time, in its output. This is not a warning to be suppressed.

**Files:** `recordkit/redact.py`, `recordkit/cli.py`, `tests/test_redact.py`.

**Acceptance:** a turn redacted, the record still rendering correctly on the site and in the PDF,
and the command's output stating plainly that git history retains the original.

**Border:** never rewrites git history on its own. Ever. That is item 3's territory and it is
guidance, not automation.

### 2 · beetle — `records unpublish`

Pull a record out of the published world without pretending it never existed.

- `records unpublish <record> [--tombstone]` — the record leaves the site, the books and the pages
  branch.
- Mechanism: the frontmatter route (`draft: true`, or `build.list: never` plus `render: never`) is
  the honest one, since it is reversible and visible in the repo. Decide which and document why.
- A tombstone is optional and off by default: a stub at the old URL saying a record was withdrawn.
  Better than a 404 for anyone who linked to it; worse than a 404 for anyone who wanted it gone.
  The user chooses.
- The pages branch matters here — `records publish --target pages-branch` force-pushes a single
  commit, so a removed record disappears from the published branch on the next publish. Confirm
  that, do not assume it.
- The PDF, EPUB and booklet are rebuilt from `records/` on disk, so `book.lua`'s draft skipping
  should already handle this. Confirm that too.
- `--restore` puts it back. A one-way command is a trap of a different kind.

**Files:** `recordkit/unpublish.py`, `recordkit/cli.py`, `tests/`, `docs/publish.md`.

**Acceptance:** a record unpublished, absent from a rebuilt site, absent from the rebuilt PDF and
EPUB, gone from the pages branch after a publish — then restored.

### 3 · cricket — When a secret lands in a transcript

It will happen. A pasted `.env`, a token in an error message, a password typed into the wrong
window. The response has to be fast, correct and honest about its limits.

- A documented emergency procedure — `docs/oops.md`, linked from `docs/publish.md` — covering, in
  order: rotate the credential first (always first; everything else is secondary), then remove it
  from the working tree, then decide about history.
- A `records scan` helper that greps the records tree for common secret shapes — high-entropy
  strings, `sk-` and `ghp_` style prefixes, `PRIVATE KEY` blocks, `.env`-shaped lines. Heuristic,
  fallible, and it says so.
- History rewriting is **guidance, not automation**. Explain what `git filter-repo` does, what it
  costs (every clone, every fork, every mirror is now wrong), and what it cannot reach — the forge's
  own caches, other people's clones, whatever the internet already indexed.
- The single most important sentence on this road belongs here: **rotate the credential.** A rewrite
  is cleanup; rotation is the fix.

**Files:** `recordkit/scan.py`, `docs/oops.md`, `docs/publish.md`.

**Acceptance:** the scanner finding a planted test secret in a scratch records dir, and the
procedure reviewed by someone who has actually done a history rewrite.

**Border:** the tool never rewrites history. It explains; the human decides and executes.

### 4 · moth — `.recordsignore`

Some files in the records tree should never be published, and there is currently no way to say so
that does not involve editing the site config.

- A `.recordsignore` file in the records dir, gitignore-style patterns, honoured by the build.
- Hugo's `ignoreFiles` already exists and `book.lua` already re-reads it raw from the config text
  and matches a documented simple-regex subset. **Reuse that path** — this item is a friendlier
  front end to an existing mechanism, not a second one.
- Precedence rules stated plainly, and the interaction with `draft: true` and `demoMode` documented.

**Acceptance:** an ignored file absent from the site, the PDF and the EPUB, with the existing
`ignoreFiles` behaviour unchanged.

### 5 · tadpole — Consent, written down

Records often contain other people. That is a fact about the product, not an edge case.

- A short `docs/other-people.md`: what to consider before publishing a conversation someone else is
  in, how to redact well (initials, roles, removing the identifying detail rather than the name),
  and how to respond to someone asking to be removed.
- Practical, not legal. It is a page about being decent, written by people who publish their own
  conversations.
- Link it from the README's "Record together" section, where multi-author instances are described.

**Acceptance:** the page exists, is short, and does not read like a terms-of-service document.

## Borders for this road

- **Never rewrite git history automatically.** Not behind a flag. The tool explains; the human acts.
- Never claim erasure. Every removal path states what remains — git history, forks, caches, the
  internet.
- Nothing here is one-way: redaction leaves a seam, unpublish restores, ignore is reversible.
- Reuse `ignoreFiles`; do not build a second exclusion mechanism.
