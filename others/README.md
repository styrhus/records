# Records Without AI (`others/`)

This directory contains the **no-AI engine and plugins** for the Records site — letting you run the mechanical slash-commands without a model. Optionally add Ollama for the AI-driven skills.

## Architecture

```
others/
├── python/              # recordkit: stateless library + CLI (JSON I/O)
│   ├── recordkit/       # modules: config, naming, create, stick, commit, mucke, etc.
│   ├── tests/           # 30 unit tests (config discovery, frontmatter, slug, etc.)
│   ├── pyproject.toml   # pip-installable package
│   └── .gitignore       # __pycache__, .pytest_cache, build artifacts
├── vscode/              # Records Chat: VSCode webview panel
│   ├── src/             # extension.ts, panel.ts (TypeScript)
│   ├── package.json     # vsce scaffold
│   └── .gitignore       # node_modules, out/, *.vsix
├── neovim/              # records.nvim: Neovim Lua plugin
│   └── lua/records/     # :Records command, chat split
└── ollama/              # Integration guide (README only)
```

## Quick Start

### 1. Install the engine

```bash
cd python
pip install -e .
```

The `records` command is now available system-wide.

### 2. Try it (from the records repo)

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
```

### 3. VSCode Plugin

From VS Code, open this repo folder:

```
F5  →  Extension Dev Host  →  Cmd/Ctrl+Shift+R  →  "Records: Open Chat"
```

In the chat panel, type:

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

The AI-only skills (`/poet`, `/pirate`, `/eq`, `/bff`, `/spellcorrect`, `/diff-*`, `/review`, `/phil-gc`) remain in `.ai/skills/` and are available in Claude Code.

## Honest Degradations

- **No AI `/record`**: falls back to `/all` (user-only). Two-sided recording returns when Ollama is configured.
- **No AI commit message**: the plugins prompt you for `-m "message"` instead of auto-authoring one.

## Ollama (Optional)

When you have a local LLM running:

```bash
ollama pull mistral
# Then configure the plugins:
# VSCode Settings → records.ollamaEndpoint → http://localhost:11434
# Neovim config → setup({ ollama_endpoint = "http://localhost:11434" })
```

`/record` becomes two-sided (user msg → model → reply + signature). See `ollama/README.md` for details.

## Development

### Engine tests

```bash
cd python && python -m pytest -q
# 30 tests, ~0.1s
```

### VSCode

```bash
cd vscode
npm install
npm run compile  # or: npm run watch
F5  # Launch Extension Dev Host
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

- **Test both plugins** against the real records site (create a record, append, feature, commit).
- **Wire Ollama support** in the plugins (detect endpoint, POST to `/api/generate`, parse response, call `append-turn`).
- **Expand to other editors** (Emacs, Vim, etc.) — the CLI is editor-agnostic, so the pattern is straightforward.
- **Package and ship** — make the engine installable via PyPI/Homebrew/Cargo, plugins via official registries.
