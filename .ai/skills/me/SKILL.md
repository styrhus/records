---
name: me
description: Use when the user invokes /me to start transcribing the user's messages verbatim into a draft markdown file (kept out of the published site) until /esc is invoked
disable-model-invocation: true
model: haiku
effort: low
argument-hint: "[#tags] [optional filename]"
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
   - `records/` already exists at the root → use it (highest priority; skip the rest)
   - `docs/` exists at the root → use `docs/records/`
   - another docs-like dir exists at the root (`doc/`, `documentation/`, `notes/`) → use `<that>/records/`
   - a docs-like dir exists one level down (e.g. `packages/docs/`) → use `<that>/records/`; prefer a `docs` match over the other names, and if several match equally, pick the first shown above
   - none exist → use `records/` at the project root
2. **Create the directory** if it does not exist: `mkdir -p <parent>/records`.
3. **Extract tags** from `$ARGUMENTS`: tags are the *leading* `#word` tokens only.
   Strip the `#`; lowercase; drop any character that is not a letter, digit or hyphen.
   Stop at the first token that does not start with `#` — a `#` later in the text
   belongs to the title. Whatever remains after the tags is the title text. Examples:
   - `#linux #hardware How to do it right` → tags `linux, hardware`; title `How to do it right`
   - `#linux` → tags `linux`; no title text
   - `How to do it right` → no tags; title `How to do it right`
4. **Pick the file path**:
   - Tags given → the file goes in `<parent>/records/<first-tag>/` (`mkdir -p` it first); no tags → directly in `<parent>/records/`.
   - Title text given → filename is the slugified title (lowercase, spaces → hyphens; append `.md` if missing).
   - No title text → filename is the date+time shown above, e.g. `2026-07-03_14-35.md`.
   - Never overwrite an existing file — append a numeric suffix (`-1`, `-2`, …) if the name is taken in that directory.
5. **Create the file** with the Write tool, containing only this frontmatter (`draft: true` keeps it off the published site; omit the `tags:` line entirely when no tags were given):

   ```markdown
   ---
   title: <title text or date+time, verbatim>
   date: <ISO timestamp from Context, verbatim>
   draft: true
   tags: [<tag1>, <tag2>]
   ---
   ```

6. Output nothing and end the turn.

## Recording (every following turn, until /esc)

From the next user message onward, transcribe the user's side of the conversation into the file. Recording is a background duty — it must not change how you otherwise behave, respond, or use tools. The /me invocation itself is NOT recorded; tool calls and tool results are NOT recorded; your responses are NOT recorded. Only record the user's messages.

On **each** of your turns while recording:

1. Handle the user's request as you normally would.
2. Append the user's message verbatim with a single Bash call, using a quoted heredoc so nothing is interpreted:

   ```bash
   cat >> <file> <<'RECORD_XEOF_7'

   <user message, verbatim, unmodified>
   RECORD_XEOF_7
   ```

3. Your response goes to the user as normal — it is never written to the file.

Rules:

- **Verbatim means verbatim**: no paraphrasing, no trimming, no fixing typos, no omitting parts of the message.
- **No headings, no Assistant sections, no signature** — no `## User` marker; the file contains only the verbatim user messages, each separated by a blank line.
- If the text contains the heredoc delimiter, pick a different delimiter.
- Never skip a turn "because it was short" or "just a tool run" — every user message gets appended.
- Recording stops ONLY when the user invokes /esc. Do not stop on your own, and do not record the /esc invocation.
