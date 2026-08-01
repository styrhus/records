---
title: suitcase — Capture
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, suitcase]
---

# 4 · suitcase — Capture

> The suitcase: the structure you carry your life in when you leave somewhere.

This is the road nobody else walks.

Everyone's conversations are locked away in other people's apps. Some of those apps let you export —
a JSON blob, a SQLite file, a directory of JSONL — and then you have a file nobody will ever read.
`records import` turns that file into records: Markdown, in your repo, on your site, in your books.

An imported record must be indistinguishable from one you wrote. Same frontmatter, same `## Human` /
`## Assistant` turns, same signature lines. If a diff can tell them apart, the importer is wrong.

## Dependencies

**bikube first, ideally.** `records import` should arrive inside an installable tool, not a cloned
repo — the people with a decade of conversations to rescue are not going to `git clone` for it.

Item 1 gates 2, 3 and 4: every source parser emits through the same core.

## Items

### 1 · flue — The importer core

A new `recordkit/importer.py` behind a `records import` subcommand, with the source parsers kept
strictly separate from the emitting.

- Define one internal shape: a conversation is a title, a timestamp, and an ordered list of
  `(role, text, model?)` turns. Every parser produces this and nothing else.
- Emit through the existing `frontmatter.py` and `writer.py` — no new writing path. This is what
  guarantees byte-compatibility with `records new` + `append-turn`.
- Filenames follow the existing convention: timestamp-named (`2026-07-06_23-22.md`) via
  `naming.py`, `date:` frontmatter authoritative for ordering.
- Tag routing reuses what `/record #tag Title` already does — an imported conversation can land in
  `records/<tag>/`.
- Collisions: importing twice must not duplicate. Decide the identity rule (source id in
  frontmatter is the obvious one), implement it, and make `--dry-run` show what would land.
- `records import --source <name> --path <file>` with the source registry open for the next three
  items.

**Files:** `recordkit/importer.py`, `recordkit/cli.py`, `tests/test_importer.py`.

**Acceptance:** a synthetic conversation imported, and its file byte-identical to the same
conversation built with `records new` + `records append-turn`. Show the `diff` returning nothing.

**Border:** stdlib only — `json`, `sqlite3`, `pathlib`, nothing else.

### 2 · beetle — Claude Code session transcripts

JSONL session files, one JSON object per line, with tool calls and system events interleaved among
the human and assistant text.

- Parse the JSONL, keep the human and assistant text turns, drop tool-call machinery and system
  events. A record is a conversation, not a trace.
- Long tool-heavy sessions produce sparse records — that is correct, not a bug.
- The model name goes into the assistant signature line so imported turns are signed like written
  ones.
- Session timestamp becomes `date:`; the first human message is a reasonable title fallback.
- Decide what happens to code blocks inside turns — they are already Markdown, so most likely
  nothing, but confirm against Goldmark `unsafe: true` rendering.

**Files:** `recordkit/importer.py` (source module or function), `tests/test_importer.py`, fixtures.

**Acceptance:** a real session transcript imported and rendered by `hugo` without warnings, with the
turns reading as a conversation.

### 3 · cricket — ChatGPT and Claude export JSON

The two big vendor exports. Both are a single JSON file containing every conversation.

- ChatGPT's export is a tree with a `mapping` of nodes and a current-leaf pointer; the linear
  conversation is the path from the leaf to the root, reversed. Branches exist. Decide the rule —
  the current leaf's path is the honest default — and document it.
- Claude's export is flatter; confirm the shape against a real file before writing the parser.
- Both produce many conversations from one file: `records import` must handle a batch, with
  `--dry-run` listing what it would write.
- Attachments and images in exports: the destination is decided —
  [schrank item 3](../schrank/ROADMAP.md) puts them in a leaf page bundle beside the record. If that
  road has landed, write them there; if not, note their presence in the record and leave the files.

**Acceptance:** an export file with at least twenty conversations imported into a scratch records
dir, all rendering, no duplicates on a second run.

**Border:** parse defensively. Vendor formats change without notice; a shape mismatch must produce a
clear error naming the field, not a traceback.

### 4 · moth — `llm` SQLite logs

Simon Willison's `llm` keeps its history in SQLite, which makes it the easiest source and a good
regression test for the core.

- Read with stdlib `sqlite3`, read-only (`file:…?mode=ro` URI). Never write to the user's log.
- Conversations group by the conversation id; prompt and response become the turn pair.
- The model name is in the row — signature lines come free.

**Acceptance:** an `llm` log imported, conversation count matching a `SELECT` against the same file.

### 5 · tadpole — Import from a directory of Markdown

The unglamorous case that will be asked for most: someone already has notes, or an old blog, or a
folder of exported chats in some other Markdown flavour.

- `--source markdown --path <dir>` walking a tree, mapping files to records.
- Frontmatter passthrough where it exists and maps cleanly; `date:` from existing frontmatter, else
  file mtime, else the filename.
- Turn detection is best-effort and must be honest about it: if a file has no `## Human` /
  `## Assistant` structure, it becomes a single-body record rather than a guessed conversation.

**Acceptance:** a directory of mixed Markdown imported, with a summary reporting how each file was
classified.

## Borders for this road

- Imported output byte-matches created output. This is the one non-negotiable.
- No network. Every source is a file the user already has on disk — the importer never logs into
  anything, never calls an API, never scrapes.
- No dependencies. If a format needs a library to parse, it does not get imported.
- The user's source files are read-only. Always.
