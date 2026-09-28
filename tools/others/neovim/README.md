# records.nvim

A chat panel in Neovim for writing records — the Markdown files that become a
[Styrhus Records](https://codeberg.org/styrhus/records) site.

`:Records` opens a split at the bottom. Type `/all #linux How To` to start a recording, then plain
lines to append to it, `/esc` to stop. `/stick`, `/gc`, `/gcp`, `/cpd`, `/myname`, `/mucke`, `/airtime`
and `/config` do what they do everywhere else in this project.

The plugin holds no logic of its own: every command runs the `records` CLI. With `ollama_endpoint`
and `ollama_model` set, `/record` becomes a real two-sided turn — the CLI still owns the HTTP, the
plugin just shells out to it, asynchronously so the editor never blocks. `:help records` documents
every command and config key.

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
| `ollama_endpoint` | `nil` | Ollama base URL, e.g. `"http://localhost:11434"`. Unset (or empty) disables Ollama entirely — every command stays mechanical. |
| `ollama_model` | `nil` | Model tag for `ollama_endpoint`, e.g. `"qwen2.5-coder:latest"`. Required alongside `ollama_endpoint`; without it `/record` records user-only and says so. |
| `stream` | `false` | Token-by-token replies via `records ollama-reply/-chat --stream`. **Off by default** — that flag is not wired into the shared `cli.py` yet (see the postkasse road), so turning this on ahead of that lands makes every Ollama turn fail the same way an unreachable endpoint does: gracefully, with the human's words still appended user-only. |

With `ollama_endpoint` and `ollama_model` set, `/record` starts a two-sided turn: your line goes to
`records ollama-reply`, its reply is appended and signed, and the call runs in the background so
typing more never waits on the model. A failed or unreachable model degrades to exactly what `/all`
would have written — your words are appended, a warning explains why there's no reply, and nothing
is ever lost. Without an active recording, a plain message with a model configured becomes an
ephemeral chat via `records ollama-chat` instead — nothing is written to disk. `/esc` resets both
the recording and the ephemeral chat history.

Ollama is optional everywhere in this project. Nothing degrades because of that: every command
without a model configured stays mechanical, and its output byte-matches what the AI-driven skills
produce.

## The watch, from Neovim

`records watch` (see the hundehus road) is a separate long-running process; the plugin can start,
stop and report on one of its own, but never touches the underlying `recordkit/watch.py`:

- `:RecordsWatch` — start `records watch --json` in the background.
- `:RecordsWatchStop` — stop it.
- `:RecordsWatchStatus` — the last build's outcome, as a `vim.notify` line. Also available as
  `require("records").watch_status()` for a status line of your own.

The watcher itself decides what "ok" means and never commits, pushes or publishes — the plugin only
reads the JSON events it emits.
