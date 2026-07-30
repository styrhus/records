# Publish anywhere

The site is one build (`bin/build.sh`) plus a delivery. Hosted forges
deliver via CI on push; everything else delivers via `records publish`.
Requirements: bash, git and a recent [Hugo](https://gohugo.io/installation/)
(extended); pandoc + WeasyPrint only if you enable the PDF/EPUB/booklet
params. No Windows — the build path is bash.

## Hosted forges (CI on push)

- **Codeberg** — fork, enable Actions in the fork's settings, push to
  `main`. Zero edits: the workflow derives your address.
- **Self-hosted Forgejo + git-pages** — the instance admin sets two
  Actions variables once (Site administration → Actions → Variables):
  `PAGES_HOST` (the domain your git-pages server serves, e.g.
  `p.example.org`) and `PAGES_RUNNER` (your runner's label, e.g. `docker`).
  Every repo on the instance then publishes on push with zero edits, at
  `https://<owner>.<PAGES_HOST>/<repo>/`. Two more variables cover runners
  that reach the forge over an internal address (e.g. in-cluster):
  `PAGES_SERVER` (internal `host:port` to deploy to when the pages domain
  isn't reachable from the runner) and `FORGE_URL` (the forge's public URL,
  e.g. `https://git.example.org` — used for the site's repo links, which
  would otherwise be derived from the internal server URL the runner sees).
  A third optional variable, `PAGES_ACTION`, points the deploy step at an
  instance-local mirror of the git-pages action (unset = the upstream at
  `codeberg.org/git-pages/action`).
- **GitHub** — enable Pages once (Settings → Pages → Source: GitHub
  Actions), push to `main`. The shipped `.github/workflows/pages.yml` does
  the rest.
- **GitLab** — push to `main`; the shipped `.gitlab-ci.yml` publishes
  Pages.

With CI publishing, the push is the deploy — nothing to run locally.

## Anywhere else: `records publish`

Install the engine once:

```bash
cd tools/others/python && pip install .
```

Set your site URL and a delivery target in `tools/hugo/hugo.yaml`:

```yaml
baseURL: https://example.org/            # uncommented = authoritative
params:
  repoURL: https://example.org/you/records  # footer + raw links; unset = no footer link
  publishTarget: rsync                   # or: pages-branch
  publishDest: you@host:/var/www/site/   # rsync target
```

Then:

```bash
records publish --dry-run   # build + show what would be delivered
records publish             # build + deliver
```

### Targets

- **`pages-branch`** — force-pushes the built site to `publishBranch`
  (default `pages`) on `publishRemote` (default `origin`). Codeberg serves
  that branch natively with no CI at all; on GitHub choose Settings → Pages
  → Deploy from a branch. The branch keeps a single commit; your source
  history is untouched.
- **`rsync`** — `rsync -az --delete` of the built site to `publishDest`: a
  VPS webroot, a homelab share, anything static. `--delete` mirrors
  deletions on the far side — run `--dry-run` first when in doubt.

`records publish` never commits or pushes your source; that stays with
`/gc`, `/gcp`, `/cpd`.

## Wire it into /cpd

```yaml
params:
  deployCommand: records publish
```

The no-CI flow is then: write → `/cpd` → commit, push, publish. `/cpd` runs
`deployCommand` first, so this wins over the shipped workflow files.

## Homelab: self-hosted Forgejo

Forgejo with Actions but no Pages service (running git-pages? see Hosted
forges above) — publish from CI to your webroot:

1. Put an SSH deploy key in the repo's Actions secrets.
2. Give the runner `rsync` and `openssh-client`.
3. A thin workflow: checkout, load the key, then
   `BASE_URL=https://your.site/ ./bin/build.sh public` and
   `rsync -az --delete public/ deploy@web:/srv/www/site/`.

Or skip Actions entirely — a bare repo with a `post-receive` hook (Hugo and
rsync installed on the host):

```bash
#!/usr/bin/env bash
set -euo pipefail
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
git --work-tree="$TMP" checkout -f main
BASE_URL=https://your.site/ "$TMP/bin/build.sh" "$TMP/public"
rsync -az --delete "$TMP/public/" /srv/www/site/
```

## Existing forks

Nothing breaks on Codeberg: with `baseURL` commented out (the shipped
state) CI derives your address exactly as before. Forks that patched the
old workflow will hit a merge conflict in `pages.yml` when pulling this
change — take the new thin workflow, and if the patch was for a custom
domain, set `baseURL` in `tools/hugo/hugo.yaml` instead. A repo literally
named `pages` now derives the domain-root URL automatically.
