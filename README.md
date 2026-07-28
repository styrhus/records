# blyant records

Your records, published. Drop Markdown into `records/`, get a website —
**blyant records** is your own publishing _datamaskineri_.

Fork, enable Actions, push — your words appear at
`https://<you>.codeberg.page/records/` (or your own domain name).

The front page explains the rest: <https://blyant.codeberg.page/records/>.

## Make it yours

It ships with **Fuglekasse**, a small default theme you restyle from
`hugo/hugo.yaml` or replace. Some like it [simple](docs/simple.md), some like
it [awesome](docs/awesome.md) — [Hugo has it all](docs/hugo.md).

## Record from your projects

Clone your fork inside any project — anywhere, under any name — and the
recording skills follow: invoked from the project workspace, they find the
clone and file transcripts there. `/cpd` commits and pushes the clone
itself, and the push publishes.

```bash
git clone https://codeberg.org/<you>/records.git
echo records/ >> .gitignore   # or track it as a submodule
```

Nothing to configure: `contentDir` in the clone's `hugo/hugo.yaml` is the
one source of truth, shared by Hugo and the skills.

## Record together

Teams, friends and lovers can share one **blyant records** instance. Add them as
collaborators on your fork, and they clone, they write, they commit — commit
to it. Every push publishes to the same site.

Who is who? It's all in git. Each record carries its author in the history —
`git log records/` never forgets. One site, many voices, and git is init
together.

## Record on your own

The skills also run without big-tech AI: a small [engine](others/README.md)
drives the mechanical ones from a VSCode chat sidebar, a Neovim split, or
plain shell — no model needed. Add [Ollama](others/ollama/README.md) and
`/record` talks back: your own local model, your records, your machine.

---

> Fase — 0.1.19 fuglekasse-scorpion
