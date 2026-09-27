-- SPDX-FileCopyrightText: 2026 tb4
-- SPDX-License-Identifier: AGPL-3.0-or-later

-- records.nvim — Neovim chat panel for the mechanical records skills.
-- Mechanical only: every command shells out to the `records` CLI, no model involved. The one
-- exception is Ollama (ollama_endpoint + ollama_model): still just the CLI, over a background job.

local M = {}

local config = {
  bin = "records",
  ollama_endpoint = nil, -- set to enable two-sided /record and ephemeral chat
  ollama_model = nil, -- required alongside ollama_endpoint
  -- Token-by-token rendering via `records ollama-reply/-chat --stream`. Off by default: --stream
  -- is not wired into cli.py yet (postkasse 2's reported, unapplied diff) — turning this on before
  -- that lands makes every Ollama turn fail the same way an unreachable endpoint does (gracefully:
  -- the human's words still get appended user-only, see ollama_turn()'s fallback).
  stream = false,
}

local recording = nil
local chat_history = {} -- ephemeral turns only; a recording's own history lives in the record file
local busy = false -- one in-flight Ollama call at a time
local chat_buf = nil
local chat_win = nil
local ns = vim.api.nvim_create_namespace("records")

local watch_job = nil
local watch_state = { running = false, last_event = nil, builds = 0, failures = 0 }

-- Forward declarations: the buffer keymaps below are set before these are defined.
local add_line, run_cli, run_cli_async, run_cli_async_stream
local on_submit, handle_slash, handle_message, route_plain_message

function M.setup(opts)
  config = vim.tbl_extend("force", config, opts or {})
end

add_line = function(text, highlight)
  if not (chat_buf and vim.api.nvim_buf_is_valid(chat_buf)) then
    return
  end
  local row = vim.api.nvim_buf_line_count(chat_buf)
  vim.api.nvim_buf_set_lines(chat_buf, row, row, false, { text })
  if highlight then
    vim.api.nvim_buf_set_extmark(chat_buf, ns, row, 0, { end_col = #text, hl_group = highlight })
  end
  if chat_win and vim.api.nvim_win_is_valid(chat_win) then
    vim.api.nvim_win_set_cursor(chat_win, { vim.api.nvim_buf_line_count(chat_buf), 0 })
  end
end

-- A growing line (or lines) appended to token by token. start_stream() opens it; every
-- append_stream_token() call redraws from the same start row, so a mid-word buffer flush never
-- shows as two separate lines.
local function start_stream()
  if not (chat_buf and vim.api.nvim_buf_is_valid(chat_buf)) then
    return nil
  end
  local row = vim.api.nvim_buf_line_count(chat_buf)
  vim.api.nvim_buf_set_lines(chat_buf, row, row, false, { "" })
  return { start_row = row, text = "" }
end

local function append_stream_token(stream, token)
  if not (stream and chat_buf and vim.api.nvim_buf_is_valid(chat_buf)) then
    return
  end
  stream.text = stream.text .. token
  local lines = vim.split(stream.text, "\n", { plain = true })
  vim.api.nvim_buf_set_lines(chat_buf, stream.start_row, -1, false, lines)
  if chat_win and vim.api.nvim_win_is_valid(chat_win) then
    vim.api.nvim_win_set_cursor(chat_win, { vim.api.nvim_buf_line_count(chat_buf), 0 })
  end
end

-- argv as a list, never a string: record titles carry '#' and spaces, which a shell would eat.
local function build_argv(command, opts)
  opts = opts or {}
  local argv = { config.bin, command }
  for _, v in ipairs(opts.positional or {}) do
    if v and v ~= "" then
      table.insert(argv, v)
    end
  end
  for k, v in pairs(opts.flags or {}) do
    if v == true then
      table.insert(argv, "--" .. k)
    elseif v then
      table.insert(argv, "--" .. k)
      table.insert(argv, tostring(v))
    end
  end
  return argv
end

run_cli = function(command, opts)
  local argv = build_argv(command, opts)
  local out = vim.fn.system(argv)
  if vim.v.shell_error ~= 0 and out == "" then
    error("could not run '" .. config.bin .. "' — is the recordkit CLI installed?")
  end
  local ok, parsed = pcall(vim.json.decode, out)
  if not ok then
    error("invalid CLI response: " .. out)
  end
  if parsed.error then
    error(parsed.error)
  end
  return parsed
end

-- Non-blocking twin of run_cli(), for calls slow enough to freeze the editor (an Ollama reply can
-- take up to DEFAULT_TIMEOUT = 120s). jobstart, not vim.system: the plugin's stated floor is
-- Neovim 0.9, and vim.system needs 0.10. on_done(ok, result_or_error) always runs, on the main loop.
run_cli_async = function(command, opts, on_done)
  local argv = build_argv(command, opts)
  local chunks = {}
  local job = vim.fn.jobstart(argv, {
    stdout_buffered = true,
    on_stdout = function(_, data)
      if data then
        vim.list_extend(chunks, data)
      end
    end,
    on_exit = function(_, code)
      local out = table.concat(chunks, "\n")
      vim.schedule(function()
        if code ~= 0 and out == "" then
          on_done(false, "could not run '" .. config.bin .. "' — is the recordkit CLI installed?")
          return
        end
        local ok, parsed = pcall(vim.json.decode, out)
        if not ok then
          on_done(false, "invalid CLI response: " .. out)
          return
        end
        if parsed.error then
          on_done(false, parsed.error)
          return
        end
        on_done(true, parsed)
      end)
    end,
  })
  if job <= 0 then
    vim.schedule(function()
      on_done(false, "could not run '" .. config.bin .. "' — is the recordkit CLI installed?")
    end)
  end
end

-- Streaming twin: `command` is expected to emit NDJSON on stdout (one {"token": "…"} object per
-- chunk, then one final object shaped like the non-streaming reply — the postkasse 2 cli.py
-- contract, not yet wired). on_token fires per chunk; on_done(ok, result_or_error) fires once, at
-- the end, same signature as run_cli_async's.
run_cli_async_stream = function(command, opts, on_token, on_done)
  local argv = build_argv(command, opts)
  local buf = ""
  local final_obj = nil
  local err_msg = nil
  local job = vim.fn.jobstart(argv, {
    stdout_buffered = false,
    on_stdout = function(_, data)
      if not data then
        return
      end
      buf = buf .. table.concat(data, "\n")
      local lines = vim.split(buf, "\n", { plain = true })
      buf = table.remove(lines) -- last element may be an incomplete line; keep it for next time
      for _, line in ipairs(lines) do
        if line ~= "" then
          local ok, obj = pcall(vim.json.decode, line)
          if ok and type(obj) == "table" then
            if obj.token ~= nil then
              vim.schedule(function()
                on_token(obj.token)
              end)
            elseif obj.error then
              err_msg = obj.error
            else
              final_obj = obj
            end
          end
        end
      end
    end,
    on_exit = function(_, code)
      vim.schedule(function()
        if err_msg then
          on_done(false, err_msg)
        elseif final_obj then
          on_done(true, final_obj)
        elseif code ~= 0 then
          on_done(false, "records " .. command .. " exited " .. tostring(code))
        else
          on_done(false, "no result from records " .. command)
        end
      end)
    end,
  })
  if job <= 0 then
    vim.schedule(function()
      on_done(false, "could not run '" .. config.bin .. "' — is the recordkit CLI installed?")
    end)
  end
end

local function ollama_config()
  if not config.ollama_endpoint or config.ollama_endpoint == "" then
    return nil
  end
  return { endpoint = config.ollama_endpoint, model = config.ollama_model }
end

local function start_recording(mode, args)
  local draft = mode == "me"
  local result = run_cli("new", { positional = { args }, flags = { draft = draft or nil } })
  -- session semantics mirror the VSCode sidebar: only /record gets a model, captured now and
  -- reset on /esc — never re-read mid-recording, so a settings change can't switch voice midway.
  local ollama = nil
  if mode == "record" then
    ollama = ollama_config()
    if ollama and (not ollama.model or ollama.model == "") then
      add_line("Set ollama_model to enable two-sided /record — recording user-only.", "WarningMsg")
      ollama = nil
    end
  end
  recording = { file = result.path, draft = draft, ollama = ollama }
  chat_history = {}
  add_line("Recording (" .. mode .. (ollama and (" · ollama " .. ollama.model) or "") .. "): "
           .. result.path, "Function")
end

local function stick_record(slug)
  if slug == "" then
    error("a slug is required: /stick <slug>")
  end
  local result = run_cli("stick", { flags = { slug = slug } })
  add_line("Featured: " .. result.path, "Function")
end

local function commit(mode, message)
  if message == "" then
    message = vim.fn.input("Commit message: ")
  end
  if message == "" then
    error("commit message required")
  end
  local push = mode ~= "gc"
  run_cli("commit", {
    flags = { message = message, push = push or nil, deploy = (mode == "cpd") or nil },
  })
  add_line(string.format("Commit %s: %s", push and "(pushed)" or "(staged)", message), "Function")
end

local function save_name(name)
  if name == "" then
    name = vim.fn.input("Your name: ")
  end
  if name == "" then
    return
  end
  run_cli("myname", { positional = { name } })
  add_line("Saved your name: " .. name, "Function")
end

local function mucke()
  if not recording then
    error("/mucke stamps the track into the record being written — start one first")
  end
  local result = run_cli("mucke", { flags = { file = recording.file } })
  add_line("Mucke: " .. tostring(result.title) .. " • " .. tostring(result.artist), "Function")
end

local function airtime()
  if not recording then
    error("/airtime measures the record being written — start one first")
  end
  local result = run_cli("airtime", { flags = { file = recording.file } })
  add_line(tostring(result.line), "Function")
end

local function show_config()
  local result = run_cli("config", {})
  add_line("Records dir: " .. result.records_dir, "Function")
end

-- The two-sided /record turn: `records ollama-reply` against the active recording. A failed or
-- unreachable model must never lose the human's words — on any failure the same text goes through
-- the plain, mechanical `append` instead, exactly like /all would have recorded it.
local function ollama_turn(text)
  if busy then
    add_line("Still waiting on a reply — one turn at a time.", "Comment")
    return
  end
  local file, ollama = recording.file, recording.ollama
  busy = true

  local function fallback(reason)
    local ok, err = pcall(run_cli, "append", { flags = { file = file, text = text } })
    busy = false
    if ok then
      add_line("Ollama failed — recorded your message user-only. (" .. tostring(reason) .. ")",
               "WarningMsg")
    else
      add_line("ERROR: " .. tostring(err), "ErrorMsg")
    end
  end

  local base_flags = { file = file, endpoint = ollama.endpoint, model = ollama.model, human = text }

  if config.stream then
    local stream = nil
    run_cli_async_stream("ollama-reply",
      { flags = vim.tbl_extend("force", base_flags, { stream = true }) },
      function(token)
        stream = stream or start_stream()
        append_stream_token(stream, token)
      end,
      function(ok, result)
        busy = false
        if not ok then
          fallback(result)
        elseif not stream then
          -- no chunks arrived (e.g. a one-word reply landed in the final line only)
          add_line(tostring(result.reply), "Function")
        end
      end)
  else
    add_line(ollama.model .. " is thinking…", "Comment")
    run_cli_async("ollama-reply", { flags = base_flags }, function(ok, result)
      busy = false
      if ok then
        add_line(tostring(result.reply), "Function")
      else
        fallback(result)
      end
    end)
  end
end

-- Without an active recording, and with a model configured, plain messages become an ephemeral
-- chat via `records ollama-chat` — same as the VSCode sidebar. Nothing is ever written to disk.
local function ephemeral_chat(text)
  local oc = ollama_config()
  if not oc or not oc.model or oc.model == "" then
    return
  end
  if busy then
    add_line("Still waiting on a reply — one turn at a time.", "Comment")
    return
  end
  busy = true

  local function record_turn(reply)
    table.insert(chat_history, { role = "user", content = text })
    table.insert(chat_history, { role = "assistant", content = reply })
  end

  local base_flags = { endpoint = oc.endpoint, model = oc.model, human = text,
                       history = vim.json.encode(chat_history) }

  if config.stream then
    local stream = nil
    run_cli_async_stream("ollama-chat",
      { flags = vim.tbl_extend("force", base_flags, { stream = true }) },
      function(token)
        stream = stream or start_stream()
        append_stream_token(stream, token)
      end,
      function(ok, result)
        busy = false
        if ok then
          record_turn(tostring(result.reply))
          if not stream then
            add_line(tostring(result.reply), "Function")
          end
        else
          add_line("ERROR: " .. tostring(result), "ErrorMsg")
        end
      end)
  else
    add_line(oc.model .. " is thinking… (not recorded)", "Comment")
    run_cli_async("ollama-chat", { flags = base_flags }, function(ok, result)
      busy = false
      if ok then
        record_turn(tostring(result.reply))
        add_line(tostring(result.reply), "Function")
      else
        add_line("ERROR: " .. tostring(result), "ErrorMsg")
      end
    end)
  end
end

handle_slash = function(cmd, args)
  local ok, err
  if cmd == "record" or cmd == "all" or cmd == "me" then
    ok, err = pcall(start_recording, cmd, args)
  elseif cmd == "esc" then
    recording = nil
    chat_history = {}
    add_line("Recording stopped.", "Statement")
    return
  elseif cmd == "stick" then
    ok, err = pcall(stick_record, args)
  elseif cmd == "gc" or cmd == "gcp" or cmd == "cpd" then
    ok, err = pcall(commit, cmd, args)
  elseif cmd == "myname" then
    ok, err = pcall(save_name, args)
  elseif cmd == "mucke" then
    ok, err = pcall(mucke)
  elseif cmd == "airtime" then
    ok, err = pcall(airtime)
  elseif cmd == "config" then
    ok, err = pcall(show_config)
  else
    add_line("ERROR: unknown command: /" .. cmd, "ErrorMsg")
    return
  end

  if not ok then
    add_line("ERROR: " .. tostring(err), "ErrorMsg")
  end
end

handle_message = function(text)
  if recording.ollama then
    ollama_turn(text)
    return
  end
  local ok, err = pcall(run_cli, "append", { flags = { file = recording.file, text = text } })
  if not ok then
    add_line("ERROR: " .. tostring(err), "ErrorMsg")
  end
end

-- Shared by on_submit and M.send: a plain (non-slash) line either appends to the active
-- recording, becomes an ephemeral chat turn, or — with neither — is a no-op the caller reports.
route_plain_message = function(text)
  if recording then
    handle_message(text)
    return true
  end
  local oc = ollama_config()
  if oc and oc.model and oc.model ~= "" then
    ephemeral_chat(text)
    return true
  end
  return false
end

on_submit = function()
  local line = vim.api.nvim_get_current_line()
  if line:match("^%s*$") then
    return
  end

  add_line("> " .. line, "Comment")
  vim.api.nvim_set_current_line("")

  if line:sub(1, 1) == "/" then
    local parts = vim.split(line:sub(2), "%s+")
    handle_slash(parts[1], table.concat(vim.list_slice(parts, 2), " "))
  elseif not route_plain_message(line) then
    add_line("Nothing is being recorded — /record, /all or /me starts one.", "Comment")
  end
end

--- Send one line to the chat exactly as if it had been typed. Used by tests and mappings.
function M.send(line)
  if not (chat_buf and vim.api.nvim_buf_is_valid(chat_buf)) then
    M.open()
  end
  if line:sub(1, 1) == "/" then
    local parts = vim.split(line:sub(2), "%s+")
    handle_slash(parts[1], table.concat(vim.list_slice(parts, 2), " "))
  else
    route_plain_message(line)
  end
end

function M.open()
  if chat_win and vim.api.nvim_win_is_valid(chat_win) then
    vim.api.nvim_set_current_win(chat_win)
    return
  end

  chat_buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_name(chat_buf, "records://chat")
  vim.bo[chat_buf].buftype = "nofile"
  vim.bo[chat_buf].modeline = false

  local height = math.floor(vim.o.lines * 0.4)
  chat_win = vim.api.nvim_open_win(chat_buf, true, {
    relative = "editor",
    width = vim.o.columns,
    height = height,
    row = vim.o.lines - height - 1,
    col = 0,
    style = "minimal",
    border = "rounded",
  })

  vim.keymap.set("n", "q", M.close, { buffer = chat_buf })
  vim.keymap.set("i", "<CR>", on_submit, { buffer = chat_buf })

  add_line("Records chat — /command or a plain message. q to close.")
  add_line("")
end

function M.close()
  if chat_win and vim.api.nvim_win_is_valid(chat_win) then
    vim.api.nvim_win_close(chat_win, true)
  end
  chat_win = nil
end

-- hundehus 3: the watch's editor half. `records watch` writes no state file (by design — it never
-- writes anything), so status comes from parsing --json events off the process this plugin itself
-- spawned. watch.py is untouched; this only ever reads its stdout.
local function watch_on_event(obj)
  watch_state.last_event = obj
  if obj.event == "build" then
    watch_state.builds = watch_state.builds + 1
    if not obj.ok then
      watch_state.failures = watch_state.failures + 1
    end
  end
end

--- Start `records watch --json` in the background. opts: { interval = number, notify = string }.
--- Returns ok, message.
function M.watch_start(opts)
  if watch_job then
    return false, "records watch is already running"
  end
  opts = opts or {}
  local argv = { config.bin, "watch", "--json" }
  if opts.interval then
    table.insert(argv, "--interval")
    table.insert(argv, tostring(opts.interval))
  end
  if opts.notify then
    table.insert(argv, "--notify")
    table.insert(argv, opts.notify)
  end

  local buf = ""
  watch_state = { running = true, last_event = nil, builds = 0, failures = 0 }
  local job = vim.fn.jobstart(argv, {
    stdout_buffered = false,
    on_stdout = function(_, data)
      if not data then
        return
      end
      buf = buf .. table.concat(data, "\n")
      local lines = vim.split(buf, "\n", { plain = true })
      buf = table.remove(lines)
      for _, line in ipairs(lines) do
        if line ~= "" then
          local ok, obj = pcall(vim.json.decode, line)
          if ok and type(obj) == "table" then
            vim.schedule(function()
              watch_on_event(obj)
            end)
          end
        end
      end
    end,
    on_exit = function()
      vim.schedule(function()
        watch_state.running = false
        watch_job = nil
      end)
    end,
  })
  if job <= 0 then
    watch_state.running = false
    return false, "could not start records watch — is the recordkit CLI installed?"
  end
  watch_job = job
  return true, "records watch started"
end

--- Stop the background watcher, if running. Returns ok, message.
function M.watch_stop()
  if not watch_job then
    return false, "records watch is not running"
  end
  vim.fn.jobstop(watch_job)
  watch_job = nil
  watch_state.running = false
  return true, "records watch stopped"
end

--- One-line human-readable status, e.g. for :RecordsWatchStatus. Never touches watch.py — reads
--- only the events this session's own `records watch --json` process has emitted so far.
function M.watch_status()
  if not watch_state.running then
    return "records watch: not running"
  end
  local ev = watch_state.last_event
  if not ev then
    return "records watch: running — no build yet"
  end
  if ev.event == "missing" then
    return "records watch: running — " .. tostring(ev.message)
  end
  local status = ev.ok and "last build ok" or "last build FAILED"
  return string.format("records watch: running — %s (%s; %d builds, %d failures)",
                       status, tostring(ev.time), watch_state.builds, watch_state.failures)
end

return M
