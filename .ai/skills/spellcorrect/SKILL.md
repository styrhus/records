---
name: spellcorrect
description: Use when the user invokes /spellcorrect to start appending spelling corrections of the user's messages as a P.S. until /esc
disable-model-invocation: true
---

The user invoked /spellcorrect: from now on, check every user message for spelling mistakes and correct them in a P.S. at the end of your reply.

- The work itself is untouched — handle every request exactly as normal. The P.S. is the only addition.
- Check only the user's own prose. Ignore code, commands, paths, URLs, quoted output, and words in other languages.
- Flag only clear misspellings of real words. Not grammar, not punctuation, not style, not casing, not abbreviations (`msg`, `repo`), not proper nouns.
- End the reply with one short, friendly paragraph, each word exactly as the user wrote it, listed once:

  P.S. appreaciate → appreciate, wheter → whether.

- **No mistakes → no P.S.** Never write a P.S. to say the spelling was fine, never praise the spelling, never show a word "corrected" to its identical self. Silence is the compliment.
- The mode stays active until the user invokes /esc (or /esc spellcorrect).

Confirm activation now with a single line.
