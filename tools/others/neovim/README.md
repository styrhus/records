# records.nvim

A chat panel in Neovim for writing records — the Markdown files that become a
[blyant records](https://codeberg.org/blyant/records) site.

`:Records` opens a split at the bottom. Type `/all #linux How To` to start a recording, then plain
lines to append to it, `/esc` to stop. `/stick`, `/gc`, `/gcp`, `/cpd`, `/myname`, `/mucke`, `/airtime`
and `/config` do what they do everywhere else in this project.

The plugin holds no logic of its own: every command runs the `records` CLI. **Mechanical only** — no
model is involved, and none is needed. `:help records` documents every command and config key.

## Install

See the one install page: [docs/install.md](../../../docs/install.md).

Short version — the plugin lives inside the records repo rather than in its own repo, so lazy.nvim
installs it by path:

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

`setup()` is optional — `:Records` works unconfigured.

### Why a subdirectory spec and not its own repo

A mirror repo would need syncing on every change, and nothing in this project syncs itself. One repo,
one source of truth, installed by path. The layout here is already the one a plugin repo needs
(`lua/`, `plugin/`, `doc/`), so a mirror stays easy to add later if the friction ever proves real.

## Configuration

| Key | Default | Meaning |
|---|---|---|
| `bin` | `"records"` | The recordkit CLI to run; an absolute path if it isn't on Neovim's PATH. |
| `ollama_endpoint` | `nil` | Reserved. Two-sided `/record` in Neovim is not wired yet — `/record` behaves like `/all` here. |

Ollama is optional everywhere in this project, and in Neovim it is not yet available at all. Nothing
degrades because of that: every command is mechanical, and its output byte-matches what the
AI-driven skills produce.
