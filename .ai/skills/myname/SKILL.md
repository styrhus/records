---
name: myname
description: Use when the user invokes /myname to record the user's name in persistent memory
disable-model-invocation: true
model: haiku
effort: low
argument-hint: "<username>"
allowed-tools:
  - Read
  - Write
  - Edit
---

The user invoked /myname: save their name to persistent memory so it is remembered across sessions.

## The name

- The name is `$ARGUMENTS`, taken verbatim (trim only leading/trailing whitespace).
- **Required.** If `$ARGUMENTS` is empty, do nothing but reply with one line asking for a name (`Usage: /myname <username>`) and stop.

## Save it

Persistent memory lives in the memory directory named in this session's memory instructions (`.../memory/`). Write there:

1. Write the file `<memory-dir>/user-name.md`, overwriting any existing one:

   ```markdown
   ---
   name: user-name
   description: The user's name
   metadata:
     type: user
   ---

   The user's name is <name>.
   ```

2. Add (or update) the pointer line in `<memory-dir>/MEMORY.md`:
   `- [User's name](user-name.md) — the user is <name>`
   Create MEMORY.md if it does not exist; do not duplicate the line if it is already there.

Confirm with one line: `Saved your name: <name>`
