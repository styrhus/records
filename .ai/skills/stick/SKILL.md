---
name: stick
description: Use when the user invokes /stick to feature a record — pins it at the top of the published site and clears its draft flag
disable-model-invocation: true
model: haiku
effort: low
argument-hint: "[optional record name]"
allowed-tools:
  - Bash(ls *)
  - Bash(find *)
  - Read
  - Edit
---

The user invoked /stick: mark one record as featured — stick it for all to see.

## Context

- Records-site configs with their contentDir, cwd and below (empty = none): !`find . -maxdepth 5 \( -path '*/.*' -o -path '*/node_modules' \) -prune -o -path '*/hugo/hugo.yaml' -print -exec grep -m1 '^contentDir:' {} \; 2>/dev/null; true`
- Existing docs-like dirs, cwd and one level down (empty = none): !`find . -mindepth 1 -maxdepth 2 -type d \( -name docs -o -name doc -o -name documentation -o -name notes -o -name records \) -not -path '*/.*' -not -path '*/node_modules/*' 2>/dev/null; true`

## Pick the records directory

Same priority order /record, /all, /me and /cpd use — resolve this once, then use `<records-dir>`
below instead of a bare `records`:

- a records-site config was found above → resolve its `contentDir` against the `hugo/` dir holding
  the config and use that path (e.g. `./notes/site/tools/hugo/hugo.yaml` + `contentDir: ../../records`
  → `notes/site/records/`); a match with no `contentDir:` line means `../records`; several matches →
  the shallowest path wins. Skip the rest.
- `records/` already exists at the root → use it (skip the rest)
- `docs/` exists at the root → use `docs/records/`
- another docs-like dir exists at the root (`doc/`, `documentation/`, `notes/`) → use `<that>/records/`
- a docs-like dir exists one level down (e.g. `packages/docs/`) → use `<that>/records/`; prefer a
  `docs` match over the other names, and if several match equally, pick the first shown above
- none exist → use `records/` at the project root

This makes /stick work from a parent project's workspace the same way its siblings do, not just from
inside the records checkout.

## Pick the file

- `$ARGUMENTS` given → slugify it (lowercase, spaces → hyphens; append `.md` if missing),
  then locate it: `find <records-dir> -name '<slug>.md'`. One match → use it. Several matches
  (same name in different folders) → list them and ask which; do not guess.
- Blank → the recording file currently active in this session (/record, /all or /me).
- No argument and no active recording → list all records (`find <records-dir> -name '*.md'`) and ask which one; do not guess.
- File not found → say so and stop.

## Edit the frontmatter

1. Add `featured: true` if not already present.
2. Remove any `draft: true` line — featuring publishes.

Touch nothing else — not the title, not the date, not the body.

Confirm with one line: `Featured: <path>`
