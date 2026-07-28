---
name: werden
description: Advance the records werden cycle and stamp the new cycle name into the living docs. Use when the user runs /werden, wants to bump the cycle, start a new build structure, or refresh where-we-are-at markers across READMEs.
disable-model-invocation: true
model: haiku
effort: low
allowed-tools:
  - Bash(.ai/skills/werden/werden.sh*)
  - Read
  - Edit
argument-hint: "[new-structure-name | --stamp]"
---

This skill was invoked by the user — just do it, don't ask for confirmation.

`/werden` moves the project to the next **werden cycle** — the project is never a state, always a
becoming — and tells the docs where we now are. A cycle is named `<number> <structure>-<animal>`
(see [others/naming/README.md](others/naming/README.md)). The animal is the *minor* part; the
structure is the *major* part.

- **`/werden`** (no arg) → bump the animal one position up `dyr.json`, keep the structure.
- **`/werden <structure>`** → start a new structure (major step); the animal resets to `flue`.
- **`/werden --stamp`** → keep the current name; only re-derive the number and re-stamp the docs.
  Use it after you hand-edit the epoch in `CURRENT`, to propagate it without advancing the cycle.

The number is `<epoch>.<major>.<minor>` (e.g. `0.1.18 fuglekasse-spider`):

- **epoch** — the leading `0`, yours alone. Edit it directly in `CURRENT`; the script preserves it
  verbatim and never derives or bumps it. (A legacy name-only `CURRENT` reads as epoch `0`.)
- **major** — 1-based index of the structure in `strukturer.json` (`fuglekasse` = 1).
- **minor** — 1-based index of the animal in `dyr.json` (`flue` = 1, `spider` = 18).

The source of truth is `CURRENT` at the repo root (one line, `<number> <structure>-<animal>`). Docs
carry an invisible marker `<!-- werden: <number> <structure>-<animal> -->` that renders as nothing
in Markdown but is trivially greppable. The README alone wears the cycle in the open, as one small
line near the bottom (the script renames it):

```markdown
> Fase — <number> <structure>-<animal>
```

## Steps

1. Run the script — it computes the next name, writes `CURRENT`, rewrites every existing marker,
   and renames the README's `> Fase — …` line:

   ```
   .ai/skills/werden/werden.sh $ARGUMENTS
   ```

2. Read its output.
   - If it lists **markers updated** and found the **fase line**, everything is stamped — go report.
   - If it says **NONE FOUND**, this is the first run: seed the stamp so future runs propagate
     automatically. Add the exact line the script printed —
     `<!-- werden: <number> <new-name> -->` — as its own line **directly under the first `#` heading**
     (or, for files with `---` frontmatter, right after the closing `---`) in each living doc:
     - [others/README.md](others/README.md)
     - [hugo/themes/Fuglekasse/README.md](hugo/themes/Fuglekasse/README.md)
   - If it says **fase line: NOT FOUND**, seed the exact line it printed —
     `> Fase — <number> <new-name>` — near the bottom of [README.md](README.md).

3. Report concisely: the `old -> new` cycle line and the docs that now carry the stamp.

Do not commit — leave that to the user (`/gc`) unless they ask.

## Notes

- If the script errors with "already at the last animal", the structure is maxed out — the user
  must pass a new structure name (`/werden <structure>`) to start the next cycle.
- Keep edits marker-only. All other prose in the living docs stays untouched; the marker (and the
  README's fase line) is how "where we are at" is communicated, so a plain grep across the repo
  always reveals the current cycle.
- The AI-free mirror is `records werden` in `others/python/` — same bump/stamp mechanics.
