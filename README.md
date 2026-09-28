# Styrhus Records

Your records, published. Drop Markdown into `records/`, get a website —
**Styrhus Records** is your own publishing _datamaskineri_.

Fork, enable Actions, push — your words appear at
`https://<you>.codeberg.page/records/` (or your own domain name). A fresh
fork starts as a working demo site; your first record replaces the demo
automatically.

The front page explains the basic functions: <https://styrhus.codeberg.page/records/>.

## Make it yours

It ships with **Fuglekasse**, a small default theme you restyle from
`tools/hugo/hugo.yaml` or replace. A second theme, **Postkasse** — same site, same
knobs, room to grow — is one line away: `theme: Postkasse`. Some like it
[simple](docs/simple.md), some like it [awesome](docs/awesome.md) —
[Hugo has it all](docs/hugo.md).

## Publish anywhere

- **Codeberg** — fork, enable Actions, push. Zero edits.
- **GitHub** — enable Pages once (Source: GitHub Actions), push.
- **GitLab** — push.
- **Your own machine, VPS or homelab** — `records publish` delivers to a
  `pages` branch or any webroot over rsync; no CI at all.

One build path behind all of them — details in
[publish anywhere](docs/publish.md).

## Record from your projects

Clone your fork inside any project — the recording skills follow, transcripts
land in the clone, and `/cpd` pushes it home. Nothing to configure —
[home is where the clone is](docs/records/developers/home-is-where-the-clone-is.md).

## Record together

Teams, friends and lovers can share one **Styrhus Records** instance. Add them as
collaborators on your fork, and they clone, they write, they commit — commit
to it. Every push publishes to the same site.

Who is who? It's all in git. Each record carries its author in the history —
`git log records/` never forgets. One site, many voices, and git is init
together.

## Record from your phone

A record is a Markdown file in `records/`, so anything that can commit one
can publish one — your forge's web editor, or git in your pocket. No app
required, though there is a small one if you want it —
[record from your phone](docs/phone.md).

## Record on your own

The skills also run without big-tech AI: a small [engine](tools/others/README.md)
drives the mechanical ones from a VSCode chat sidebar, a Neovim split, an Emacs
window, or plain shell — no model needed. Add
[Ollama](tools/others/ollama/README.md) and `/record` talks back: your own local
model, your records, your machine. It's one page from nothing to a written
record — [install it](docs/install.md).

---

> Fase — 0.12.4 badstu-moth

Code: AGPL-3.0-or-later · prose: CC BY-SA 4.0 — see [LICENSE.md](LICENSE.md).
