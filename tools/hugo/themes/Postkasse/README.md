# Postkasse

<!-- werden: 0.12.4 badstu-moth -->

The growth theme for [Styrhus Records](https://codeberg.org/styrhus/records) — Norwegian for
*mailbox*, wearing the name of the werden cycle that dreamed it.

[Fuglekasse](../Fuglekasse/README.md) is the default theme and stays deliberately small: flat
templates, inline CSS, no build step, no assets pipeline. That fence is a feature, so it holds —
and everything that wants to grow past it lives here instead. Postkasse has an **assets pipeline**
and is allowed **JavaScript**. That is the entire reason it is a separate theme.

Postkasse renders the same site Fuglekasse does, and then grows past it. The stylesheet and the
script are built, minified and fingerprinted out of `assets/` instead of sitting inline in
`baseof.html`, and on that foundation live the features the fence keeps out of Fuglekasse:
site-wide [search](#search), build-time [backlinks](#backlinks), an honest [RSS feed](#rss),
[reading chrome](#reading-chrome), [attachment rendering](#attachments) and per-record
[Open Graph cards](#meta-description-and-link-previews) — each documented below.

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

- `record.html` takes the same dict — `{content, prefix?, voice?}`, plus an optional `page` key
  for attachment resolution — strips assistant signature lines, rewrites relative `records/` links
  to forge raw URLs, and wraps turns in `<section class="user|assistant">`. Postkasse's copy
  delegates to `strip-signatures.html`, `resolve-attachments.html` and
  `rewrite-record-links.html`, so the signature rule lives in **one** place per renderer (theme
  partial, `book.lua`) instead of two inside the theme — and its forge-link regex is deliberately
  tighter than Fuglekasse's (relative paths only), because the loose form mangled attachment URLs
  on a site served under a path containing `records/`.
- `repo-link.html` takes the same `{kind: "raw"|"tree", branch?}` and resolves the same
  Forgejo/GitHub/GitLab shapes.
- `lang-badge.html`, `comment-link.html`, `head-extra.html` and `static-url.html` are unchanged
  copies, as is the `_markup/render-codeblock-assistant.html` code-block hook.

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
    light: { bg: "#d5d6db", fg: "#343b58", dim: "#5a5d67", accent: "#34548a", surface: "#e5e6ea", card: "#f5f5f7" }
    dark:  { bg: "#282a36", fg: "#f8f8f2", dim: "#a0aad8", accent: "#bd93f9", surface: "#21222c", card: "#323445" }
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

Inside `side-1.md` and `bakside.md` a horizontal rule (`---` on its own line, with a blank line above
it) renders as a **sunken divider** — a rounded trough one line-height tall, carved out of the page
background. Elsewhere — records, `forside.md` — a rule keeps the browser default. Web only; the PDF
and EPUB are unaffected. Watch the blank line: `---` directly under a line of text is Markdown for a
heading, not a rule.

## Anchored separators

Set `params.threeDotAnchor: true` (single-flowing only) to turn the `· · ·` dividers into clickable
anchors, and to add one above the very first record — so every point in the stream is a shareable
link. With **Book look** on, the `forside`, `side-1` and `bakside` pages never carry a divider (with
or without this option), so the covers sit flush against the stream, as in the book. Each divider becomes an `<a href="#XXXXX">` whose id is five characters from the URL-safe
alphabet `A–Z a–z 0–9 - . _ ~` (66 characters, `66⁵ ≈ 1.25 billion` possible ids). The ids are
**stable across builds** — derived by hashing each record's slug (Hugo has no build-time RNG), so a
copied link survives a rebuild. They collide only on a slug-hash collision, negligible in practice.
**Off by default**; ignored (with a build warning) in every other page mode, and the PDF/EPUB book
is unaffected — this is web-only.

## Time-gap labels

Set `params.showTimeEarlier: true` (single-flowing only) to label each record with the distance
back from the newest one: a small dim line reading `3 days earlier`, `2 months and 4 days earlier`
or `1 year and 2 months earlier` floats in the record's top-right corner, beside its first turn
(to the left of the `permalinkButton` icon when that is on too). The newest record is "now", so it
states its own date there instead — formatted with `params.dateTitleFormat`, falling back to
`2006-01-02` when that is unset, and wrapped in a `<time datetime>` element. It carries the extra
class `time-now` (styled like the rest by default; a fork's stylesheet can pick it out), and
bookLook's cover pages carry no label at all and never serve as the anchor. The gap arithmetic is
deliberately approximate — 30-day months, twelve-month years, anything under a minute rounded up
to one — a sense of distance rather than a timestamp, recomputed on every build so the labels
follow the newest record. The PDF and EPUB label their records the same way. **Off by default**;
ignored (with a build warning) in every other page mode.

## Chapters

Name a first-level folder in your content directory after a number — arabic (`records/2/`) or roman
(`records/iv/`, case-insensitive) — and the home page groups its records into a **chapter** that
folds and unfolds when its title is clicked. Chapters appear in `single` and `basic` modes; `posts`
stays flat and `single-flowing` flattens them into its stream.

`params.chapterState` sets the fold state: `"latest"` *(default)* opens the chapter holding the
newest record, `"expanded"` opens every chapter, `"collapsed"` closes every one. A single chapter
overrides it with `chapterOpen: true` or `chapterOpen: false` in its `_index.md` front matter.

Set `params.chapterToggle: true` when most chapters are rarely written to. The home page then shows
only the chapter holding the newest record — open, with its title hidden, so its records read like
loose ones — and a small chapters icon, right-aligned above them, reveals every chapter as usual.
**Off by default**, honoured in `single` and `basic` (elsewhere it warns and is ignored). The switch
is a plain checkbox, so it works without JavaScript; with it, the reader's choice is remembered in
the browser (`localStorage`), a link into a hidden chapter (a TOC entry, a `#` anchor) shows all
chapters, and an active filter shows matches in every chapter. If the newest record sits outside a
chapter, the folded view shows no chapters at all.

Records outside numbered folders render first; chapters follow in ascending order, arabic before
roman (`-1, 0, 2, i, iv`), regardless of `singleOrder` — that only orders records *inside* a
chapter. Give a chapter a title with an `_index.md` carrying a `title:` (`1 — This is Chapter 1`);
the `_index.md` never becomes a record. Hovering a chapter title reveals a `#` anchor that links to
it without toggling the fold; on touch screens, which have no hover, the `#` anchors stay visible. Note that a folder whose name is a valid roman numeral (`cd`, `mix`,
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
Highlight API tint and underline the matches.

Filter state lives in the URL query string —
`?tags=a,b&language=nb,none&from=2026-01-01&to=2026-12-31&word=foo%7Cbar` — so a filtered view is a
shareable link that survives reload. Tags containing a comma cannot be filtered (the comma is the
separator). Without JavaScript the panel opens and closes as a plain `<details>`, controls inert.

## Search

Set `params.showSearch: true` for site-wide search — a magnifier beside the site title on **every**
page, opening a panel that queries every record you have. **Off by default**, and it needs one line
in the site config as well (below).

It is a static file and a loop, not a service and not a library. At build time
`layouts/home.json.json` writes `/index.json`: one object per record with its title, ISO date, tags,
link and text. The browser fetches that file **on the first search**, never on page load, lowercases
it once, and answers every keystroke from memory.

Words are ANDed and matched as substrings, so a partial word finds the whole one; `"quote a phrase"`
to keep it together. A hit in the title outranks a hit in the tags, which outranks the body, and how
often a term occurs breaks the rest of the tie; equal scores go to the newer record. Twenty results
at most — past that the answer is a better query, not a longer list. `/` opens search from anywhere
on the page, up/down walk the results, Enter follows one, Escape closes.

Links follow the page mode, exactly as the feed and the backlinks do: the record's own URL in
`basic`/`posts`, the front-page `#slug` anchor in `single`/`single-flowing`, where no record page is
built. In `single` a result inside a collapsed chapter unfolds it on arrival.

**Signature lines never reach the index.** The text goes through the same `strip-signatures.html`
the page and the feed use, so a `— model-name` line the page hides cannot be searched for either.
Speaker headings go too — `Human` and `Assistant` stand in every record and would match everything —
and so does the `Assistant` label the ```` ```assistant ```` fence adds. Code blocks stay: a function
name is one of the things worth finding.

### Turning it on

Two switches, because a theme cannot set them both. Hugo merges `outputFormats` and `mediaTypes`
from a theme config but **not** `outputs`, so the output itself is one knowing edit in
`tools/hugo/hugo.yaml`, the same shape RSS needs:

```yaml
outputs:
  home: [html, json]     # publishes /index.json

params:
  showSearch: true       # shows the search button
```

Uncomment both. With the param on and the output missing the build warns and shows nothing rather
than shipping a box that finds nothing. There is nothing to mirror in `one-page.yaml`. The format is
Hugo's built-in `json` on purpose — naming a theme-declared format there would make a Fuglekasse
build fail outright, where `json` merely warns that no template matched.

### What it costs

`params.searchWords` decides how much of each record reaches the index. `0` *(the default)* indexes
the whole text; a number indexes the opening N words instead. Titles and tags are indexed in full
either way. Measured on a synthetic corpus (mean 4.9 kB per record):

| records | `searchWords` | raw | gzip | per record |
|---|---|---|---|---|
| 100 | 0 (whole text) | 363 KB | 111 KB | 3.7 KB |
| 1 000 | 0 (whole text) | 4.1 MB | 1.2 MB | 4.2 KB |
| 1 000 | 200 | 1.2 MB | 373 KB | 1.2 KB |
| 1 000 | 120 | 843 KB | 249 KB | 0.9 KB |
| 1 000 | 40 | 369 KB | 104 KB | 0.4 KB |

The whole text scales linearly and honestly: 10 000 records is around **41 MB raw / 12 MB gzip**,
which is not a file to hand a browser. A word cap does not — it holds the index near a fixed size
per record however far the archive grows. Rule of thumb: the whole text up to a few thousand
records, `searchWords: 120` or so past that, accepting that a phrase deep inside a long
conversation stops being findable. Nothing here splits or shards the index; the cap is the answer,
and it is deliberately the only one.

Without JavaScript the wrapper ships `hidden` and the script removes it, so a reader sees no search
affordance at all — not a dead input. What it does not do: no stemming or fuzzy matching (`records`
will not find a record that only says `record`); only records are indexed (`site.RegularPages` — not
the `_index.md` intro, chapter titles, attachment filenames or the license page); and search and the
`single`-mode filter do not know about each other — a result whose card the filter hides is
navigated to and not seen.

## Backlinks

`params.showBacklinks` (default **true**): records that link to a record are listed under it as
**Referenced by**, computed at build time from the markdown source — before relative `records/`
links become forge raw URLs, which is why the graph is not empty. A link counts when its last path
segment names a record, so `records/<slug>.md`, `../<slug>.md`, `/<slug>/` and `<slug>/index.md`
are all the same target; external links, `#fragments` and self-links are skipped. Shown on record
pages and `single` cards (linking to `#slug` there); not in `single-flowing`, which shows no
per-record metadata. Two records with the same base name in different folders are one node.
Reference-style link definitions (`[a]: …`) and autolinks are not scanned.

## RSS

Off until the site config says so, and Postkasse-only. Swap the `disableKinds` line in `hugo.yaml`
(and `one-page.yaml`) for the commented alternative there — Hugo ignores root keys in theme
configs, so no theme can flip it. `layouts/rss.xml` then publishes `/index.xml` with **full record
content**, not summaries: a summary of a conversation is its opening exchange out of context.
Signature lines are stripped through the same `strip-signatures.html` partial the page uses, so a
line the page hides cannot reach the feed; attachment and record links are resolved and made
absolute so a reader away from the site still resolves them. `params.feedCount` (default 20) caps
the items; in the one-page modes items link to `/#<slug>`. **Leaving RSS enabled under Fuglekasse
publishes Hugo's embedded feed instead — signatures and all.** The feed carries no
`content:encoded` and no `<enclosure>`, so a podcast client will not pick up audio attachments.

## Reading chrome

Four params, all **off by default**, each independently switchable, each warning where it has no
effect:

- `showReadingTime` — `1 min · 21 words` under the title, computed at build (`.ReadingTime`; the
  count includes code blocks). Record pages, posts excerpts and single cards; not `single-flowing`.
- `stickyNav` — `single-flowing` only: a slim bar naming the record you are scrolled into.
  Filled and revealed by JavaScript; a reader without it sees nothing, not an empty bar.
- `permalinkButton` — `single`/`single-flowing` only: replaces the record-level hover `#` with a
  visible link icon. Without JavaScript it is an ordinary anchor; with it, a click copies the
  absolute URL and says so.
- `keyNav` — `single`/`single-flowing` only: `j`/`n` next record, `k`/`p` previous. Ignores modifier chords and typing in fields,
  unfolds a collapsed chapter before scrolling, updates the hash. The keys are documented only
  here — there is no on-screen hint.

## Attachments

A record that carries files is a leaf page bundle — `records attach` does the conversion, and
[`docs/attachments.md`](../../../../docs/attachments.md) documents the convention. Postkasse
renders them as what they are, through render hooks in `layouts/_markup/`:

- **Images** get `loading=lazy`, intrinsic dimensions and a `srcset` at 480/960/1440
  (`params.responsiveImages`, default **true**; jpeg/png/webp). A markdown *title* — `![alt](img
  "caption")` — becomes a `<figure>` with a caption. A captioned image must stand on its own line;
  written mid-sentence the paragraph splits around it.
- **Video and audio** links become players (`<video controls>`, `<audio controls>`, `preload=none`).
- **A PDF or any other file** becomes a typed, sized download link.
- `params.showAttachments` (default **false**) adds a strip under the record listing everything in
  its bundle.

The hooks resolve URLs through the page's own resources, so they are site-root-absolute and survive
the one-page modes — under Fuglekasse a relative `image.png` on a `single` front page 404s, and
here it does not. Raw HTML (`<img src="shot.png">` under `unsafe: true`) is rewritten too, but only
by resource name: raw HTML pointing outside the record's own bundle, `srcset=`/`poster=`
attributes, and `<source>` tags without `src=` are left as written. The PDF/EPUB books do not use
the hooks — `book.lua` already resolves images its own way, and a video link stays a labelled link
there.

## Get PDF

Printing a page straight from the browser always uses the light palette, even for a
reader in dark mode, and leaves out the floating buttons and the logo; the PDF below is
the proper book.

Set `params.pdf` to a filename — `pdf: records.pdf` — and the footer shows a **Get PDF** link to
that file at the site root. **Unset by default**: the theme only renders the link; the file is built
by the [Styrhus Records](https://codeberg.org/styrhus/records) repo's Pages workflow with the tooling
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

## Featured records

`featured: true` in a record's front matter — what `/stick` writes — pins the
record above the date ordering on the front page in every mode, including
`singleOrder: desc`, where it would otherwise sit at the bottom. In the two
one-page modes it also takes a faint accent tint: in `single` a tinted variant
of the normal card, in `single-flowing` a soft rounded panel lifted off the
bare stream. The tint is mixed from your own palette, so it follows a fork's
colours in both light and dark. The PDF/EPUB books stay chronological.

## Voice-recorded records

Give a record `voiceRecorded: true` and a small microphone icon in the accent colour follows the
**Human** label on every human turn — on the record page, in all home modes, and in the PDF/EPUB —
marking the conversation as spoken rather than typed.

## Assistant blocks

A fenced code block marked `assistant` is not shown as code: its content is parsed as Markdown and
rendered inside a slate panel labelled **Assistant**, in the same small-caps type as the `## Assistant`
turn headings. Use it for output from another model quoted inside a record.

````markdown
```assistant
# Dyr

**tadpole** *(5)* — bygger seg om innenfra.
```
````

The panel has its own fill in each colour scheme — a mid slate on a light page, a faint lift off the
background on a dark one — while its text, links, borders and code fills come from the *dark* half of
`params.style`, so a fork's palette carries into them. The label is near-white on a light page and
light grey on a dark one. Headings inside are a step smaller than the same headings outside, and
their ids are dropped, so a `## Assistant` line *inside* the block cannot break the turn splitting.
Nested fences work if the outer fence uses more backticks than the inner one. Same rendering in the
PDF and EPUB; the print booklet draws the panel as an outlined white box.

## Turn labels

The turn headings show the words written in the record, **Human** and **Assistant**. To show other
words, set them in `hugo.yaml`:

```yaml
params:
  turnLabels:
    human: Menneske
    assistant: Assistent
```

This changes only what readers see. The records still say `## Human` and `## Assistant`, turn anchors
stay `#human-N`, and a named turn keeps its name (`Menneske (Ola)`). Legacy `## User` headings take
the human label too. The assistant label also names the assistant-block panel. The PDF, EPUB and
booklet use the same words, but they read `hugo.yaml` only, so set the labels there rather than
through a `HUGO_PARAMS_TURNLABELS_*` variable.

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

`params.logoSize` sizes it: `default` (48px, the default), `bigger-1` (60px, +25%), `bigger-2`
(72px, +50%) or `bigger-3` (96px, +100%). The bigger steps only apply above `48rem` of viewport
width — narrower screens (phones) always get the default size. An unknown value warns and falls
back to `default`.

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

## Meta description and link previews

`layouts/_partials/head-meta.html` writes the page's `<meta name="description">`
and its OpenGraph tags — the line search engines show under the title, and the
card chat apps build when someone pastes a link. Both matter most in
`single`/`single-flowing` mode, where the front page is the whole site and so
the whole search surface.

The description is derived at build time, so it never goes stale:

1. the page's own `description:` front matter, if it has one;
2. on the home page only, `params.description`;
3. otherwise the opening **14 words** — of the newest record on the home page,
   of the page itself everywhere else — followed by `...`.

The excerpt is taken from the rendered text with the `Human`/`Assistant`
headings, the `— model` signature lines and any code blocks removed, so it
starts at real conversation rather than at a speaker label or a paste. A
record that opens with something unpresentable gets a hand-written
`description:` in its front matter.

Change the cut length by editing `$words` at the top of the partial.

Alongside it every page gets `og:title` (the same display title as `<title>`,
without the site suffix), `og:type` (`website` on the front page, `article` on
a record), `og:url`, `og:site_name`, `og:locale` and `og:description`, plus
`article:published_time` on records.

`og:image` is the one that needs a file from you: set `params.ogImage` to
something in `static/`, around 1200x630. It must be a raster format — the
crawlers that render previews do not accept SVG, which is why it does not fall
back to `params.logo`. Unset, no image tag is written and previews fall back to
whatever the client picks. `params.cdnURL` applies here like it does to the
other static assets.

Or let the records draw their own: set `params.ogCards: true` and
`bin/build.sh` runs `records card` over every record after the Hugo build,
writing a 1200x630 SVG quote card in the site's palette to
`/cards/<slug>.svg`, and each record page's `og:image` points at its card
(the home page keeps `params.ogImage`). Postkasse-only, skipped in the
one-page modes (no per-record pages to carry the tag) and skipped with a note
when python3 or recordkit is absent — the pandoc pattern. Two caveats, stated
rather than hidden: the cards are SVG, which Slack and Discord render but many
crawlers do not (rasterizing would be a dependency, and PNG conversion is
explicitly not `card.py`'s job); and the tag is emitted whenever the param is
set, even if generation was skipped — the same trust the **Get PDF** link
places in `params.pdf`.

## Extra `<head>` markup

For JSON-LD, an extra meta tag or a site-verification token, override the empty
`head-extra.html` partial instead of the whole template: create
`layouts/_partials/head-extra.html` in your site (beside `hugo.yaml`, not in the
theme) and put the markup there.

```html
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Book","name":"…"}
</script>
```

A site-level `layouts/baseof.html` would also work, but it shadows the theme's
copy wholesale — every later theme change to the head, the palette or the CSS
then silently stops reaching your site, and the symptom is a new feature simply
not appearing. The partial only ever holds your own markup, so it cannot go
stale that way.

## License

AGPL-3.0-or-later for the theme code. The bundled *Architects Daughter* font is SIL OFL 1.1 — see
[`static/fonts/OFL.txt`](static/fonts/OFL.txt).
