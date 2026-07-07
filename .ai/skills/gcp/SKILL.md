---
name: gcp
description: Stage all changes, commit, and push
disable-model-invocation: true
model: haiku
effort: low
allowed-tools:
  - Bash(git *)
argument-hint: "[optional commit intent]"
---

This skill was manually invoked by the user — this IS an explicit request to commit and push. Do not ask for confirmation. Just run the commands. Everything happens in the one repository at `$PWD`.

## Status and diff

!`git status --short; git diff HEAD`

## Steps

The diff is already shown above — author the commit message from it directly. Always write a concise conventional commit message (`feat`/`fix`/`chore`/`docs`/`refactor`/etc.) focused on "why". If `$ARGUMENTS` is provided, treat it as intent to fold into that style — not verbatim text. No Co-Authored-By lines.

Then commit and push in a single chain:

```
git add -A && git commit -m "msg" && git push
```

If the status above shows no changes, report that; still push if the branch is ahead of the remote.

## Restrictions

- **Never create a PR.** This skill only commits and pushes. Stop after `git push` succeeds.
