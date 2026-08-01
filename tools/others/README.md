# blyant records Without AI (`tools/others/`)

<!-- werden: 0.12.1 badstu-flue -->

This directory contains the **no-AI engine and plugins** for the blyant records site — letting you run the mechanical slash-commands without a model. Optionally add Ollama for the AI-driven skills.

## Architecture

```
tools/others/
├── python/              # recordkit: stateless library + CLI (JSON I/O)
│   ├── recordkit/       # modules: config, naming, create, stick, commit, publish, mucke, werden, etc.
│   ├── tests/           # 102 unit tests (config discovery, frontmatter, ollama, publish, etc.)
│   ├── pyproject.toml   # pip-installable package
│   └── .gitignore       # __pycache__, .pytest_cache, build artifacts
├── naming/              # werden-cycle name pools (dyr.json, strukturer.json) + scheme doc
├── vscode/              # Records Chat: VSCode sidebar chat view (installable .vsix)
│   ├── src/             # extension.ts, chatViewProvider.ts (TypeScript)
│   ├── media/           # activity-bar SVG + marketplace icon
│   ├── package.json     # vsce packaging (npm run package)
│   └── .gitignore       # node_modules, out/, *.vsix
├── neovim/              # records.nvim: Neovim Lua plugin
│   └── lua/records/     # :Records command, chat split
└── ollama/              # Ollama integration guide (two-sided /record — implemented)
```

## Quick Start

### 1. Install the engine

```bash
cd python
pip install -e .
```

The `records` command is now available system-wide.

### 2. Try it (from the blyant records repo)

```bash
# Create a record
records new "#linux #hw How To"
# Output: {"path": "records/linux/how-to.md", "title": "How To", "tags": ["linux", "hw"], …}

# Show the records dir
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

### 3. VSCode Plugin

Package once and install permanently (VS Code and VSCodium):

```bash
cd vscode
npm install && npm run package
codium --install-extension records-chat-0.5.0.vsix   # or: code --install-extension …
```

Reload the editor and click the birdhouse icon in the activity bar (or `Ctrl/Cmd+Shift+R`,
`Ctrl/Cmd+Shift+\` — `Ctrl+|` on a US layout — or "Records: Open Chat" in the palette; all
focus the chat input). For development, F5 from `vscode/` still launches an Extension Dev
Host instead.

In the chat view, type:

```
/all #linux How To
hello world
/esc
/stick how-to
/gcp docs: update
```

### 4. Neovim Plugin

Install via your package manager (e.g. `lazy.nvim`), then:

```vim
:Records
/all #linux How To
hello world
/esc
```

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
| `/werden` | `/werden [structure \| --stamp]` | Advance the development cycle (`CURRENT` + doc markers). |

The AI-only skills (`/poet`, `/pirate`, `/eq`, `/bff`, `/spellcorrect`, `/diff-*`, `/review`, `/phil-gc`) remain in `.ai/skills/` and are available in Claude Code.

## Honest Degradations

- **No AI `/record`**: falls back to `/all` (user-only). Two-sided recording returns when Ollama is configured.
- **No AI commit message**: the plugins prompt you for `-m "message"` instead of auto-authoring one.

## Ollama (Optional)

When you have a local LLM running:

```bash
ollama pull mistral
# Then configure the VSCode extension:
# Settings → records.ollamaEndpoint → http://localhost:11434
#          → records.ollamaModel    → mistral:latest
```

`/record` becomes two-sided (user msg → model → reply + signature), with multi-turn context
per recording session, via `records ollama-reply` (Neovim wiring pending). Workspace files
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

## Development

### Engine tests

```bash
cd python && python -m pytest -q
# 102 tests, ~0.3s
```

### VSCode

```bash
cd vscode
npm install
npm run compile  # or: npm run watch
F5               # Launch Extension Dev Host
npm run package  # Build the installable .vsix (then codium/code --install-extension)
```

### Neovim

No build step — copy the plugin to your runtimepath or manage with a package manager.

## Conventions

- **Frontmatter output** byte-matches the `.ai/skills/` records (ordering, omitted `tags:` when no tags, `draft:` placement).
- **Records dir discovery** mirrors the skills exactly (shallowest `hugo.yaml`, then `records/` → `docs/records/` → other fallbacks).
- **Tag routing** identical: `#tags` → `records/first-tag/`.
- **Cross-platform**: uses `pathlib` (Python), Lua I/O (Neovim), Node.js child_process (VSCode).
- **No git hooks or side effects** — the plugins are purely mechanical; they don't touch `.git` or trigger deployments on their own.

## Files

- `python/.gitignore` — Python bytecode, test cache, build output
- `vscode/.gitignore` — Node modules, compiled output, extension package
- `neovim/.gitignore` — Neovim runtime cache (doc/tags)
- Root `.gitignore` — added VSCode and Neovim artifacts, not picked up by the subproject ignores

## Next Steps

- **Test both plugins** against the real blyant records site (create a record, append, feature, commit).
- **Wire Ollama in Neovim** (the CLI's `ollama-reply` does the HTTP work; VSCode is done) and add the voice skills as system-prompt presets.
- **Expand to other editors** (Emacs, Vim, etc.) — the CLI is editor-agnostic, so the pattern is straightforward.
- **Package and ship** — make the engine installable via PyPI/Homebrew/Cargo, plugins via official registries.
