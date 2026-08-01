---
title: booth — The booth
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, booth]
---

# 9 · booth — The booth

> A booth is small on purpose. You step in, something is captured, you step out.

Two booths, one road.

The **recording booth**: a room with a door and nothing else in it. Today writing a record means an
editor, a sidebar, a plugin, a model, a config. Sometimes you want a box you type into. `records
booth` is that box — stdlib `curses`, no model required, the whole ceremony reduced to a screen and
a prompt.

The **photo booth**: the strip of pictures you take out with you. `records card` turns one turn into
a single SVG you can post anywhere — drawn from your own site's palette, generated locally, no
service, no tracking pixel, no account.

Both are small. Both are about the moment of capture rather than the machinery around it.

## Dependencies

None. Both commands are additive.

Item 1 is the cheaper and more immediately useful of the two; item 2 is the more fun.

## Items

### 1 · flue — `records card`

A single turn, rendered as an image you can share.

- New `recordkit/card.py` behind `records card <record> [--turn N] [--out FILE]`.
- Output is **SVG**, hand-written from a template string. No rendering library, no font embedding
  headaches, no dependency — text, a border, the site's colours.
- Colours come from the site's own `params.style` (light palette), read through the existing
  `config.py` discovery, so a fork's card looks like a fork's site.
- Content: the turn text, the speaker label, the record's display title and date, and the record's
  URL. Signature lines are stripped, like everywhere else.
- Long turns need a rule — wrap to a width, truncate at a sensible line count with an ellipsis, and
  say so rather than silently cutting mid-sentence. Text metrics without a font library are
  approximate; use a monospace-ish assumption and accept it.
- `--turn N` selects; default is the first Human turn, which is usually the interesting one.
- PNG conversion is explicitly not our job. Anyone can convert an SVG; a converter would be a
  dependency.

**Files:** `recordkit/card.py`, `recordkit/cli.py`, `tests/test_card.py`.

**Acceptance:** a card generated from a real record, opened in a browser, with the palette matching
the built site.

**Border:** stdlib only, static output, no service. The card is a file.

### 2 · beetle — The curses booth

`records booth` — one box, one conversation.

- New `recordkit/booth.py` using stdlib `curses`. Terminals are everywhere and the dependency is
  zero.
- The whole flow, no configuration: open, type, submit a turn, keep typing, close. Escape ends the
  session, exactly like `/esc`.
- It creates and appends through `create.py` and `writer.py` — the same path the plugins use, so
  output is byte-identical. Nothing new is written to disk by this module itself.
- Show only what is needed: the record being written, the turn count, a hint line. Deliberately
  unremarkable.
- Handle the boring correctness: terminal resize, `SIGINT`, a records dir that cannot be found
  (fail with the message `records doctor` would give), UTF-8 input including the characters
  Norwegian and German actually use.
- No model. The booth works with nothing installed but Python.

**Files:** `recordkit/booth.py`, `recordkit/cli.py`, `tests/test_booth.py` (logic separated from
curses so it can be tested without a terminal).

**Acceptance:** a complete record written in the booth, byte-identical to the same content written
through `records new` + `records append`.

**Border:** no dependency. `curses` is stdlib; a TUI framework is not.

### 3 · cricket — The booth talks back

The optional half: the booth with Ollama behind it.

- `records booth --endpoint … --model …` routes each turn through the existing
  `ollama.reply` path — the same code the sidebar uses, no second implementation.
- Streaming, if [postkasse item 2](../postkasse/ROADMAP.md) has landed; a spinner and a wait if not.
- Failure behaviour is the project's standing rule: the human's words are appended regardless, with
  a visible warning. A dead model never costs a sentence.
- Without `--model`, the booth stays exactly as item 2 left it. The model is an addition, never a
  requirement.

**Acceptance:** a two-sided conversation written in the booth against a local Ollama, plus the same
session with Ollama stopped showing the user-only fallback.

### 4 · moth — Cards for the site

Once cards exist as files, the site can use them.

- Optional per-record Open Graph image, generated at build and referenced from the theme's `<head>`,
  so a shared link previews as the record's own words rather than nothing.
- This is theme work, which means it belongs in **Postkasse**, not Fuglekasse — see
  [kiste](../kiste/ROADMAP.md). If kiste has not landed, this item waits.
- Build integration goes through `bin/build.sh`, gated on a param, skipping cleanly when the CLI is
  absent — the same discipline the pandoc step already follows.

**Acceptance:** a record URL pasted into a link-preview tool showing its own card.

**Border:** Fuglekasse does not grow. This is a Postkasse feature.

## Borders for this road

- Stdlib only: `curses` for the booth, string templating for the SVG.
- Static output. A card is a file on disk; there is no card service, no share endpoint, no analytics.
- Byte-compatibility: anything the booth writes matches what the CLI and plugins write.
- The booth works with no model. Ollama is an addition to it, never a prerequisite.
