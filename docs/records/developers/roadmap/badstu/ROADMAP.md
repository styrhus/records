---
title: badstu — Steam
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, badstu]
---

# 12 · badstu — Steam

> The sauna: heat, sweat, cold water. The room where people talk without titles.

**This is the road under our feet.** `CURRENT` reads `0.12.1 badstu-flue`.

Two things happen in the heat at once.

The project gets **help**: a roadmap split into claimable items, a handoff protocol, folders that
let separate sessions work without collision. Many hands, one small project.

And the project gets **honest**: everything the repo currently *says* about itself gets checked
against the code that is supposed to back it. The GitHub and GitLab shims have never run. The
booklet is silently skipped because the runner image lacks pypdf, and the skip is a stderr note
nobody reads. `records publish --target rsync` cannot work on the shipped image — no rsync, no ssh.
A README sentence that is not true is a bug with better manners.

Sweat it out. What survives is the project.

## Dependencies

None. This road is the floor everything else stands on, which is why it is first.

Items 2 and 3 both touch CI; do 3 before 2 if you want the booklet exercised by the same run.

## Items

### 1 · flue — The roadmap and the handoff protocol

**Done.** This file, its ten siblings, and [how a road is walked](../README.md) are the item.

The shape: `docs/records/developers/roadmap/<structure>/{ROADMAP,STATUS}.md`, one folder per road,
items numbered by the animal pool, `STATUS.md` as a claim table. The top
[ROADMAP.md](../../ROADMAP.md) links into each folder and keeps the borders section.

**Acceptance:** every road named in the top roadmap's table has a folder containing both files, and
no relative link in the roadmap resolves to a missing path.

### 2 · beetle — CI truth: the shims actually run

The `.github/workflows/pages.yml` and `.gitlab-ci.yml` shims are shipped and unexercised. Until a
real run publishes a real site, "publish anywhere" is a claim, not a fact.

- Rehearse on the scratch repos rather than the canonical instance. `menneske/records-smoke` exists
  for exactly this (remote `smoke`); Actions must be enabled on it first — that toggle is the
  human's, ask for it rather than working around it.
- Push a minimal fork state to GitHub and to GitLab. Enable Pages once on GitHub (Source: GitHub
  Actions) per [docs/publish.md](../../../../publish.md).
- Confirm the derived `baseURL` is what `bin/build.sh` claims it derives: GitHub via
  `configure-pages` → `BASE_URL`, GitLab via `CI_PAGES_URL`.
- Confirm `HUGO_PARAMS_REPOURL` derivation lands the right forge link shape per
  `params.repoLinkStyle` — `auto` must pick GitHub and GitLab correctly from the host.
- Record what actually happened. If a shim is broken, fix the shim; if the docs oversell, fix the
  docs.

**Files:** `.github/workflows/pages.yml`, `.gitlab-ci.yml`, `bin/build.sh`, `docs/publish.md`.

**Acceptance:** a live URL on each of GitHub Pages and GitLab Pages serving a built site, with the
footer repo link pointing at the right forge, pasted into the session.

**Border:** no second build path. If a provider needs something, it goes into `bin/build.sh`'s
existing URL ladder, not into the shim.

### 3 · cricket — The runner image stops lying

`bin/build.sh` skip-notes the booklet when `python3 -c 'import pypdf'` fails, and
`records publish --target rsync` needs binaries the image does not carry.

- Add `pypdf` to the hugo-runner image (`tb4/hugo-runner-image`, Alpine base) so
  `tools/pandoc/impose.py` runs and `params.booklet` produces a real file in CI.
- Add `rsync` and `openssh-client` so the rsync publish target is reachable from a runner.
- Keep the image small; these are three packages, not a platform.
- Re-run a build with `booklet:` uncommented and confirm the imposed A4 PDF appears at the site root.

**Files:** the hugo-runner image repo; verified through `bin/build.sh` and `tools/pandoc/build.sh`.

**Acceptance:** a CI build log showing the booklet built rather than skipped, and `rsync --version`
succeeding inside the image.

**Border:** the skip paths stay. An image without pypdf must still exit 0 — forks may use their own.

### 4 · moth — The audit: every claim checked

Read the living docs against the code, one section at a time, and fix whichever side is wrong.

- `CLAUDE.local.md` and its tracked mirror `CLAUDE.local.md.example.md` — config keys, ordering
  rules, pageModes, the rendering pipeline, the CLI surface. This file is dense and load-bearing;
  drift here misleads every future session.
- `tools/others/README.md` — the CLI commands listed must match `recordkit/cli.py`'s subparsers, and
  the test count must match what `pytest` reports.
- `tools/hugo/themes/Fuglekasse/README.md` — every `params.*` documented must exist in
  `themes/Fuglekasse/hugo.toml`, and every param in the toml must be documented.
- The root `README.md` and `docs/*.md` — no promise the code does not keep.

**Acceptance:** a diff, plus a list of every discrepancy found and which side was corrected. "No
discrepancies" is an acceptable result only with the comparison shown.

### 5 · tadpole — The theme audited cold

Fuglekasse is minimal, which makes it auditable in one sitting.

- No-JS: every mode renders and every control degrades. The filter becomes an inert `<details>`, the
  TOC still folds, chapters still open. Verify by disabling JavaScript, not by reading the template.
- Contrast and focus: the light and dark palettes checked against WCAG AA, visible focus rings on
  the anchors, the TOC button, the filter controls.
- Semantics: heading order inside records, the mic icon's accessible name, `lang` on the cards.
- Print: the `pdf.css` mirror still matches `baseof.html` after every palette change.

**Files:** `tools/hugo/themes/Fuglekasse/layouts/baseof.html`, `tools/pandoc/pdf.css`.

**Acceptance:** the findings list with before/after for each fix, and a build inspected in a browser.

**Border:** no growth in Fuglekasse. Fixing contrast is repair; adding a widget is not.

### 6 · snail — Weight: what happens at ten thousand records

Nobody has asked. The single and single-flowing modes put every record on one page.

- Generate a synthetic records dir (throwaway, outside the repo) at 100 / 1 000 / 10 000 records.
- Measure `hugo --minify` time, output size, and the single-page HTML weight.
- Measure `tools/pandoc/build.sh` — the PDF path is the likely first casualty.
- Measure the filter's client-side work; the `wordText` expando cache was built for this, confirm it
  holds.
- Write the honest number into the docs: the record count at which each mode stops being pleasant,
  and what to switch to.

**Acceptance:** a small table of measurements in this folder's `STATUS.md` notes, and a documented
recommendation.

**Border:** measure first. No optimisation lands on this road without a number in front of it.

## Borders for this road

- Verification does not get to change behaviour quietly. If the audit finds a bug, fix it as a bug,
  visibly.
- The scratch repos are for rehearsal. The canonical instances (`tb4/pages`, `blyant/records`) are
  not test targets.
- Agents never run `/werden`. Turning the cycle is the human's.
