# When the deploy breaks, or publish pushed the wrong thing

Two accidents that feel the same from the outside — the site is not what it
should be — and have nothing to do with each other underneath. Neither is
urgent the way a leaked credential is; if that is what happened, go to
[when a key lands in a transcript](oops.md) instead and come back later.

Part one is the site that stopped deploying. Part two is the `records publish`
that force-pushed over something you wanted.

## Part one: the site stopped deploying

### 1. Find out whether anything ran at all

Open the run list first — Forgejo and Codeberg: the repository's **Actions**
tab; GitHub: **Actions**; GitLab: **Build → Pipelines**.

Three reasons a deploy never starts, and none of them is a failure:

- **The push touched nothing the workflow watches.** `.forgejo/workflows/pages.yml`
  has a `paths:` filter: `tools/hugo/**`, `records/**`, `static/**`,
  `tools/pandoc/**`, `tools/pwa/**`, `bin/build.sh` and the workflow file
  itself. A commit that only changes `docs/`, `AGENTS.md` or
  `tools/others/` deliberately does not rebuild the site. To deploy anyway:
  Actions → *Deploy to Pages* → **Run workflow** (the shim keeps a
  `workflow_dispatch` trigger for exactly this).
- **The job's guard is false.** That workflow runs on codeberg.org, or on an
  instance whose admin has set the Actions variable `PAGES_HOST`. Without
  either, the job is skipped — the run appears, the job does not, and nothing
  reports an error.
- **The push went to a branch other than `main`.**

### 2. Read the failure from the top

A failed run is read downwards, not from the last red line. Where it stops
tells you what kind of problem it is:

1. **Before any step prints anything** — workflow *preparation* failed. The
   cause is almost always a `uses:` the forge cannot resolve: a self-hosted
   instance mirrors only some actions, and an unmirrored one kills the job
   before the first step. This has nothing to do with your commit, and a
   re-run will not fix it. The instance's `PAGES_ACTION` variable exists to
   point the deploy step at a local mirror.
2. **Doctor (optional pre-flight)** — `records doctor` found a build-stopper
   and exited non-zero. It names the problem and the remedy in the log;
   reproduce it locally with

   ```bash
   PYTHONPATH=tools/others/python python3 -m recordkit doctor --repo .
   ```

   Nothing after this step ran, so there is only one thing to fix.
3. **Build** — `bin/build.sh`. The usual three: `cannot resolve the site URL`
   (no `baseURL`, no `BASE_URL`, no CI variable the ladder recognises), a Hugo
   template or content error, or a record with an unparseable `date:`. Missing
   pandoc, WeasyPrint or pypdf are *not* failures — the script prints a skip
   note and the site still ships.
4. **Derive deploy URL / Deploy to Pages** — the site was built; delivery
   failed. Look at the token, the pages server, and the action — not at your
   records.

### 3. Your commit, or the ground moving?

The honest answer usually comes from two checks.

**Did your push even touch the build surface?**

```bash
git log --oneline -5 -- tools/hugo records static bin/build.sh
```

**Re-run the last green run, unchanged.** Forgejo, Codeberg and GitHub all
offer a re-run on a past run. If a run that was green yesterday fails today on
the same commit, nothing you wrote did it.

What floats here is worth knowing before you need it. The Forgejo/Codeberg shim
uses the container image `codeberg.org/tb4/hugo-runner:latest` and the deploy
action `codeberg.org/git-pages/action@v2` — both can move underneath you, and
Hugo comes from that image (the bundled themes need ≥ 0.158). An instance admin
can pin both with the `RUNNER_IMAGE` and `PAGES_ACTION` variables. The GitLab
shim pins its image (`hugomods/hugo:debian-0.164.0`); the GitHub shim installs
Hugo per run at `hugo-version: latest`, so that one floats too.

A build that works locally and fails in CI points at the image:

```bash
BASE_URL=http://localhost/ ./bin/build.sh /tmp/site
```

### 4. Getting the site back while you work it out

- `git revert <commit>` and push. The site is regenerated from whatever is on
  `main`; there is no separate state to repair.
- Or deliver by hand, bypassing CI: set a `publishTarget` and run
  `records publish` (part two is about what that does — read it first).
- Do not delete the pages branch to "start clean". It is the live site.

## Part two: `records publish` pushed the wrong thing

With `publishTarget: pages-branch`, `records publish` force-pushes. There is no
confirmation step today and no prompt: `--dry-run` is the only brake, and you
have to remember it.

### 1. What actually happened

In order: `bin/build.sh` writes the site into `public/`, any `public/.git` is
deleted, `.nojekyll` is created, then a throwaway repository is initialised
*inside* `public/`, everything is added as one commit, and that commit is
pushed with `--force` to `publishBranch` (default `pages`) on the remote's URL.
Afterwards the throwaway `.git` is deleted again.

Three consequences that decide what you can recover:

- The branch now holds **exactly one commit**. Whatever history it had is
  unreferenced on the remote.
- The commit you just pushed exists **nowhere locally** — the repository that
  made it was deleted on the way out.
- Your own clone's `origin/pages` was **not** updated. `publish` pushes to the
  remote's URL rather than its name, so the remote-tracking ref still says
  whatever your last `git fetch` said. That is the single most useful fact on
  this page.

### 2. The cheap fix, first

The pages branch is an artifact, not source. If `main` is right, the fix is to
build and publish again — the force-push that caused the problem also solves
it:

```bash
records publish --dry-run   # builds, delivers nothing, reports the file count
records publish
```

Do this before hunting for the old commit. Most of the time it is the whole
repair.

### 3. When publishing again is not enough

It is not enough when the branch carried something the build does not produce:

- a domain file added by hand — `.domains` on Codeberg Pages, `CNAME` on
  GitHub Pages,
- files published from a different commit, a different repository, or a
  different machine,
- anything edited directly on the branch in the forge's web editor.

Those are gone from the branch and will be gone again on the next publish. The
durable fix is to move such files into `static/`, which the build copies into
the site every time.

### 4. Getting the old branch tip back

In order of how often it works:

1. **Your own clone, if it ever fetched the branch.** Nothing that `publish`
   does updates it, and a later `git fetch` leaves the old value in the
   reflog either way:

   ```bash
   git rev-parse origin/pages
   git reflog show refs/remotes/origin/pages
   git push --force origin <old-sha>:refs/heads/pages
   ```

   The last line only works while the objects are still in that clone — so do
   this before any `git gc`, and keep the clone until you are sure.
2. **Another clone, or a CI cache**, that fetched the branch more recently than
   you did.
3. **A webhook's delivery log.** Every push payload carries the `before` commit
   of the ref it moved. Forgejo: Settings → Webhooks → the hook → recent
   deliveries. This only helps if the repository had a webhook at the time.
4. **The forge's own copy.** The orphaned objects usually survive on the server
   until it garbage-collects, but no ref points at them and most forges will
   not hand you a commit by hash on request. On a self-hosted instance this is
   one command for the admin; on a hosted forge it is a support ticket, and the
   answer may be no. Same wall as [oops.md](oops.md) describes from the other
   side.
5. **Rebuild it from the source.** Check out the commit the branch was built
   from and publish again. The bytes differ — the commit message carries a
   fresh `publish <date>` stamp — but the site is the same site.

### 5. The rsync target, briefly

With `publishTarget: rsync`, delivery is `rsync -az --delete` into
`publishDest`: everything at the destination that is not in the built site is
erased. `records publish` refuses a destination it recognises as catastrophic —
the filesystem root, a home directory — and `records doctor` reports the same
refusal before you ever run it, so `records doctor` is the authoritative list,
not this page. What no guard can refuse is a destination that is perfectly
reasonable and simply not the one you meant. There is no undo for that; there
are only your backups. `records publish --dry-run` passes `-n
--itemize-changes` to rsync and prints exactly what would change.

## What you can and cannot get back

| | |
|---|---|
| the built site | always — it is regenerated from source |
| the pages branch's contents | always, by publishing again |
| the pages branch's *history* | usually not; it was one commit either way |
| a hand-added `CNAME` / `.domains` on the branch | only if you have a copy; move it to `static/` |
| a webroot after `rsync --delete` | only from your backups |
| your records and your source | untouched — `publish` never touches them |

## The short version

1. **Nothing deployed?** Check whether a run even started: the `paths:` filter
   and the job guard are the usual answers, and `workflow_dispatch` runs it
   anyway.
2. **A run failed?** Read it from the top. Preparation = an action the forge
   cannot resolve; doctor = one named problem; build = URL, template or date;
   deploy = the token or the server.
3. **Not sure whose fault it is?** Re-run the last green run. If it is red
   now, the ground moved, not your commit.
4. **Published the wrong thing?** Publish the right thing. Then, and only
   then, go looking for the old tip — starting with your own clone's
   `origin/pages`.

See also: [publish anywhere](publish.md), [when a key lands in a
transcript](oops.md).
