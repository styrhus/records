# Records Chat — VSCode Extension

A sidebar chat view for the records site's mechanical skills, with optional Ollama support.
Works in VS Code and VSCodium alike.

## Features

- Persistent chat in the activity bar (birdhouse icon) — open it once, it stays put
- Ephemeral chat: with an Ollama model configured, chatting works without an active
  recording — history lives in memory only, nothing is written to disk
- Slash-command autocomplete: type `/` for a filtered command popup with argument hints
- `@` file attachments: type `@` to pick workspace files/folders as model-only context
- Active-editor context chip: the open file is sent as context (click the chip to disable)
- Settings gear (⚙) to set the Ollama endpoint/model; active model shown under the input
- `/record`, `/all`, `/me` — create and transcribe records with Hugo frontmatter
- `/stick [slug]` — feature a record (adds `featured: true`, clears `draft:`)
- `/gc`, `/gcp`, `/cpd` — commit / push / deploy
- `/myname <name>` — save your name locally
- `/mucke` — stamp the now-playing MPRIS track
- `/config` — show the resolved records directory
- `/esc` — stop recording
- Missing-CLI detection: if the `records` binary isn't found, the chat shows install
  instructions and a button to open the `records.binaryPath` setting

## Prerequisites

The extension drives the `recordkit` CLI. Install it from the repo root:

```bash
pip install -e others/python     # or: pipx install ./others/python
```

If the `records` command isn't on your PATH, set `records.binaryPath` to its full path.

## Install

Build the extension package once, then install the `.vsix` permanently:

```bash
cd others/vscode
npm install
npm run package          # produces records-chat-0.5.0.vsix
codium --install-extension records-chat-0.5.0.vsix   # VSCodium
code --install-extension records-chat-0.5.0.vsix     # VS Code
```

Reload the editor — the birdhouse icon appears in the activity bar. Click it, press
`Ctrl+Shift+R` / `Cmd+Shift+R` or `Ctrl+Shift+\` / `Cmd+Shift+\` (that's `Ctrl+|` on a
US layout), or run "Records: Open Chat" from the command palette. All of these focus the
chat's text input directly.

> `npm run package` needs Node; with mise: `mise exec node@24 -- npm run package`.
> Note: `Ctrl+Shift+R` shadows the editor's default Refactor binding while an editor has focus.
> On non-US layouts the second binding follows the physical `\` key — check
> Preferences → Keyboard Shortcuts if it doesn't respond, and rebind as needed.

## Usage

```
/all #linux How To      ← start recording (creates the record file)
hello world             ← free text is appended as a Human turn
/esc                    ← stop recording
/stick how-to           ← feature it
/gcp docs: update       ← commit + push
```

## Development

Open `others/vscode/` in the editor, `npm install`, then press F5 to launch the
Extension Development Host (`npm run watch` for incremental compiles).

## Publishing (later)

The metadata is registry-ready; publishing is a manual step once accounts exist:

- **Open VSX** (VSCodium's default registry): create an Eclipse account + namespace, then
  `npx ovsx publish -p <token>`.
- **VS Code Marketplace**: create an Azure DevOps publisher, then `npx vsce publish`.

The `publisher` field is `tb4` — it must match the registry namespace/publisher id you claim.

## Settings

- `records.binaryPath` (default: `"records"`) — path to the recordkit CLI
- `records.ollamaEndpoint` (default: `""`) — Ollama endpoint URL enabling two-sided `/record`; empty = disabled
- `records.ollamaModel` (default: `""`) — Ollama model tag (e.g. `qwen2.5-coder:latest`); required when the endpoint is set

## Ollama Integration

With `records.ollamaEndpoint` and `records.ollamaModel` set, `/record` becomes two-sided:
each chat message goes through `records ollama-reply`, which sends the record's turns so far
to the model (`/api/chat`) and appends the reply as a signed `## Human`/`## Assistant` turn
(the model tag is stripped by the site during rendering). While the model generates, the
input is locked and a busy line shows; there is no streaming. If Ollama is unreachable or
errors, the message is recorded user-only and a warning appears. `/all` and `/me` always
record user-only. Voice skills as system-prompt presets are still future.

Without an active recording, messages still reach the model via `records ollama-chat`:
the conversation is ephemeral — history is kept in the extension's memory and sent with
each turn, nothing touches disk, and a failed turn just shows an error. The in-memory
history resets when a recording starts (`/record`, `/all`, `/me`) and on `/esc`. With no
model configured and no recording, the chat shows a dim hint instead of an error.

### File context (`@` and the editor chip)

Attachments and the active-editor file are passed to `records ollama-reply` as
`--context-file` / `--context-dir` and injected as a single system message for that API
call only — the record never contains file contents, so published transcripts stay clean.
The typed `@path` mention remains part of your recorded message; the auto-attached editor
file leaves no trace in the record. Context is **per-turn**: the model won't remember an
attached file on the next message unless you attach it again. Folders send a file listing
(paths only). Limits: 64 KiB per file, 256 KiB total, 500 listing entries; binary and
missing files degrade to a marker instead of failing the turn. The `@` picker lists up to
2000 workspace files (common build/VCS dirs excluded). Without a configured model,
attachments are ignored and the message is recorded user-only with a notice.

See `../ollama/README.md`.
