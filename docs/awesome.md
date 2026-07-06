# Make it awesome

Want the site to look like *you*? The quickest changes are in
`hugo/hugo.yaml`; the full design lives in the **Fuglekasse** theme under
`hugo/themes/Fuglekasse/`.

## The three layouts

They live in `hugo/themes/Fuglekasse/layouts/`:

- `baseof.html` — the frame: head, all the CSS, header, footer
- `home.html` — the front page: greeting, intro, the list of records
- `page.html` — a single record: wraps the user and assistant turns in
  styleable sections

## Colors

Set the palette from `hugo/hugo.yaml` — no need to open the theme.
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
family, or drop a `.woff2` into `hugo/themes/Fuglekasse/static/fonts/` and set
`params.style.fontfile` to it.

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
