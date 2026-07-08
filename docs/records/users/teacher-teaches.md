---
title: Teacher teaches
date: 2026-07-08T02:32:54+02:00
tags: [users, how-to]
---

## User

I've forked this repo to /home/tb4/Prosjekter/nettsider/tb4-rot (codeberg.org/tb4/pages.git)

you are a teacher and teach a user how they cleanly can "pull" changes in this repo to their fork.

produce a docs/pulls.md pulls.md will be formated like a conversation:

```
## User

<pretend to be user>

## Assistant

<you are the teacher>
```

Just like the /record skill produces. But here you produce both voices.

Use the knowledge that the user has short attention span. User must be given easy to understand explanations. User appreciates comparisions to similar procedures (pull, merge, ...) in other technical or mechanical fields or in Nature.

When refering to the repos, use ssh://git@codeberg.org/tb4/pages.git and ssh://git@codeberg.org/tb4/records.git.

## Assistant

[docs/pulls.md](../../../docs/pulls.md) is done — a teacher/student dialogue in the same `## User` / `## Assistant` format the /record skill produces.

It walks through the fork-sync routine in small steps: adding `upstream` (`ssh://git@codeberg.org/tb4/records.git`) as a second remote next to `origin` (`ssh://git@codeberg.org/tb4/pages.git`), then fetch, merge, and push, ending with the `git pull upstream main` shortcut. Each concept gets an analogy for the short-attention-span reader: upstream/downstream river for the repos, phone contacts for remotes, a delivery truck for fetch, streams joining for merge, two cooks on one recipe line for conflicts, and a warehouse shelf for the fork on Codeberg.

One note: in your actual clone at `~/Prosjekter/nettsider/tb4-rot`, the Codeberg fork remote is named `codeberg` (not `origin`, which points to your local git server). The doc teaches the conventional origin/upstream naming since it's a generic guide — for your own clone, substitute `codeberg` for `origin` and everything else applies unchanged.

— claude-fable-5

## User

/phil-gc

## Assistant

Done. Teaching materials and transcript recorded.

— claude-fable-5

```
It is good to rub and polish our brain against another.

— Michel de Montaigne

— (20caa74)
```

