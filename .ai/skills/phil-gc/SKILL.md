---
name: phil-gc
description: Stage all changes and create a git commit whose message is a short philosopher quote with signature (no push)
disable-model-invocation: true
model: haiku
effort: low
allowed-tools:
  - Bash(git *)
argument-hint: "[optional theme or philosopher]"
---

This skill was manually invoked by the user — this IS an explicit request to commit. Do not ask for confirmation. Just run the commands. Everything happens in the one repository at `$PWD`.

## Status and diff

!`git status --short; git diff HEAD`

## The commit message

Instead of a conventional-commit line, the message is a **short, real quote from a philosopher** that resonates with what the diff changes — followed by the philosopher's signature.

- Pick a genuine, attributed quote (real philosopher, real line). No invented quotes.
- Keep it short — one or two sentences. Precision over grandeur.
- Let the diff guide the choice: match the quote's theme to what actually changed. `$ARGUMENTS`, if given, is a theme or a preferred philosopher to lean toward.
- Format the message as the quote, a blank line, then `— Philosopher Name`:

```
The limits of my language mean the limits of my world.

— Ludwig Wittgenstein
```

No Co-Authored-By lines.

## Commit

Commit in a single chain:

```
git add -A && git commit -m "quote

— Philosopher Name"
```

If the status above shows no changes, report that and stop.
