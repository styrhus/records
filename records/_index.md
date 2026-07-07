---
title: Velkommen
date: 2026-07-05T01:30:00+02:00
---

This is your **records** site. Every Markdown file in `records/` becomes a page;
this repository carries the machinery to write and publish them.

**records** primary focus is enabling publishing websites directly from a Editor (i.e. Codium) with useful AI helpers.

## The helpers

Nine AI skills live in `.ai/skills/`:

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

[Fork this repository](https://codeberg.org/tb4/records), enable Actions in your fork's settings, then push to
`main`. Your site will be on `https://<your-user>.codeberg.page/<your-repo>/` — nothing to configure; the
owner and repository name are derived from the push itself.

The tiny footer link comes from `hugo/hugo.yaml` params: `repoURL` is the
codeberg door. The look is the <img src="fuglekasse.svg" width="20" height="20" alt="" style="vertical-align:-4px"> **Fuglekasse** theme; its colors and greeting
font live in that same `hugo/hugo.yaml`.

> If you want a license link in the footer, add your own`records/LICENSE.md` with `title: License`.

When you have found your footing, rewrite this page — it is
`records/_index.md`, the front page itself.
