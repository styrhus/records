---
name: record
description: Use when the user invokes /record to start transcribing the conversation verbatim into a markdown file until /esc is invoked
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

The user invoked /record: create the transcript file, then stay silent. **Do not respond to the user** — no greeting, no confirmation, no summary. End the turn with no text output. The user continues the conversation "fresh"; your only job on this turn is to set up the file.

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
3. **Pick the filename**:
   - If `$ARGUMENTS` is provided, use it as the filename (slugify: lowercase, spaces → hyphens; append `.md` if missing).
   - Otherwise use the date+time shown above, e.g. `2026-07-03_14-35.md`.
   - Never overwrite an existing file — append a numeric suffix (`-1`, `-2`, …) if the name is taken.
4. **Create the file** with the Write tool, containing only this frontmatter:

   ```markdown
   ---
   title: <date+time or user given argument verbatim>
   date: <ISO timestamp from Context, verbatim>
   ---
   ```

5. Output nothing and end the turn.

## Recording (every following turn, until /esc)

From the next user message onward, transcribe the conversation into the file. Recording is a background duty — it must not change how you otherwise behave, respond, or use tools. The /record invocation itself is NOT recorded; tool calls and tool results are NOT recorded. Only record the user's messages and your text responses.

On **each** of your turns while recording:

1. Handle the user's request as you normally would.
2. After composing your final response text, append both sides verbatim with a single Bash call, using a quoted heredoc so nothing is interpreted:

   ```bash
   cat >> <file> <<'RECORD_XEOF_7'

   ## User

   <user message, verbatim, unmodified>

   ## Assistant

   <your full response text, verbatim, exactly as you will output it>

   — <your model version/tag, e.g. qwen2.5-coder:14b>
   RECORD_XEOF_7
   ```

3. Then output that exact same response text to the user.

Rules:

- **Verbatim means verbatim**: no paraphrasing, no trimming, no fixing typos, no omitting parts of either message.
- **Sign every Assistant entry** with your exact model ID (as stated in your system prompt, e.g. `qwen2.5-coder:14b`) on a final `— <model-id>` line. The signature goes in the file only — never include it in the response you show the user.
- If the text contains the heredoc delimiter, pick a different delimiter.
- Never skip a turn "because it was short" or "just a tool run" — every user message and every response you give gets appended.
- Recording stops ONLY when the user invokes /esc. Do not stop on your own, and do not record the /esc invocation.
