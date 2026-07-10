#!/usr/bin/env bash
# Build the site's records into one PDF: book.lua assembles, pandoc renders
# HTML with the site-matching stylesheet, WeasyPrint prints it.
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

# params.pdf names the output file; unset/commented = feature off.
PDF_NAME="$(yaml_value '[[:space:]]*pdf')"
if [ -z "$PDF_NAME" ]; then
  echo "pandoc/build.sh: params.pdf unset in $SITE_CONFIG — skipping PDF build"
  exit 0
fi

# contentDir as Hugo reads it, resolved relative to the config's directory.
CONTENT_DIR="$(yaml_value 'contentDir')"
RECORDS_DIR="${RECORDS_DIR:-$(cd "$(dirname "$SITE_CONFIG")/${CONTENT_DIR:-../records}" && pwd)}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pandoc lua "$SCRIPT_DIR/book.lua" "$RECORDS_DIR" "$ROOT" "$SITE_CONFIG" > "$TMP/book.json"
pandoc -f json "$TMP/book.json" \
  --standalone --toc --toc-depth=2 \
  -c "$SCRIPT_DIR/pdf.css" \
  --highlight-style "$SCRIPT_DIR/highlight.theme" \
  -o "$TMP/book.html"
mkdir -p "$OUTDIR"
weasyprint "$TMP/book.html" "$OUTDIR/$PDF_NAME"
echo "pandoc/build.sh: built $OUTDIR/$PDF_NAME from $RECORDS_DIR"
