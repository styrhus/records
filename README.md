# hugo-runner-image

Builds the `hugo-runner` OCI image used as the job container for e.g., the miniMe
Hugo workflows (the >50-fork fan-out). The image bakes in everything those
jobs need so they start instantly:

- **node 22** — required by `actions/checkout` and the git-pages action
- **git, wget, tar** — from the base image
- **Hugo extended** — pinned in [`VERSION`](VERSION).

Base image: `code.forgejo.org/oci/node:22-bookworm` (Forgejo's Docker Hub
mirror — no Hub rate limits).

## Published to

| Registry | Image |
|----------|-------|
| codeberg.org | `codeberg.org/tb4/hugo-runner:<version>` and `:latest` |

The Codeberg copy is what the menneske sibling forks' runner labels should reference
(e.g. `minime:docker://codeberg.org/tb4/hugo-runner:0.162.1`), so the package
must be **publicly pullable** — check its visibility in
<https://codeberg.org/tb4/-/packages> after the first push.

## How it builds

[`.forgejo/workflows/build.yml`](.forgejo/workflows/build.yml) runs on the
local runner (`runs-on: docker`) on every push to `main` (and via
`workflow_dispatch`). The job container mounts the host docker socket, which
the runner only permits because `container.valid_volumes` whitelists
`/var/run/docker.sock` (configured in forgejo-1 `config/services.yaml` for
the git.euh.no runner only — never enable this on the Codeberg runners).

[`build.sh`](build.sh) is the manual fallback: same build/tag/push sequence
on any docker host, tokens supplied via `REGISTRY_TOKEN_FORGEJO` /
`REGISTRY_TOKEN_CODEBERG` env vars.

## Bumping Hugo

Edit [`VERSION`](VERSION), commit, push. The workflow rebuilds and pushes
`:<new version>` and moves `:latest`.

## Verify a published image

```sh
docker run --rm codeberg.org/tb4/hugo-runner:$(cat VERSION) \
  bash -c 'hugo version && node --version && git --version'
```
