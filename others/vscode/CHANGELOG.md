# Changelog

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
