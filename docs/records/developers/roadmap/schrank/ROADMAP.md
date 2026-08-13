---
title: schrank — Preservation
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, schrank]
---

# 8 · schrank — Preservation

> The cupboard: where things wait without spoiling.

Every other road on this map is about reach — getting records out, onto a site, into a feed, onto a
phone. This road assumes the opposite. It assumes Hugo is gone, pandoc is gone, this repo is
abandoned, and the person opening the cupboard is you in twenty years or someone who inherited your
laptop.

What survives? Markdown files survive. Git history survives, if the repo does. Images referenced by
relative paths survive only if someone kept them. Nothing else here is guaranteed.

So: bundle it, checksum it, and make the plain-text fallback something a human can read with `cat`.

Preservation is the least exciting road and the one people are gladdest about later.

## Dependencies

None strictly. But **suitcase pairs naturally** — the moment someone imports a decade of
conversations, they want to know it is safe, and imported exports are exactly where attachments
first show up.

Item 1 gates item 2 (verify reads what archive writes).

## Items

### 1 · flue — `records archive`

One self-contained bundle holding everything needed to rebuild or simply to read.

- New `recordkit/archive.py` behind `records archive [--repo .] [--out FILE]`.
- Contents: the whole records tree, referenced images and attachments, the site `hugo.yaml`, the
  `CURRENT` cycle line, and a manifest.
- The manifest is the point: a JSON file listing every entry with size and SHA-256, the werden
  cycle, the source repo URL, the git commit, and a UTC timestamp. Written first, readable without
  unpacking.
- Include a plain `README.txt` at the bundle root, written for someone with no context: what this
  is, that the `.md` files are the content and are readable as-is, how the `## Human` /
  `## Assistant` structure works, and what the signature lines mean.
- `zipfile` and `hashlib`, both stdlib. Deterministic output — same input, same bytes, so archives
  can be diffed and deduplicated. That means fixed timestamps in the zip entries and sorted entry
  order.
- `--dry-run` lists what would go in, and what would be left out and why.

**Files:** `recordkit/archive.py`, `recordkit/cli.py`, `tests/test_archive.py`,
`tools/others/README.md`.

**Acceptance:** an archive of this repo's records, unpacked in an empty directory, with every
checksum verified and the `README.txt` read by someone who has not seen the project.

**Border:** stdlib only. No tar-with-compression-library, no external checksum tool.

### 2 · beetle — `records verify`

An archive nobody has ever opened is a hope, not a backup.

- `records verify <archive>` recomputes every checksum against the manifest and reports mismatches,
  missing entries and unexpected extras.
- `records verify --repo .` does the same against a live checkout: does every relative image
  reference in every record resolve to a file that exists?
- Broken-reference detection is the everyday value here. A record pointing at an image that was
  moved renders as a broken image on the site and a missing figure in the PDF, silently.
- Exit non-zero on any fault; `--json` for machines.

**Files:** `recordkit/archive.py` or `recordkit/verify.py`, `tests/`.

**Acceptance:** a deliberately corrupted archive rejected with the failing entry named, and a
checkout with one broken image reference reported.

### 3 · cricket — Attachments get a home

Nothing supports attachments today. `recordkit` copies no files; the VSCode `@` picker looks like
attachment support but is not — its picks become `--context-file`/`--context-dir`, model-only
context that `ollama.py` documents as *never written to the record*. An image has exactly one home
right now: hand-copied into repo-root `static/`, hand-linked.

**The convention is decided: Hugo leaf page bundles.** A record with attachments becomes a folder
holding `index.md` and its files:

```
records/2026-07-06_23-30/
├── index.md
├── image.png     →  /2026-07-06_23-30/image.png
├── paper.pdf     →  /2026-07-06_23-30/paper.pdf
└── clip.mp4      →  /2026-07-06_23-30/clip.mp4
```

Verified against the real config and theme on Hugo 0.164 before this was written down:

- **Any file type publishes verbatim** — png, pdf, mp4, jpg, bin — no processing, no config, no
  asset pipeline.
- **URLs do not change.** `:contentbasename` resolves a leaf bundle to its folder name, so
  `/2026-07-06_23-30/` is byte-identical to what the flat `.md` gives today.
- **Chapters survive** — a bundle inside `records/3/` still groups under `chapter-3`.
- **Tag folders survive** — the `cascade` (`kind: section` → `render: never`) never touches bundles;
  they are kind *page*.
- **Relative links pass through** — `record.html`'s forge rewrite only matches `records/`-prefixed
  links, so `![shot](image.png)` is left alone and resolves beside `index.html`.

The work is making the tooling agree:

- **`create.py` / `naming.py`** — a bundle mode writing `<slug>/index.md`. Flat records stay flat;
  a record only becomes a bundle when it has something to carry.
- **`stick.py`** — `find_record` rglobs `<slug>.md` and will miss `<slug>/index.md`. It also needs
  the folder name, not `index`, as the display slug.
- **`book.lua:293`** — `base = f.rel:match("([^/]+)%.md$")` yields `"index"` for a bundle, breaking
  the title, the slug and the filename-date fallback. Fall back to the parent folder name. Its
  `resolveLocal(src, recDir)` already resolves relative assets against the record directory, so
  bundle assets work in the PDF and EPUB for free once naming is fixed.
- **Size discipline** — git is a poor blob store. Document a threshold and what to do above it,
  honestly, including "don't".

Rendering is the other half and belongs to [kiste item 6](../kiste/ROADMAP.md) — in single and
single-flowing modes every record renders on `/`, where a relative `image.png` resolves to
`/image.png` and 404s. That is a theme fix, not an engine one.

Downstream: the importer's deferred attachments ([suitcase item 3](../suitcase/ROADMAP.md)) land
here, and audio — should [akvarium's](../akvarium/ROADMAP.md) third rung ever exist — uses this and
nothing else.

**Files:** `recordkit/create.py`, `recordkit/naming.py`, `recordkit/stick.py`,
 `tools/pandoc/book.lua`, `docs/`, `AGENTS.md`.

**Acceptance:** a record with an image, a PDF and a video rendering correctly on the site, in the
PDF and in the EPUB — plus an existing flat record left untouched and byte-identical.

**Border:** no git-annex, no LFS, no external store. If it does not fit in a git repo, the honest
answer is that it does not belong in one.

### 4 · moth — The plain-text export

The last resort, and the one that will still work.

- `records export --format text --out DIR` writing the whole corpus as one readable text tree, or
  optionally a single concatenated file.
- No Markdown syntax that needs rendering to make sense — headings become plain labelled turns,
  links keep their URL inline, images become `[image: path]`.
- Chronologically ordered, with a table of contents at the top of the single-file form.
- This is the format you hand to an archive, a lawyer, or a grandchild.

**Acceptance:** the whole records tree exported and read end to end in `less` without confusion.

### 5 · tadpole — Integrity over time

Small habits that turn the above into an actual practice.

- A `records archive --check` mode suitable for a cron job, reporting only on fault.
- Optional: record-level checksums in a sidecar manifest committed to the repo, so git itself
  notices silent corruption.
- Document a rotation suggestion — keep N archives, where to put them, why "one copy" is not a
  backup.

**Acceptance:** a documented practice someone could follow, plus the `--check` mode working from
cron.

### 6 · snail — `records attach`

The convention from item 3 is useless if putting a file into a record is a manual four-step dance.

- New `recordkit/attach.py` behind `records attach <record> <file>… [--title TEXT]`.
- It does the whole move: converts a flat record to a bundle if it is not one already (`<slug>.md`
  → `<slug>/index.md`, preserving bytes), copies the file in, and prints the Markdown link to paste
  — or appends it to the current turn.
- Filename hygiene: slugify, preserve the extension, never overwrite (reuse `naming.unique_path`).
- Refuses nothing by type. Photo, video, PDF, archive, whatever — the record is yours.
- `--dry-run` shows the conversion and the copy without doing either. Converting a record's shape is
  the kind of thing people want to see first.
- The plugins get it next: the VSCode `@` picker gains a *recorded* mode distinct from its existing
  model-context mode, so the two never get confused again. Drag-and-drop into the sidebar is the
  obvious follow-up and can be its own animal.

**Files:** `recordkit/attach.py`, `recordkit/cli.py`, `tests/test_attach.py`,
`tools/others/vscode/src/`, `tools/others/README.md`.

**Acceptance:** a flat record converted and given an image, a PDF and a video in one command, the
site rendering all three, and the record's URL unchanged from before the conversion.

**Border:** the file is copied, never moved. The user's source stays where it was.

## Borders for this road

- Stdlib only, as always: `zipfile`, `hashlib`, `json`.
- No external storage, no cloud, no service. An archive is a file you put somewhere yourself.
- Deterministic output. Archives that differ byte-wise for identical input cannot be diffed or
  deduplicated, which defeats half the purpose.
- The plain-text export must be readable with no tooling at all. If it needs this repo to make
  sense, it has failed.
