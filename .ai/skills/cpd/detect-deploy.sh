#!/usr/bin/env bash
# Report the deploy method available in $PWD for the cpd skill.
# Precedence: params.deployCommand in hugo/hugo.yaml > push-triggered CI workflow.
set -u

cmd=$(sed -n -E 's/^[[:space:]]+deployCommand:[[:space:]]*//p' "$PWD/hugo/hugo.yaml" 2>/dev/null \
      | head -n1 | sed -E "s/^[\"']//; s/[\"']$//")

if [ -n "$cmd" ]; then
  echo "deploy: $cmd"
  exit 0
fi

for wf in "$PWD"/.forgejo/workflows/*.yml "$PWD"/.forgejo/workflows/*.yaml \
          "$PWD"/.github/workflows/*.yml "$PWD"/.github/workflows/*.yaml; do
  if [ -f "$wf" ]; then
    echo "deploy: automatic on push (${wf#"$PWD"/})"
    exit 0
  fi
done

echo "(no deploy method found — set deployCommand under params: in hugo/hugo.yaml)"
