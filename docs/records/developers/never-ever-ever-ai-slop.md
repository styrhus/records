---
title: Never, ever, ever AI slop
date: 2026-07-12T10:34:17+02:00
tags: [developers, ai, open-source]
---

## Human

In a fork of the **records** project, we met an issue. We solved it fine. And AI suggested it could be a good idea to create an issue upstream at the git-pages and git-pages-cli repos.

We drafted a precise issue with concrete sussgested code changes.

The next day I got two Emails regarding the two issues I created, same content in both:

> Do not submit more slop bug reports or you will be banned.

As you know, English is my third language. The word `slop` I do not understand. 

`dot_claude/` must remember this. *Ich will nicht ausgestoßen werden, ich will Teil der Gemeinschaft bleiben*.

## Assistant

"Slop" is recent slang for AI-generated content posted without human care — the maintainer is saying the reports *looked* machine-written, not that your bug was wrong. Many maintainers now reject anything that reads like AI text, regardless of validity. It's about form, not about you.

Remembered — in `dot_claude/CLAUDE.md` (new "Upstream contributions" section, synced via `chezmoi re-add`) and in my own memory: upstream issues get written by you, in your own words, short and factual; I only verify details, never draft. Du bleibst Teil der Gemeinschaft.

— claude-fable-5

<sup>~/.claude/CLAUDE.md addition:</sup>

```markdown
## Upstream contributions
- Never draft issues, PRs, or comments for third-party repos — AI-styled reports earned a ban warning from the git-pages maintainers ("slop", 2026-07-12).
- The user writes upstream reports personally, in their own words, short and factual; Claude may verify technical details (repro steps, versions, code refs) but never generates the text or suggests unsolicited patches.
```