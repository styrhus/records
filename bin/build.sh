#!/usr/bin/env bash
# The one build path: site + books into a single output dir, used identically
# by CI, `records publish` and manual runs.
# Usage: bin/build.sh [outdir]   (default: <repo-root>/public, gitignored)
# Site URL precedence: $BASE_URL > $PAGES_HOST derivation > Codeberg CI derivation > $CI_PAGES_URL > error.
# When $GITHUB_ENV is set, appends PAGES_URL=<resolved> for the deploy step.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTDIR="${1:-$ROOT/public}"
case "$OUTDIR" in /*) ;; *) OUTDIR="$(pwd)/$OUTDIR" ;; esac

if ! command -v hugo >/dev/null 2>&1; then
  echo "bin/build.sh: hugo not found — install it: https://gohugo.io/installation/" >&2
  exit 1
fi

resolve_url() {
  # Uncommented baseURL in the site config is authoritative everywhere.
  local config_url
  config_url="$(sed -n 's/^baseURL:[[:space:]]*//p' "$ROOT/tools/hugo/hugo.yaml" | head -1 | sed "s/[[:space:]]*#.*\$//; s/[\"']//g")"
  if [ -n "$config_url" ]; then
    echo "$config_url"
    return 0
  fi
  if [ -n "${BASE_URL:-}" ]; then
    echo "$BASE_URL"
    return 0
  fi
  # PAGES_HOST (a git-pages domain, set via instance Actions vars) generalizes
  # the Codeberg derivation to any forge.
  if [ -n "${PAGES_HOST:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ]; then
    local owner="${GITHUB_REPOSITORY%%/*}" name="${GITHUB_REPOSITORY#*/}"
    # git-pages convention: a repo literally named "pages" serves at the domain root.
    if [ "$name" = pages ]; then
      echo "https://${owner}.${PAGES_HOST}/"
    else
      echo "https://${owner}.${PAGES_HOST}/${name}/"
    fi
    return 0
  fi
  if [ -n "${GITHUB_REPOSITORY:-}" ]; then
    case "${GITHUB_SERVER_URL:-}" in
      https://codeberg.org | https://codeberg.org/)
        local owner="${GITHUB_REPOSITORY%%/*}" name="${GITHUB_REPOSITORY#*/}"
        # A repo literally named "pages" serves at the domain root on Codeberg.
        if [ "$name" = pages ]; then
          echo "https://${owner}.codeberg.page/"
        else
          echo "https://${owner}.codeberg.page/${name}/"
        fi
        return 0
        ;;
    esac
  fi
  if [ -n "${CI_PAGES_URL:-}" ]; then
    echo "$CI_PAGES_URL"
    return 0
  fi
  return 1
}

if ! PAGES_URL="$(resolve_url)"; then
  echo "bin/build.sh: cannot resolve the site URL — set baseURL in tools/hugo/hugo.yaml, pass BASE_URL, or run in Codeberg/GitLab CI" >&2
  exit 1
fi
PAGES_URL="${PAGES_URL%/}/"

if [ -n "${GITHUB_ENV:-}" ]; then
  echo "PAGES_URL=${PAGES_URL}" >>"$GITHUB_ENV"
fi

# repoURL for raw-link rewrites: an uncommented repoURL in the site config is
# authoritative (as with baseURL); else honour the caller's env, else derive
# from CI env. FORGE_URL (instance Actions var) wins over GITHUB_SERVER_URL,
# which in-cluster runners see as an internal address; CI_PROJECT_URL covers
# GitLab.
CONFIG_REPOURL="$(sed -n 's/^[[:space:]]*repoURL:[[:space:]]*//p' "$ROOT/tools/hugo/hugo.yaml" | head -1 | sed "s/[[:space:]]*#.*\$//; s/[\"']//g")"
if [ -z "$CONFIG_REPOURL" ] && [ -z "${HUGO_PARAMS_REPOURL:-}" ]; then
  if [ -n "${GITHUB_REPOSITORY:-}" ] && [ -n "${FORGE_URL:-}" ]; then
    export HUGO_PARAMS_REPOURL="${FORGE_URL%/}/${GITHUB_REPOSITORY}"
  elif [ -n "${GITHUB_REPOSITORY:-}" ] && [ -n "${GITHUB_SERVER_URL:-}" ]; then
    export HUGO_PARAMS_REPOURL="${GITHUB_SERVER_URL%/}/${GITHUB_REPOSITORY}"
  elif [ -n "${CI_PROJECT_URL:-}" ]; then
    export HUGO_PARAMS_REPOURL="$CI_PROJECT_URL"
  fi
fi

# One-page modes publish one index.html: no per-record pages, no sitemap.
# Hugo config cannot branch on its own params, so the rules live in a second
# config merged in here (see tools/hugo/one-page.yaml).
PAGE_MODE="${HUGO_PARAMS_PAGEMODE:-$(sed -n 's/^[[:space:]]*pageMode:[[:space:]]*//p' "$ROOT/tools/hugo/hugo.yaml" | head -1 | sed "s/[[:space:]]*#.*\$//; s/[\"']//g")}"
HUGO_CONFIG=hugo.yaml
case "$PAGE_MODE" in
  single|single-flowing) HUGO_CONFIG="hugo.yaml,one-page.yaml" ;;
esac

# --cleanDestinationDir: unpublished/renamed pages must leave the outdir, or they
# ride the next pages-branch publish forever. Books/PWA/cards are re-added below.
(cd "$ROOT/tools/hugo" && hugo --minify --cleanDestinationDir --config "$HUGO_CONFIG" --baseURL "$PAGES_URL" --destination "$OUTDIR")

# Phone app: tools/pwa/ is copied in only when params.phoneApp names the path
# segment to serve it at. Unset = not shipped, because the page holds a forge
# token and no fork should publish one it did not ask for.
APP="$(sed -n 's/^[[:space:]]*phoneApp:[[:space:]]*//p' "$ROOT/tools/hugo/hugo.yaml" | head -1 | sed "s/[[:space:]]*#.*\$//; s/[\"']//g; s#/*\$##")"
if [ -n "$APP" ]; then
  case "$APP" in
    */*|.*) echo "bin/build.sh: params.phoneApp must be a single path segment, got '$APP'" >&2; exit 1 ;;
  esac
  mkdir -p "$OUTDIR/$APP"
  cp -R "$ROOT/tools/pwa/." "$OUTDIR/$APP/"
fi

# Books: tools/pandoc/build.sh self-gates on params.pdf/epub/booklet; when the
# toolchain is missing (stock CI runners, laptops) skip with a note instead.
BOOKS="$(grep -E '^[[:space:]]*(pdf|epub|booklet):' "$ROOT/tools/hugo/hugo.yaml" || true)"
if [ -n "$BOOKS" ]; then
  if ! command -v pandoc >/dev/null 2>&1; then
    echo "bin/build.sh: book params set but pandoc is missing — skipping book build" >&2
  elif printf '%s\n' "$BOOKS" | grep -Eq '^[[:space:]]*(pdf|booklet):' && ! command -v weasyprint >/dev/null 2>&1; then
    echo "bin/build.sh: params.pdf/booklet need weasyprint — skipping book build" >&2
  else
    "$ROOT/tools/pandoc/build.sh" "$OUTDIR"
  fi
fi

# OG cards (Postkasse only): params.ogCards runs `records card` per record
# into $OUTDIR/cards/<slug>.svg, for head-meta.html to point og:image at.
# Needs only python3 — recordkit ships in-repo; skip cleanly, like the pandoc
# step above, when it's missing. No-op off-Postkasse and in single(-flowing)
# mode, which renders no per-record pages to link a card from.
OG_CARDS="${HUGO_PARAMS_OGCARDS:-$(sed -n 's/^[[:space:]]*ogCards:[[:space:]]*//p' "$ROOT/tools/hugo/hugo.yaml" | head -1 | sed "s/[[:space:]]*#.*\$//; s/[\"']//g")}"
THEME="$(sed -n 's/^theme:[[:space:]]*//p' "$ROOT/tools/hugo/hugo.yaml" | head -1 | sed "s/[[:space:]]*#.*\$//; s/[\"']//g")"
if [ -n "$OG_CARDS" ] && [ "$OG_CARDS" != "false" ] && [ "$THEME" = "Postkasse" ]; then
  case "$PAGE_MODE" in
    single|single-flowing)
      echo "bin/build.sh: params.ogCards set but pageMode is $PAGE_MODE — no per-record pages, skipping OG card generation" >&2
      ;;
    *)
      if ! command -v python3 >/dev/null 2>&1 || [ ! -d "$ROOT/tools/others/python/recordkit" ]; then
        echo "bin/build.sh: params.ogCards set but python3/recordkit is missing — skipping OG card generation" >&2
      else
        RECORDS_DIR="$(cd "$ROOT" && PYTHONPATH="$ROOT/tools/others/python" python3 -m recordkit config)" || RECORDS_DIR=""
        RECORDS_DIR="$(printf '%s' "$RECORDS_DIR" | python3 -c 'import json, sys; print(json.load(sys.stdin)["records_dir"])' 2>/dev/null)" || RECORDS_DIR=""
        if [ -n "$RECORDS_DIR" ] && [ -d "$RECORDS_DIR" ]; then
          mkdir -p "$OUTDIR/cards"
          CARD_COUNT=0
          while IFS= read -r -d '' rec; do
            base="$(basename "$rec" .md)"
            case "$base" in
              # doctor.py's reserved names, plus bookLook's cover pages.
              _index|LICENSE|404|forside|side-1|bakside) continue ;;
            esac
            if PYTHONPATH="$ROOT/tools/others/python" python3 -m recordkit card "$rec" \
                --out "$OUTDIR/cards/$base.svg" --repo "$ROOT" >/dev/null; then
              CARD_COUNT=$((CARD_COUNT + 1))
            else
              echo "bin/build.sh: records card skipped $rec (no turns to draw from)" >&2
            fi
          done < <(find "$RECORDS_DIR" -name '*.md' -print0)
          echo "bin/build.sh: wrote $CARD_COUNT OG card(s) to $OUTDIR/cards/" >&2
        fi
      fi
      ;;
  esac
fi
