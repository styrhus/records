# Install

Everything here gets you from zero to a written record. The CLI first — every editor plugin needs
it — then whichever editor you use.

If you only want the site and none of the tooling, you don't need this page at all: a record is a
Markdown file in `records/`, and any text editor writes one.

## 1. The CLI

`recordkit` is the engine: it creates records with correct frontmatter, features them, commits,
publishes, and stamps the now-playing track. Pure Python, **no dependencies**, no model.

```bash
pipx install recordkit
```

`pip install recordkit` works too; `pipx` just keeps it out of your system Python. From a clone:

```bash
pipx install ./tools/others/python
```

Check it:

```bash
records --version
cd ~/path/to/your/records-checkout
records config          # {"records_dir": "…/records"}
```

`records config` is the honest test — it resolves the records directory the same way every plugin
does, by finding the shallowest `hugo.yaml` above you and reading its `contentDir`. If it answers,
everything else will work.

Write your first record without any editor plugin at all:

```bash
records new "#linux Fixing the printer"
records append --file records/linux/fixing-the-printer.md --text "It was the driver."
```

## 2. Your editor

Each plugin is a thin front end. None of them contains protocol logic — they all shell out to the CLI
above, so anything the CLI can do, they can do, and nothing else.

### VS Code / VSCodium

Install **Records Chat** from the registry:

- VSCodium and other Open VSX clients: search `Records Chat`, publisher `tb4`
- VS Code: search `Records Chat` in the Marketplace

Or from a built package: `codium --install-extension records-chat-<version>.vsix`.

Open it with the birdhouse icon in the activity bar, `Ctrl+Shift+R`, `Ctrl+Shift+\`, or
"Records: Open Chat". If `records` isn't on your PATH, set `records.binaryPath` to its full path.

Details: [tools/others/vscode/README.md](../tools/others/vscode/README.md).

### Neovim

The plugin lives inside this repo rather than in its own, so install it by path. With lazy.nvim:

```lua
{
  "records.nvim",
  dir = "~/path/to/records/tools/others/neovim",
  cmd = "Records",
  config = function()
    require("records").setup({ bin = "records" })
  end,
}
```

With packer, or by hand:

```bash
cp -r records/tools/others/neovim ~/.local/share/nvim/site/pack/manual/start/records
```

`:Records` opens the panel; `:help records` documents every command. `setup()` is optional.

Details: [tools/others/neovim/README.md](../tools/others/neovim/README.md).

### Emacs

```elisp
(add-to-list 'load-path "~/path/to/records/tools/others/emacs")
(require 'records)
```

`M-x records` opens the panel; `RET` prompts for a line.

Details: [tools/others/emacs/README.md](../tools/others/emacs/README.md).

### Claude Code, or any AI coding agent

The `.ai/skills/` directory holds the conversation skills (`/record`, `/all`, `/me`, `/stick`,
`/gc`, `/gcp`, `/cpd`, …). `.claude/skills/` symlinks into it, so a Claude Code session in this
checkout has them already. They write the same files the CLI does.

## 3. Using the panel

Identical in all three editors:

```
/all #linux How To      start a recording (creates the file)
hello world             plain text is appended as a Human turn
/esc                    stop recording
/stick how-to           feature it — pins it to the top of the index
/gcp docs: update       commit and push
```

| Command | Does |
|---|---|
| `/record [#tag] [title]` | Start recording — two-sided with Ollama, otherwise user-only |
| `/all [#tag] [title]` | Start a user-only recording |
| `/me [#tag] [title]` | Start a draft recording, kept off the site |
| `/esc` | Stop recording |
| `/stick <slug>` | Feature a record |
| `/gc`, `/gcp`, `/cpd` | Commit / commit + push / commit + push + deploy |
| `/myname <name>` | Save your name locally, for the `## Human (name)` headings |
| `/mucke` | Stamp the now-playing MPRIS track into the record |
| `/airtime` | Human vs Assistant token share of the record — in VS Code also of the memory-only chat |
| `/config` | Show the resolved records directory |

The first word of a title may be a `#tag`; the record is then filed under that tag's folder.

The CLI carries ten more commands that no editor panel exposes — `import`, `archive`, `verify`,
`export`, `attach`, `pack`, `card`, `booth`, `doctor` and `watch`. `records doctor` is the one to
run first if anything here misbehaves; it says what is wrong and what to do about it. They are all
listed in [the engine's README](../tools/others/README.md#the-engines-own-commands).

## 4. Ollama is optional

This is the only place that sentence needs to live.

Every command above is **mechanical**: deterministic, model-free, and byte-identical to what the AI
skills produce. Nothing requires a model, nothing phones home, nothing is sent anywhere.

A local [Ollama](https://ollama.com) endpoint adds one thing — `/record` becomes two-sided, so the
model's replies are recorded as `## Assistant` turns alongside yours:

```bash
ollama pull mistral
```

Then point the editor at it:

- **VS Code / VSCodium** — `records.ollamaEndpoint` (e.g. `http://localhost:11434`) and
  `records.ollamaModel` (e.g. `mistral:latest`); the gear (⚙) in the chat writes both.
- **Neovim, Emacs** — not wired yet. `/record` behaves like `/all` there.
- **Directly** — `records ollama-reply` and `records ollama-chat` do the HTTP; see
  [tools/others/ollama/README.md](../tools/others/ollama/README.md).

If Ollama is unreachable mid-recording, the turn is recorded user-only with a warning. Nothing is
lost, and no editor ever needs the model to keep working.

## 5. Publishing what you wrote

That is its own page: [docs/publish.md](publish.md) — Codeberg Pages by default, GitHub/GitLab Pages
via shipped shims, or `records publish` to any pages branch or webroot with no CI at all.
