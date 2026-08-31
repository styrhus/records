# Hugo has it all

This site is plain [Hugo](https://gohugo.io/). Its whole look is one small
default theme — **Fuglekasse** — that you restyle from `tools/hugo/hugo.yaml`, edit,
or replace. A second theme, **Postkasse**, ships beside it and is selected with a
single line in `tools/hugo/hugo.yaml`: `theme: Postkasse`. Anything Hugo can do,
your records home can do.

## How it is wired

- `tools/hugo/hugo.yaml` — the configuration and the brand knobs; content comes from
  `../../records`
- `static/` (repo root) — your own assets: logo, favicon, images. Fork-owned
  like `records/`; upstream never ships or moves files there
- `tools/hugo/themes/Fuglekasse/` — the default theme: four templates and one font,
  the entire design
- `tools/hugo/themes/Postkasse/` — the second theme: the same look and params, plus
  an assets pipeline; switch with `theme: Postkasse`
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
  through page summaries. Postkasse ships its own `layouts/rss.xml` that
  strips them; enabling it is a one-line `disableKinds` edit documented in
  `tools/hugo/hugo.yaml`. Under Fuglekasse, leave it off or add your own
  `tools/hugo/layouts/rss.xml`.

## How far it scales

Measured on a seeded synthetic corpus (mean 4.9 kB per record, hugo 0.165,
8 cores): build time is never the wall — 10 000 records build in 7.5 s
(`basic`) — but peak memory is about 2.5 GB there, which is the real CI
constraint. The one-page modes are the wall: `single` and `single-flowing`
put roughly 10 kB of HTML and 254 DOM elements per record on one page. They
stay comfortable to about 250 records, the gzipped front page crosses 1 MB
around 530, and at 10 000 the page is 93 MB and has stopped being a web
page. Above a few hundred records switch to `basic` — 10 000 records make a
929 kB front index and one ~23 kB page each — and prefer Postkasse, whose
external CSS/JS keeps the output at 120 MB where Fuglekasse's inlining
reaches 279 MB. Avoid `posts` at that scale: pagination re-runs the record
sort per page and takes minutes where `basic` takes seconds.

## Go further

Menus, shortcodes, image processing, multilingual sites — the
[Hugo documentation](https://gohugo.io/documentation/) covers it all.
Any template you add under `tools/hugo/layouts/` takes over from the active theme
and Hugo's defaults.
