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

All three paths build with a pinned Hugo, so the same commit keeps
building the same site; raising a pin is a deliberate step, written down
in [raising the build toolchain](toolchain.md).

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

When a deploy stops working, or a publish force-pushes over something you
wanted back, the recovery steps are in [when the deploy breaks](recover.md).

## Taking a record back

```bash
records unpublish bicycles              # out of the site and the books
records unpublish bicycles --tombstone  # …and leave a stub at the old URL
records unpublish bicycles --restore    # put it back
```

Unpublishing sets `draft: true` in the record's own front matter. That is the
one mechanism both halves of the build already honour: Hugo skips drafts
(`bin/build.sh` never passes `--buildDrafts`), and `tools/pandoc/book.lua`
drops any record whose `draft` is true, so the PDF, EPUB and booklet lose it
too. `build.list: never` plus `build.render: never` would work for Hugo alone,
but they are nested keys that the book build does not read. A second flat key,
`unpublished: <timestamp>`, records that the tool did it, so `--restore` can
tell it from a draft you wrote by hand; a record that is already a draft is
refused rather than swallowed.

`--tombstone` leaves a stub at the old URL — better than a 404 for anyone who
linked to it, worse than a 404 for anyone who wanted it gone; you choose. The
URL comes from the filename, so the stub takes the record's filename over and
the record moves beside it as `<name>.withdrawn.md`, still a draft. The stub
carries the original date (so it keeps its place) but neither the title nor a
word of the conversation.

**Rebuild through `bin/build.sh` (which `records publish` does for you).** It
passes `--cleanDestinationDir`, so the withdrawn record's old page leaves
`public/` with the rebuild before the force-push. A hand-run `hugo` does not
clean its destination — if you build that way, empty the directory yourself:

```bash
records publish            # builds clean, then delivers
rm -rf public && hugo ...  # only needed on hand-run hugo builds
```

Nothing here is erasure, and the command says so on every run: git history
still holds the record, so does every clone, fork and mirror made before now,
and so do the forge's caches and whatever the internet already indexed. If what
leaked was a credential, rotate it — a removal is cleanup, rotation is the fix.

`records redact <record> --turn N --remove` is the smaller tool for the same
problem: it rewrites one turn in place and leaves `[redacted]` where the text
was — a seam a reader can see, not a silent edit. It shows the diff and asks
first (`--dry-run` to look without being asked, `--yes` to skip the question),
and it never touches git.

## Never publishing it in the first place

Patterns in `records/.recordsignore` — gitignore-shaped, one per line — keep
files out of the build entirely:

```
# never publish these
private/
*.env
scratch.md
```

```bash
records ignore           # write the patterns into the site config
records ignore --check   # CI: fail if the config is stale
```

`.recordsignore` is a front end to Hugo's `ignoreFiles`, not a second mechanism:
`records ignore` translates the patterns into a generated `ignoreFiles:` block in
`tools/hugo/hugo.yaml`, which Hugo and `tools/pandoc/book.lua` already read, so
the site, the PDF and the EPUB all follow. The block is generated, which is why
there is a `--check`: a stale one is a lie about what you publish. See the
comments beside it in the site config for the pattern subset and how it interacts
with `draft: true` and `demoMode`.

An ignored file is still in your repository and still in git history. This is
about not publishing, not about secrecy.

## When it was a secret

If what leaked was a credential, none of the above is the fix. **Rotate the key**,
then work down [when a key lands in a transcript](oops.md) — it covers
`records scan`, what a `git filter-repo` rewrite does and what it costs, and what
nothing at all can reach.

If what leaked was somebody else, [the other people in your
records](other-people.md) is the page for that one.

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
