---
title: Voice — the argument against building it
date: 2026-08-01T17:00:55+01:00
tags: [developers, roadmap, akvarium]
---

# Voice — the argument against building it

> The third rung asked for an argument before it asked for code. Here is the argument, and it
> comes out against.

[akvarium item 3](ROADMAP.md#3--cricket--maybe-voice-capture) says *maybe*, twice, and sets the
first deliverable as "a design note arguing why it should exist at all". This is that note. It
concludes the rung should not be built — not because voice does not belong in records, but
because the useful half of it already works and the other half belongs to a different road.

## What the rung would be

The border predates the road and is absolute: **no voice-to-text engine. Not ours, not bundled,
not called.** A rung that transcribes is not this rung. Strip transcription out and what remains
is: capture audio in the browser, store it somewhere, set `voiceRecorded: true`.

That flag already works end to end. It renders an accent-coloured microphone beside every Human
heading — on the site, in the PDF and in the EPUB. Its meaning is exactly *this was spoken*. It
has never meant that a machine wrote it down.

## Why it should not be built

**1. Audio without words is not a record.** A record is `## Human` and `## Assistant` sections of
Markdown. The site, the books and the flowing layout all render text. An audio file with no text
beside it produces an empty turn — a page with a microphone icon and nothing under it. Whatever
that is, it is not the thing this project publishes.

**2. The transcription problem is already solved, by someone else, correctly.** Every phone has
dictation built into its keyboard. Tap the microphone, speak, and the text appears in the field —
in the forge's web editor, in a git client, in the phone app. The words land in the record as
words, and then `voiceRecorded: true` marks honestly how they got there.

That is not a workaround. It satisfies the border precisely: the engine bundles no model, calls
no service and ships no transcriber. The user's own operating system does the work, at the user's
own request, before our code ever sees the text. We stay out of it, which is the entire point of
the border.

So the feature exists today, costs nothing, and needs one line of documentation rather than a
rung.

**3. Where the audio would live is not this road's question.** Storing a captured file means
deciding how a record carries attachments, and that decision belongs to
[schrank](../schrank/ROADMAP.md) — records as Hugo leaf bundles, `records attach` doing the move.
Building capture first means inventing a second scheme for the same problem, which is the failure
mode the road already warns about in its own notes.

**4. The remaining value is an attachment, not a voice feature.** The one thing capture would
genuinely add is *the audio itself, kept beside the words*. That is worth having. It is also
exactly `records attach` applied to an `.m4a`, and it needs no concept of voice at all.

## What to do instead

- **Document the flag.** One short section: dictate with your phone's keyboard, then add
  `voiceRecorded: true`. This is the whole of rung 3's user-visible value, and it is available
  now.
- **Let schrank carry the audio.** When `records attach` lands, "keep the recording beside the
  transcript" is a composition of two things that already exist, not a new road.
- **Leave the border where it is.** Nothing here argues for moving it.

## What would change this answer

If `records attach` ships and people then ask for a capture button that records, attaches and
flags in one motion — that is a small, well-defined convenience built on solid ground, and it
would belong to whichever road owns the composing surface, likely
[booth](../booth/ROADMAP.md). It would not need this rung reopened; it would need one button.

Until then, *maybe* resolves to *no*, and the microphone icon keeps meaning what it always meant.
