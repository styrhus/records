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

## Pick the file

- `$ARGUMENTS` given → slugify it (lowercase, spaces → hyphens; append `.md` if missing),
  then locate it: `find records -name '<slug>.md'`. One match → use it. Several matches
  (same name in different folders) → list them and ask which; do not guess.
- Blank → the recording file currently active in this session (/record, /all or /me).
- No argument and no active recording → list all records (`find records -name '*.md'`) and ask which one; do not guess.
- File not found → say so and stop.

## Edit the frontmatter

1. Add `featured: true` if not already present.
2. Remove any `draft: true` line — featuring publishes.

Touch nothing else — not the title, not the date, not the body.

Confirm with one line: `Featured: <path>`
