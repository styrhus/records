# Keep it simple

Small changes, big difference. Everything here is one file, one edit.

## Your own words on the front page

The front page is `records/_index.md`. Open it, delete what is there,
write what you want. It is a normal Markdown file.

## The big greeting

The handwritten word at the top of the front page comes from
`hugo/hugo.yaml`:

```yaml
params:
  greeting: Velkommen
```

Change it to your own word, or remove the line for no greeting at all.

## The site title

Also in `hugo/hugo.yaml`: `title: Records`. It shows in the header and
in the browser tab.

## A different color

The theme's colors and greeting font also live in `hugo/hugo.yaml`, under
`params.style`. Change one and rebuild — see [make it awesome](awesome.md).

## Writing records

Every Markdown file in `records/` becomes a page. Name them one of two ways:

- `2026-07-05_18-41.md` — date and time are read from the filename.
- `her-er-jeg.md` — any name you like; add `date:` in the frontmatter.

Useful frontmatter:

- `title:` — shown in the list and on the page
- `draft: true` — keep writing, stay unpublished
- `featured: true` — pin the record to the top of the list

The AI skills listed on the front page (`/record`, `/stick`, and friends)
handle most of this for you.

## Publish

Push to `main`. The workflow builds and publishes the site — nothing
else to do.
