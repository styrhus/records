---
name: cpd
description: Show the diff for confirmation, then stage, commit, push, and deploy
disable-model-invocation: true
model: haiku
effort: low
allowed-tools:
  - Bash(git *)
  - Bash(find *)
  - Bash(ls *)
  - Bash(make deploy)
  - Bash(./deploy.sh)
argument-hint: "[optional commit intent]"
---

Before running anything, present the diff to the user (summarized, with the proposed commit message) and ask for confirmation. Only proceed with the steps after the user confirms.

## Records checkout

!`find . -maxdepth 5 \( -path '*/.*' -o -path '*/node_modules' \) -prune -o -path '*/hugo/hugo.yaml' -print -exec grep -E '^contentDir:|^[[:space:]]*deployCommand:' {} \; 2>/dev/null; true`

The repository to commit, `<repo>`, is the one holding the `hugo/hugo.yaml` above — the parent of its `hugo/` dir, or the grandparent when that parent is named `tools/` (several matches → the shallowest path wins; no match → `$PWD`). If `<repo>` is not `.`, the status and diff below show the wrong repository: run `git -C <repo> status --short` and `git -C <repo> diff HEAD` and present those instead.

## Status and diff

!`git status --short; git diff HEAD`

## Steps

1. **Commit + push.** Author the commit message from the diff directly. Always write a concise conventional commit message (`feat`/`fix`/`chore`/`docs`/`refactor`/etc.) focused on "why". If `$ARGUMENTS` is provided, treat it as intent to fold into that style — not verbatim text. No Co-Authored-By lines.

   Run it as a single chain:

   ```
   git -C <repo> add -A && git -C <repo> commit -m "msg" && git -C <repo> push
   ```

   If the status is empty, skip the commit but still push if the branch is ahead, then deploy.

2. **Deploy.** Determine the method, in this order:
   - a `deployCommand` line is shown under Records checkout above → run that command from `<repo>`
   - otherwise, if `ls` finds a workflow file in `<repo>/.forgejo/workflows/` or `<repo>/.github/workflows/`, or `<repo>/.gitlab-ci.yml` exists → nothing to run — the push in step 1 already triggered the deploy; report that the workflow is publishing the site.
   - neither → report that no deploy method was found and stop; do not invent a deploy command. (`deployCommand` under `params:` in `tools/hugo/hugo.yaml` sets one — `deployCommand: records publish` with a configured `publishTarget` is the no-CI path. Write it as `records publish --yes`: cpd runs the deploy command with its output captured, so `publish`'s force-push confirmation has no terminal to ask on and refuses, and the deploy reports success while publishing nothing.)

   Run the deploy **after** commit + push succeeds. Report the deploy output.
