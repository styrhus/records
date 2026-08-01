# Hugo has it all

This site is plain [Hugo](https://gohugo.io/). Its whole look is one small
default theme — **Fuglekasse** — that you restyle from `tools/hugo/hugo.yaml`, edit,
or replace. Anything Hugo can do, your records home can do.

## How it is wired

- `tools/hugo/hugo.yaml` — the configuration and the brand knobs; content comes from
  `../../records`
- `static/` (repo root) — your own assets: logo, favicon, images. Fork-owned
  like `records/`; upstream never ships or moves files there
- `tools/hugo/themes/Fuglekasse/` — the default theme: four templates and one font,
  the entire design
- `bin/build.sh` — the one build path: resolves the site URL, runs Hugo and
  the book build; CI calls it, and so can you
- `.forgejo/workflows/pages.yml` — builds and publishes on every push to
  `main`; forks publish to their own address with zero edits

## Run it locally

Install [Hugo](https://gohugo.io/installation/), then:

```sh
cd tools/hugo
hugo server
```

## Deliberately switched off

- **Taxonomies** — no tags, no categories, no clutter. Remove them from
  `disableKinds` in `tools/hugo/hugo.yaml` to turn them back on.
- **RSS** — Hugo's built-in feed template would leak the signature lines
  through page summaries. Add your own `tools/hugo/layouts/rss.xml` if you
  want a feed.

## Go further

Menus, shortcodes, image processing, multilingual sites — the
[Hugo documentation](https://gohugo.io/documentation/) covers it all.
Any template you add under `tools/hugo/layouts/` takes over from Fuglekasse
and Hugo's defaults.
