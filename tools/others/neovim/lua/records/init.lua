-- records.nvim — Neovim chat panel for the mechanical records skills.
-- Mechanical only: every command shells out to the `records` CLI, no model involved.

local M = {}

local config = {
  bin = "records",
  ollama_endpoint = nil, -- reserved; two-sided /record in Neovim is not wired yet
}

local recording = nil
local chat_buf = nil
local chat_win = nil
local ns = vim.api.nvim_create_namespace("records")

-- Forward declarations: the buffer keymaps below are set before these are defined.
local add_line, run_cli, on_submit, handle_slash, handle_message

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

-- argv as a list, never a string: record titles carry '#' and spaces, which a shell would eat.
run_cli = function(command, opts)
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

local function start_recording(mode, args)
  local draft = mode == "me"
  local result = run_cli("new", { positional = { args }, flags = { draft = draft or nil } })
  recording = { file = result.path, draft = draft }
  add_line("Recording (" .. mode .. "): " .. result.path, "Function")
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

local function show_config()
  local result = run_cli("config", {})
  add_line("Records dir: " .. result.records_dir, "Function")
end

handle_slash = function(cmd, args)
  local ok, err
  if cmd == "record" or cmd == "all" or cmd == "me" then
    ok, err = pcall(start_recording, cmd, args)
  elseif cmd == "esc" then
    recording = nil
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
  local ok, err = pcall(run_cli, "append", { flags = { file = recording.file, text = text } })
  if not ok then
    add_line("ERROR: " .. tostring(err), "ErrorMsg")
  end
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
  elseif recording then
    handle_message(line)
  else
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
  elseif recording then
    handle_message(line)
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

return M
