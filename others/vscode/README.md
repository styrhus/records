# Records Chat — VSCode Extension

A sidebar chat view for the records site's mechanical skills, with optional Ollama support.
Works in VS Code and VSCodium alike.

## Features

- Persistent chat in the activity bar (birdhouse icon) — open it once, it stays put
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
npm run package          # produces records-chat-0.2.0.vsix
codium --install-extension records-chat-0.2.0.vsix   # VSCodium
code --install-extension records-chat-0.2.0.vsix     # VS Code
```

Reload the editor — the birdhouse icon appears in the activity bar. Click it, or press
`Ctrl+Shift+R` / `Cmd+Shift+R`, or run "Records: Open Chat" from the command palette.

> `npm run package` needs Node; with mise: `mise exec node@24 -- npm run package`.
> Note: `Ctrl+Shift+R` shadows the editor's default Refactor binding while an editor has focus.

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
- `records.ollamaEndpoint` (default: `""`) — optional Ollama endpoint to enable two-sided `/record`

## Ollama Integration (Future)

When `ollamaEndpoint` is configured, `/record` becomes two-sided: user messages are sent to
the local model, and assistant replies are stamped with the model tag (stripped by the site
during rendering). All voice skills become system-prompt presets.

See `../ollama/README.md`.
