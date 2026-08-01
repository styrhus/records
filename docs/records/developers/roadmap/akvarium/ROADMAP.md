---
title: akvarium — Android
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, akvarium]
---

# 6 · akvarium — Android

> The aquarium: you can see everything and touch nothing. Writing through the glass.

A ladder, named but not solved. Each rung is genuinely harder than the last, and the road is honest
about that: rung one is a documentation task that could land tomorrow, rung three is a maybe that
may stay a maybe forever.

The saving grace is the architecture. A record is a Markdown file committed to a git repo. Phones
can already do that. Most of this road is discovering how little needs building.

## Dependencies

Item 1 depends on nothing and can be done today.

Item 2 wants bikube's install story to exist so the PWA has something to point at for the desktop
half, but it does not strictly require it.

## Items

### 1 · flue — The phone document

The rung that can land any day, because everything it describes already works.

- Walk the actual paths on a real Android phone and write down what happens:
  - The Forgejo / Codeberg web editor — create a file in `records/`, commit, watch CI publish.
  - A git client (Termux + git, or an app) — clone, write in any editor, commit, push.
  - Markdown editors that can commit, if any behave well.
- Filename convention on a phone: the timestamp name is tedious to type by hand. Say so, and give a
  copy-paste template with the frontmatter block.
- What does *not* work, stated plainly — no `/record` skills, no signature automation, no Ollama.
- Land it as `docs/phone.md`, linked from the root README.

**Acceptance:** a record written and published entirely from a phone, and the doc that describes how.

**Border:** documentation only. This item builds nothing.

### 2 · beetle — A small PWA

A single-page web app, served from the site itself, that commits a record through the forge API.

- Static: it ships in `static/` and is served by the same Pages host as the site. No backend.
- Auth is a forge access token, held in the browser's local storage and never leaving it. Say this
  clearly in the UI, because it is the whole trust model.
- Forge API differences are real — Forgejo/Gitea, GitHub and GitLab each have their own contents
  endpoint. Support Forgejo first (the canonical host), structure the code so the others are a
  small adapter, and do not pretend the others exist until they are tested.
- It writes exactly what the CLI writes: timestamp filename, the same frontmatter, `## Human` turns.
  Byte-compatibility is checked, not assumed.
- Offline: composing works offline, committing queues until there is a connection.

**Files:** `tools/hugo/static/` or a dedicated `tools/pwa/`, plus documentation.

**Acceptance:** a record composed on a phone, committed through the API, and published — with the
file byte-identical to one `records new` would produce.

**Border:** no backend, no accounts, no hosted anything. The PWA is a static file that talks to your
forge with your token.

### 3 · cricket — *Maybe* voice capture

Maybe means maybe.

The frontmatter flag `voiceRecorded: true` already exists and already renders a mic icon on every
Human heading, in the site, the PDF and the EPUB. What it means is: *this was spoken*. It does not
mean a machine transcribed it.

- If this rung is ever built, it captures audio and **marks** the record. It does not transcribe.
- Where the audio lives is the hard question, and it belongs to
  [schrank](../schrank/ROADMAP.md) — attachments are that road's problem, and this rung should not
  invent a second answer.
- The border in the roadmap is explicit and predates this file: **no voice-to-text engine.** A rung
  that transcribes is not this rung.

**Acceptance:** deliberately unspecified. If someone reaches this rung, the first deliverable is a
design note arguing why it should exist at all.

## Borders for this road

- No voice-to-text engine. Not ours, not bundled, not called.
- No backend, no accounts, no hosted service. The phone talks to your forge, or to nothing.
- Byte-compatibility with CLI output holds on every rung that writes a record.
- Honesty about rungs: this road ships documentation before it ships software, and says which is
  which.
