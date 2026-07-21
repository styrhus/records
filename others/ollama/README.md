# Ollama Integration for Records

The Records engine (`../python/`) and plugins (VSCode, Neovim) are fully usable with **no AI** — they support all mechanical skills (create, feature, commit/deploy, now-playing) plus user-only recording (`/all`, `/me`).

**Ollama** is the documented seam where a locally-hosted LLM brings back the AI features:
- Two-sided `/record` — user message → local model → assistant reply + signature
- Voice/style skills — `/poet`, `/pirate`, `/eq`, `/bff`, `/spellcorrect` — as system-prompt presets

## Setup (Future)

When you want to enable Ollama:

1. **Install and run Ollama** locally (https://ollama.ai). By default it listens on `http://localhost:11434`.

2. **Pull a model** you like:
   ```bash
   ollama pull mistral
   # or
   ollama pull neural-chat
   # or
   ollama pull your-preferred-model
   ```

3. **Configure the plugins** to point to your endpoint:
   - **VSCode**: Settings → `records.ollamaEndpoint` → `http://localhost:11434`
   - **Neovim**: In your config, pass the endpoint to `setup()`:
     ```lua
     require("records").setup({
       ollama_endpoint = "http://localhost:11434"
     })
     ```

4. **Use `/record` two-sided**:
   - Type a user message or slash-command
   - The plugin sends it to the local model (via the recordkit CLI, to be implemented)
   - The model's reply appears in the chat, and is written to the file as:
     ```
     ## Human
     <your message>
     
     ## Assistant
     <model response>
     
     — model-name:7b
     ```
   - The signature (model tag) is automatically stripped by Hugo during rendering.

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
- **No context window** — each `/record` turn is independent; multi-turn memory is on the roadmap.
- **No prompt templates** — model behavior depends entirely on the system prompt and the model itself.
- **No tool use** — the model can't call commands or read files; it's pure text-in, text-out.

## Fallback (No Ollama)

If Ollama is not configured or the endpoint is unreachable:
- `/record` falls back to `/all` (user-only recording).
- Voice skills are unavailable (the UI will warn).
- All mechanical skills continue to work.

This keeps the Records site usable offline or on minimal hardware.

## Building Support

The plugins (VSCode, Neovim) need to:
1. Detect if `ollama_endpoint` is configured.
2. When `/record` is invoked and Ollama is available:
   - Send the user's message to the CLI with a flag (e.g., `--ollama-reply`).
   - The CLI POSTs the message to `http://localhost:11434/api/generate` (or `/api/chat`).
   - Parse the model's response and pipe it to the display.
   - Call `records append-turn --file ... --human ... --assistant ... --model <tag>`.
3. Fall back to user-only mode if Ollama is absent or fails.

Voice skills can piggyback on this by injecting a system prompt into the request.

---

For now, enjoy the Records engine without AI — it's complete and rock-solid. Ollama support
is a natural extension whenever you want it.
