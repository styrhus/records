---
title: akvarium — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, akvarium, status]
---

# 6 · akvarium — status

Road: **Android** · [plan](ROADMAP.md) · [protocol](../README.md)

Unwalked. A ladder — the rungs are not equal in size.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `docs/phone.md` — the paths that already work | open | — | a record written and published from a phone |
| 2 | beetle | Static PWA committing via forge API | open | — | phone-composed record byte-identical to `records new` |
| 3 | cricket | *Maybe* voice capture (marks, never transcribes) | open | — | a design note arguing it should exist |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue can land today.** It builds nothing — it walks the real paths on a real phone and
  writes down what happens. The cheapest useful item on any road.
- **2 · beetle**: Forgejo first, since that is the canonical host. GitHub and GitLab adapters only
  when actually tested — do not ship untested provider claims (that is the mistake
  [badstu item 2](../badstu/ROADMAP.md) exists to fix).
- **3 · cricket is a maybe, on purpose.** The first deliverable is an argument, not code. Audio
  storage belongs to [schrank](../schrank/ROADMAP.md); do not invent a second scheme here.
- The `voiceRecorded: true` flag already works end to end (site, PDF, EPUB). It marks. It does not
  transcribe, and nothing on this road changes that.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
