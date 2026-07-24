---
title: Velkommen
date: 2026-07-05T01:30:00+02:00
---

This is your **records** site. Every Markdown file in `records/` becomes a page;
this repository carries the machinery to write and publish them.

**records** focuses on publishing straight from your editor, with useful
helpers. They run in well-known AI agents, or without one: a small
[engine](https://codeberg.org/tb4/records/src/branch/main/others) drives
the mechanical helpers from a VSCode chat sidebar, a Neovim split, or a
plain `records` CLI — no model needed. Plug in
[Ollama](https://codeberg.org/tb4/records/src/branch/main/others/ollama)
and `/record` talks back with your own local model.

No helpers required, though: write or drop `.md` files into `records/` by
hand and they publish just the same.

## The helpers

The essentials:

- `/record` — transcribe the conversation into a record until `/esc`; start with `#tags` (`/record #linux How to do it right`) to file it under `records/linux/`
- `/stick` — feature a record: pin it to the top and clear its draft flag
- `/cpd` — stage everything, commit, push — and the push publishes the site
- `/esc` — stop active modes; name one to stop only it

Twenty skills live in [`.ai/skills/`](https://codeberg.org/tb4/records/src/branch/main/.ai/skills) —
drafts-only recording, commit variants, diff summaries, spelling corrections, and a few voices.



## Publishing

[Fork this repository](https://codeberg.org/tb4/records), enable Actions in your fork's settings, then push to
`main`. Your site will be on `https://<your-user>.codeberg.page/<your-repo>/` — nothing to configure; the
owner and repository name are derived from the push itself.

The tiny footer link comes from `hugo/hugo.yaml` params: `repoURL` is the
codeberg door. The look is the <img src="fuglekasse.svg" width="20" height="20" alt="" style="vertical-align:-4px"> **Fuglekasse** theme; its colors and greeting
font live in that same `hugo/hugo.yaml`.

> If you want a license link in the footer, add your own `records/LICENSE.md`. Its `title:` becomes the link text (defaults to "License").

When you have found your footing, rewrite this page — it is
`records/_index.md`, the front page itself.
