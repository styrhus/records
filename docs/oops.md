# When a key lands in a transcript

Sooner or later you paste something you should not have. A `.env` file. A token
inside an error message. A password typed into the window you were recording
instead of the one you meant. The record gets committed, the site rebuilds, and
the key is on the internet.

This page is the order to do things in. The order matters more than any single
step on it.

## 1. Rotate the credential

**Do this first. Before you edit the file. Before you finish reading this page.**

Revoke the key at whoever issued it and take a new one. GitHub, your cloud, your
database, your forge — every one of them has a page for it, and none of them
charge you for the trouble.

From the moment a secret was pushed, treat it as public. Not "probably fine, it
was only up for four minutes" — scrapers watch public forge event feeds, and
four minutes is plenty. The only question that matters is whether the key still
works, and rotation is the one action that answers it.

Everything after this section is cleanup. Cleanup is worth doing. It is not the
fix, and a tidied-up history with a live key in it is worse than an untouched
history with a dead one, because it feels finished.

If you cannot rotate it yourself — a shared account, a key that belongs to
someone else — tell the person who can, now, and work through the rest of this
page while they do it.

## 2. Find out what else is in there

If one thing got pasted, look for the others.

```bash
records scan                       # the records tree
records scan path/to/record.md     # one file
records scan --json                # for a script or a CI step
```

It looks for private-key blocks, tokens with a recognisable issuer prefix
(`sk-`, `ghp_`, `AKIA…`, `glpat-` and friends), JWTs, credentials embedded in
URLs, `.env`-shaped assignments, and long random-looking strings. Findings are
printed with the first four characters and a length, never in full: a report
that quotes the secret has made another copy of it, in your scrollback and
possibly in a CI log.

It is a heuristic and it says so in its own output. It flags things that are not
secrets, and it misses secrets it has no shape for. A clean scan is evidence,
not a promise — read the diff yourself.

It deliberately ignores `.recordsignore` and `draft: true`. Neither of those
keeps a file out of git, and git is what leaked.

Exit code is non-zero when it finds anything, so it works in a pre-commit hook
or a CI job. Put it there before you need it rather than after.

## 3. Take it out of the working tree

Now make the current state of the repository correct.

```bash
records redact <record> --turn N --remove    # a turn inside a record
records unpublish <record>                   # the whole record, reversibly
```

Or edit the file by hand and commit. Any of these is fine; the point is that the
tip of your branch no longer contains the secret.

Then rebuild and publish, so the site, the PDF, the EPUB and the pages branch
stop carrying it.

**This is the step people mistake for being done.** After it, the working tree
is clean and git history still has every byte. Anyone can run `git log -p` and
read the key. If that is acceptable to you — because the credential is dead,
which it is, because you did step 1 — you can stop here. Many people should.

## 4. Decide about history

Rewriting history is a real option and a heavy one. This project's tools will
never do it for you, not behind a flag and not with a confirmation prompt. What
follows is an explanation so you can decide; the running of it is yours.

The tool for it is [git-filter-repo](https://github.com/newren/git-filter-repo).
Work on a fresh clone, keep the old one until you are sure:

```bash
pipx install git-filter-repo

printf 'literal:ghp_theTokenThatLeaked==>REMOVED\n' > /tmp/leaked.txt
git filter-repo --replace-text /tmp/leaked.txt
rm /tmp/leaked.txt
```

Removing a whole file instead of a string is `--invert-paths --path
records/2026-08-30_11-04.md`.

### What it costs

Every commit from the touched one onward gets a new hash. That is not a detail;
it is the whole cost, and it lands on everyone:

- You force-push, and every other clone of the repository is now a different
  repository. Everyone with one has to re-clone, or reset onto the new history
  by hand.
- Open pull requests and merge requests point at commits that no longer exist.
  Expect to reopen them.
- Signed commits lose their signatures. Tags need re-pointing.
- Links to specific commits — in issues, in chat, in other people's notes —
  become 404s.

On a repository only you have cloned, this is twenty minutes. On one with forks
and contributors, it is a small announcement and a bad afternoon.

### What it cannot reach

A rewrite fixes your history. It does not reach:

- **The forge's own storage.** The old commits usually stay reachable by hash on
  Codeberg, GitHub, GitLab and Forgejo until the server garbage-collects, which
  may be never without a support request. Ask them to run it. Some will.
- **Forks.** A fork is a separate repository holding the old objects. On some
  forges a fork can even keep the original commits reachable from the parent's
  URL space. You cannot rewrite someone else's fork; you can only ask.
- **Other people's clones**, including CI caches, backup jobs and the laptop of
  whoever cloned it on Tuesday.
- **CI logs and build artefacts**, which are stored separately from the repo and
  outlive it.
- **Anything already fetched.** Search engine caches, the Internet Archive,
  package mirrors, scrapers, dataset builders. There is no recall for these.

Which is the same sentence as the top of this page, from the other end: rotate
the credential. It is the only step that reaches all of the above.

Do not delete and recreate the repository as a shortcut. It breaks every link
anyone ever made to it, and it does not un-leak the key either.

## What is actually forgotten

Being precise about this is the point of the page.

| | after step 3 | after a rewrite |
|---|---|---|
| your working tree | clean | clean |
| the built site, PDF, EPUB, pages branch | clean after a rebuild | clean |
| your local git history | still has it | rewritten (old objects until `git gc`) |
| the forge's copy | still has it | usually still reachable by hash |
| forks and other clones | still have it | still have it |
| CI logs, caches, mirrors | still have them | still have them |
| search caches, archives, scrapers | still have them | still have them |
| the credential itself | **dead, if you did step 1** | **dead, if you did step 1** |

## Telling people

If the key was shared — a team token, a database password, anything that is not
only yours — say so, plainly, early, in whatever channel that team uses. Include
what leaked, when, that it has been rotated, and what people need to do (usually:
pull a new value, and re-clone if you rewrote history).

A short honest message on the day is a smaller event than a quiet one found
later.

## The short version

1. **Rotate the credential.** Now.
2. `records scan` — see what else is in there.
3. Redact or unpublish, rebuild, publish. The site is clean; git is not.
4. Decide about history with open eyes, and say out loud what is still out there.

See also: [publishing](publish.md), [the other people in your
records](other-people.md).
