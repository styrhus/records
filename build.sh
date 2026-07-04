#!/usr/bin/env bash
# Manual build/push fallback — same sequence as .forgejo/workflows/build.yml,
# runnable on any host with docker (bootstrap, or when CI is down).
#
# Usage:
#   REGISTRY_TOKEN_FORGEJO=... REGISTRY_TOKEN_CODEBERG=... ./build.sh
#
# Tokens need scope write:package for user tb4 on the respective forge.
# Omit a token to skip pushing to that registry (build + tag still happen).
set -euo pipefail
cd "$(dirname "$0")"

IMAGE_NAME="tb4/hugo-runner"
FORGEJO_REGISTRY="git"
CODEBERG_REGISTRY="codeberg.org"
REGISTRY_USER="tb4"
HUGO_VERSION="$(tr -d '[:space:]' < VERSION)"

docker build \
  --build-arg "HUGO_VERSION=${HUGO_VERSION}" \
  -t "${FORGEJO_REGISTRY}/${IMAGE_NAME}:${HUGO_VERSION}" \
  -t "${FORGEJO_REGISTRY}/${IMAGE_NAME}:latest" \
  -t "${CODEBERG_REGISTRY}/${IMAGE_NAME}:${HUGO_VERSION}" \
  -t "${CODEBERG_REGISTRY}/${IMAGE_NAME}:latest" \
  .

push_to() {
  local registry="$1" token="$2"
  if [ -z "$token" ]; then
    echo "No token for ${registry}; skipping push." >&2
    return 0
  fi
  echo "$token" | docker login "$registry" -u "$REGISTRY_USER" --password-stdin
  docker push "${registry}/${IMAGE_NAME}:${HUGO_VERSION}"
  docker push "${registry}/${IMAGE_NAME}:latest"
  docker logout "$registry"
}

push_to "$FORGEJO_REGISTRY" "${REGISTRY_TOKEN_FORGEJO:-}"
push_to "$CODEBERG_REGISTRY" "${REGISTRY_TOKEN_CODEBERG:-}"
