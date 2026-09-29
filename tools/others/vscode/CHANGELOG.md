# Changelog

## 0.7.0

- The chat moves to the secondary side bar (VS Code 1.106+), as a tab next to other chat extensions such as Claude Code and Mistral Vibe; older editors keep it in the activity bar.
- New **Records** list in the activity bar: every record in the resolved records directory, newest first, with title, age, section and draft/featured state; click to open, live-refreshing as records are written.
- Assistant replies render as Markdown — headings, lists, emphasis, links, inline and fenced code (with a Copy button), blockquotes, tables — escaped first, only `http(s)`/`mailto` links. Streamed replies render as they arrive.
- Restyled with the editor's theme: proportional UI font, user messages as bubbles, status lines small and dim, errors and command output as accented blocks, animated busy indicator, welcome screen on an empty chat.
- New composer: a multi-line box (Enter sends, Shift+Enter adds a line, grows with its content) with a toolbar — attach (`@`), commands (`/`), the model pill (opens the Ollama settings, replacing the ⚙ button and the model line) and a send button. Context chips sit inside the box.
- Header shows the recording state — recording (with file and model), draft, ephemeral chat or idle — and a stop button for `/esc`.
- Fix: context files in multi-root workspaces. `@` picks and the editor chip now reach the CLI as absolute paths, so a file from any folder other than the first is no longer reported missing to the model; the `@` picker labels entries with their folder name when several are open.

## 0.6.0

- First registry release: the extension is published to Open VSX instead of sideloaded as a `.vsix`; the VS Code Marketplace follows.
- README rewritten to stand on its own as a registry page — what the extension is, that it drives the `records` CLI (`pipx install styrhus-records`), and that Ollama is optional.
- Registry metadata: keywords, homepage, issue tracker, gallery banner.
- `.vscodeignore` excludes `*.vsix`, so built packages can no longer end up inside a built package.

## 0.5.0

- Ephemeral chat without an active recording: with a model configured, messages go through `records ollama-chat`, history lives in the extension's memory only and nothing touches disk; it resets on `/record`, `/all`, `/me` and `/esc`.
- With no model and no recording, a dim hint replaces the old "No active recording session." error.
- Second keybinding `Ctrl+Shift+\` / `Cmd+Shift+\` (`Ctrl+|` on US layouts) on `records.openChat`, which now also focuses the input field.
- Status lines render dim; the `> ` user echo and model replies stay prominent.

## 0.4.0

- Chat messages word-wrap; long lines no longer produce a horizontal scrollbar.
- Slash-command autocomplete: typing `/` opens a popup with all commands and descriptions, filtered as you type (arrows/Tab/Enter to pick, Escape to dismiss); a known command shows its argument hint below the message log.
- Settings gear (⚙) next to the input: an inline panel edits `records.ollamaEndpoint` / `records.ollamaModel` and persists them to the user settings.json.
- `@` file attachments: typing `@` opens a workspace file/folder picker; picks become chips and their contents (folders: a file listing) are sent to Ollama as model-only context via the new `records ollama-reply --context-file/--context-dir` flags. The typed `@path` stays in the recorded message; the file contents are never written to the record, and context is per-turn.
- Active-editor context: the file open in the editor shows as a chip above the input and is sent as model context; click the chip to toggle it off.
- Active model line under the input (`model @ endpoint`, or `no model — user-only recording`), live-updating on settings changes.
- Webview HTML moved to `src/webviewContent.ts`; the slash-command registry (`src/commands.ts`) feeds both autocomplete and dispatch.

## 0.3.0

- Two-sided `/record` via Ollama: with `records.ollamaEndpoint` and the new `records.ollamaModel` setting configured, chat messages go through `records ollama-reply` (Ollama `/api/chat`) and each reply is appended as a signed `## Human`/`## Assistant` turn; context is multi-turn within a recording session.
- Busy indicator while the model generates (input locked — no streaming); replies render green with preserved line breaks.
- On Ollama failure the message is recorded user-only with a visible warning; `/all` and `/me` stay user-only.
- CLI errors (`{"error": ...}` on stdout) now surface their message in the chat instead of a raw exit-code error.

## 0.2.0

- Chat moved from an editor webview panel to a persistent sidebar view (activity-bar birdhouse icon); `Records: Open Chat` and `Ctrl/Cmd+Shift+R` now focus the view.
- Installable `.vsix` packaging via `@vscode/vsce` (`npm run package`), with Marketplace/Open VSX-ready metadata.
- CLI detection on open: a missing `records` binary shows install instructions and an Open Settings button for `records.binaryPath`; changing the setting re-probes.

## 0.1.0

- Initial webview chat panel with slash commands routed to the recordkit CLI.
