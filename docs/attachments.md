# Attachments

A record is a Markdown file. When it needs to carry something — a photo, a
screen recording, a PDF — the file goes **next to the words it belongs to**,
in your own repo. There is no store, no service, and nothing to sign up for.

## The shape

A record that carries files becomes a folder. Hugo calls this a *leaf page
bundle*:

```
records/2026-07-06_23-30/
├── index.md      the record itself
├── image.png     →  /2026-07-06_23-30/image.png
├── paper.pdf     →  /2026-07-06_23-30/paper.pdf
└── clip.mp4      →  /2026-07-06_23-30/clip.mp4
```

Inside `index.md` you reference them by plain filename:

```markdown
![the whiteboard](image.png)

[the paper](paper.pdf)

<video src="clip.mp4" controls></video>
```

**The URL does not change.** A flat `records/2026-07-06_23-30.md` and a bundle
`records/2026-07-06_23-30/index.md` both publish at `/2026-07-06_23-30/`, so
converting a record never breaks a link anyone has. Chapters and tag folders
work exactly as before — a bundle inside `records/3/` still groups under
chapter 3.

Any file type publishes verbatim. No processing, no configuration, no asset
pipeline: what you put in the folder is what gets served.

## Doing it

```bash
records attach records/2026-07-06_23-30.md ~/Pictures/whiteboard.jpg
```

That converts the flat record to a bundle if it is not one already, copies the
file in, and prints the Markdown to paste. `--append` writes the link into the
record for you; `--dry-run` shows the conversion and the copy without doing
either — worth using the first time, because changing a record's shape is the
kind of thing you want to see before it happens.

Your source file is **copied, never moved**. It stays where it was.

Filenames are slugified and extensions preserved, and nothing is ever
overwritten — a second `whiteboard.jpg` becomes `whiteboard-1.jpg`.

To start a record that already expects attachments:

```bash
records new --bundle "Whiteboard session"
```

Flat records stay flat. A record only becomes a folder when it has something
to carry.

## Size discipline

Git is a poor blob store, and this is the honest part of the page.

Git keeps **every version of every file forever**. A 40 MB video committed
once, then replaced, is 80 MB in the repository — permanently, for everyone
who clones it, including you on a slow connection in three years. Text
compresses and diffs; binaries do neither.

A rough guide, not a rule:

| Size | Verdict |
|---|---|
| under 1 MB | Fine. Screenshots, diagrams, small photos. Commit freely. |
| 1–10 MB | Fine occasionally. A handful per repo, not per record. |
| 10–100 MB | Think. Can it be smaller? A 4 MB re-encode usually says everything the 60 MB original did. |
| over 100 MB | Don't. |

Above the line, the honest answers are: **shrink it** (re-encode the video,
resize the photo — the site displays it in a column of text, not a cinema),
**link it** (host the file wherever it already lives and put a URL in the
record), or **leave it out** (a record describing a video is often worth more
than the video, and always worth more than a repository nobody can clone).

There is deliberately no git-annex, no LFS and no external store here. Those
solve the problem by adding a second thing that has to survive alongside your
repo — which is exactly the dependency this project exists to avoid. If it
does not fit in a git repo, the honest answer is that it does not belong in
one.

## Checking they are still there

```bash
records verify --repo .
```

Every image and media reference in every record, resolved the way the site
resolves it. A record pointing at a file that was moved or deleted renders as
a broken image on the site and a missing figure in the PDF, silently — this is
how you find out first. See [preservation](preservation.md).

## Known limitation

In `pageMode: single` and `single-flowing`, every record renders on the front
page, where a relative `image.png` resolves against `/` instead of the
record's own URL and 404s. Bundles render correctly on their own pages and in
the PDF and EPUB. The front-page fix belongs to the theme, and is on the
roadmap.
