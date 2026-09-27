# recordkit

The AI-free engine behind [blyant records](https://codeberg.org/blyant/records) — a
publish-your-conversations site where every record is a Markdown file in your own repo.

`recordkit` is a stateless CLI that emits JSON. It creates records with correct Hugo frontmatter,
features them, commits, publishes the built site, and stamps the now-playing track — all
deterministically, with **no model involved and no runtime dependencies**. Output byte-matches what
the AI-driven skills produce.

```bash
pipx install recordkit
```

```bash
records config                        # the resolved records directory
records new "#linux #hw How To"       # create a record
records append --file <path> --text "…"
records stick <slug>                  # feature it
records commit --message "…" --push
records publish                       # build and deliver, no CI needed
```

An optional local [Ollama](https://ollama.com) endpoint makes `/record` two-sided
(`records ollama-reply`, `records ollama-chat`). It is optional in the strict sense: every mechanical
command works with no model configured at all.

Editor plugins for VS Code / VSCodium, Neovim and Emacs drive this same CLI — no protocol logic lives
in the editors.

**Full install guide, for the CLI and every editor:**
<https://codeberg.org/blyant/records/src/branch/main/docs/install.md>

AGPL-3.0-or-later licensed. Requires Python 3.9+.
