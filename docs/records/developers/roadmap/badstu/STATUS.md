---
title: badstu — status
date: 2026-08-01T15:05:00+01:00
tags: [developers, roadmap, badstu, status]
---

# 12 · badstu — status

Road: **Steam** · [plan](ROADMAP.md) · [protocol](../README.md)

Cycle: this road is **now** (`CURRENT` = `0.12.1 badstu-flue`).

| # | Animal | Item | State | Owner | Verify |
|---|---|---|---|---|---|
| 1 | flue | The roadmap and the handoff protocol | done | claude-opus-5 | `ls docs/records/developers/roadmap/*/ROADMAP.md \| wc -l` → 11 |
| 2 | beetle | CI truth: GitHub + GitLab shims actually run | blocked | — | live Pages URL from each provider |
| 3 | cricket | Runner image gains pypdf, rsync, openssh | open | — | CI log shows booklet built, not skipped |
| 4 | moth | The audit: every doc claim checked against code | done | assistant | discrepancy list + diff |
| 5 | tadpole | Theme audited cold (no-JS, contrast, focus, print) | open | — | findings list + browser check |
| 6 | snail | Weight: 100 / 1k / 10k records measured | open | — | measurement table in notes |

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
- **4 · moth does not parallelize.** The audit reads and corrects the whole repo by definition — run
  it with no other session active. **2 · beetle** also shares the CI shims with
  [hundehus 4](../hundehus/ROADMAP.md).

## Picking one up

Set `State` → `wip`, put yourself in `Owner`, read [ROADMAP.md](ROADMAP.md), make `Verify` pass with
its real output shown, tick to `done`. Leave the commit to the human. Full protocol:
[how a road is walked](../README.md).
