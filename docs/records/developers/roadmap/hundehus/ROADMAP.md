---
title: hundehus — The watch
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, hundehus]
---

# 7 · hundehus — The watch

> The doghouse: where the loyal thing sleeps, outside, facing the door.

A dog is useful because it has no opinions. It notices, and it barks. It does not decide what to do
about the intruder, and it certainly does not open the gate.

This road builds the project's dog: a small process that watches the checkout, rebuilds when a
record changes, and tells you when something is wrong — and never, under any circumstance, commits,
pushes or publishes on its own. Automation that acts is a liability in a repo whose contents are
someone's conversations. Automation that *notices* is pure gain.

Beside the dog, a nose: `records doctor`, which sniffs a checkout and reports what will fail before
you find out from CI.

## Dependencies

None. Both commands are additive and stdlib-only.

Item 1 before item 2 — the watcher's usefulness is largely in reporting what the doctor knows how to
check.

## Items

### 1 · flue — `records doctor`

The single highest-value command nobody has written. A fork lands, something is misconfigured, and
the failure surfaces three steps later in a CI log.

- New `recordkit/doctor.py` behind `records doctor [--repo .]`, emitting the same JSON shape as
  every other subcommand plus a human-readable mode.
- Checks, each reporting `ok` / `warn` / `error` with a one-line remedy:
  - **Config discovery** — is there a `*/hugo/hugo.yaml`, and does its `contentDir` resolve to a
    directory that exists? This is the failure that makes every skill silently write to the wrong
    place.
  - **URL resolution** — would `bin/build.sh` find a `baseURL`? Walk the same ladder it walks
    (explicit `baseURL` → `BASE_URL` → `PAGES_HOST` → Codeberg derivation → `CI_PAGES_URL`) and say
    which rung would win, or that none would.
  - **Toolchain** — `hugo` present and ≥ 0.158 (the theme needs `site.Language.Locale`); `pandoc`
    and `weasyprint` if any book param is set; `pypdf` if `booklet:` is set; `rsync` if
    `publishTarget: rsync`.
  - **Publish config** — `publishTarget` set to something known, `publishDest` not empty/root/home,
    `deployCommand` pointing at something that exists, or a CI workflow present in the checkout.
  - **Records** — the records dir is non-empty or `demoMode` is on; no record with a `date:` Hugo
    cannot parse; no reserved key (`demo`) misused.
  - **Git** — a remote exists, the branch matches `repoBranch`, the checkout is not detached.
- Exit code 0 when nothing is `error`, 1 otherwise. `--json` for machines.

**Files:** `recordkit/doctor.py`, `recordkit/cli.py`, `tests/test_doctor.py`, `tools/others/README.md`.

**Acceptance:** `records doctor` run against (a) this repo, (b) a deliberately broken scratch
checkout, with both outputs pasted and the broken one naming every fault.

**Border:** the doctor reports. It never fixes, never writes, never touches config.

### 2 · beetle — `records watch`

The dog itself.

- New `recordkit/watch.py` behind `records watch [--repo .] [--interval N]`.
- Stdlib only, which means **polling**, not inotify — a `stat` sweep over the records dir at a
  sensible interval. This is not a performance-critical path; a second of latency is fine and a
  dependency is not.
- On change: run the build (`bin/build.sh`, the one build path) and report success or failure.
- Debounce. An editor writing a file produces several events; one rebuild is correct.
- Handle the obvious edge cases: file deleted, file renamed, records dir vanishing (say so, keep
  running), the build taking longer than the interval (skip, don't queue forever).
- Clean exit on `SIGINT`, always.

**Files:** `recordkit/watch.py`, `recordkit/cli.py`, `tests/test_watch.py`.

**Acceptance:** the watcher running while a record is edited, rebuilding once per save, and
surviving a deliberately broken build without dying.

**Border:** **it never commits, never pushes, never publishes.** Not behind a flag, not behind a
config key. The dog barks; the human opens the gate.

### 3 · cricket — The bark

Noticing is only half of it. A watcher whose output scrolls past in a terminal nobody is looking at
is a watcher that does nothing.

- Desktop notification on build failure, and optionally on success. Freedesktop `notify-send` if
  present, silent no-op if not — detected, never depended on.
- `recordkit/mucke.py` already talks to MPRIS over D-Bus, so the pattern for optional desktop
  integration exists in this codebase. Follow it.
- Editor surfacing: the VSCode sidebar shows watcher status as a status line (the dim `status`
  class already exists); Neovim gets the same through a small status function.
- Quiet by default. A tool that notifies too much gets muted, and then it is worse than nothing.

**Files:** `recordkit/watch.py`, `tools/others/vscode/src/`, `tools/others/neovim/lua/records/init.lua`.

**Acceptance:** a failed build producing exactly one notification, and the same run on a machine
without `notify-send` producing no error.

### 4 · moth — The doctor goes to CI

Once the doctor knows what breaks, the CI shims can ask it before spending five minutes finding out.

- An optional early step in each workflow calling `records doctor --json`, failing fast with a
  readable message.
- Optional is load-bearing: the shims must still work with no Python and no `recordkit` installed.
  Skip cleanly, exactly like `bin/build.sh` skip-notes a missing pandoc.
- The failure message names the rung of the URL ladder that came up empty — the single most common
  fork failure.

**Files:** `.forgejo/workflows/pages.yml`, `.github/workflows/pages.yml`, `.gitlab-ci.yml`.

**Acceptance:** a deliberately misconfigured fork failing in the doctor step with a message that
names the fault, and the same workflow passing unchanged with `recordkit` absent.

## Borders for this road

- **Nothing on this road acts on your repo.** No auto-commit, no auto-push, no auto-publish, not
  even opt-in. This is the road's defining constraint and its reason for existing.
- Stdlib only: polling over inotify, `notify-send` detected rather than depended on.
- One build path — the watcher calls `bin/build.sh` and does not reimplement any part of it.
- The doctor never writes. Reporting and repairing are different jobs, and only one of them is safe
  to automate.
