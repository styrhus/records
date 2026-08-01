#!/usr/bin/env bash
# Build records.pyz: the whole engine as one file that runs on any Python 3.9+.
# Zero dependencies is what makes this a stdlib zipapp and nothing more.
# Usage: tools/others/python/build-pyz.sh [outfile]   (default: dist/records.pyz)
# Deterministic: fixed mtimes and modes, so the same source gives the same bytes.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
OUT="${1:-$HERE/dist/records.pyz}"
case "$OUT" in /*) ;; *) OUT="$(pwd)/$OUT" ;; esac

# 1980-01-01 UTC: the zip format's own epoch floor, and the usual reproducible default.
EPOCH="${SOURCE_DATE_EPOCH:-315532800}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "build-pyz.sh: python3 not found" >&2
  exit 1
fi

WERDEN="$(head -1 "$ROOT/CURRENT" 2>/dev/null | tr -d '\n' || true)"
if [ -z "$WERDEN" ]; then
  echo "build-pyz.sh: no CURRENT at $ROOT — the artefact would carry no version" >&2
  exit 1
fi

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# The package, minus anything the interpreter generated.
mkdir -p "$STAGE/recordkit"
for f in "$HERE"/recordkit/*.py; do
  cp "$f" "$STAGE/recordkit/"
done

# One version story: derived from CURRENT, never typed.
printf '"""Stamped by build-pyz.sh — the werden cycle this artefact was built from."""\n\nWERDEN = "%s"\n' \
  "$WERDEN" >"$STAGE/recordkit/_pyz.py"

cp "$HERE/pyz_main.py" "$STAGE/__main__.py"

# Same bytes from the same source: zipapp sorts its entries, so only the
# per-file metadata is left to pin down.
find "$STAGE" -type f -exec chmod 644 {} +
find "$STAGE" -exec touch -h -d "@$EPOCH" {} + 2>/dev/null ||
  find "$STAGE" -exec touch -d "@$EPOCH" {} +

mkdir -p "$(dirname "$OUT")"
python3 -m zipapp "$STAGE" -p '/usr/bin/env python3' -c -o "$OUT"
chmod 755 "$OUT"

( cd "$(dirname "$OUT")" && sha256sum "$(basename "$OUT")" >"$(basename "$OUT").sha256" )

echo "build-pyz.sh: $OUT"
echo "  werden  $WERDEN"
echo "  bytes   $(wc -c <"$OUT")"
echo "  sha256  $(cut -d' ' -f1 "$OUT.sha256")"
