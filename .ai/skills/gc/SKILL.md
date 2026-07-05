---
name: gc
description: Stage all changes and create a git commit (no push)
disable-model-invocation: true
model: haiku
effort: low
allowed-tools:
  - Bash(git *)
  - Bash(.ai/skills/gc/detect-dirty-repos.sh)
argument-hint: "[optional commit intent]"
---

This skill was manually invoked by the user — this IS an explicit request to commit. Do not ask for confirmation. Just run the commands.

## Important: VSCode multi-root workspaces

In a VSCode window with multiple folders, dirty files may live in **more than one git repository** — not just the one at `$PWD`. The injection below asks the editor which folders are open (via the IDE lock file, falling back to a `.code-workspace` file) and prints the status + diff of every dirty repo. **You must commit every repo listed below**, not only the current one.

## Dirty repos — status and diff

!`.ai/skills/gc/detect-dirty-repos.sh`

## Steps

The diffs are already shown above — author the commit message(s) from them directly. Always write a concise conventional commit message (`feat`/`fix`/`chore`/`docs`/`refactor`/etc.) focused on "why". If `$ARGUMENTS` is provided, treat it as intent to fold into that style — not verbatim text. No Co-Authored-By lines.

Then commit **every** dirty repo in a **single Bash tool call**. Use `git -C <repo-path>` so you never `cd`; chain `add` and `commit` with `&&` within a repo, and separate repos with newlines so they run independently:

```
git -C <repoA> add -A && \
git -C <repoA> commit -m "msg A"
git -C <repoB> add -A && \
git -C <repoB> commit -m "msg B"
```

If only one repo is dirty, that's just the single two-command chain. If the injection above says `(no changes in any open repo)`, report that and stop.
