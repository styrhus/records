# CLAUDE.local.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A publish-your-conversations site: Markdown transcripts in `records/` are built by Hugo and deployed to Codeberg Pages (`https://<owner>.codeberg.page/<repo>/`). Forks publish their own site with zero edits — owner/repo/URL are derived from the push in `.forgejo/workflows/pages.yml`.

## Layout

- `records/` — the content, and the only "data" here. `_index.md` is the front page. Records are timestamp-named (`2026-07-06_23-22.md`). 
- `hugo/` — the Hugo site. `hugo.yaml` is the site config (`contentDir: ../records` — there is no `content/` dir).
- `hugo/themes/Fuglekasse/` — the default theme. Deliberately minimal: flat template system (Hugo ≥ 0.146, so `home.html`/`page.html`, no `_default/`), all CSS inline at the top of `layouts/baseof.html`, no assets pipeline, no build step.
- `.ai/skills/` — the conversation skills (`/record`, `/all`, `/me`, `/stick`, `/esc`, `/gc`, `/gcp`, `/phil-gc`, `/cpd`, `/diff-1`…`/diff-20`, `/review`, `/poet`, `/pirate`, `/eq`, `/bff`, `/spellcorrect`); `.claude/skills/` symlinks into it. Skills copied from the user's dotfiles keep their content, but the commit skills (`/gc`, `/gcp`, `/phil-gc`) are simplified to the single repo at `$PWD` — no VSCode multi-root handling, plain `git status`/`git diff` injection, no detect-dirty-repos.sh. The recording skills (`/record`, `/all`, `/me`) and `/cpd` are checkout-aware: they `find` the shallowest `*/hugo/hugo.yaml` (maxdepth 4, dot-dirs and node_modules pruned) from `$PWD` and read its `contentDir` (missing line = `../records`) — so a records clone nested inside another project works from that project's workspace, and inside this repo the probe resolves to `./records` as before. The recording skills write transcripts to the resolved dir, falling back to the old docs-like-dir heuristics when no config is found. `/cpd` runs git as `git -C <checkout>` (no config found = `$PWD`), presents the diff and commit message for confirmation before running, and takes its deploy command from `params.deployCommand` in the discovered `hugo.yaml` (commented by default; unset = a push-triggered workflow in the checkout is the deploy, nothing to run — detected via `ls`, no helper script). `/stick` remains `$PWD`-scoped: run it from the records checkout.
- `others/` — an optional AI-free engine and editor plugins that run the *mechanical* skills without a model. `python/` is the deterministic `recordkit` library + `records` CLI (records-dir discovery, tag routing, frontmatter, git/deploy, MPRIS) emitting JSON; `vscode/` and `neovim/` are chat-style plugins that call the CLI; `ollama/` documents wiring a local model back in for the AI skills. Covers `/record` setup, `/all`, `/me`, `/esc`, `/stick`, `/gc`, `/gcp`, `/cpd`, `/myname`, `/mucke`. See `others/README.md`.
- `.mem/` — a gitignored directory for local memory the plugins write (e.g. `/myname`); a tracked `.gitkeep` keeps it present in fresh clones.
- `docs/` — user-facing customization guides linked from the README.

## Commands

```bash
cd hugo
hugo                 # build to hugo/public/ (gitignored)
hugo server          # local dev at :1313
HUGO_PARAMS_PAGEMODE=single hugo server   # try a param override without editing config
```

There are no tests or linters; verification is building and inspecting output. Note: `hugo --quiet` suppresses `WARN` lines — build without it when checking template warnings.

## Architecture

**Config layering.** Theme defaults live in `hugo/themes/Fuglekasse/hugo.toml` `[params]`; the site's `hugo.yaml` `params:` deep-merges over them (site wins); `HUGO_PARAMS_*` env vars override both (CI uses `HUGO_PARAMS_REPOURL`). New theme options must follow this pattern: default in theme toml, read via `site.Params.*`, documented in the theme README and as a commented example in `hugo.yaml`.

**Rendering pipeline.** Records are `## User` / `## Assistant` turns with assistant signature lines (`— model-name`). `layouts/_partials/record.html` takes rendered HTML (`.Content` or `.Summary`) and: strips signatures, rewrites relative `records/` links to forge raw URLs, and wraps each turn in `<section class="user|assistant">` for styling. All record display — single pages (`page.html`), the posts-mode excerpts, and single-mode cards (`home.html`) — must go through this partial.

**pageMode.** `params.pageMode` switches the home page: `basic` (link index, default), `posts` (latest `postsCount` excerpts with Read-more), `single` (one-page site: `_index.md` card first, then every record ascending as a document card; no auto links to records). `home.html` warns and falls back to basic on unknown values; `baseof.html` tags `<main class="mode-…">` for the CSS.

**Content conventions.** The explicit `date:` frontmatter field is authoritative for ordering (`frontmatter.date: [':default', ':filename']`); the filename is only a fallback for records without a `date:` field, so a record's position never depends on its filename. All three pageModes order by `.Date` (index modes newest-first, single mode oldest-first). Permalinks use the full `:contentbasename` (time-only slugs would collide across days). Frontmatter flags: `draft: true` (archetype default; kept out of the site), `featured: true` (pinned to top of index, set by `/stick`), `showDate: false` (hides that page's `.post-date` line in all three render spots; 404.md sets it). A file named `records/LICENSE.md` gets a footer link (link text = its `title:`, any value; falls back to "License") and is excluded from record lists — both keyed on the filename, not the title. `tags: [a, b]` renders as dim display-only `#a #b` labels (`.post-tags`, above `.post-date`) in the same three render spots; `params.showTags` (theme default `true`) toggles them site-wide, `showTags: false` opts a page out; taxonomies stay disabled, so tags never become links. `/record #tag Title` (also `/all`, `/me`) files the record under `records/<first-tag>/` with the remaining text as title and all tags in frontmatter; `/stick` resolves slugs folder-aware via `find`. A site-config `cascade` in `hugo.yaml` targets `kind: section` with `build.render/list: never`, so folder URLs like `/linux/` 404 (and no section-template WARN) while records inside keep `/linux/<slug>/` URLs. The 404 page is content: the theme ships `content/404.md` (merged under the site content by Hugo's mounts; a `records/404.md` shadows it). A content file at path `/404` shadows Hugo's standalone 404 kind — that's why the file itself must carry `url: /404.html`, `layout: "404"`, and `build.list: never`, and overrides must keep that front matter block. The built `404.html` is what Codeberg Pages serves for missing URLs. `params.dateTitleFormat` (unset in the theme; the site sets `"02. January 2006"`) renders timestamp-fallback titles as `.Date` formatted with that Go layout — in `page.html`, all three home modes, and the `<title>` tag; hand-written titles are never reformatted. `params.datePostFormat` (unset in the theme; the site sets `"02. January 2006 15:04"`) adds a bottom-right `.post-date` line with the formatted `.Date` to record pages and posts/single-mode cards; unset shows none.

**Deliberate omissions.** RSS and taxonomies are disabled in `hugo.yaml` — the embedded RSS template would leak signature lines through summaries. Goldmark `unsafe: true` is intentional (records are trusted first-party content).

## Conventions

- Keep the theme minimal: four templates + one partial, inline CSS, no build tooling. Resist adding partials, JS, or asset pipelines.
- `records/` markdown is user content — don't edit records except via the skills or on explicit request.

## Editing this file

This file (`CLAUDE.local.md`) may be edited without asking for confirmation. Keep it accurate: when a change alters documented behavior — config keys, ordering, pageModes, the rendering pipeline — update the matching section in the same turn.

The working `CLAUDE.local.md` is gitignored (`*.local.md`), so edits to it are never committed. To keep a change in version control (and reach forks), mirror it into the tracked `CLAUDE.local.md.example.md` in the same turn — matching that file's shorter, genericized tone rather than pasting full private detail.
