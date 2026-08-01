---
title: suitcase — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, suitcase, status]
---

# 4 · suitcase — status

Road: **Capture** · [plan](ROADMAP.md) · [protocol](../README.md)

Four of five walked, 2026-08-01. Item 3 waits for real export files.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | The importer core (`recordkit/importer.py`) | done | opus, 2026-08-01 | `diff` of imported vs. created record returns nothing |
| 2 | beetle | Claude Code JSONL transcripts | done | opus, 2026-08-01 | real session imported, `hugo` builds warning-free |
| 3 | cricket | ChatGPT + Claude export JSON | blocked | — | 20+ conversations imported, idempotent on re-run |
| 4 | moth | `llm` SQLite logs | done | opus, 2026-08-01 | count matches a `SELECT` on the same file |
| 5 | tadpole | Directory of Markdown | done | opus, 2026-08-01 | classification summary per file |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue gates everything else.** Do not write a source parser before the core exists; the whole
  point is that parsers never touch the writing path.
- **Preferred after bikube** — `records import` should arrive inside an installable tool, not a
  cloned repo. Not a hard lock.
- **The idempotency rule, as built:** the frontmatter pair `source:` + `sourceId:`, written together
  and *only when the parser supplies an id*. Import scans the records dir for that pair and skips
  what it finds, so a second run writes nothing. A conversation without an id gets no identity keys
  and cannot be deduplicated — which is exactly what makes the synthetic acceptance case
  byte-identical to `records new` + `records append-turn`. Every real parser supplies one:
  session uuid, conversation id, path relative to the import root.
- **3 · cricket** needs real export files to confirm shapes. Vendor formats drift; do not write the
  parser from memory or from documentation alone. Blocked for that reason on 2026-08-01: no ChatGPT
  or Claude export exists on this machine. Unblock by dropping an export file in and re-reading the
  item — the core and the registry are ready for it (`sources.PARSERS`).
- Attachments and images in exports are deferred to [schrank](../schrank/ROADMAP.md). Note them in
  the record, do not invent a storage scheme here.

## What landed

`recordkit/importer.py` (the shape, `emit`, `imported_ids`, `run`) and `recordkit/sources.py`
(`claude-code`, `llm`, `markdown` + the `PARSERS` registry), with `tests/test_importer.py` and
`tests/test_sources.py`. Emitting goes through `create.new_record` and `writer.append_human` /
`append_assistant` only — no second writing path exists.

Deviations from the plan, all deliberate:

- **`cli.py` is untouched.** Parallel sessions were running, so the subparser is a ready-to-paste
  `TODO(cli)` block at the foot of `importer.py`. Until it is wired, `records import` is reachable
  as `importer.run(source, path, records_dir)`. Same reason `CLAUDE.local.md` and
  `tools/others/README.md` are unedited — see the handoff notes in the session report.
- **Date order for `markdown` is frontmatter → filename timestamp → mtime**, not the plan's
  frontmatter → mtime → filename: mtime always exists, so the filename branch would be dead code.
- **Parsers live in `sources.py`, tests in `tests/test_sources.py`** rather than all inside
  `importer.py` / `test_importer.py` — the plan's "source module or function", taken as a module.
- **An unstructured Markdown file becomes one human turn**, reported as `body` in the summary; only
  files with real `## Human`/`## Assistant` headings are read as conversations.

Found while verifying against real data, fixed here because imports walk straight into it:
`frontmatter.build` interpolated titles raw, so a title starting with a YAML indicator (`@`, `` ` ``,
`*`, `|`, `>`, `%`, `[`, `{`, quote) or holding `: ` **failed the Hugo build** — `Chapter 1:
Beginnings` was enough. `build` now quotes such scalars and `frontmatter.read` unquotes them.

Still open, and not this road's to fix: a title containing ` #` is read by YAML as a comment and
silently loses everything after it (`Title #b` renders as `Title`). Quoting it in `build` would
break `tools/pwa/fixtures.json`, the engine↔`record.js` byte contract, so the importer neutralises
` #` in parser-derived titles and the engine still writes it bare. Both sides of that contract need
the same fix — a note for whoever owns [akvarium](../akvarium/ROADMAP.md).

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
