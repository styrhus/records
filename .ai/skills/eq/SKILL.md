---
name: eq
description: Use when the user invokes /eq to cap every reply at the token length of their own message until /esc
disable-model-invocation: true
---

The user invoked /eq: Equal mode. From now on, no reply may use more tokens than the message the user sent you in that turn.

- The work itself is untouched — tools, edits, verification run exactly as normal. Only the length of your prose is capped.
- Budget: your visible response text must be ≤ the token count of the user's message for that turn. Shorter is fine.
- Tool calls and their output do not count against the budget; only your response prose does.
- If the honest answer won't fit, cut words, not correctness: keep paths, commands, errors, and numbers factual and drop everything else.
- The mode stays active until the user invokes /esc.

Confirm activation now in one short line (within budget).
