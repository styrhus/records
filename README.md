# hugo-runner-image

Builds the `hugo-runner` OCI image used as the job container for the miniMe
Hugo workflows (the 53-fork fan-out). The image bakes in everything those
jobs need so they start instantly:

- **node 22** — required by `actions/checkout` and the git-pages action
- **git, wget, tar** — from the base image
- **Hugo extended** — pinned in [`VERSION`](VERSION), so fork jobs stop
  downloading the 25 MB tarball from GitHub on every run

Base image: `code.forgejo.org/oci/node:22-bookworm` (Forgejo's Docker Hub
mirror — no Hub rate limits).

## Published to

| Registry | Image |
|----------|-------|
| git.euh.no | `git.euh.no/tb4/hugo-runner:<version>` and `:latest` |
| codeberg.org | `codeberg.org/tb4/hugo-runner:<version>` and `:latest` |

The Codeberg copy is what the sibling forks' runner labels should reference
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

## One-time setup

1. **git.euh.no token**: user settings → Applications → generate token with
   `write:package` scope. Store in Vault:
   `vault kv patch kv/projects/kott/forgejo-1/registry forgejo_token='<TOKEN>'`
   (use `put` if the secret doesn't exist yet).
2. **codeberg.org token**: same, under the tb4 Codeberg account, scope
   `write:package`. Store as field `codeberg_token` on the same Vault path.
3. Push this repo to git.euh.no (`ENABLE_PUSH_CREATE_USER` is on, so the
   push creates the repo):

   ```sh
   git remote add origin https://git.euh.no/tb4/hugo-runner-image.git
   git push -u origin main
   ```

4. On the new repo: Settings → Actions → Secrets → add
   `REGISTRY_TOKEN_FORGEJO` and `REGISTRY_TOKEN_CODEBERG` with the tokens
   from steps 1–2.
5. Re-run the workflow (it will have failed on the first push without the
   secrets): Actions → Build and push hugo-runner → Re-run, or push again.

## Bumping Hugo

Edit [`VERSION`](VERSION), commit, push. The workflow rebuilds and pushes
`:<new version>` and moves `:latest`. Runner labels pin the exact version,
so update them (forgejo-1 `config/services.yaml` / miniMe workflows) when
you want the fleet to move.

## Verify a published image

```sh
docker pull codeberg.org/tb4/hugo-runner:$(cat VERSION)   # must work anonymously
docker run --rm codeberg.org/tb4/hugo-runner:$(cat VERSION) \
  bash -c 'hugo version && node --version && git --version'
```
