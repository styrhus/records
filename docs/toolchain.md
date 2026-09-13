# Raising the build toolchain

The site is built by CI, and CI used to build it with whatever was newest that
morning: the Forgejo path ran `codeberg.org/tb4/hugo-runner:latest`, the GitHub
path ran `peaceiris/actions-hugo` with `hugo-version: 'latest'`. Both are pinned
now, so the same commit builds the same way tomorrow as it did today.

A pin you never raise is just an old `latest`. This is how it gets raised.

## Where the pins are

| Path | File | Pin |
|------|------|-----|
| Forgejo / Codeberg | `.forgejo/workflows/pages.yml` | `codeberg.org/tb4/hugo-runner:0.165.0` |
| GitHub | `.github/workflows/pages.yml` | `hugo-version: '0.165.0'` |
| GitLab | `.gitlab-ci.yml` | `hugomods/hugo:debian-0.164.0` |

The runner image's tag is the Hugo version inside it, which is why all three
read the same way. The floor is separate and lives with the themes:
`min_version` in `tools/hugo/themes/*/theme.toml` (`0.158.0` today) is the
oldest Hugo the templates are known to work with — never pin below it.

`vars.RUNNER_IMAGE` still overrides the Forgejo pin. It is for pointing a
runner at a local registry cache, not for floating the version again; set it to
a tag, not to `latest`.

## Raising them

1. **Pick the version.** For the Forgejo path, list what the package actually
   publishes — a tag that does not exist is not a pin:

   ```bash
   curl -s "https://codeberg.org/api/v1/packages/tb4?type=container&q=hugo-runner" \
     | grep -o '"version":"[^"]*"'
   ```

   If the package ever stops publishing versioned tags, pin by digest instead
   (`codeberg.org/tb4/hugo-runner@sha256:…`) and say so here. To read a tag's
   digest without pulling it:

   ```bash
   TOK=$(curl -s "https://codeberg.org/v2/token?scope=repository:tb4/hugo-runner:pull&service=container_registry" \
     | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
   curl -sI -H "Authorization: Bearer $TOK" \
     -H "Accept: application/vnd.oci.image.index.v1+json" \
     "https://codeberg.org/v2/tb4/hugo-runner/manifests/<tag>" | grep -i docker-content-digest
   ```

2. **Build with it locally, before CI sees it.** The build script is the same
   one CI runs, so a local run is the real test:

   ```bash
   curl -sL -o /tmp/hugo.tar.gz \
     "https://github.com/gohugoio/hugo/releases/download/v<version>/hugo_extended_<version>_linux-amd64.tar.gz"
   tar xzf /tmp/hugo.tar.gz -C /tmp hugo
   PATH=/tmp:$PATH BASE_URL="https://example.invalid/" ./bin/build.sh /tmp/site-new
   ```

3. **Compare against the last good output.** Build the current pin the same way
   into a second directory and diff the two trees. Hugo's own version string and
   fingerprinted asset names move on a version bump; page structure should not:

   ```bash
   diff -rq /tmp/site-old /tmp/site-new
   ```

   Read every difference before accepting it. A changed `<main>`, a dropped
   page, or a template warning that was not there before is a reason to stop,
   not a reason to bump the pin and see what CI says.

4. **Raise the pin in one commit per path** — the workflow file, this table, and
   the workflow's own comment, which must never claim something the pin does not
   do. Change the theme `min_version` only when the templates actually start
   needing the newer Hugo.

5. **Watch the first CI run.** A pin that builds locally can still fail on a
   runner that is missing pandoc or WeasyPrint; the books self-gate on their
   params, so check what the run actually produced, not only that it was green.

## When the pin is the problem

If a build breaks and the pin is the suspect, put the old value back and push —
that is the whole rollback. The pin is one line in one file, and the previous
value is in `git log -p -- .forgejo/workflows/pages.yml`. Recovery for a deploy
that has already gone out is [when the deploy breaks](recover.md).
