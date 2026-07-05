---
name: review
description: Review uncommitted changes and flag anything risky
disable-model-invocation: true
model: sonnet
allowed-tools: Bash(git *)
---

Review the current uncommitted changes:

!`git status`
!`git diff`
!`git diff --staged`

Summarize what's changing, assess quality, and flag any risks (security issues, breaking changes, logic errors, missing error handling).
