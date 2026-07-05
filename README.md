# hugo-runner-image

Builds the `hugo-runner` OCI image for the miniMe Hugo workflows (the >50-fork
fan-out): node 22, git, and Hugo extended — pinned in [`VERSION`](VERSION) —
on base `code.forgejo.org/oci/node:22-bookworm`.

- Published to `codeberg.org/tb4/hugo-runner:<version>` and `:latest`; keep it publicly pullable — the menneske sibling forks pull it by runner label.
- Built by [`.forgejo/workflows/build.yml`](.forgejo/workflows/build.yml) on push to `main` (host docker socket; whitelisted only on the git.euh.no runner). Manual fallback: [`build.sh`](build.sh).
- Hugo bumps itself weekly via [`check-hugo-release.yml`](.forgejo/workflows/check-hugo-release.yml); manual: edit [`VERSION`](VERSION), commit, push.
- [`pages.yml`](.forgejo/workflows/pages.yml) dogfoods the image: builds `records/` into the site at <https://tb4.codeberg.page/hugo-runner-image/>; fork it to publish your own blank-slate records site.
- Verify: `docker run --rm codeberg.org/tb4/hugo-runner:$(cat VERSION) bash -c 'hugo version && node --version && git --version'`
