---
name: airtime
description: Use when the user invokes /airtime to report the token share of Human vs Assistant turns so far in the conversation
disable-model-invocation: true
---

The user invoked /airtime: measure how much of the conversation so far each side has taken up, and answer with the split.

- Human = everything the user typed or pasted (messages, slash-command arguments). Assistant = your visible reply prose, code you wrote in replies included.
- Not counted: tool calls and tool output, thinking, system/harness injections (skill bodies, reminders), and this /airtime exchange itself.
- Measure from the conversation in your context — no tools, no transcript files. Estimate the same way on both sides — about 4 characters per token, as `records airtime` does — so the ratio holds even if the absolute counts are off.
- Round to whole percents that sum to 100.
- If earlier turns were compacted into a summary, measure only what is visible and append `(since compaction)`.
- Nothing before this invocation → `Human: 0%, Assistant: 0%`.

Reply with exactly one line and nothing else — `Human: NN%, Assistant: NN%` (e.g. `Human: 12%, Assistant: 88%`).
