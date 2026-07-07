---
name: diff-10
description: Summarize the last 10 commit(s) as a table of short sha, verbatim commit message, and a prose summary of each commit's diff
disable-model-invocation: true
allowed-tools: Bash(git *)
argument-hint: "[prose style for the diff summaries]"
---

The user invoked /diff-10: summarize the last 10 commit(s) of this repository.

## The 10 most recent commit(s) — message + patch

!`git log -10 -p --pretty=format:'===COMMIT %h===%n%B'`

## What to produce

Read each commit's message and patch above, then output **one** Markdown table with a single row per commit, newest first, and exactly these three columns:

| Commit | Message | Changes |
|--------|---------|---------|

- **Commit** — the short SHA shown after `===COMMIT`.
- **Message** — the commit message **verbatim**. Cap the shown text at three lines: keep the first three lines and append `…` if it is longer.
- **Changes** — your own prose summary of that commit's diff: what actually changed and why it matters, not a file list. Hard cap: five lines. This prose must NOT contain path/file names, command names, or SHAs — describe changes conceptually, in plain words only.

Formatting rules for cells: use `<br>` for line breaks inside a cell, and escape any literal `|` as `\|`.

If `$ARGUMENTS` is non-empty, treat it as the desired **style/voice** for the Changes column only (e.g. "terse", "playful", "reviewer tone") — never as literal text, and never touching the Message column, which stays verbatim.

Output only the table (a one-line title above it is fine). No preamble, no trailing commentary.
