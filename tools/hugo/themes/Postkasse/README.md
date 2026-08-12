# Postkasse

<!-- werden: 0.12.2 badstu-beetle -->

The growth theme for [blyant records](https://codeberg.org/blyant/records) — Norwegian for
*mailbox*, wearing the name of the werden cycle that dreamed it.

[Fuglekasse](../Fuglekasse/README.md) is the default theme and stays deliberately small: flat
templates, inline CSS, no build step, no assets pipeline. That fence is a feature, so it holds —
and everything that wants to grow past it lives here instead. Postkasse has an **assets pipeline**
and is allowed **JavaScript**. That is the entire reason it is a separate theme.

Today Postkasse renders the same site Fuglekasse does. The difference is structural: the stylesheet
and the script are built, minified and fingerprinted out of `assets/` instead of sitting inline in
`baseof.html`. Site-wide search, build-time backlinks, an honest RSS feed and reading chrome are
planned on top of that foundation — see the
[kiste roadmap](../../../../docs/records/developers/roadmap/kiste/ROADMAP.md).

## Switching themes

One line in your site's `hugo.yaml`:

```yaml
theme: Postkasse
```

Nothing else changes. Every `params.*` key below behaves exactly as it does under Fuglekasse, the
records directory is untouched, and the PDF/EPUB build (`bin/build.sh` → `tools/pandoc/`) needs no
change — it reads `records/` and the site config, never the theme. Switch back by putting
`Fuglekasse` there again.

## The assets pipeline

`layouts/baseof.html` builds two resources:

| Source | Built as | Notes |
|---|---|---|
| `assets/css/postkasse.css` | `/css/postkasse.min.<hash>.css` | executed as a template — `params.style` feeds the palette and the `@font-face` |
| `assets/js/postkasse.js` | `/js/postkasse.min.<hash>.js` | plain JavaScript, loaded with `defer` |

The hash is cache-busting only; no `integrity` attribute is emitted, because an SRI hash needs CORS
headers the CDN in `params.cdnURL` is not guaranteed to send.

`params.cdnURL` works for the built assets as well as for `static/` files. Two partials do this,
and they are not interchangeable:

- `_partials/static-url.html` takes a **path** (`favicon`, `logo`, `pdf`, `epub`, `booklet`, the
  font file) and resolves it site-relative, or under `cdnURL` in production builds.
- `_partials/asset-url.html` takes a **resource**. A built resource's `.RelPermalink` already
  carries the baseURL sub-path, so the CDN form strips that before re-prefixing — passing a resource
  through `static-url.html` would double the sub-path on a site served at `…/records/`.

To restyle, edit `assets/css/postkasse.css` — but reach for `params.style` first (below); it covers
the palette and the display font without opening the theme.

## Shipped files

Postkasse ships copies of three things from Fuglekasse, on purpose:

- **The font** (`static/fonts/architects-daughter.woff2` + `OFL.txt`). Only the *active* theme's
  `static/` is mounted, and `tools/pandoc/book.lua` looks the display font up at
  `themes/<theme>/static/<params.style.fontfile>`. The copy is what keeps the PDF build working with
  no theme-specific branch in `book.lua`.
- **`static/fuglekasse.svg`**, so a site carrying the default `logo: fuglekasse.svg` (and the
  `favicon` fallback) keeps resolving when it switches themes. Postkasse ships **no mark of its
  own** — point `params.logo` and `params.favicon` at your own file in the repo-root `static/`.
- **`content/`** — the front page (`_index.md`), the 404 page (`404.md`) and the demo record. Theme
  content does not chain between themes either; without these the site would lose its front page and
  its `/404.html`.

## The mirrored contract

Postkasse is a **standalone theme**, not a Hugo theme component. Its partials are copies of
Fuglekasse's and carry the same contract:

- `record.html` takes the same dict — `{content, prefix?, voice?}` — strips assistant signature
  lines, rewrites relative `records/` links to forge raw URLs, and wraps turns in
  `<section class="user|assistant">`.
- `repo-link.html` takes the same `{kind: "raw"|"tree", branch?}` and resolves the same
  Forgejo/GitHub/GitLab shapes.
- `lang-badge.html`, `comment-link.html` and `static-url.html` are unchanged copies.

**These are copies and must be kept in step.** That is the accepted cost of a standalone theme: it
buys Postkasse the freedom to diverge without any pressure on Fuglekasse. The signature-stripping
rule already lived in two places before this theme existed (`record.html` and `book.lua`); it now
lives in three.

## Customising

The whole look is driven from your site's `hugo.yaml` — you rarely need to open the
theme. Postkasse ships the same defaults Fuglekasse does; anything you set in `hugo.yaml` wins:

```yaml
params:
  style:
    font: "Architects Daughter"   # the handwritten greeting font family
    light: { bg: "#d5d6db", fg: "#343b58", dim: "#9699a3", accent: "#34548a", surface: "#e5e6ea", card: "#f5f5f7" }
    dark:  { bg: "#282a36", fg: "#f8f8f2", dim: "#8b96c9", accent: "#bd93f9", surface: "#21222c", card: "#323445" }
```

- `bg` background · `fg` text · `dim` quiet text (footer, labels) · `accent` links and
  the user border · `surface` code blocks, table stripes, blockquotes, TOC and Spotify
  panels · `card` single-mode record page background.
- Light mode defaults to Tokyo Night Light, dark mode to Dracula.
- To swap the greeting font file, drop a `.woff2` into `static/fonts/` and point
  `style.fontfile` at it. Keep it in `static/`, not `assets/` — `book.lua` reads it from there.

Theme `[params]` defaults do not chain between themes, so `hugo.toml` here repeats Fuglekasse's full
set. Layering is unchanged: theme `hugo.toml` → site `hugo.yaml` → `HUGO_PARAMS_*`.

## Page mode

`params.pageMode` picks how the home page presents your records. All four modes work:

- `basic` *(default)* — a reverse-chronological link index, one line per record.
- `posts` — a feed of the latest records, each with an excerpt and a *Read more* link.
  `params.postsCount` (default `3`) sets how many appear.
- `single` — a one-page site: every record rendered inline as a "document" card, `_index.md` on
  top. `params.singleOrder` sets the order — `"asc"` *(default)* oldest→newest, `"desc"` newest
  first.
- `single-flowing` — one continuous conversation: only the Human/Assistant turns, no titles, tags,
  dates or chapters (numbered folders are flattened), records split by a dimmed `· · ·` divider and
  ordered per `singleOrder`. The PDF/EPUB build follows the same presentation.

An unknown value warns and falls back to `basic`.

Both single modes publish **one page**: every record is already on the front page, so
`bin/build.sh` merges `tools/hugo/one-page.yaml` for them and the built site is `index.html`,
`404.html`, a `LICENSE.md` page if you keep one, your `static/` files, the PDF/EPUB/booklet and the
attachments beside a record in a page bundle — no per-record URLs and no `sitemap.xml`. Link to a
record by its in-page anchor (`/#<slug>`) rather than `/<slug>/`; a page that should be published on
its own anyway can say `build: {render: always}` in its front matter. A hand-run `hugo`/`hugo server`
skips the merge and still writes the record pages.

## Book look

For a `single-flowing` site that should read as a proper book, set `params.bookLook: true` and drop
up to three specially named files in your content directory root: `forside.md` (front cover —
rendered first, standing in for the `_index.md` intro), `side-1.md` (page 1) and `bakside.md` (back
cover, always last). Dated records flow between them per `singleOrder`; each file is optional. Give
them a `title:` so the table of contents has something to show.

The PDF/EPUB build follows suit — the generated cover is dropped in favour of `forside`, the
specials get their own pages, and the `· · ·` dividers separate only the dated records. **Off by
default**; in any other page mode the param is ignored with a build warning.

## Anchored separators

Set `params.threeDotAnchor: true` (single-flowing only) to turn the `· · ·` dividers into clickable
anchors, and to add one above the very first record — so every point in the stream is a shareable
link. Each divider becomes an `<a href="#XXXXX">` whose id is five characters from the URL-safe
alphabet `A–Z a–z 0–9 - . _ ~` (66 characters, `66⁵ ≈ 1.25 billion` possible ids). The ids are
**stable across builds** — derived by hashing each record's slug (Hugo has no build-time RNG), so a
copied link survives a rebuild. They collide only on a slug-hash collision, negligible in practice.
**Off by default**; ignored (with a build warning) in every other page mode, and the PDF/EPUB book
is unaffected — this is web-only.

## Chapters

Name a first-level folder in your content directory after a number — arabic (`records/2/`) or roman
(`records/iv/`, case-insensitive) — and the home page groups its records into a **chapter** that
folds and unfolds when its title is clicked. Chapters appear in `single` and `basic` modes; `posts`
stays flat and `single-flowing` flattens them into its stream.

`params.chapterState` sets the fold state: `"latest"` *(default)* opens the chapter holding the
newest record, `"expanded"` opens every chapter, `"collapsed"` closes every one. A single chapter
overrides it with `chapterOpen: true` or `chapterOpen: false` in its `_index.md` front matter.

Records outside numbered folders render first; chapters follow in ascending order, arabic before
roman (`-1, 0, 2, i, iv`), regardless of `singleOrder` — that only orders records *inside* a
chapter. Give a chapter a title with an `_index.md` carrying a `title:` (`1 — This is Chapter 1`);
the `_index.md` never becomes a record. Hovering a chapter title reveals a `#` anchor that links to
it without toggling the fold. Note that a folder whose name is a valid roman numeral (`cd`, `mix`,
`ml`) becomes a chapter too — pick a different tag name if that is not what you mean.

## Table of contents

Set `params.showToc: true` for a floating table of contents — a button pinned to the top-right of
the **home page** in every mode but `posts`. **Off by default.**

Clicking it opens a panel: loose records first, then each chapter as a row you click to reveal its
records. In `single`/`single-flowing` the links jump to the record on the same page (opening a
collapsed chapter on the way); in `basic` they open the record's own page. In `single-flowing` the
panel is a flat list in stream order — the only place record titles appear.

## Filtering

Set `params.showFilter: true` for a record filter on the `single` home page — a funnel button
pinned bottom-left (beside the Spotify logo when that is set) opening a panel above it. **Off by
default** and honoured only in `single` mode; elsewhere it warns and is ignored.

The panel offers the tags actually used across your records (a card matches on *any* checked tag),
the languages set in front matter plus a `(none)` bucket, an inclusive from/to date range, and a
**Word** field. The groups combine: a card must pass every active group. Chapters whose cards are
all filtered away hide; chapters holding matches open automatically and return to their
`chapterState` fold when the filter clears.

The Word field searches everything visible on a card as you type, tried as a case-insensitive
regular expression (`foo|bar`, `\bword\b`) and falling back to a literal search on invalid syntax.
Whitespace is collapsed first, so a phrase matches across line breaks. Browsers with the CSS Custom
Highlight API tint the matches.

Filter state lives in the URL query string —
`?tags=a,b&language=nb,none&from=2026-01-01&to=2026-12-31&word=foo%7Cbar` — so a filtered view is a
shareable link that survives reload. Tags containing a comma cannot be filtered (the comma is the
separator). Without JavaScript the panel opens and closes as a plain `<details>`, controls inert.

## Get PDF

Set `params.pdf` to a filename — `pdf: records.pdf` — and the footer shows a **Get PDF** link to
that file at the site root. **Unset by default**: the theme only renders the link; the file is built
by the [blyant records](https://codeberg.org/blyant/records) repo's Pages workflow with the tooling
in `tools/pandoc/`, which turns the whole site into one PDF book — cover, table of contents with
page numbers, loose records then chapters ascending, in the site's light palette and typography.
Drafts, `LICENSE.md`, `404.md` and `ignoreFiles` matches stay out, signature lines are stripped, and
`singleOrder`, `dateTitleFormat`, `datePostFormat` and `showTags` are honoured. With
`pageMode: single-flowing` the book mirrors the flowing layout — no contents page, titles, dates or
per-record page breaks.

Set `params.epub` the same way for a **Get EPUB** link: same assembled book, styled structurally
(`tools/pandoc/epub.css`), since e-readers override fonts and render grayscale — the site palette
does not carry over. Set `params.booklet` for a **Get booklet** link: the same book at A5, imposed
two-up on A4 landscape sheets in folding order, on a white background to spare ink. Print two-sided
(flip on the **short** edge) and fold. With **Book look** on, a blank verso follows `forside` and
`side-1` and `bakside` stays last, so the outer sheet folds into the two covers. The booklet
additionally needs `pypdf` next to WeasyPrint; the build skips just the booklet, with a note, when
it is missing. All three params are independent and unset by default.

Records without a hand-written `title:` show their timestamp slug (`2026-07-06_23-25`). Set
`params.dateTitleFormat` to a Go/Hugo [date layout](https://gohugo.io/methods/time/format/) — e.g.
`"02. January 2006"` — to render those as formatted dates everywhere titles appear; explicit titles
are never reformatted. Set `params.datePostFormat` (same syntax) to also show the record's date
bottom-right on record pages and in the posts/single home modes; a page opts out with
`showDate: false`.

Dates without a UTC offset — front matter `date:` values and filename timestamps — are interpreted
in the site's `timeZone`. It is a root `hugo.yaml` key, not a param: Hugo ignores root keys in theme
configs, so no theme can ship a default.

## Tags

Give a record `tags: [linux, hardware]` and dim `#linux #hardware` labels appear under the post — on
the record page and in the posts/single home modes. Display only: no tag pages, no links. On by
default (`params.showTags: true`); set it `false` to hide them site-wide, or opt one record out with
`showTags: false`. Records may live in subfolders (`records/linux/…`); those folders are
organisation only and render no index page.

## Voice-recorded records

Give a record `voiceRecorded: true` and a small microphone icon in the accent colour follows the
**Human** label on every human turn — on the record page, in all home modes, and in the PDF/EPUB —
marking the conversation as spoken rather than typed.

## Footer repo link

`params.repoURL` puts a small link to your repository in the footer (and, with
`params.insidesBranch`, a second link to that branch). `params.showRepoURL: false` hides both —
`repoURL` itself stays useful, as it also rewrites relative `records/` links to raw forge URLs. On
by default.

Those rewritten links follow your forge's URL shape: `params.repoLinkStyle` is `auto` by default —
a github.com or gitlab.com `repoURL` gets the GitHub/GitLab shapes, everything else Forgejo/Gitea —
or set `forgejo` | `github` | `gitlab` explicitly (say, for self-hosted GitLab). An unknown value
warns and falls back to `forgejo`. `params.repoBranch` (default `main`) is the branch those links
point at. The PDF/EPUB raw links follow the same rules.

## Logo

Set `params.logo` to a file in `static/` to pin a brand mark to the bottom-right corner of every
page — a fixed, non-clickable image that stays put while you scroll. Postkasse ships no mark of its
own; drop yours into the repo-root `static/`. Unset, no logo is shown.

## Favicon

Set `params.favicon` to a file in `static/` for the browser-tab icon (`<link rel="icon">`). Unset,
it falls back to the shipped `fuglekasse.svg`. Kept separate from `params.logo` because favicons are
square while logos are often rectangular.

## Spotify

Set `params.spotify` to a Spotify URL — share form
(`https://open.spotify.com/playlist/<id>`) or embed form, both work — and a small Spotify logo is
pinned to the bottom-left corner of every page, opposite `params.logo`. Clicking it opens the
embedded player above the logo; clicking elsewhere closes it (the music keeps playing). Nothing is
fetched from Spotify until first open, so the player sizes itself to the visible panel. Works
without JavaScript via a `noscript` fallback. Unset, no logo is shown.

## Comment links

Set `params.commentURL` to your forge's new-issue endpoint and every record gets a small **Comment**
link (bottom-right, styled like the post date) opening a prefilled issue titled
`[<site> - #<record-slug>]: `. It appears on record pages and single-mode cards; `LICENSE.md` is
skipped. The `<site>` label defaults to your `baseURL` host; `params.commentSite` overrides it (useful
under a custom domain the build does not know about). **Unset by default**, and the PDF/EPUB books
never include them.

## Demo mode

`params.demoMode` (default `false`) renders the theme-shipped demo records — content files carrying
`demo: true` in their front matter (Postkasse ships one, `content/example/example-recording.md`) —
but only while the site has no real records: your first record hides them automatically, nothing to
edit. `false` never shows them.

The theme also ships the default front page (`content/_index.md`). Like the 404 page below it is
shadowed by your own: create `records/_index.md` and it replaces the theme's, independent of
`demoMode`.

Two limitations, by design: hidden demo records still exist at their direct URLs and in the sitemap
(they are only unlisted), and demo content never appears in the PDF/EPUB/booklet builds (those read
the records directory from disk, never theme content). `demo` is thereby a reserved front-matter key.

## 404 page

Postkasse ships a default error page (`content/404.md`), built to `/404.html` so the host serves it
for missing URLs. To write your own, shadow it with a `404.md` in your content directory, keeping
this front matter:

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

Below the front matter the body is plain Markdown. (`url` and `layout` make the page render as
`/404.html`; `showDate: false` hides the post date; `build.list: never` keeps it out of record
lists.)

## License

MIT for the theme code. The bundled *Architects Daughter* font is SIL OFL 1.1 — see
[`static/fonts/OFL.txt`](static/fonts/OFL.txt).
