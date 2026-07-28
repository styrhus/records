# Ollama Integration for blyant records

The Records engine (`../python/`) and plugins (VSCode, Neovim) are fully usable with **no AI** — they support all mechanical skills (create, feature, commit/deploy, now-playing) plus user-only recording (`/all`, `/me`).

**Ollama** is the seam where a locally-hosted LLM brings back the AI features:
- Two-sided `/record` — user message → local model → assistant reply + signature (**implemented**: recordkit CLI + VSCode extension)
- Voice/style skills — `/poet`, `/pirate`, `/eq`, `/bff`, `/spellcorrect` — as system-prompt presets (future)

## Setup

To enable Ollama:

1. **Install and run Ollama** locally (https://ollama.ai). By default it listens on `http://localhost:11434`.

2. **Pull a model** you like:
   ```bash
   ollama pull mistral
   # or
   ollama pull neural-chat
   # or
   ollama pull your-preferred-model
   ```

3. **Configure the plugins** to point to your endpoint and model:
   - **VSCode**: Settings → `records.ollamaEndpoint` → `http://localhost:11434` and
     `records.ollamaModel` → the model tag (e.g. `mistral:latest`). Both are required.
   - **Neovim** (not wired yet): In your config, pass the endpoint to `setup()`:
     ```lua
     require("records").setup({
       ollama_endpoint = "http://localhost:11434"
     })
     ```

4. **Use `/record` two-sided**:
   - Type a user message after `/record`
   - The plugin sends it through `records ollama-reply` (see below)
   - The model's reply appears in the chat, and is written to the file as:
     ```
     ## Human
     <your message>
     
     ## Assistant
     <model response>
     
     — model-name:7b
     ```
   - The signature (model tag) is automatically stripped by Hugo during rendering.

## The CLI command

The recordkit CLI does the HTTP work, so every plugin gets Ollama for free:

```bash
records ollama-reply --endpoint http://localhost:11434 --model mistral:latest \
                     --file records/2026-07-24_12-00.md --human "your message"
```

It rebuilds the chat history from the record file's `## Human`/`## Assistant` sections
(signature lines stripped), POSTs to `<endpoint>/api/chat` (`stream: false`, default
timeout 120s, `--timeout` to override), appends the new signed turn, and prints
`{"file", "model", "reply", "appended"}` as JSON. On failure nothing is appended and it
exits 1 with `{"error": "..."}`.

Repeatable `--context-file <path>` / `--context-dir <path>` flags attach workspace context
for that turn: file contents (64 KiB/file, binary/missing files degrade to a marker) and
directory listings (paths only, 500 entries), 256 KiB total, sent as a single system
message to the model. Context is model-only and per-turn — it is never written to the
record. The VSCode extension's `@` attachments and active-editor chip use these flags.

`records ollama-chat` is the fileless sibling for chatting without a recording: same flags
minus `--file`, prior turns passed as a JSON array via `--history` (`-` = stdin, default
`[]`), same context flags. It prints `{"model", "reply", "appended": false}` and never
touches disk — the VSCode extension uses it for ephemeral chat, keeping the history in
memory per session:

```bash
echo '[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]' |
records ollama-chat --endpoint http://localhost:11434 --model mistral:latest \
                    --human "your message" --history -
```

## Model Recommendations

- **mistral** (7B) — fast, good for general recording
- **neural-chat** (7B) — conversation-focused, slightly more verbose
- **dolphin-mixtral** (8x7B, MoE) — larger context, better at complex prompts
- **zephyr** — general-purpose, instruction-tuned

Small models (7B–13B) run on modest hardware (8GB RAM+). Larger models (Mixtral, etc.)
benefit from a GPU or 16GB+ RAM.

## Voice Skills as Prompts (Future)

When two-sided `/record` is active, the style skills can be hooked into the CLI as
system-prompt modifiers:

- `/poet` → system prompt: "Reply in short, precise poetic prose."
- `/pirate` → system prompt: "Speak like a pirate."
- `/eq` → system prompt: "Keep your reply under N tokens." (token budget from user message)
- etc.

The plugins would maintain the active skill set and pass it to the CLI, which would
prepend it to the user's message when calling the model.

## Limitations

- **No streaming** yet — the plugin waits for the full model response before showing it.
- **Context is per record** — the chat history is rebuilt from the record file on every turn, so context resets when a new recording starts (or `/esc`).
- **No prompt templates** — model behavior depends entirely on the system prompt and the model itself.
- **No tool use** — the model can't call commands or read files on its own; it only sees what `--context-file`/`--context-dir` hand it, and that context is per-turn.

## Fallback (No Ollama)

If Ollama is not configured or the endpoint is unreachable:
- `/record` falls back to `/all` (user-only recording).
- Voice skills are unavailable (the UI will warn).
- All mechanical skills continue to work.

This keeps the blyant records site usable offline or on minimal hardware.

## Status

- **recordkit CLI**: done — `records ollama-reply` and the fileless `records ollama-chat` (stdlib urllib, unit-tested with a mocked HTTP layer).
- **VSCode**: done (0.3.0) — `/record` goes two-sided when `records.ollamaEndpoint` + `records.ollamaModel` are set, with a busy indicator and the user-only fallback; `/all` and `/me` stay user-only.
- **Neovim**: pending — wire `config.ollama_endpoint` (+ a model option) to `ollama-reply` in `handle_slash`.
- **Voice skills**: pending — piggyback by injecting a system prompt into the request (the `messages` array makes this a small change).
