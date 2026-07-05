---
name: me
description: Use when the user invokes /me to start transcribing the user's messages verbatim into a draft markdown file (kept out of the published site) until /esc is invoked
disable-model-invocation: true
model: haiku
effort: low
argument-hint: "[optional filename]"
allowed-tools:
  - Bash(mkdir *)
  - Bash(ls *)
  - Bash(find *)
  - Bash(date *)
  - Bash(cat >> *)
  - Write
---

The user invoked /me: create the transcript file, then stay silent. **Do not respond to the user** — no greeting, no confirmation, no summary. End the turn with no text output. The user continues the conversation "fresh"; your only job on this turn is to set up the file.

## Context

- Current date+time: !`date +%Y-%m-%d_%H-%M`
- ISO timestamp (for frontmatter): !`date -Iseconds`
- Existing docs-like dirs, cwd and one level down (empty = none): !`find . -mindepth 1 -maxdepth 2 -type d \( -name docs -o -name doc -o -name documentation -o -name notes -o -name records \) -not -path '*/.*' -not -path '*/node_modules/*' 2>/dev/null; true`

## Setup (this turn)

1. **Pick the parent directory** for `records/`, in this priority order:
   - `docs/` exists at the root → use `docs/records/`
   - another docs-like dir exists at the root (`doc/`, `documentation/`, `notes/`) → use `<that>/records/`
   - a docs-like dir exists one level down (e.g. `packages/docs/`) → use `<that>/records/`; prefer a `docs` match over the other names, and if several match equally, pick the first shown above
   - none exist → use `records/` at the project root
2. **Create the directory** if it does not exist: `mkdir -p <parent>/records`.
3. **Pick the filename**:
   - If `$ARGUMENTS` is provided, use it as the filename (slugify: lowercase, spaces → hyphens; append `.md` if missing).
   - Otherwise use the date+time shown above, e.g. `2026-07-03_14-35.md`.
   - Never overwrite an existing file — append a numeric suffix (`-1`, `-2`, …) if the name is taken.
4. **Create the file** with the Write tool, containing only this frontmatter (`draft: true` keeps it off the published site):

   ```markdown
   ---
   title: <date+time or user given argument verbatim>
   date: <ISO timestamp from Context, verbatim>
   draft: true
   ---
   ```

5. Output nothing and end the turn.

## Recording (every following turn, until /esc)

From the next user message onward, transcribe the user's side of the conversation into the file. Recording is a background duty — it must not change how you otherwise behave, respond, or use tools. The /me invocation itself is NOT recorded; tool calls and tool results are NOT recorded; your responses are NOT recorded. Only record the user's messages.

On **each** of your turns while recording:

1. Handle the user's request as you normally would.
2. Append the user's message verbatim with a single Bash call, using a quoted heredoc so nothing is interpreted:

   ```bash
   cat >> <file> <<'RECORD_XEOF_7'

   ## User

   <user message, verbatim, unmodified>
   RECORD_XEOF_7
   ```

3. Your response goes to the user as normal — it is never written to the file.

Rules:

- **Verbatim means verbatim**: no paraphrasing, no trimming, no fixing typos, no omitting parts of the message.
- **No Assistant sections, no signature** — the file contains only `## User` entries.
- If the text contains the heredoc delimiter, pick a different delimiter.
- Never skip a turn "because it was short" or "just a tool run" — every user message gets appended.
- Recording stops ONLY when the user invokes /esc. Do not stop on your own, and do not record the /esc invocation.
