# Fuglekasse

The default theme for [records](https://codeberg.org/tb4/records) — Norwegian for
*nesting box*. A deliberately small, config-driven Hugo theme for publishing
conversation transcripts: three templates, one web font, no build step.

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

To go further, the three templates live in `layouts/`, and all the CSS is at the top of
`layouts/baseof.html`.

## License

MIT for the theme code. The bundled *Architects Daughter* font is SIL OFL 1.1 — see
[`static/fonts/OFL.txt`](static/fonts/OFL.txt).
