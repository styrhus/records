# Record from your phone

A record is a Markdown file in `records/`. Committing it publishes it. That is
the whole architecture, and it means your phone already has everything it
needs — a browser, or a git client. Nothing here is a workaround; it is the
same path your laptop takes.

## The whole trick

Push a file into `records/` on `main` and the site rebuilds. The shipped
workflows watch that folder, so a commit made from a phone triggers exactly
the same build as one made from a terminal — no separate mobile path exists,
because none is needed.

What a phone does not get is the tooling around the file: the skills, the
signatures, the local model. See [what does not work](#what-does-not-work).

## The forge web editor

The shortest route, and it needs nothing installed.

1. Open your repo on Codeberg (or any Forgejo/Gitea, GitHub, GitLab).
2. Go to `records/`, then **New file**.
3. Type a filename, paste the block below, write underneath it, **Commit**.

```yaml
---
title: A walk in the rain
date: 2026-08-01T16:20:00
---
```

Then a blank line, then your words. Push done, CI builds, the record is live.

## You do not have to type a timestamp

Records are conventionally named `2026-08-01_16-20.md`, which is miserable to
thumb-type. You can skip it: `date:` in the frontmatter is what decides a
record's position, and the filename timestamp is only a fallback for records
that have no `date:` field.

So name the file anything readable — `walk-in-the-rain.md` — and let `date:`
do the ordering. The `+01:00` offset is optional: `timeZone` in
`tools/hugo/hugo.yaml` interprets a bare local time, so `2026-08-01T16:20:00`
is enough. `date: 2026-08-01` works too, when the day is precision enough.

One catch worth the ten seconds it saves you: **seconds are not optional**.
`2026-08-01T16:20` fails the build with *"the date front matter field is not
a parsable date"*. Write `:00` on the end, or drop the time entirely.

## Tags are folders

The CLI files a record under its first tag. In a web editor you do it by
typing the path — a `/` in the filename field creates the folder:

```
records/linux/walk-in-the-rain.md
```

Tags in frontmatter are separate, and are what actually shows on the page:

```yaml
tags: [linux, hw]
```

Other flags worth knowing on a small screen: `draft: true` keeps a record off
the site until you remove it.

## Speak it instead

Your keyboard already has a microphone. Tap it, talk, and the words arrive as
text — in the web editor, in a git client, anywhere you can type. Then mark the
record for what it is:

```yaml
voiceRecorded: true
```

That puts a microphone beside every Human heading, on the site and in the PDF
and EPUB alike. It means *this was spoken*; it does not mean a machine wrote it
down, and this project ships no transcriber — your phone did the listening, at
your asking, before any of our code saw the text. The reasoning is in
[the argument against building it](records/developers/roadmap/akvarium/voice.md).

## A git client

Your fork is an ordinary git repo, so any Android client that can commit and
push will do. The known-good route is [Termux](https://termux.dev/):

```bash
pkg install git
git clone https://codeberg.org/you/records.git
cd records && nano records/walk-in-the-rain.md
git commit -am "record" && git push
```

Authenticate over HTTPS with a forge access token rather than a password —
generate one in your forge settings, scoped to repository write.

## What does not work

- **The skills** — `/record`, `/all`, `/me`, `/stick`, `/cpd` and the rest are
  editor plugins for Claude Code, VSCode and Neovim. There is no phone build,
  and there is no plan for one.
- **Signature lines** — `— model-name` under an Assistant turn is written by
  the engine. On a phone you type it yourself or leave it out.
- **Ollama** — the engine talks to a local model on your machine. Your phone
  is not running one, and it will not reach across the internet to yours.
- **`records publish`** — bash plus Hugo. Publish from CI instead; on a phone
  the push *is* the deploy.
- **Previews** — no local Hugo means no `hugo server`. Commit and look at the
  site.

## An app, if you want one

`tools/pwa/` is a small page that composes a record and commits it through
your forge's API, so you get a text box instead of a file editor. It is
off by default — set `phoneApp` in `tools/hugo/hugo.yaml` to ship it with
your site, and read [the phone app](app.md) before you do, because it holds
an access token in your browser.

The web editor above needs none of that, and will outlive it.
