# The phone app

A single page that composes a record and commits it to your repo through your
forge's API. It ships with the site, holds your token in your browser, and has
no backend, no account and no service behind it. If that sentence worries you,
the web editor in [record from your phone](phone.md) needs none of it.

## Switch it on

```yaml
params:
  phoneApp: skriv        # unset = not shipped
```

`bin/build.sh` copies `tools/pwa/` into the built site under that name, so the
page appears at `https://your.site/skriv/`. Unset it and nothing is published —
the default, because a page that holds an access token should be a choice.

Open it, fill in the forge panel once, and **Add to home screen**. It caches
itself, so it opens without a connection.

## The trust model, in full

- **The token lives in your browser's local storage on that device.** It is
  sent to your forge and to nowhere else. There is no server here to send it to.
- **Anyone who unlocks your phone can read it.** Scope the token to the one
  repository, give it repository write and nothing more, and revoke it in your
  forge settings the moment the phone goes missing.
- **The page is served from your own site**, so the only party in the exchange
  besides you is your forge.

## Your forge has to allow it

A page cannot call an API that does not permit cross-origin requests, and this
is where forges differ. Checked directly, 2026-08-01:

- **Codeberg** — allowed. The preflight answers with
  `Access-Control-Allow-Origin: *` and permits `Authorization`, so the app works
  against `codeberg.org` with no configuration at all.
- **Self-hosted Forgejo or Gitea** — blocked by default. The API returns no CORS
  headers, and the browser refuses before the request is sent. An instance admin
  turns it on in `app.ini`:

  ```ini
  [cors]
  ENABLED = true
  ALLOW_DOMAIN = your.pages.domain
  ```

- **GitHub and GitLab** — not supported. GitHub's API does send CORS headers, so
  an adapter would be short, but none is shipped: this project does not claim
  provider support it has not exercised.

When the browser blocks the call, the app says so and names `[cors]` rather than
showing a bare network error.

## What it writes

The same bytes `records new` writes — timestamp filename or slug, the same
frontmatter block, the same single blank line between message blocks. The
`#tag Title` line takes the same syntax the `/record` skill does, so the first
tag files the record in `records/<tag>/`.

That claim is checked rather than asserted. `tools/pwa/fixtures.json` holds the
cases; `tools/pwa/record.js` and the engine each run them, and both have to
agree:

```bash
cd tools/others/python && python -m pytest tests/test_phone_fixtures.py
```

The browser's half of the same file is at `/skriv/selftest.html` — a page you can
open on the phone itself.

## What it does not do

- **No assistant turns.** It writes your side. The `— model` signature line comes
  from the engine, which is not running on your phone.
- **No Ollama, no skills.** See [record from your phone](phone.md).
- **No history.** It commits; your repo is the history. Close a record with
  **Finish** and start another.
- **Offline it composes but does not commit.** Writes queue until the connection
  returns, then push themselves.
