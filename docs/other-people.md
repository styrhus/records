# The other people in your records

A conversation usually has someone else in it. Sometimes they are the other
speaker; more often they are the person the conversation is about — the
colleague who made the decision, the friend with the diagnosis, the ex, the
child, the neighbour with the dog.

Publishing your own words is your call. Publishing theirs, or about them, is a
different thing, and it is worth about ninety seconds of thought before the
record goes up. This page is those ninety seconds. It is not a policy and it is
not legal advice — it is what people who publish their own conversations have
learned about being decent while doing it.

## Before you publish

Read the record once more with the other person reading over your shoulder.

- **Would they recognise themselves?** If yes, would they mind? If you do not
  know, that is a real answer, and it usually means ask.
- **Is the identifying detail doing any work?** Most of the time the story
  survives losing the name, the employer, the town and the date. If it does not
  survive, that is worth noticing too.
- **Is it yours to tell?** A conversation you had is yours. A thing someone told
  you in confidence during it is not, even though it is in your transcript.
- **Health, money, immigration status, sexuality, religion, anything involving a
  child.** Different bar. Ask, or leave it out.
- **The internet is not your friend group.** Something that reads as affectionate
  among people who know you can read as contempt to a stranger, and strangers are
  the audience.

If the other party is a model rather than a person, none of this applies to
them. It still applies to everyone they were talking about.

## Redacting well

Bad redaction removes the name and leaves everything that made the name
unnecessary.

> My manager at [redacted] told me the Oslo office is closing in March.

That protects nobody. Take out the detail, not the label:

> A manager told me the office is closing.

Things that work:

- **Initials or a role.** "K." or "my manager" reads naturally and carries the
  conversation. A role is usually better than an initial, because an initial
  invites guessing.
- **Blur the specifics, keep the shape.** "a hospital", "last spring", "a big
  employer". The story almost always survives it.
- **Remove, do not paraphrase into something false.** Do not invent a different
  city. A record that quietly says untrue things is worse than one with a gap in
  it.
- **Leave the seam visible.** `records redact` writes `[redacted]` and does not
  pretend the turn was always that way. A visible gap is honest; a smooth,
  edited-down version is a small lie about what was said.

Things that do not work: nicknames everybody in the group knows, reversible
initials in a small field, and leaving a name in the filename, the tags, the
front matter title or an attached image while removing it from the body. Search
the whole record, not the paragraph.

## When someone asks to be taken out

Say yes.

Not because you are obliged to — that depends on where you live, what was said,
and this page is not the place to guess. Say yes because you published a
conversation with someone in it who does not want to be there, and the cost of
taking it down is an afternoon.

```bash
records redact <record> --turn N --remove   # a turn
records unpublish <record>                  # the whole record
```

Then rebuild and publish, so the site, the books and the pages branch all follow.

Then tell them what actually happened, in plain words:

- The page is gone and will not come back.
- The repository's git history still contains the original, because that is what
  git is. If they want that gone too, it is a history rewrite — possible, heavy,
  and described in [oops.md](oops.md).
- Forks, other people's clones, caches and archives are outside your reach. You
  can say who to ask; you cannot promise on their behalf.

Do not promise erasure. Promise what you can do, do it the same week, and be
accurate about the rest. Someone who asked to be removed is owed the truth about
what remains more than they are owed a comforting sentence.

## What you can honestly promise

You control the site, the books, the pages branch and the tip of your branch.
You do not control git history without a rewrite, other people's copies, or
anything already indexed.

That is a smaller promise than "I'll delete it". It is the one you can keep.

## Recording together

If several people write into the same instance, agree once, up front, on who may
publish a conversation the others are in — and whether the answer is "whoever
wrote it" or "everyone in it". Write the answer down somewhere in the repository.
It is a two-line agreement that saves an argument later.

See also: [publishing](publish.md), [when a key lands in a
transcript](oops.md).
