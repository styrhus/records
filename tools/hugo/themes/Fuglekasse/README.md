# Fuglekasse

<!-- werden: 0.12.2 badstu-beetle -->

The default theme for [blyant records](https://codeberg.org/blyant/records) — Norwegian for
*nesting box*. A deliberately small, config-driven Hugo theme for publishing
conversation transcripts: four templates, one web font, no build step.

## Customising

The whole look is driven from your site's `hugo.yaml` — you rarely need to open the
theme. Fuglekasse ships the defaults below; anything you set in `hugo.yaml` wins:

```yaml
params:
  style:
    font: "Architects Daughter"   # the handwritten greeting font family
    light: { bg: "#d5d6db", fg: "#343b58", dim: "#9699a3", accent: "#34548a", surface: "#e5e6ea", card: "#f5f5f7" }
    dark:  { bg: "#282a36", fg: "#f8f8f2", dim: "#8b96c9", accent: "#bd93f9", surface: "#21222c", card: "#323445" }
```

- `bg` background · `fg` text · `dim` quiet text (footer, labels) · `accent` links and
  the user border · `surface` code blocks, table stripes, blockquotes, TOC and Spotify
  panels (lighter than `bg` in light mode, slightly darker in dark mode) · `card`
  single-mode record page background (lighter than `bg` in both modes, for contrast).
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
  oldest→newest (top→bottom), `"desc"` puts the newest at top.
- `single-flowing` — one continuous conversation: greeting and `_index.md`
  intro on top, then only the Human/Assistant turns of every record — no
  titles, tags, dates or chapters (numbered folders are flattened into the
  stream). Records are separated by a dimmed centred `· · ·` divider and
  ordered by date per `params.singleOrder`. The PDF/EPUB build follows the same
  presentation (no table of contents, no per-record page breaks or chapter
  files).

Both single modes publish **one page**. Since every record is already on the
front page, `bin/build.sh` merges `tools/hugo/one-page.yaml` for them, and the
built site is `index.html`, `404.html`, a `LICENSE.md` page if you keep one,
your `static/` files, the PDF/EPUB/booklet and the attachments beside a record
in a page bundle — no per-record URLs and no `sitemap.xml`. Link to a record
with its in-page anchor (`/#<slug>`, or a `· · ·` anchor — see below) rather
than `/<slug>/`. A page you want published on its own anyway can say so in its
front matter with `build: {render: always}`. Running `hugo` or `hugo server` by
hand skips the merge, so previews still show the per-record pages.

## Book look

For a `single-flowing` site that should read as a proper book, set
`params.bookLook: true` and drop up to three specially named files in your
content directory root: `forside.md` (front cover — rendered first, standing
in for the `_index.md` intro), `side-1.md` (page 1, right after the cover)
and `bakside.md` (back cover, always last). The dated records flow between
them per `singleOrder`; each file is optional and any subset works. They
render in the stream like any other record — give them a `title:` so the
table of contents has something to show.

The PDF/EPUB build follows suit: the generated cover page (greeting, title,
date) is dropped in favour of `forside.md`, `forside` and `side-1` each end
their page, `bakside` starts a fresh one, and the `· · ·` dividers only
separate the dated records. **Off by default**; in every other page mode the
param is ignored (with a build warning) and the three files are ordinary
records.

Inside `side-1.md` and `bakside.md` a horizontal rule (`---` on its own line,
with a blank line above it) renders as a **sunken divider** — a rounded trough
one line-height tall, carved out of the page background. Elsewhere — records,
`forside.md` — a rule keeps the browser default. Web only; the PDF and EPUB
are unaffected. Watch the blank line: `---` placed directly under a line of
text is Markdown for a heading, not a rule.

## Anchored separators

Set `params.threeDotAnchor: true` (single-flowing only) to turn the `· · ·`
dividers into clickable anchors, and to add one above the very first record —
so every point in the stream is a shareable link. Each divider becomes an
`<a href="#XXXXX">` whose id is five characters from the URL-safe alphabet
`A–Z a–z 0–9 - . _ ~` (66 characters, `66⁵ ≈ 1.25 billion` possible ids).

The ids are **stable across builds**: each is derived by hashing the record's
slug (Hugo has no build-time RNG), so a link you copy today still works after
the next rebuild. They look random but are deterministic. Ids collide only on a
hash collision over the record slugs, which is negligible in practice.

**Off by default**; in every other page mode the param is ignored (with a build
warning). The PDF/EPUB book is unaffected — this is a web-only feature.

## Chapters

Name a first-level folder in your content directory after a number — arabic
(`records/-1/`, `records/0/`, `records/2/`) or roman (`records/i/`, `records/iv/`,
case-insensitive) — and the home page groups its records into a **chapter**: a
block titled with the folder name that folds and unfolds when its title is
clicked. Chapters appear in the `single` and `basic` page modes (the `posts`
feed stays flat, and `single-flowing` flattens chapters into its stream).

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
in every page mode but `posts`. It is **off by default** and does nothing in
`posts` mode.

Clicking the button opens a panel: loose (non-chapter) records first, then each
chapter as a row you click to reveal its records. In `single` mode the links
jump to the record on the same page (opening its chapter if it was collapsed);
in `basic` mode they open the record's own page. In `single-flowing` mode the
panel is a flat record list (chapters are flattened) whose links jump to the
record's spot in the stream — the records' display titles appear only here.

## Filtering

Set `params.showFilter: true` to add a record filter to the `single` home page —
a small funnel button pinned to the bottom-left corner (beside the Spotify logo
when that is set) that opens a panel above it. It is **off by default** and
honoured only in `single` mode; in every other page mode the param is ignored
(with a build warning).

The panel offers the tags actually used across your records (a card matches if
it carries *any* checked tag), the languages set in front matter plus a
`(none)` bucket for records without one (the language section only appears once
some record sets a `language:`), an inclusive from/to date range, and a **Word**
field. The groups combine: a card must pass every active group to stay visible.
Chapters whose cards are all filtered away hide too; chapters holding matches
open automatically while a filter is active and return to their `chapterState`
fold when it clears.

The Word field searches everything visible on a card — title, conversation
text, tags, date line — as you type. The input is tried as a case-insensitive
regular expression (`foo|bar`, `\bword\b`); invalid regex syntax falls back to
a plain case-insensitive text search, so `c++(` and friends still find their
literal selves. Whitespace is collapsed before matching, so a phrase matches
across line breaks. In browsers with the CSS Custom Highlight API the matched
words are tinted in the visible cards; elsewhere the filtering works the same
without the tint.

The filter state lives in the URL query string —
`?tags=a,b&language=nb,none&from=2026-01-01&to=2026-12-31&word=foo%7Cbar` —
kept in sync as you click and type, so a filtered view is a shareable link and
survives reload. A `#` anchor pointing at a filtered-out record does not scroll
anywhere until the filter clears. Tags containing a comma cannot be filtered
(the comma is the list separator). Without JavaScript the panel still opens and
closes as a plain `<details>`, but the controls do nothing.

## Get PDF

Set `params.pdf` to a filename — `pdf: records.pdf` — and the footer shows a
**Get PDF** link to that file at the site root. It is **unset by default**: the
theme only renders the link; the file itself is built by the
[blyant records](https://codeberg.org/blyant/records) repo's Pages workflow with the
tooling in `tools/pandoc/`, which turns the whole site into one PDF book — cover
(greeting and title), table of contents with page numbers, loose records first,
then chapters ascending, each record under its display title, in the site's
light palette and typography (`params.style.light`, syntax colours included).
Drafts, `LICENSE.md`, `404.md` and `ignoreFiles` matches stay out, signature
lines are stripped, and `singleOrder`, `dateTitleFormat`, `datePostFormat` and
`showTags` are honoured. The word-folder caveat from Chapters applies to the
PDF too. Comment the param out to disable both the link and the CI build.
With `pageMode: single-flowing` the book mirrors the site's flowing layout:
cover, then one continuous stream with `· · ·` dividers — no table of
contents, record titles, tags, dates, chapters or per-record page breaks.

Set `params.epub` the same way — `epub: records.epub` — for a **Get EPUB**
footer link. The same workflow step and tooling build it from the same
assembled book (same content, order and exclusions), but styled structurally
(`tools/pandoc/epub.css`): e-readers override fonts and render grayscale, so the
site palette does not carry over. Also unset by default; the two params are
independent — set either or both. In `single-flowing` mode the EPUB is one
continuous chapter — no table of contents or per-record file split.

Set `params.booklet` — `booklet: records-booklet.pdf` — for a paper-saving
**Get booklet** footer link: the same book rendered at A5 and imposed two-up
onto A4 landscape sheets in folding order, so four site pages share each sheet
of paper. Print it two-sided (flip on the **short** edge), fold the stack in
half, and it reads like a little newspaper; the page background is plain white
to spare ink (other palette colours carry over from the PDF). With
**Book look** on, the booklet behaves like a real book: a blank verso follows
`forside` and `side-1` (so each opens on a right-hand A5 page), and `bakside`
stays the very last page — the outer sheet prints `bakside` and `forside`
side by side, folding into the back and front covers. Also unset by
default and independent of the
other two params; the build additionally needs `pypdf` next to WeasyPrint
(the workflow skips just the booklet, with a note, when it is missing).

Records without a hand-written `title:` show their timestamp slug
(`2026-07-06_23-25`). Set `params.dateTitleFormat` to a Go/Hugo
[date layout](https://gohugo.io/methods/time/format/) — e.g. `"02. January 2006"` —
to render those as formatted dates ("06. July 2026") everywhere titles appear.
Explicit titles are never reformatted; unset keeps the raw slug.

Set `params.datePostFormat` (same layout syntax) to also show the record's date
bottom-right in each post — on record pages and in the posts/single home modes.
Unset, no post date is shown. A single page can opt out with `showDate: false`
in its front matter.

Dates without a UTC offset — front matter `date:` values and filename
timestamps — are interpreted in the site's `timeZone`, so CI builds on UTC
machines keep your wall-clock times. It's a root `hugo.yaml` key, not a param:
Hugo ignores root keys in theme configs, so Fuglekasse can't ship a default —
the blyant records repo's `hugo.yaml` sets `timeZone: Europe/Oslo`; point it at your
own zone.

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

Those rewritten links (and the footer branch link) follow your forge's URL
shape: `params.repoLinkStyle` is `auto` by default — a github.com or gitlab.com
`repoURL` gets the GitHub/GitLab shapes, everything else the Forgejo/Gitea
shape — or set `forgejo` | `github` | `gitlab` explicitly (say, for
self-hosted GitLab). `params.repoBranch` (default `main`) is the branch those
links point at. The PDF/EPUB raw links follow the same rules.

## CDN

Set `params.cdnURL` to a CDN pull-zone URL that fetches from this site, and
production builds serve static assets — favicon, the greeting font,
`params.logo`, and the PDF/EPUB/booklet — from there instead of the site
itself. Local development (`hugo server`) always stays site-relative. Unset
serves everything from the site, as usual.

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
playing). Nothing is fetched from Spotify until the panel is first opened — the
player loads on first open, so it sizes itself to the visible panel (a hidden
load would render the compact layout). Works without JavaScript via a
`noscript` fallback that loads the player with the page. Unset, no logo is
shown.

## Comment links

Set `params.commentURL` to your forge's new-issue endpoint —
`commentURL: https://codeberg.org/you/yourrepo/issues/new` — and every record
gets a small **Comment** link (bottom-right, styled like the post date) that
opens a prefilled issue titled `[<site> - #<record-slug>]: `. The link appears
on record pages and on the single-mode cards; `LICENSE.md` is skipped. The
`<site>` label defaults to your `baseURL` host; set `params.commentSite` to
override it (useful when the site is served under a custom domain the build
does not know about). **Unset by default** — no links are rendered, and the
PDF/EPUB books never include them.

## Demo mode

`params.demoMode` (default `false`) renders the theme-shipped demo records —
content files carrying `demo: true` in their front matter (the theme ships one,
`content/example/example-recording.md`) — but only while the site has no real
records: the first record of your own hides them automatically, nothing to
edit. `false` never shows them. The blyant records site ships `demoMode: true`
so a fresh fork is a working site out of the box.

The theme also ships the default front page (`content/_index.md`, the welcome
text). Like the 404 page below, it is shadowed by your own: create
`records/_index.md` and it replaces the theme's, independent of `demoMode`.

Two limitations, by design: hidden demo records still exist at their direct
URLs and in the sitemap (they are only unlisted), and demo content never
appears in the PDF/EPUB/booklet builds (those read the records directory from
disk, never theme content). `demo` is thereby a reserved front-matter key.

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
