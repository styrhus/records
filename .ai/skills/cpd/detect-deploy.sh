#!/usr/bin/env bash
# Report the deploy method available in $PWD for the cpd skill.
# Precedence: deploy.sh > Makefile target > push-triggered CI workflow.
set -u

has_script=false
has_make=false
ci_workflow=""

[ -f "$PWD/deploy.sh" ] && has_script=true
for mf in Makefile GNUmakefile makefile; do
  if [ -f "$PWD/$mf" ] && grep -qE '^deploy:' "$PWD/$mf"; then
    has_make=true
    break
  fi
done
for wf in "$PWD"/.forgejo/workflows/*.yml "$PWD"/.forgejo/workflows/*.yaml \
          "$PWD"/.github/workflows/*.yml "$PWD"/.github/workflows/*.yaml; do
  if [ -f "$wf" ]; then
    ci_workflow="${wf#"$PWD"/}"
    break
  fi
done

if $has_script; then
  echo "deploy: ./deploy.sh"
elif $has_make; then
  echo "deploy: make deploy"
elif [ -n "$ci_workflow" ]; then
  echo "deploy: automatic on push ($ci_workflow)"
else
  echo "(no deploy method found — no ./deploy.sh, no 'deploy:' Makefile target, no CI workflow)"
fi
