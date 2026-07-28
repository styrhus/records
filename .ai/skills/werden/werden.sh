#!/usr/bin/env bash
# werden.sh — advance or set the records werden-cycle name and stamp it into docs.
#
# Usage: werden.sh [new-structure-name | --stamp]
#   no arg   : bump the animal (minor) one position up dyr.json, keep the structure
#   arg      : start a new structure (major), reset the animal to the first entry (flue)
#   --stamp  : keep the current name; just recompute the number and re-stamp everywhere
#              (--here is an alias). Use it to propagate a hand-edited epoch without advancing.
#
# The current cycle lives in CURRENT at the repo root as a single line
# "<epoch>.<major>.<minor> <structure>-<animal>"  (e.g. "0.1.18 fuglekasse-spider").
# The number is derived + user-owned: epoch is the user's (preserved verbatim, never bumped
# here); major = 1-based index of the structure in strukturer.json; minor = 1-based index of
# the animal in dyr.json. A legacy name-only CURRENT is tolerated on read (epoch defaults to 0).
# Docs carry the marker  <!-- werden: <epoch>.<major>.<minor> <structure>-<animal> -->
# which this script rewrites in place wherever it appears. The README instead wears the
# cycle as a single visible line near the bottom: "> Fase — <number> <name>" (renamed here).
set -euo pipefail

# pwd -P: physical path, so the self-skip below still matches when the script is
# invoked through a symlinked route (.claude/skills -> .ai/skills).
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"

NAMING="$ROOT/tools/others/naming"
STATE="$ROOT/CURRENT"
ANIMALS_JSON="$NAMING/dyr.json"
STRUCTURES_JSON="$NAMING/strukturer.json"

# Ordered pools, one token per line — parsed without jq (each entry is its own "quoted" line).
mapfile -t ANIMALS    < <(grep -oE '"[^"]+"' "$ANIMALS_JSON"    | tr -d '"')
mapfile -t STRUCTURES < <(grep -oE '"[^"]+"' "$STRUCTURES_JSON" | tr -d '"')

first_animal="${ANIMALS[0]}"
first_structure="${STRUCTURES[0]}"

index_of() {  # index_of <needle> <array-elements...> -> prints index or -1
  local needle="$1"; shift
  local i=0
  for x in "$@"; do [[ "$x" == "$needle" ]] && { echo "$i"; return 0; }; i=$((i+1)); done
  echo -1
}

# --- mode: --stamp (--here) keeps the current name, only re-derives + re-stamps ---
STAMP_ONLY=""
if [[ "${1:-}" == "--stamp" || "${1:-}" == "--here" ]]; then STAMP_ONLY="yes"; shift; fi

# --- read current state: "<epoch>.<major>.<minor> <name>" or legacy "<name>" ---
OLD_NUM=""; OLD=""
if [[ -f "$STATE" ]]; then
  IFS=$' \t\r\n' read -ra parts < "$STATE" || true
  if [[ "${#parts[@]}" -ge 2 ]]; then
    OLD_NUM="${parts[0]}"; OLD="${parts[-1]}"        # number token + name token
  elif [[ "${#parts[@]}" -eq 1 ]]; then
    OLD="${parts[0]}"                                 # legacy: name only, no number
  fi
fi

# Epoch is the user's: read it from CURRENT, preserve verbatim, default 0 if absent/invalid.
epoch="${OLD_NUM%%.*}"
if [[ ! "$epoch" =~ ^[0-9]+$ ]]; then
  [[ -n "$OLD_NUM" ]] && echo "warn: epoch '${OLD_NUM}' not numeric; using 0" >&2
  epoch=0
fi

# --- compute the cycle name ---
if [[ -n "$STAMP_ONLY" ]]; then
  if [[ -z "$OLD" ]]; then
    echo "error: --stamp needs an existing cycle in CURRENT, found none" >&2; exit 1
  fi
  structure="${OLD%-*}"; animal="${OLD##*-}"          # keep the current name as-is
elif [[ $# -ge 1 && -n "${1:-}" ]]; then
  structure="$1"
  animal="$first_animal"
  if [[ "$(index_of "$structure" "${STRUCTURES[@]}")" == "-1" ]]; then
    echo "warn: '$structure' is not in strukturer.json (using it anyway)" >&2
  fi
elif [[ -z "$OLD" ]]; then
  structure="$first_structure"; animal="$first_animal"
else
  structure="${OLD%-*}"; cur_animal="${OLD##*-}"
  idx="$(index_of "$cur_animal" "${ANIMALS[@]}")"
  if [[ "$idx" == "-1" ]]; then
    echo "error: current animal '$cur_animal' not found in dyr.json" >&2; exit 1
  fi
  next=$((idx + 1))
  if [[ "$next" -ge "${#ANIMALS[@]}" ]]; then
    echo "error: already at the last animal ('$cur_animal'); pass a new structure name to start a new cycle" >&2
    exit 1
  fi
  animal="${ANIMALS[$next]}"
fi

NEW="$structure-$animal"

# --- derive the number: <epoch>.<major>.<minor>, both parts 1-based indices into the pools ---
maj_idx="$(index_of "$structure" "${STRUCTURES[@]}")"   # -1 → off-list, flagged as major 0
min_idx="$(index_of "$animal" "${ANIMALS[@]}")"
NUM="$epoch.$((maj_idx + 1)).$((min_idx + 1))"

# --- persist ---
printf '%s %s\n' "$NUM" "$NEW" > "$STATE"

# --- stamp docs: rewrite every existing marker ---
# -I skips binaries; public/ is Hugo build output, .mem/ is plugin-local memory.
updated=()
while IFS= read -r f; do
  # Skip the skill's own dir and the recordkit mirror — both hold the marker as literal text.
  case "$f" in "$SCRIPT_DIR"/*|*/skills/werden/*|"$ROOT"/tools/others/python/*) continue ;; esac
  sed -i -E "s/<!-- werden:[^>]*-->/<!-- werden: $NUM $NEW -->/g" "$f"
  updated+=("${f#"$ROOT"/}")
done < <(grep -rlIF --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=public --exclude-dir=.mem -- '<!-- werden:' "$ROOT" 2>/dev/null || true)

# --- README fase line: the one place the cycle is worn in the open, not whispered in comments ---
README="$ROOT/README.md"
fase_renamed=""
if [[ -f "$README" ]] && grep -qE '^> Fase — ' "$README"; then
  sed -i -E "s/^> Fase — .*/> Fase — $NUM $NEW/" "$README"
  fase_renamed="yes"
fi

# --- report ---
echo "cycle: ${OLD_NUM:+$OLD_NUM }${OLD:-<none>} -> $NUM $NEW${STAMP_ONLY:+  (--stamp: no advance)}"
echo "state: ${STATE#"$ROOT"/}"
if [[ ${#updated[@]} -eq 0 ]]; then
  echo "markers: NONE FOUND — seed  <!-- werden: $NUM $NEW -->  into the living docs (see SKILL.md)"
else
  echo "markers updated (${#updated[@]}):"
  for f in "${updated[@]}"; do echo "  $f"; done
fi
if [[ -n "$fase_renamed" ]]; then
  echo "fase line: > Fase — $NUM $NEW"
else
  echo "fase line: NOT FOUND — seed  '> Fase — $NUM $NEW'  near the bottom of README.md (see SKILL.md)"
fi
