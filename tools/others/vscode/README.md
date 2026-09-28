# Records Chat

Write your conversations down, and publish them as your own static site.

[Styrhus Records](https://codeberg.org/styrhus/records) turns Markdown transcripts into a published
site. This extension is the editor side of it: a sidebar chat where you record a conversation — with
yourself, or with a local model — and it lands as a Markdown file in your own repo, with correct
frontmatter, ready to build and publish. No account, no service, no data leaving your machine.

Works in VS Code and VSCodium alike.

## Requires the `records` CLI

The extension has no logic of its own — it drives
[recordkit](https://pypi.org/project/recordkit/), a dependency-free Python CLI:

```bash
pipx install recordkit
```

If `records` isn't on your PATH afterwards, set `records.binaryPath` to its full path.

A local [Ollama](https://ollama.com) model is **optional**. Without one, every command still works;
recordings are simply one-sided. Full setup for the CLI and every editor:
[docs/install.md](https://codeberg.org/styrhus/records/src/branch/main/docs/install.md).

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
- `/airtime` — Human vs Assistant token share (the active recording, else the memory-only chat)
- `/config` — show the resolved records directory
- `/esc` — stop recording
- Missing-CLI detection: if the `records` binary isn't found, the chat shows install
  instructions and a button to open the `records.binaryPath` setting

## Opening it

The birdhouse icon in the activity bar. Or `Ctrl+Shift+R` / `Cmd+Shift+R`, or `Ctrl+Shift+\` /
`Cmd+Shift+\` (that's `Ctrl+|` on a US layout), or "Records: Open Chat" from the command palette —
all of them focus the chat's text input directly.

> `Ctrl+Shift+R` shadows the editor's default Refactor binding while an editor has focus. On non-US
> layouts the second binding follows the physical `\` key — check Preferences → Keyboard Shortcuts
> if it doesn't respond, and rebind as needed.

## Usage

```
/all #linux How To      ← start recording (creates the record file)
hello world             ← free text is appended as a Human turn
/esc                    ← stop recording
/stick how-to           ← feature it
/gcp docs: update       ← commit + push
```

## Development

Open `tools/others/vscode/` in the editor, `npm install`, then press F5 to launch the
Extension Development Host (`npm run watch` for incremental compiles). `npm run package` builds the
`.vsix`; built `.vsix` files are throwaway build artefacts — never committed, never packaged.
Release steps live in
[tools/others/README.md](https://codeberg.org/styrhus/records/src/branch/main/tools/others/README.md).

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

See [tools/others/ollama/README.md](https://codeberg.org/styrhus/records/src/branch/main/tools/others/ollama/README.md).
