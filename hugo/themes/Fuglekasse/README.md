# Fuglekasse

The default theme for [records](https://codeberg.org/tb4/records) — Norwegian for
*nesting box*. A deliberately small, config-driven Hugo theme for publishing
conversation transcripts: four templates, one web font, no build step.

## Customising

The whole look is driven from your site's `hugo.yaml` — you rarely need to open the
theme. Fuglekasse ships the defaults below; anything you set in `hugo.yaml` wins:

```yaml
params:
  style:
    font: "Architects Daughter"   # the handwritten greeting font family
    light: { bg: "#d5d6db", fg: "#343b58", dim: "#9699a3", accent: "#34548a", surface: "#cbccd1" }
    dark:  { bg: "#282a36", fg: "#f8f8f2", dim: "#8b96c9", accent: "#bd93f9", surface: "#44475a" }
```

- `bg` background · `fg` text · `dim` quiet text (footer, labels) · `accent` links and
  the user border · `surface` code blocks.
- Light mode defaults to Tokyo Night Light, dark mode to Dracula.
- To swap the greeting font file, drop a `.woff2` into `static/fonts/` and point
  `style.fontfile` at it.

To go further, the templates live in `layouts/`, and all the CSS is at the top of
`layouts/baseof.html`.

## Page mode

`params.pageMode` picks how the home page presents your records:

- `basic` *(default)* — a reverse-chronological link index, one line per record.
- `posts` — a feed of the latest records, each with an excerpt and a *Read more*
  link. `params.postsCount` (default `3`) sets how many appear.
- `single` — a one-page site: no auto-generated record links; instead every
  record is rendered inline as a "document" card, with `_index.md` on top.
  `params.singleOrder` sets the record order — `"asc"` *(default)* runs
  oldest→newest (top→bottom), `"desc"` puts the newest at top. Records are still
  reachable by direct URL, so links you write inside `records/*.md` keep working.

## Chapters

Name a first-level folder in your content directory after a number — arabic
(`records/-1/`, `records/0/`, `records/2/`) or roman (`records/i/`, `records/iv/`,
case-insensitive) — and the home page groups its records into a **chapter**: a
block titled with the folder name that folds and unfolds when its title is
clicked. Chapters appear in the `single` and `basic` page modes (the `posts`
feed stays flat).

`params.chapterState` sets the fold state: `"latest"` *(default)* opens the
chapter holding the newest record and collapses the rest, `"expanded"` opens
every chapter, `"collapsed"` closes every one. A single chapter overrides the
global setting with `chapterOpen: true` or `chapterOpen: false` in its
`_index.md` front matter (unset inherits `chapterState`).

Hovering a chapter title reveals a `#` link (as on record titles) that anchors
to `#chapter-<folder-name>`; clicking it links to the chapter without toggling
the fold.

Records outside numbered folders render first, exactly as without chapters;
the chapters follow in ascending order, arabic before roman (`-1, 0, 2, i, iv`),
regardless of `singleOrder` — that setting only orders the records *inside*
each chapter. An empty chapter folder shows nothing (git does not even track
empty directories); the chapter appears once its first record lands there.
Note that a folder whose name happens to be a valid roman numeral (`cd`,
`mix`, `ml`) is treated as a chapter too — pick a different tag name if that
is not what you mean.

Give a chapter a title by dropping an `_index.md` in its folder with a `title:`
— `records/1/_index.md` with `title: This is Chapter 1` renders the heading as
`1 — This is Chapter 1`. It is optional and needs an explicit `title:` (a bare
`_index.md` shows just the number); the `_index.md` never becomes a record of
its own.

## Table of contents

Set `params.showToc: true` to add a floating table of contents — a small button
pinned to the top-right corner of the **home page** (it stays put as you scroll)
in the `single` and `basic` page modes. It is **off by default** and does
nothing in `posts` mode.

Clicking the button opens a panel: loose (non-chapter) records first, then each
chapter as a row you click to reveal its records. In `single` mode the links
jump to the record on the same page (opening its chapter if it was collapsed);
in `basic` mode they open the record's own page.

## Get PDF

Set `params.pdf` to a filename — `pdf: records.pdf` — and the footer shows a
**Get PDF** link to that file at the site root. It is **unset by default**: the
theme only renders the link; the file itself is built by the
[records](https://codeberg.org/tb4/records) repo's Pages workflow with the
tooling in `pandoc/`, which turns the whole site into one PDF book — cover
(greeting and title), table of contents with page numbers, loose records first,
then chapters ascending, each record under its display title, in the site's
light palette and typography (`params.style.light`, syntax colours included).
Drafts, `LICENSE.md`, `404.md` and `ignoreFiles` matches stay out, signature
lines are stripped, and `singleOrder`, `dateTitleFormat`, `datePostFormat` and
`showTags` are honoured. The word-folder caveat from Chapters applies to the
PDF too. Comment the param out to disable both the link and the CI build.

Set `params.epub` the same way — `epub: records.epub` — for a **Get EPUB**
footer link. The same workflow step and tooling build it from the same
assembled book (same content, order and exclusions), but styled structurally
(`pandoc/epub.css`): e-readers override fonts and render grayscale, so the
site palette does not carry over. Also unset by default; the two params are
independent — set either or both.

Records without a hand-written `title:` show their timestamp slug
(`2026-07-06_23-25`). Set `params.dateTitleFormat` to a Go/Hugo
[date layout](https://gohugo.io/methods/time/format/) — e.g. `"02. January 2006"` —
to render those as formatted dates ("06. July 2026") everywhere titles appear.
Explicit titles are never reformatted; unset keeps the raw slug.

Set `params.datePostFormat` (same layout syntax) to also show the record's date
bottom-right in each post — on record pages and in the posts/single home modes.
Unset, no post date is shown. A single page can opt out with `showDate: false`
in its front matter.

## Tags

Give a record `tags: [linux, hardware]` in its front matter and dim `#linux
#hardware` labels appear under the post — on the record page and in the
posts/single home modes. They are display only: no tag pages, no links.
On by default (`params.showTags: true`); set it to `false` to hide them
site-wide, or opt a single record out with `showTags: false` in its front
matter. Records may live in subfolders (`records/linux/…`); the folders are
organisation only and render no index page of their own.

## Voice-recorded records

Give a record `voiceRecorded: true` in its front matter and a small
microphone icon in the accent colour follows the **Human** label on every
human turn — on the
record page, in all home modes, and in the PDF/EPUB books — marking the
conversation as spoken rather than typed. Absent or `false`, nothing changes.

## Footer repo link

`params.repoURL` puts a small link to your repository in the footer (and, with
`params.insidesBranch`, a second link to that branch). Set
`params.showRepoURL: false` to hide both — `repoURL` itself stays useful, as it
also rewrites relative `records/` links to raw forge URLs. On by default.

## Logo

Set `params.logo` to a file in `static/` (the theme ships `fuglekasse.svg`, or
drop your own into your site's `static/`) to pin a brand mark to the bottom-right
corner of every page. It is a fixed, non-clickable image that stays put while you
scroll. Unset, no logo is shown.

## Favicon

Set `params.favicon` to a file in `static/` to use as the browser-tab icon
(`<link rel="icon">`). Unset, it falls back to the shipped `fuglekasse.svg`. It is
kept separate from `params.logo` because favicons are square while logos are often
rectangular.

## Spotify

Set `params.spotify` to a Spotify URL — the share form
(`https://open.spotify.com/playlist/<id>`) or the embed form
(`…/embed/playlist/<id>`), both work — and a small Spotify logo is pinned to
the bottom-left corner of every page, opposite `params.logo` bottom-right,
staying put while you scroll. Clicking it opens a panel with the embedded
player above the logo; clicking anywhere else closes it (the music keeps
playing). Browsers that honour lazy-loaded iframes fetch nothing from Spotify
until the panel is first opened; the rest load the player with the page. Works
without JavaScript. Unset, no logo is shown.

## 404 page

Fuglekasse ships a default error page (`content/404.md`), built to `/404.html`
so the host serves it for missing URLs. To write your own, shadow it with a
`404.md` in your content directory, keeping this front matter:

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

Below the front matter, the body is plain Markdown. (`url` and `layout` make
the page render as `/404.html`; `showDate: false` hides the post date;
`build.list: never` keeps it out of record lists.)

## License

MIT for the theme code. The bundled *Architects Daughter* font is SIL OFL 1.1 — see
[`static/fonts/OFL.txt`](static/fonts/OFL.txt).
