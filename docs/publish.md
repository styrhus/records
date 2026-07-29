# Publish anywhere

The site is one build (`bin/build.sh`) plus a delivery. Hosted forges
deliver via CI on push; everything else delivers via `records publish`.
Requirements: bash, git and a recent [Hugo](https://gohugo.io/installation/)
(extended); pandoc + WeasyPrint only if you enable the PDF/EPUB/booklet
params. No Windows — the build path is bash.

## Hosted forges (CI on push)

- **Codeberg** — fork, enable Actions in the fork's settings, push to
  `main`. Zero edits: the workflow derives your address.
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

Forgejo with Actions but no Pages service — publish from CI to your
webroot:

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
