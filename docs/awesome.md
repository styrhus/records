# Make it awesome

Want the site to look like *you*? The quickest changes are in
`tools/hugo/hugo.yaml`; the full design lives in the **Fuglekasse** theme under
`tools/hugo/themes/Fuglekasse/`.

## The layouts

They live in `tools/hugo/themes/Fuglekasse/layouts/`:

- `baseof.html` — the frame: head, all the CSS, header, footer
- `home.html` — the front page: greeting, intro, the list of records
- `page.html` — a single record: wraps the user and assistant turns in
  styleable sections
- `404.html` — the error page for missing URLs

## Colors

Set the palette from `tools/hugo/hugo.yaml` — no need to open the theme.
Fuglekasse ships Tokyo Night Light (light mode) and Dracula (dark); override
any key under `params.style`:

```yaml
params:
  style:
    light: { bg: "#d5d6db", fg: "#343b58", dim: "#9699a3", accent: "#34548a", surface: "#cbccd1" }
    dark:  { bg: "#282a36", fg: "#f8f8f2", dim: "#8b96c9", accent: "#bd93f9", surface: "#44475a" }
```

`bg` background · `fg` text · `dim` quiet text (footer, labels) · `accent`
links and the user border · `surface` code blocks. The raw CSS still sits at
the top of `baseof.html` if you want to go deeper.

## Fonts

The greeting uses Architects Daughter. Point `params.style.font` at another
family, or drop a `.woff2` into `tools/hugo/themes/Fuglekasse/static/fonts/` and set
`params.style.fontfile` to it.

## Chapters

Put records in a folder named after a number — `records/1/`, `records/2/`
(or roman: `records/i/`, `records/ii/`) — and the front page groups them into
a **chapter**: a titled block that folds open and shut. Loose records show
first; chapters follow in order.

To name a chapter, add a file `records/1/_index.md` with a title:

```yaml
---
title: This is Chapter 1
---
```

The heading then reads `1 — This is Chapter 1`. Skip the file (or the title)
and the chapter just shows its number.

## The footer

The small links at the bottom come from `repoURL` in `tools/hugo/hugo.yaml`. Don't
want your repo linked? Set `showRepoURL: false` under `params:` — the link
disappears, while `repoURL` keeps rewriting relative links inside records.
Add a `records/LICENSE.md` and a license link appears too. Its `title:` becomes
the link text — any language works (`title: Lizenz`); without one it reads "License".

## The error page

Broken links land on the theme's default 404 page. To write your own, add a
`records/404.md` — it shadows the theme's — keeping this front matter above
your Markdown:

```yaml
---
title: Page not found
url: /404.html
layout: "404"
showDate: false
build:
  list: never
---
```

## See it while you work

```sh
cd tools/hugo
hugo server
```

Open the address it prints; every edit reloads instantly.
