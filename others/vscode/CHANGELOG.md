# Changelog

## 0.2.0

- Chat moved from an editor webview panel to a persistent sidebar view (activity-bar birdhouse icon); `Records: Open Chat` and `Ctrl/Cmd+Shift+R` now focus the view.
- Installable `.vsix` packaging via `@vscode/vsce` (`npm run package`), with Marketplace/Open VSX-ready metadata.
- CLI detection on open: a missing `records` binary shows install instructions and an Open Settings button for `records.binaryPath`; changing the setting re-probes.

## 0.1.0

- Initial webview chat panel with slash commands routed to the recordkit CLI.
