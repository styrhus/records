# Make it awesome

Want the site to look like *you*? The whole design lives in three small
files in `hugo/layouts/`. No theme, no framework — what you see is all
there is.

## The three layouts

- `baseof.html` — the frame: head, all the CSS, header, footer
- `home.html` — the front page: greeting, intro, the list of records
- `page.html` — a single record: wraps the user and assistant turns in
  styleable sections

## Colors

All CSS sits at the top of `baseof.html`. Two palettes are built in:
Tokyo Night Light for light mode, Dracula for dark mode. Change the
variables and everything follows:

```css
--bg       /* background */
--fg       /* text */
--dim      /* quiet text: footer, labels */
--accent   /* links, the user border */
--surface  /* code blocks */
```

## Fonts

The greeting uses Architects Daughter, loaded from
`hugo/static/fonts/`. Drop your own `.woff2` file there and update the
`@font-face` rule in `baseof.html`.

## The footer

The small links at the bottom come from `repoURL` in `hugo/hugo.yaml`.
Add a `records/LICENSE.md` with `title: License` and a license link
appears too.

## See it while you work

```sh
cd hugo
hugo server
```

Open the address it prints; every edit reloads instantly.
