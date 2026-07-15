#!/usr/bin/env bash
# Build the site's records into one PDF, EPUB and/or print booklet: book.lua
# assembles, pandoc renders — HTML printed by WeasyPrint for the PDF and the
# booklet (A5 pages imposed 2-up on A4 landscape), straight to EPUB otherwise.
# Usage: pandoc/build.sh [outdir]   (default: hugo/public)
# Env overrides: SITE_CONFIG, RECORDS_DIR (testing).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
OUTDIR="${1:-$ROOT/hugo/public}"
SITE_CONFIG="${SITE_CONFIG:-$ROOT/hugo/hugo.yaml}"

yaml_value() { # yaml_value <pattern> — first uncommented "key: value", stripped
  sed -n "s/^$1:[[:space:]]*//p" "$SITE_CONFIG" | head -1 | sed "s/[[:space:]]*#.*$//; s/[\"']//g"
}

# params.pdf / params.epub / params.booklet name the output files;
# unset/commented = feature off.
PDF_NAME="$(yaml_value '[[:space:]]*pdf')"
EPUB_NAME="$(yaml_value '[[:space:]]*epub')"
BOOKLET_NAME="$(yaml_value '[[:space:]]*booklet')"
if [ -z "$PDF_NAME" ] && [ -z "$EPUB_NAME" ] && [ -z "$BOOKLET_NAME" ]; then
  echo "pandoc/build.sh: params.pdf/epub/booklet unset in $SITE_CONFIG — skipping book build"
  exit 0
fi

# single-flowing has no record-title headings — no TOC, no EPUB per-record split.
PAGE_MODE="$(yaml_value '[[:space:]]*pageMode')"
TOC_ARGS=(--toc --toc-depth=2)
SPLIT_ARGS=(--split-level=2)
if [ "$PAGE_MODE" = "single-flowing" ]; then
  TOC_ARGS=()
  SPLIT_ARGS=()
fi

# contentDir as Hugo reads it, resolved relative to the config's directory.
CONTENT_DIR="$(yaml_value 'contentDir')"
RECORDS_DIR="${RECORDS_DIR:-$(cd "$(dirname "$SITE_CONFIG")/${CONTENT_DIR:-../records}" && pwd)}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pandoc lua "$SCRIPT_DIR/book.lua" "$RECORDS_DIR" "$ROOT" "$SITE_CONFIG" > "$TMP/book.json"
mkdir -p "$OUTDIR"

if [ -n "$PDF_NAME" ]; then
  pandoc -f json "$TMP/book.json" \
    --standalone "${TOC_ARGS[@]}" \
    -c "$SCRIPT_DIR/pdf.css" \
    --highlight-style "$SCRIPT_DIR/highlight.theme" \
    -o "$TMP/book.html"
  weasyprint "$TMP/book.html" "$OUTDIR/$PDF_NAME"
  echo "pandoc/build.sh: built $OUTDIR/$PDF_NAME from $RECORDS_DIR"
fi

# Print booklet: the same book at A5 on white (booklet.css), imposed two-up
# onto A4 landscape sheets in folding order by impose.py (pypdf); padding
# pages stay pypdf-blank white, matching the page background.
if [ -n "$BOOKLET_NAME" ]; then
  if python3 -c 'import pypdf' 2>/dev/null; then
    # bookLook: keep bakside the very last page (the back cover, sharing the
    # outer sheet with forside) — padding blanks go before it.
    IMPOSE_ARGS=()
    if [ "$PAGE_MODE" = "single-flowing" ] && [ "$(yaml_value '[[:space:]]*bookLook')" = "true" ] \
       && [ -f "$RECORDS_DIR/bakside.md" ]; then
      IMPOSE_ARGS=(--pad-before-last)
    fi
    pandoc -f json "$TMP/book.json" \
      --standalone "${TOC_ARGS[@]}" \
      -c "$SCRIPT_DIR/pdf.css" -c "$SCRIPT_DIR/booklet.css" \
      --highlight-style "$SCRIPT_DIR/highlight.theme" \
      -o "$TMP/booklet.html"
    weasyprint "$TMP/booklet.html" "$TMP/booklet-a5.pdf"
    python3 "$SCRIPT_DIR/impose.py" "${IMPOSE_ARGS[@]}" "$TMP/booklet-a5.pdf" "$OUTDIR/$BOOKLET_NAME"
    echo "pandoc/build.sh: built $OUTDIR/$BOOKLET_NAME from $RECORDS_DIR"
  else
    echo "pandoc/build.sh: params.booklet set but pypdf is missing — skipping booklet" >&2
  fi
fi

if [ -n "$EPUB_NAME" ]; then
  # title = dc:title (book.lua only sets pagetitle); header-includes cleared —
  # its palette/@font-face CSS is PDF-only. Split at h2 = one file per record.
  pandoc -f json "$TMP/book.json" \
    --lua-filter "$SCRIPT_DIR/epub.lua" \
    "${TOC_ARGS[@]}" "${SPLIT_ARGS[@]}" \
    -M title="$(yaml_value 'title')" \
    -M header-includes= \
    -c "$SCRIPT_DIR/epub.css" \
    --highlight-style "$SCRIPT_DIR/highlight.theme" \
    -o "$OUTDIR/$EPUB_NAME"
  echo "pandoc/build.sh: built $OUTDIR/$EPUB_NAME from $RECORDS_DIR"
fi
