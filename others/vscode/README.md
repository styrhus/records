# Records Chat — VSCode Extension

A webview chat panel for the records site's mechanical skills, with optional Ollama support.

## Features

- `/record`, `/all`, `/me` — create and transcribe records with Hugo frontmatter
- `/stick [slug]` — feature a record (adds `featured: true`, clears `draft:`)
- `/gc`, `/gcp`, `/cpd` — commit / push / deploy
- `/myname <name>` — save your name locally
- `/mucke` — stamp the now-playing MPRIS track
- `/config` — show the resolved records directory
- `/esc` — stop recording

## Installation

1. Ensure `recordkit` is installed and the `records` command is in your PATH:
   ```bash
   cd ../python && pip install -e .
   ```

2. Open the VSCode folder and press F5 to launch the Extension Dev Host.

3. Run the command palette (`Cmd/Ctrl+Shift+P`) and select "Records: Open Chat" or press
   `Ctrl+Shift+R` / `Cmd+Shift+R`.

## Settings

- `records.binaryPath` (default: `"records"`) — path to the recordkit CLI
- `records.ollamaEndpoint` (default: `""`) — optional Ollama endpoint to enable two-sided `/record`

## Ollama Integration (Future)

When `ollamaEndpoint` is configured, `/record` becomes two-sided: user messages are sent to
the local model, and assistant replies are stamped with the model tag (stripped by the site
during rendering). All voice skills become system-prompt presets.

See `../ollama/README.md`.
