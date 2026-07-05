---
title: Welcome
date: 2026-07-05T01:30:00+02:00
featured: true
---

This is your records site. Every Markdown file in `records/` becomes a page;
this repository carries the machinery to write and publish them.

## The skills

Nine Claude Code skills live in `.ai/skills/` (`.claude/skills` points there):

- `/record` — transcribe the whole conversation into a record until `/esc`
- `/all` — like `/record`, but keeps only your (the human's) messages
- `/me` — like `/all`, but as a draft, kept out of the published site
- `/stick` — feature a record: pin it to the top and clear its draft flag
- `/esc` — stop active modes (record / all / me / poet)
- `/gc` — stage everything and commit
- `/gcp` — stage everything, commit, and push
- `/review` — review uncommitted changes and flag risks
- `/poet` — every reply becomes short poetic prose until `/esc`

## Publishing

If you forked the whole repository, make this branch your `main` first:
`git push origin +ready-to-fork:main`. Enable Actions in your repository
settings, then push to `main`.
`.forgejo/workflows/pages.yml` builds the site and publishes it at
`https://<your-user>.codeberg.page/<your-repo>/` — nothing to configure; the
owner and repository name are derived from the push itself.

The upstream CC BY-SA license record was not carried over: these records are
yours. If you want a license link in the footer, add your own
`records/LICENSE.md` with `title: License`.

When you have found your footing, delete this record.
