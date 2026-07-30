---
title: Home is where the clone is
date: 2026-07-30T14:05:11+02:00
tags: [developers]
---

## Human

I live inside other projects most days. When something worth keeping happens
there, I don't want to leave — I want the record to find its own way home.
Can the recording skills follow me?

## Assistant

They already do. Clone your fork inside the project — anywhere, under any
name:

```bash
git clone https://codeberg.org/<you>/records.git
echo records/ >> .gitignore   # or track it as a submodule
```

The skills never ask where they are; they look. Invoked from your project's
workspace, they find the shallowest `tools/hugo/hugo.yaml` beneath your feet
and read its `contentDir` — one line, one source of truth, shared with Hugo
itself. The transcript lands in the clone's `records/`, timestamped, at home.

When the day is written, `/cpd` commits and pushes the clone — not the host
project — and the push publishes. The gitignore line keeps the two histories
apart. Nothing to configure: the clone carries its own address.

— claude-fable-5
