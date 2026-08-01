---
title: bikube — Reach
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, bikube]
---

# 3 · bikube — Reach

> The hive: a structure whose whole purpose is that things leave it and come back.

The engine works. Almost nobody can install it. Today `recordkit` is a directory in a cloned repo
and `records-chat` is a `.vsix` you sideload — which is fine for the person who wrote it and
useless for anyone else.

This road makes the engine reachable: `pipx install recordkit`, an extension in the registries, a
Neovim plugin the lazy way. Nothing here changes what the engine *does*.

## Dependencies

**postkasse should land first.** Shipping with known-open seams exports the debt to everyone who
installs. That is a preference, not a lock — an agent may take a bikube item early if the human says
so.

## Items

### 1 · flue — `pipx install recordkit`

`tools/others/python/pyproject.toml` already declares version `0.5.0` and a `records` entry point.
The gap is publication and the version story.

- Derive the package version from the repo-root `CURRENT` so PyPI speaks werden — a tiny
  `pyproject.toml` dynamic-version hook reading the one line, or a build step that stamps
  `recordkit/__init__.py`. Whichever, `__version__`, `pyproject.toml` and `CURRENT` must agree, and
  the check for that agreement is a test.
- Confirm the sdist and wheel contain what they should: `recordkit/` and nothing from `tools/`.
- Publish to TestPyPI first, install with `pipx` into a clean environment, run `records config` in a
  directory containing a records checkout.
- Then PyPI. Document the release steps in `tools/others/README.md`.

**Files:** `tools/others/python/pyproject.toml`, `recordkit/__init__.py`, `tools/others/python/tests/`,
`tools/others/README.md`.

**Acceptance:** `pipx install recordkit` in a clean container, followed by a real `records new` and
`records append` against a checkout, output pasted.

**Border:** zero runtime dependencies. `pyproject.toml` declares none and that stays true — a
version hook must not add one.

### 2 · beetle — Open VSX, then the Marketplace

Publisher `tb4` is already set in `tools/others/vscode/package.json`, and `npm run package` builds
the `.vsix`.

- **Open VSX first.** Codeberg-first is a habit, not an accident, and Open VSX is what VSCodium
  users actually query. Register the namespace, publish with `ovsx`.
- Then the Visual Studio Marketplace via `vsce publish`.
- The extension's README needs to stand alone on a registry page: what it is, that it needs the
  `records` CLI, how to get it (item 1), what Ollama adds and that it is optional.
- Add `.vscodeignore` discipline — `node_modules`, `out` sources and the accumulated `.vsix` files
  in the folder must not ship inside the package.
- Icon and gallery banner already live in `media/`.

**Files:** `tools/others/vscode/package.json`, `.vscodeignore`, `README.md`, `CHANGELOG.md`.

**Acceptance:** the extension installable by name from Open VSX in a clean VSCodium, connecting to a
`pipx`-installed CLI.

**Note:** four built `.vsix` files (0.2.0–0.5.0) sit in `tools/others/vscode/`. Decide whether they
are release artefacts worth keeping or clutter to gitignore; either is fine, drifting is not.

### 3 · cricket — `records.nvim` installable

`tools/others/neovim/lua/records/init.lua` is a working plugin in a repo that is not a plugin repo.

- Give it the layout lazy.nvim and packer expect: `lua/records/init.lua` at the root of something
  installable, plus `doc/records.txt` for `:help records`.
- Decide the distribution shape: a subdirectory spec (`{ dir = ... }`) documented for people who
  already cloned records, or a small mirror repo. Write down which and why.
- `M.setup(opts)` is the config surface — document every key, including `ollama_endpoint`.
- The plugin must degrade to mechanical-only when no model is configured, exactly like the sidebar.

**Files:** `tools/others/neovim/`, `tools/others/neovim/README.md`.

**Acceptance:** a lazy.nvim spec that installs the plugin in a clean Neovim config, `:Records`
opening, and a record created.

### 4 · moth — Emacs

Named because the README already promised it: the CLI is editor-agnostic, so the pattern is
straightforward.

- A small `records.el` — a buffer, a prompt, `call-process` to the `records` CLI, the same slash
  registry the other two plugins share.
- Mechanical commands first. Ollama afterwards, or never, at the implementer's discretion.
- MELPA is a nice-to-have, not the item.

**Files:** `tools/others/emacs/`.

**Acceptance:** a record created from Emacs against a real checkout.

**Border:** the same one every plugin obeys — no protocol logic in the editor. If Emacs needs
something the CLI cannot do, the CLI grows, not the plugin.

### 5 · tadpole — One install story, written once

Four install paths (pipx, Open VSX, lazy.nvim, Emacs) and one plugin architecture. Right now the
prose is spread across three READMEs and will drift the moment one of them ships.

- A single `docs/install.md` covering the CLI and each editor, linked from the root `README.md`.
- The plugin READMEs shrink to "what this plugin does" plus a link.
- Ollama's optionality stated in exactly one place.

**Acceptance:** a reader who has never seen the repo gets from zero to a written record by following
one page.

## Borders for this road

- No dependencies enter the engine to make packaging easier.
- Registries are distribution, not a service. Nothing here phones home, checks for updates, or
  collects anything.
- Version is derived from `CURRENT`; there is no second version number to maintain.
