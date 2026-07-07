---
name: esc
description: Use when the user invokes /esc to stop active session modes (recording, poetic, equal, pirate, spell correction)
disable-model-invocation: true
model: haiku
effort: low
argument-hint: "[mode]"
---

The user invoked /esc: stop session modes. This invocation and this response are NOT recorded.

Mode argument: `$ARGUMENTS` — if this names a mode (record / all / me / poet / eq / pirate / spellcorrect), stop only it; if blank, stop every active mode.

- Recording (/record, /all, /me): stop appending to the transcript. Confirm: `Recording stopped: <path>`
- Poetic mode (/poet): resume normal prose. Confirm: `Poetic mode stopped.`
- Equal mode (/eq): drop the token-length cap on replies. Confirm: `Equal mode stopped.`
- Pirate mode (/pirate): resume normal voice. Confirm: `Pirate mode stopped.`
- Spell correction (/spellcorrect): stop appending the P.S. Confirm: `Spell correction stopped.`

One confirmation line per stopped mode. If nothing matching was active, reply: `No active mode.`
