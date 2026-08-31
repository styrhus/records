---
title: badstu — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, badstu, status]
---

# 12 · badstu — status

Road: **Steam** · [plan](ROADMAP.md) · [protocol](../README.md)

Cycle: this road is **now** (`CURRENT` = `0.12.3 badstu-cricket`).

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | The roadmap and the handoff protocol | done | claude-opus-5 | `ls docs/records/developers/roadmap/*/ROADMAP.md \| wc -l` → 11 |
| 2 | beetle | CI truth: GitHub + GitLab shims actually run | blocked | — | live Pages URL from each provider |
| 3 | cricket | Runner image gains pypdf, rsync, openssh | open | — | CI log shows booklet built, not skipped |
| 4 | moth | The audit: every doc claim checked against code | done | assistant | discrepancy list + diff |
| 5 | tadpole | Theme audited cold (no-JS, contrast, focus, print) | open | — | findings list + browser check |
| 6 | snail | Weight: 100 / 1k / 10k records measured | done | Claude Opus 5, 2026-08-31 | measurement table in notes; book path stays unmeasured (pandoc absent — belongs with item 3's runner image) |

`State` ∈ `open` · `wip` · `done` · `blocked`

## Notes

- **4 · moth done** (2026-08-01, assistant + one delegated sonnet session): 25 claims
  checked — 16 ok, 6 doc fixes (`CLAUDE.local.md.example.md`: pageMode gained
  `single-flowing`, explicit diff-skill list, VSCode covers `/config` not `/werden`;
  `docs/hugo.md`: `contentDir ../../records`, four templates; Fuglekasse README:
  new CDN section for the real-but-undocumented `params.cdnURL`), 1 code-side
  inconsistency reported (repoURL/insidesBranch lack commented placeholders in the
  theme's hugo.toml — filed as an issue, not fixed here), 2 unverifiable (version
  archaeology). Test-count claim "102" matches `grep -h "^\s*def test_" tests/*.py | wc -l`
  → 102 exactly (pytest unavailable here; note: one parametrized test would make
  `pytest --collect-only` report ~106 collected items).
- **2 · beetle is blocked** on Actions being enabled for the `menneske/records-smoke` scratch repo.
  That toggle belongs to the human — ask, don't route around it. Do not rehearse on `tb4/pages` or
  `blyant/records`.
- **3 · cricket** touches a different repo (`tb4/hugo-runner-image`). The change is three Alpine
  packages; keep the skip paths in `bin/build.sh` intact so forks on other images still exit 0.
- **6 · snail** generates its synthetic records outside this repo. Nothing throwaway lands in
  `records/`.

## 6 · snail — the measurements (2026-08-31)

Deterministic seeded corpora (seed 20260831, nesting: 100 ⊂ 1k ⊂ 10k; mean 4.9 kB/record, real
turn/signature/code-block shapes), built via `bin/build.sh` at HEAD `240abc7`, hugo v0.165.0
extended, 8 cores / 8 GB, median of 3 runs:

| Records | Theme | pageMode | `hugo --minify` | Peak RSS | `public/` | front `index.html` | gzip -9 |
|---|---|---|---|---|---|---|---|
| 100 | Fuglekasse | basic | 0.17 s | 137 MB | 2.71 MB | 32.0 kB | 9.7 kB |
| 100 | Fuglekasse | single | 0.20 s | 110 MB | 0.87 MB | 829 kB | 167 kB |
| 100 | Postkasse | basic | 0.14 s | 127 MB | 1.09 MB | 16.1 kB | 5.0 kB |
| 1 000 | Fuglekasse | basic | 0.67 s | 337 MB | 27.5 MB | 113 kB | 25.0 kB |
| 1 000 | Fuglekasse | single | 1.24 s | 352 MB | 9.33 MB | 9.29 MB | 1.81 MB |
| 1 000 | Postkasse | basic | 0.59 s | 333 MB | 11.6 MB | 97.3 kB | 20.1 kB |
| 10 000 | Fuglekasse | basic | 7.45 s | 2 300 MB | 279 MB | 929 kB | 171 kB |
| 10 000 | Fuglekasse | single | 13.05 s | 2 535 MB | 97.9 MB | 97.9 MB | 18.97 MB |
| 10 000 | Postkasse | basic | 4.92 s | 2 317 MB | 120 MB | 913 kB | 167 kB |

(`single-flowing` tracks `single` within ~4 %; Postkasse and Fuglekasse are within 0.02 % of each
other in the one-page modes.)

- **Build time is never the wall** — except in `posts` mode, whose paginated `home.html` re-runs
  its `where`/`sort` per paginator page: 0.22 s / 4.59 s / **351.6 s** at 100 / 1k / 10k. The
  number is recorded; no optimisation proposed, per the border.
- **The one-page modes are the wall**: ~9.8 kB HTML and 254 DOM elements per record, all on one
  page. Comfortable to ~250 records; the gzipped front page crosses 1 MB at ~530; at 10 000 it is
  93 MB, 2.54 M DOM elements — not a web page any more.
- **Peak memory is the real CI constraint**: ~2.5 GB at 10 000 records.
- **Theme weight at scale**: Fuglekasse inlines its chrome into every page (~82 % of its 279 MB
  `basic` output at 10k is repeated theme bytes); Postkasse externalises CSS/JS and emits 120 MB
  for the identical site.
- **The filter** (`single` + `showFilter`): the `wordText` expando cache holds — correct, lazy,
  and it removes exactly the per-keystroke re-materialisation it was built to remove, at the cost
  of ~46 M retained characters at 10k. What breaks first is *beside* it, uncached in the same
  handler: the highlight `TreeWalker` over every visible text node (2.62 M at 10k; a common word
  allocates 350 k+ ranges per keystroke) and the 10 000 `classList.toggle` style recalcs, with no
  debounce. Workable at 1 000; not at 10 000. The filter is only offered in `single` mode — which
  is precisely the mode that dies first.
- **Unmeasured, honestly**: the pandoc/weasyprint book path — absent on the measuring box. Its
  structure (one AST, one paged layout, then pypdf re-imposition) makes the PDF the likely first
  casualty; measuring it belongs with **3 · cricket**'s runner image, where pypdf lands anyway.
  The corpus generator is deterministic (`gen_records.py --seed 20260831`) — same seed, same
  bytes, regenerate anywhere.
- **4 · moth does not parallelize.** The audit reads and corrects the whole repo by definition — run
  it with no other session active. **2 · beetle** also shares the CI shims with
  [hundehus 4](../hundehus/ROADMAP.md).

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
