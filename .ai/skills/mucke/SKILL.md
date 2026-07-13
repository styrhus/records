---
name: mucke
description: Use when the user invokes /mucke to stamp the currently playing track (looked up via MPRIS) into a file
disable-model-invocation: true
model: haiku
effort: low
argument-hint: "[file]"
shell: bash
allowed-tools:
  - Read
  - Edit
---

The user invoked /mucke: append the now-playing track to a file.

Now playing (captured at invocation):

- Title: !`playerctl metadata title 2>/dev/null || echo __NOTHING_PLAYING__`
- Artist: !`playerctl metadata artist 2>/dev/null`

## Steps

1. Title reads `__NOTHING_PLAYING__` or is empty → say nothing is playing and stop.
2. Target file: the file attached or named in `$ARGUMENTS`; if none, the file currently open in the IDE. Still none, or several → ask which; do not guess.
3. Append one line at the end of the file, separated from existing content by a blank line — the music icon, then title and artist verbatim (no escaping, no reformatting), joined by ` • `, all wrapped in a right-aligned div:

   ```
   <div style="text-align:right"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px" aria-hidden="true"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg> <title> • <artist></div>
   ```

4. Touch nothing else in the file.

Confirm with one line: `Mucke: <title> • <artist> → <path>`
