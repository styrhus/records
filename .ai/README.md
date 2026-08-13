# .ai/

Vendor-neutral home for the repo's AI assets. `skills/` holds the conversation skills — one `<name>/SKILL.md` per slash command, in the [Agent Skills](https://agentskills.io/specification) format.

Agents find them through discovery symlinks at the repo root:

```
.claude/skills -> ../.ai/skills    # Claude Code
.agents/skills -> ../.ai/skills    # Codex, Mistral Vibe, other .agents/ readers
```

A tool with a different discovery path gets another symlink, never a copy — `.ai/skills/` stays the single source. Cross-vendor portability notes (Claude-specific frontmatter keys, the `` !`command` `` injection syntax) are in the root `AGENTS.md`, which `CLAUDE.md` symlinks to.

The mechanical skills also run without any model via the `records` CLI — see `tools/others/README.md`.
