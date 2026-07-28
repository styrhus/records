# records.nvim — Neovim Integration

A Lua plugin for the blyant records site's mechanical skills in Neovim.

## Installation

Using `lazy.nvim`:

```lua
{
  "blyant/records",
  dir = "~/path/to/records/others/neovim",
  config = function()
    require("records").setup({
      bin = "records",          -- path to recordkit CLI
      ollama_endpoint = nil,    -- optional Ollama for two-sided /record
    })
  end,
}
```

Or install manually:

```bash
git clone https://codeberg.org/blyant/records.git
mkdir -p ~/.config/nvim/pack/manual/start
cp -r records/others/neovim ~/.config/nvim/pack/manual/start/records
```

Then in your `init.lua`:

```lua
require("records").setup()
```

## Usage

Run `:Records` to open the chat split (bottom of the window). Inside:

- `/record [#tags title]` — create and transcribe a record
- `/all`, `/me` — user-only recording (`/me` marks as draft)
- `/stick [slug]` — feature a record
- `/gc`, `/gcp`, `/cpd` — commit / push / deploy (requires message)
- `/myname <name>` — save your name locally
- `/mucke` — stamp the now-playing MPRIS track
- `/config` — show the resolved records directory
- `/esc` — stop recording
- Type plain messages while recording to append them
- `q` to close the chat panel

## Ollama Integration (Future)

When `ollama_endpoint` is configured, `/record` becomes two-sided and voice skills become
system-prompt presets. See `../ollama/README.md`.
