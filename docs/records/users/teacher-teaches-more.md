---
title: Teacher teaches more
date: 2026-07-08
tags: ["user", "how-to", "git"]
---

## Human

I just merged from upstream. Magic.

But why isn't my own `records/_index.md` overwritten by such a merge?

I want to learn.

```
> git merge upstream/main main
Merge made by the 'ort' strategy.
 hugo/themes/Fuglekasse/layouts/baseof.html | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

---

## Assistant

Good question — and the answer is more interesting than "git was nice to your file."
I inspected the actual repo before answering.

### Investigation (real facts from the repo)

Merge commit `2eae758` had two parents:
- `HEAD^1` = `537e939` (your old `main`)
- `HEAD^2` = `2117e23` (upstream/main)

Merge base (common ancestor): `5c53a89`

What upstream actually changed since the merge base:

```
 hugo/themes/Fuglekasse/layouts/baseof.html | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

`git diff --stat <base> upstream -- records/_index.md` was **empty** → upstream made no
change to that file since you diverged.

The three blob hashes of `records/_index.md`:

| Version | blob hash |
|---|---|
| merge base (ancestor) | `038fb95` |
| upstream/main | `038fb95` ← identical to base |
| your main | `6dd8864` ← you changed it |

### The wrong mental model

You're picturing merge as *"copy upstream's files over mine, and something protected my
file."* That's not how git works. **Merge never overwrites files. It combines *changes*.**

### What merge actually does: three-way comparison

For every file, git looks at **three versions**:

1. The merge base — the common ancestor where you and upstream last agreed (`5c53a89`)
2. Your version (`HEAD`, your `main`)
3. Their version (`upstream/main`)

Then per file it asks: *what did each side change since the base?* and combines those
changes. Only one side changed a file → take that side. Both changed the same lines →
conflict. Nobody changed it → leave it alone.

### Your file, by the numbers

- Upstream never touched this file. Their version equals the base version
  (`038fb95` = `038fb95`). Since the base, upstream's "change" is *nothing*.
- You changed it since the base (`038fb95` → `6dd8864`).

So git's logic: *base and upstream agree, only your side differs → your side is the only
change → keep it.* Nothing from upstream to bring in, so nothing to overwrite. That's also
why the merge summary listed only `baseof.html` — the single file upstream *did* change.

### The important nuance

Upstream **does have** a `records/_index.md` — a *different* one (`038fb95` vs your
`6dd8864`). Naive "copy their tree over mine" would have clobbered yours. Three-way merge
didn't, because it saw upstream made no *change* there relative to the shared history.

### When your file *would* have been affected

- Upstream edits a different part of the file than you did → git merges both hunks
  automatically.
- Upstream edits the same lines you did → **conflict**; git stops and asks you to resolve.
- You had never touched it and upstream changed it → you'd get upstream's version (the only
  case that looks like "overwrite").

**Mental model to keep: git merges diffs against a common ancestor, not files against
files.** Your `_index.md` survived because, measured against that ancestor, only *you* had
a change to make.
