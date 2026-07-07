# records

Your records, published. Fork, enable Actions, push — your words appear at
`https://<you>.codeberg.page/records/`.

The front page explains the rest: <https://tb4.codeberg.page/records/>.

## Make it yours

It ships with **Fuglekasse**, a small default theme you restyle from
`hugo/hugo.yaml` or replace. Some like it [simple](docs/simple.md), some like
it [awesome](docs/awesome.md) — [Hugo has it all](docs/hugo.md).

## Record from your projects

Clone your fork inside any project — anywhere, under any name — and the
recording skills follow: invoked from the project workspace, they find the
clone's `hugo/hugo.yaml`, read its `contentDir`, and file transcripts there.
`/cpd` commits and pushes the clone itself, and the push publishes.

```bash
git clone https://codeberg.org/<you>/records.git
echo records/ >> .gitignore   # or track it as a submodule
```

Nothing to configure: `contentDir` is the one source of truth, shared by Hugo
and the skills.
