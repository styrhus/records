# blyant records Without AI (`tools/others/`)

<!-- werden: 0.12.3 badstu-cricket -->

This directory contains the **no-AI engine and plugins** for the blyant records site — letting you run the mechanical slash-commands without a model. Optionally add Ollama for the AI-driven skills.

## Architecture

```
tools/others/
├── python/              # recordkit: stateless library + CLI (JSON I/O), published to PyPI
│   ├── recordkit/       # modules: config, naming, create, stick, commit, publish, mucke, werden, etc.
│   ├── tests/           # unit tests (config discovery, frontmatter, ollama, publish, version, etc.)
│   ├── pyproject.toml   # version derived from CURRENT via recordkit.__version__
│   ├── README.md        # the PyPI landing page
│   └── .gitignore       # __pycache__, .pytest_cache, build artifacts
├── naming/              # werden-cycle name pools (dyr.json, strukturer.json) + scheme doc
├── vscode/              # Records Chat: VSCode sidebar chat view (Open VSX + Marketplace)
│   ├── src/             # extension.ts, chatViewProvider.ts, commands.ts, webviewContent.ts
│   ├── media/           # activity-bar SVG + marketplace icon
│   ├── package.json     # vsce packaging (npm run package)
│   └── .gitignore       # node_modules, out/, *.vsix
├── neovim/              # records.nvim: Neovim Lua plugin
│   ├── lua/records/     # the plugin itself
│   ├── plugin/          # registers :Records without setup()
│   └── doc/             # :help records
├── emacs/               # records.el: M-x records, one file, no dependencies
└── ollama/              # Ollama integration guide (two-sided /record — implemented)
```

## Quick Start

### 1. Install the engine

```bash
pipx install recordkit
```

The `records` command is now available system-wide. From a clone: `pipx install ./python`.

Installing the editor plugins is one page: [docs/install.md](../../docs/install.md).

### 2. Try it (from the blyant records repo)

```bash
# Create a record
records new "#linux #hw How To"
# Output: {"path": "records/linux/how-to.md", "title": "How To", "tags": ["linux", "hw"], …}

# Show the records dir — "source" says whether it was found in the checkout
# ("discovered"), stated with --dir, or is the conventional name assumed
# ("assumed", with "exists": false on a checkout that has none yet)
records config

# Append a user message
records append --file records/linux/how-to.md --text "hello world"

# Feature it
records stick --slug how-to

# Commit it
records commit -m "docs: add linux hardware notes" --push

# Build and deliver the site without CI (params.publishTarget in hugo.yaml)
records publish --dry-run
records publish

# Advance the werden cycle (or --stamp to re-stamp without advancing)
records werden
# Output: {"old": "0.1.18 fuglekasse-spider", "new": "0.1.19 fuglekasse-scorpion", …}
```

### 3. The editors

Install steps for all three live on one page — [docs/install.md](../../docs/install.md). Once a
plugin is in place the panel is identical everywhere:

```
/all #linux How To
hello world
/esc
/stick how-to
/gcp docs: update
```

| Editor | Open it | Notes |
|---|---|---|
| VS Code / VSCodium | birdhouse icon, `Ctrl/Cmd+Shift+R`, `Ctrl/Cmd+Shift+\`, or "Records: Open Chat" | Ollama wired |
| Neovim | `:Records` | `:help records` — Ollama wired via `ollama_endpoint`/`ollama_model` |
| Emacs | `M-x records` | `RET` prompts for a line |

## Mechanical Skills (No AI Needed)

All of these work without a model:

| Skill | Syntax | What it does |
|-------|--------|-------------|
| `/record`, `/all`, `/me` | `/all [#tags title]` | Create & transcribe a record. `/me` marks as draft. |
| `/esc` | `/esc` | Stop recording. |
| `/stick` | `/stick [slug]` | Feature a record (add `featured: true`, drop `draft:`). |
| `/gc`, `/gcp`, `/cpd` | `/gc -m "msg"` | Commit / push / deploy. `-m` required (no AI to author). |
| `/myname` | `/myname <name>` | Save your name locally (in `.mem/`). |
| `/mucke` | `/mucke` | Stamp now-playing MPRIS track into a file. |
| `/airtime` | `/airtime` | Human vs Assistant token share of the record (VS Code: of the unrecorded chat too). |
| `/werden` | `/werden [structure \| --stamp]` | Advance the development cycle (`CURRENT` + doc markers). |

The AI-only skills (`/poet`, `/pirate`, `/eq`, `/bff`, `/spellcorrect`, `/diff-*`, `/review`, `/phil-gc`) remain in `.ai/skills/` and are available in Claude Code.

## The Engine's Own Commands

These have no slash-command counterpart — they are the CLI's, and they need no model either:

| Command | What it does |
|---------|-------------|
| `records import --source <s> --path <p>` | Import conversations from an export: `claude-code`, `llm`, `markdown`. Idempotent — a second run writes nothing. |
| `records archive [--check]` | One zip holding records, referenced assets, the site config and a SHA-256 manifest. Deterministic. `--check` is cron mode: silent when healthy. |
| `records verify [<archive>]` | Recompute an archive's checksums, or — with no argument — check that every reference in every record still resolves. |
| `records export --out <path> [--single]` | The whole corpus as plain text that needs no tooling at all. |
| `records attach <record> <files…>` | Copy files into a record, converting it to a Hugo leaf bundle. The URL does not change. |
| `records pack [--out <file>]` | The built site collapsed into one offline HTML file. Post-processes `public/`; never builds. Needs `pageMode: single` or `single-flowing`. |
| `records card <record> [--turn N]` | One turn as an SVG quote card in the site's own palette. |
| `records booth` | A stdlib-curses composing screen. Writes byte-identically to `records new` + `append`. |
| `records doctor` | Report what will fail in this checkout — reporting only, never fixing. |
| `records watch` | Rebuild when a record changes. Never commits, never pushes, never publishes. |
| `records redact <record> --turn N (--remove \| --replace <text>)` | Rewrite one turn in place, leaving a `[redacted]` seam — `--remove` leaves the marker alone, `--replace` puts text beside it. Shows the diff and asks first (`--dry-run`, `--yes`); never touches git, and every run states what remains. |
| `records unpublish <record>` | Draft a record out of the site, the books and the pages branch; `--tombstone` leaves a stub at the old URL, `--restore` brings it back. Empty the output dir before publishing — Hugo overwrites, it does not delete. |
| `records scan [<path>]` | Look for credential-shaped strings in the records. Heuristic, and it says so; matches are masked, never printed in full. Non-zero exit on any finding. |
| `records ignore [--check]` | Translate `records/.recordsignore` into the site config's generated `ignoreFiles:` block, so Hugo and `book.lua` both honour it. `--check` reports drift and writes nothing. |

`doctor`, `watch`, `scan` and `ignore` print human-readable text and own their flags (`--json`
for machine output); every other command emits JSON on stdout like the rest of the CLI.

## Honest Degradations

- **No AI `/record`**: falls back to `/all` (user-only). Two-sided recording returns when Ollama is configured.
- **No AI commit message**: the plugins prompt you for `-m "message"` instead of auto-authoring one.
- **No Python in CI**: `records doctor` runs as an optional early step in all three CI shims; a fork with no Python still builds, it just skips the check.
- **OG cards are SVG** (poor crawler support outside Slack/Discord) and Postkasse-only; Fuglekasse sites keep the site-level `ogImage` only.

## Ollama (Optional)

When you have a local LLM running:

```bash
ollama pull mistral
# Then configure the VSCode extension:
# Settings → records.ollamaEndpoint → http://localhost:11434
#          → records.ollamaModel    → mistral:latest
```

`/record` becomes two-sided (user msg → model → reply + signature), with multi-turn context
per recording session, via `records ollama-reply` — in VSCode and, since postkasse-flue landed
there, in Neovim (`require('records').setup{ollama_endpoint=…, ollama_model=…}`). Workspace files
can ride along as model-only context (never written to the record):

```bash
records ollama-reply --endpoint http://localhost:11434 --model mistral:latest \
  --file records/2026-07-24_10-00.md --human "explain this" \
  --context-file src/main.py --context-dir docs
```

Without an active recording, the VSCode chat still talks to the model via
`records ollama-chat` — same flags minus `--file`, prior turns passed as JSON
(`--history`, `-` = stdin), nothing written to disk:

```bash
records ollama-chat --endpoint http://localhost:11434 --model mistral:latest \
  --human "explain this" --history '[{"role": "user", "content": "earlier turn"}]'
```

In the VSCode extension the same flags back `@` file attachments and the active-editor
context chip. See `ollama/README.md` for details.

Both commands also take `--preset <name>` — a voice from `recordkit/presets/` (`pirate`, `poet`,
`bff`), a deterministic system prompt composed ahead of the `--context-*` material and never
written to the record — and `--stream`, which switches stdout to NDJSON (one `{"token": …}` line
per chunk, then the usual final result line) so an editor can render the reply as it arrives; what
lands in the record is byte-identical either way. Both plugins stream only when their `stream`
setting is switched on.

## Development

### Engine tests

```bash
cd python && python -m pytest -q
```

### VSCode

```bash
cd vscode
npm install
npm run compile  # or: npm run watch
F5               # Launch Extension Dev Host
npm run package  # Build the .vsix (a throwaway artefact — gitignored, never packaged)
```

### Neovim, Emacs

No build step. Neovim: `lua/`, `plugin/`, `doc/` — the layout a package manager expects.
Emacs: one file, `records.el`.

## Releasing

Both releases are manual and both need credentials, so they are the human's to run.

### The engine → PyPI

The version is not chosen here — it is the werden cycle number, stamped into
`recordkit/__init__.py` by `/werden` and read by `pyproject.toml`. A structure step *down* the pool
derives a lower number; bump the epoch in `CURRENT` by hand first, or the older release stays
"latest" on PyPI. See [naming/README.md](naming/README.md).

```bash
cd python
python -m pytest -q                       # test_version.py checks CURRENT == __version__
rm -rf dist && pipx run build             # sdist + wheel
python -m zipfile -l dist/*.whl           # must contain recordkit/ and nothing from tools/
pipx run twine check dist/*

pipx run twine upload --repository testpypi dist/*
pipx install --index-url https://test.pypi.org/simple/ recordkit   # in a clean container
records config                            # against a real checkout

pipx run twine upload dist/*              # then PyPI, for real
```

### The extension → Open VSX, then the Marketplace

Open VSX first: it is what VSCodium users actually query, and Codeberg-first is deliberate here.

```bash
cd vscode
npm install && npm run package            # records-chat-<version>.vsix
npx vsce ls                               # inspect what is about to ship

npx ovsx create-namespace tb4 -p "$OVSX_TOKEN"     # once, ever
npx ovsx publish records-chat-<version>.vsix -p "$OVSX_TOKEN"

npx vsce publish -p "$AZURE_TOKEN"        # then the Marketplace
```

The `publisher` field is `tb4` and must match the namespace claimed on each registry. The extension
keeps its own npm-semver in `package.json` — it is not the engine, and it is not the werden cycle.

## Conventions

- **Frontmatter output** byte-matches the `.ai/skills/` records (ordering, omitted `tags:` when no tags, `draft:` placement).
- **Records dir discovery** mirrors the skills exactly (shallowest `hugo.yaml`, then `records/` → `docs/records/` → other fallbacks).
- **Tag routing** identical: `#tags` → `records/first-tag/`.
- **Cross-platform**: uses `pathlib` (Python), Lua I/O (Neovim), Node.js child_process (VSCode), `call-process` (Emacs).
- **No protocol logic in an editor** — plugins parse a slash command and call the CLI. If an editor needs something the CLI can't do, the CLI grows.
- **No git hooks or side effects** — the plugins are purely mechanical; they don't touch `.git` or trigger deployments on their own.

## Files

- `python/.gitignore` — Python bytecode, test cache, build output, `uv.lock`
- `vscode/.gitignore` — Node modules, compiled output, extension package
- `neovim/.gitignore` — Neovim runtime cache (doc/tags)
- Root `.gitignore` — added VSCode and Neovim artifacts, not picked up by the subproject ignores

## Next Steps

- **Wire Ollama in Emacs** (the CLI's `ollama-reply` does the HTTP work; VSCode and Neovim are done — `records-ollama-endpoint` is still a reserved defcustom).
- **Walk both plugins against a real site** — the postkasse 5 walkthrough: every command, VSCode and Neovim, on a scratch clone with a live Ollama.
- **Upload the releases** — the packaging is done and the runbooks are above; PyPI and Open VSX need credentials.
