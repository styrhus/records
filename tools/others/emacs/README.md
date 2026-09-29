# records.el

A chat panel in Emacs for writing records — the Markdown files that become a
[Styrhus Records](https://codeberg.org/styrhus/records) site.

`M-x records` opens a window at the bottom. `RET` prompts for a line: `/all #linux How To` starts a
recording, plain text appends to it, `/esc` stops. `/stick`, `/gc`, `/gcp`, `/cpd`, `/myname`,
`/mucke`, `/airtime` and `/config` do what they do everywhere else in this project.

The package holds no logic of its own: every command runs the `records` CLI via `call-process` and
parses its JSON. **Mechanical only** — no model is involved, and none is needed.

## Install

See the one install page: [docs/install.md](../../../docs/install.md).

Short version, once `pipx install styrhus-records` has given you the CLI:

```elisp
(add-to-list 'load-path "~/path/to/records/tools/others/emacs")
(require 'records)
```

Or with `use-package`:

```elisp
(use-package records
  :load-path "~/path/to/records/tools/others/emacs"
  :commands (records records-send))
```

MELPA is a nice-to-have, not a requirement — the package is one file with no dependencies beyond
Emacs 27.1.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `records-bin` | `"records"` | The recordkit CLI to run; an absolute path if it isn't on `exec-path`. |
| `records-ollama-endpoint` | `nil` | Reserved. Two-sided `/record` in Emacs is not wired yet — `/record` behaves like `/all` here. |

`records-send` is the non-interactive entry point: `(records-send "/all #test Title")` handles a line
exactly as if it had been typed. That is what the acceptance check drives.
