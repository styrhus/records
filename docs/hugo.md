# Hugo has it all

This site is plain [Hugo](https://gohugo.io/) — no theme standing in the
way. Anything Hugo can do, your records home can do.

## How it is wired

- `hugo/hugo.yaml` — the configuration; content comes from `../records`
- `hugo/layouts/` — three templates, and that is the entire design
- `.forgejo/workflows/pages.yml` — builds and publishes on every push to
  `main`; forks publish to their own address with zero edits

## Run it locally

Install [Hugo](https://gohugo.io/installation/), then:

```sh
cd hugo
hugo server
```

## Deliberately switched off

- **Taxonomies** — no tags, no categories, no clutter. Remove them from
  `disableKinds` in `hugo/hugo.yaml` to turn them back on.
- **RSS** — Hugo's built-in feed template would leak the signature lines
  through page summaries. Add your own `hugo/layouts/rss.xml` if you
  want a feed.

## Go further

Menus, shortcodes, image processing, multilingual sites — the
[Hugo documentation](https://gohugo.io/documentation/) covers it all.
Any template you add under `hugo/layouts/` takes over from Hugo's
defaults.
