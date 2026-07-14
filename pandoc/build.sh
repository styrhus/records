#!/usr/bin/env bash
# Build the site's records into one PDF and/or EPUB: book.lua assembles, pandoc
# renders — HTML printed by WeasyPrint for the PDF, straight to EPUB otherwise.
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

# params.pdf / params.epub name the output files; unset/commented = feature off.
PDF_NAME="$(yaml_value '[[:space:]]*pdf')"
EPUB_NAME="$(yaml_value '[[:space:]]*epub')"
if [ -z "$PDF_NAME" ] && [ -z "$EPUB_NAME" ]; then
  echo "pandoc/build.sh: params.pdf and params.epub unset in $SITE_CONFIG — skipping book build"
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
