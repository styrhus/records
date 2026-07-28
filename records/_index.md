---
title: Velkommen
date: 2026-07-05T01:30:00+02:00
---

This is your **blyant records** site. Every Markdown file in `records/` becomes a page;
this repository carries the machinery to write and publish them.

**blyant records** publishes straight from your editor, with helpers along the
way. They run in well-known AI agents — or with no model at all, and even
with your own local one; the
[README](https://codeberg.org/blyant/records) covers both.

No helpers required, though: write or drop `.md` files into `records/` by
hand and they publish just the same.

## The helpers

The essentials:

- `/record` — transcribe the conversation into a record until `/esc`; start with `#tags` (`/record #linux How to do it right`) to file it under `records/linux/`
- `/stick` — feature a record: pin it to the top and clear its draft flag
- `/cpd` — stage everything, commit, push — and the push publishes the site
- `/esc` — stop active modes; name one to stop only it

The full set lives in [`.ai/skills/`](https://codeberg.org/blyant/records/src/branch/main/.ai/skills) —
drafts-only recording, commit variants, diff summaries, spelling corrections, and a few voices.

## Publishing

[Fork this repository](https://codeberg.org/blyant/records), enable Actions in your fork's settings, then push to
`main`. Your site appears at `https://<your-user>.codeberg.page/<your-repo>/` — nothing to configure; the
owner and repository name are derived from the push itself.

The look is the <img src="fuglekasse.svg" width="20" height="20" alt="" style="vertical-align:-4px"> **Fuglekasse** theme;
its colors, greeting font and the tiny footer links all live in `hugo/hugo.yaml` — `repoURL` is the codeberg door.

> If you want a license link in the footer, add your own `records/LICENSE.md`. Its `title:` becomes the link text (defaults to "License").

When you have found your footing, rewrite this page — it is
`records/_index.md`, the front page itself.
