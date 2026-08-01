# Preservation

Publishing is about reach. This page is about the other thing: what is still
here in twenty years, when Hugo is gone, pandoc is gone, this repository is
abandoned, and the person opening the cupboard is you — or someone who
inherited your laptop.

Markdown files survive. Git history survives, if the repo does. Images
referenced by relative paths survive only if somebody kept them. Nothing else
is guaranteed.

So: bundle it, checksum it, and keep a plain-text copy a human can read with
`cat`.

## One bundle

```bash
records archive                      # ./records-2026-08-01_16-30.zip
records archive --out ~/backups/records.zip
records archive --dry-run            # what would go in, and what would not
```

The archive holds the whole records tree, every image and attachment the
records actually reference, the site config, the cycle line — and a manifest.

The manifest is the point. It is the **first** entry in the zip, so it can be
read without unpacking anything:

```bash
unzip -p records-2026-08-01_16-30.zip manifest.json
```

Inside: every entry with its size and SHA-256, the werden cycle, the source
repo URL, the git commit, and a UTC timestamp. There is also a `README.txt`
written for somebody with no context at all — what the files are, how a
`## Human` / `## Assistant` record reads, what the signature lines mean, and
how to check the checksums by hand with nothing but Python.

Output is **deterministic**: fixed timestamps on the zip entries, sorted entry
order. Two archives of an unchanged tree are byte-identical, so they diff and
deduplicate. The one varying input is the manifest's `created` stamp — set
`SOURCE_DATE_EPOCH` to pin that too:

```bash
SOURCE_DATE_EPOCH=1000000000 records archive --out a.zip
```

`zipfile` and `hashlib`, both from the Python standard library. No compression
library, no external checksum tool, nothing to install.

## Reading it back

An archive nobody has ever opened is a hope, not a backup.

```bash
records verify records-2026-08-01_16-30.zip
```

Every checksum recomputed against the manifest. Mismatches, missing entries
and unexpected extras are each reported by name; the exit code is non-zero if
anything is wrong.

The other mode is the one you will use far more often:

```bash
records verify --repo .
```

Does every image and media reference in every record still resolve to a file
that exists? A record pointing at something that was moved renders as a broken
image on the site and a missing figure in the PDF, **silently**. This is how
you find out first. See [attachments](attachments.md).

## The plain-text copy

The format that outlives all of the above, including this project:

```bash
records export --format text --out ~/archive/records-text/
records export --format text --single --out ~/archive/records.txt
```

No Markdown syntax that needs rendering to make sense. Turns become labelled
speakers, links carry their URL inline, images say `[image: path]`, code
becomes indented blocks. The single-file form opens with a table of contents
and a paragraph explaining, to someone who has never heard of any of this,
what they are looking at.

This is the copy you hand to an archive, a lawyer, or a grandchild.

## Making it a habit

One archive, made once, is a souvenir. The habit is the backup.

```bash
records archive --check
```

`--check` verifies an existing archive **and** the live checkout, and prints
nothing at all when everything is fine. That silence is deliberate: it is what
makes it usable from cron, which mails you whatever a job prints. It exits
non-zero and prints the faults as JSON when something is wrong.

```cron
# Sunday 03:00 — a fresh archive, then check it
0 3 * * 0  cd ~/records && records archive --out ~/backups/records-$(date +\%F).zip
5 3 * * 0  cd ~/records && records archive --check --out ~/backups/records-$(date +\%F).zip
```

### Rotation

A suggestion, not a policy:

- **Keep about a dozen.** Weekly archives for the last three months. They are
  mostly text; a year of them is usually smaller than one video.
- **Three places, two kinds.** The repository itself, an external disk you can
  hold, and one somewhere else entirely. At least one of them should not be a
  disk that is plugged into the same machine as the others.
- **One copy is not a backup.** A copy on the same disk as the original dies
  with the disk. A copy only in a cloud account dies with the account. This is
  the whole reason the archive is one boring, self-describing zip file: you
  can put it anywhere, including somewhere that has never heard of this
  project.
- **Check the oldest one, not the newest.** The newest archive was written
  minutes ago and is fine. Rot shows up in the ones nobody has touched.

There is deliberately no upload, no service and no account here. An archive is
a file. Where it goes is yours to decide.
