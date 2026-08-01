---
title: akvarium — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, akvarium, status]
---

# 6 · akvarium — status

Road: **Android** · [plan](ROADMAP.md) · [protocol](../README.md)

Walked once, 2026-08-01. Two rungs wait on a real phone; the third is answered.

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | `docs/phone.md` — the paths that already work | wip | opus, 2026-08-01 | a record written and published from a phone |
| 2 | beetle | Static PWA committing via forge API | wip | opus, 2026-08-01 | phone-composed record byte-identical to `records new` |
| 3 | cricket | *Maybe* voice capture (marks, never transcribes) | done | opus, 2026-08-01 | a design note arguing it should exist |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **1 · flue — written, not yet walked.** `docs/phone.md` is in, linked from the root README, and
  says only what the repo and the live API prove. It stays `wip` because its acceptance is *a
  record written and published entirely from a phone*, and no phone was involved: claims about
  editor apps nobody ran are exactly what [badstu 2](../badstu/ROADMAP.md) exists to stop. Walk
  the two paths it describes and tick it.
- **2 · beetle — built, half-verified.** `tools/pwa/` ships behind `params.phoneApp` (unset =
  not published, since the page holds a token). The byte half of its acceptance passes:
  `tools/pwa/fixtures.json` is checked by both `tests/test_phone_fixtures.py` (16 passed) and
  `tools/pwa/selftest.html` (15 cases, green in chromium). It stays `wip` for the other half — a
  live token-authenticated commit from a phone, which needs a token and a phone.
- **CORS decides this road, and it was checked** (2026-08-01): `codeberg.org` answers the
  preflight with `Access-Control-Allow-Origin: *` and allows `Authorization`, so the app works
  there unconfigured. A stock self-hosted Forgejo returns **405 with no CORS headers** —
  `g.xil.no` among them — and needs `[cors] ENABLED = true`. GitHub's API is open too, but no
  adapter ships: untested is untested.
- **3 · cricket — answered, and the answer is no.**
  [The argument against building it](voice.md) concludes the rung should not exist: audio without
  words is not a record, phone keyboard dictation already does the transcribing (the user's OS,
  not our engine — the border holds), and where audio lives belongs to
  [schrank](../schrank/ROADMAP.md). What survived is one documented paragraph in `docs/phone.md`.
- The `voiceRecorded: true` flag already works end to end (site, PDF, EPUB). It marks. It does not
  transcribe, and nothing on this road changes that.

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
