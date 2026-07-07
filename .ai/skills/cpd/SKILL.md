---
name: cpd
description: Show the diff for confirmation, then stage, commit, push, and deploy
disable-model-invocation: true
model: haiku
effort: low
allowed-tools:
  - Bash(git *)
  - Bash(.ai/skills/cpd/detect-deploy.sh)
  - Bash(make deploy)
  - Bash(./deploy.sh)
argument-hint: "[optional commit intent]"
---

Before running anything, present the diff below to the user (summarized, with the proposed commit message) and ask for confirmation. Only proceed with the steps after the user confirms. Everything happens in the one repository at `$PWD`.

## Status and diff

!`git status --short; git diff HEAD`

## Deploy method

!`.ai/skills/cpd/detect-deploy.sh`

## Steps

1. **Commit + push.** The diff is already shown above — author the commit message from it directly. Always write a concise conventional commit message (`feat`/`fix`/`chore`/`docs`/`refactor`/etc.) focused on "why". If `$ARGUMENTS` is provided, treat it as intent to fold into that style — not verbatim text. No Co-Authored-By lines.

   Run it as a single chain:

   ```
   git add -A && git commit -m "msg" && git push
   ```

   If the status above is empty, skip the commit but still push if the branch is ahead, then deploy.

2. **Deploy.** Run the command reported under "Deploy method" above, from `$PWD`:
   - `deploy: <command>` → run that command (set via `deployCommand` under `params:` in `hugo/hugo.yaml`)
   - `deploy: automatic on push (<workflow>)` → nothing to run — the push in step 1 already triggered the deploy; report that the workflow is publishing the site.
   - `(no deploy method found ...)` → report this and stop; do not invent a deploy command.

   Run the deploy **after** commit + push succeeds. Report the deploy output.
