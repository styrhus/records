---
title: postkasse — Seams
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, postkasse]
---

# 2 · postkasse — Seams

> The mailbox: the smallest structure that still receives something from the world.

Finish what's begun before carrying it further. Every item here is a seam left open when something
larger shipped — the VSCode side of Ollama landed and Neovim didn't, the engine got tests and
`stick.py` didn't, the voice skills stayed AI-only when they could be files.

Unfinished seams are debt that gets exported the moment the engine is packaged. That is why this
road matters more than its position suggests.

## Dependencies

None. Every item is self-contained and can be picked up cold.

Item 1 should land before item 2 — streaming is easier to add to two call sites that already exist
than to one that does and one that doesn't.

## Items

### 1 · flue — Ollama reaches Neovim

`recordkit/ollama.py` already does all the HTTP. The VSCode extension routes messages through
`records ollama-reply` and falls back to a user-only `append` when Ollama fails. Neovim does not
ask at all.

- In `tools/others/neovim/lua/records/init.lua`, `handle_slash` (line ~126) gains the same routing:
  when `ollama_endpoint` and a model are configured and a recording is active, shell out to
  `records ollama-reply --endpoint … --model … --file … --human …`.
- Mirror the VSCode failure behaviour exactly: on a non-zero exit, fall back to plain `append` and
  show a warning. A failed model must never lose the human's words.
- Mirror the session semantics too: endpoint and model captured when `/record` starts, reset on
  `/esc`.
- Without an active recording and with a model configured, route to `records ollama-chat` for an
  ephemeral turn — same as the sidebar.

**Files:** `tools/others/neovim/lua/records/init.lua`, `tools/others/neovim/README.md`.

**Acceptance:** a real `/record` turn in Neovim against a local Ollama, with the model's reply
appended to the record and signed; plus a turn with Ollama stopped, showing the user-only fallback.

**Border:** no HTTP in Lua. The plugin calls the CLI; the CLI owns the protocol.

### 2 · beetle — Replies learn to stream

Both plugins currently lock the input and wait. For a local model on modest hardware that is a long
silence.

- In `recordkit/ollama.py`, add a streaming path: `stream: true` in the request body, chunked reads
  over the existing stdlib `urllib` response, each JSON line yielded as it arrives.
- Surface it as an opt-in flag (`--stream`) so the existing non-streaming behaviour and its tests
  stay untouched. Streaming writes to stdout as it goes; the final append is unchanged.
- The record is still written once, at the end, through `writer.append_turn`. A half-written turn
  must never reach disk.
- On failure mid-stream, nothing is appended — same contract as today.
- Consume it in VSCode (webview message per chunk) and in Neovim (buffer append per chunk).

**Files:** `recordkit/ollama.py`, `recordkit/cli.py`, `tests/test_ollama.py`,
`tools/others/vscode/src/`, `tools/others/neovim/lua/records/init.lua`.

**Acceptance:** `python -m pytest tests/test_ollama.py` green with new streaming tests against a
mocked chunked response, plus a visible token-by-token reply in both plugins.

**Border:** stdlib only. No `requests`, no SSE library — `urllib` reads lines.

### 3 · cricket — Voice skills become presets

`/poet`, `/pirate`, `/eq`, `/bff`, `/werden`'s verse — the voices live as AI-only skills. Most of
them are a system prompt and nothing more, which means they can be files the engine reads.

- Add a preset directory (e.g. `tools/others/python/recordkit/presets/`) holding one plain-text
  system prompt per voice.
- `records ollama-reply` and `records ollama-chat` gain `--preset <name>`, injecting the file's
  contents as a system message — the same slot `build_context` already uses, composed alongside it.
- The skills in `.ai/skills/` that are purely a voice point at their preset file rather than
  restating the prompt, so the AI path and the local path speak identically.
- Voices that are not purely a system prompt stay AI-only, and the plan says which and why.

**Files:** `recordkit/presets/`, `recordkit/ollama.py`, `recordkit/cli.py`, `tests/test_ollama.py`,
the relevant `.ai/skills/*/SKILL.md`.

**Acceptance:** `records ollama-chat --preset pirate --human "hello"` returns a reply in voice, and
the preset file is the only place that voice is defined.

**Border:** deterministic files. No model in the engine, no prompt generated at runtime.

### 4 · moth — `/stick` becomes checkout-aware, and gets tests

`/record`, `/all`, `/me` and `/cpd` all discover the records dir by finding the shallowest
`*/hugo/hugo.yaml` and reading its `contentDir`. `/stick` alone is still `$PWD`-scoped, so it only
works from inside the records checkout.

- Point the skill at the same discovery `recordkit/config.py` already implements, so `/stick` works
  from a parent project's workspace like its siblings.
- Add `tools/others/python/tests/test_stick.py` — the module has none. Cover `find_record` (slugify
  round-trip, folder-aware `rglob`, the multiple-match case) and `feature_file` (adds
  `featured: true`, drops `draft:`, leaves the rest of the frontmatter byte-identical).
- Multiple matches must stay an explicit outcome, not a silent first-hit.

**Files:** `.ai/skills/stick/SKILL.md`, `recordkit/stick.py`, `tools/others/python/tests/test_stick.py`.

**Acceptance:** `cd tools/others/python && python -m pytest` green with the new file, and `/stick`
run from a parent directory featuring a record in the nested clone.

### 5 · tadpole — The plugins tested against the real site

`tools/others/README.md` has asked for this since it was written: exercise both plugins end to end
against a real blyant records checkout — create a record, append to it, feature it, commit it.

- Walk every mechanical command in both plugins: `/record`, `/all`, `/me`, `/esc`, `/stick`, `/gc`,
  `/gcp`, `/cpd`, `/myname`, `/mucke`, `/werden`.
- Note every rough edge, then fix the ones that are bugs and file the rest into this road's notes.
- Remove the "Next Steps" line from `tools/others/README.md` once it is true.

**Acceptance:** a walkthrough log of all eleven commands in each plugin, with outcomes.

**Border:** the walkthrough writes to a scratch clone, not to a published instance.

## Borders for this road

- The engine stays stdlib-only and model-optional; every mechanical command must keep working with
  no model configured.
- Mechanical output byte-matches AI output. An appended turn from Ollama and one from a skill are
  the same bytes.
- Nothing here grows the theme or the build.
