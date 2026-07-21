-- records.nvim — Neovim chat panel for mechanical records skills
-- Usage: :Records to open, see setup() for config

local M = {}

local config = {
  bin = "records",
  ollama_endpoint = nil,
}

local recording = nil
local chat_buf = nil
local chat_win = nil

function M.setup(opts)
  opts = opts or {}
  config = vim.tbl_extend("force", config, opts)
end

function M.open()
  if chat_win and vim.api.nvim_win_is_valid(chat_win) then
    vim.api.nvim_set_current_win(chat_win)
    return
  end

  chat_buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_name(chat_buf, "records://chat")
  vim.api.nvim_buf_set_option(chat_buf, "buftype", "nofile")
  vim.api.nvim_buf_set_option(chat_buf, "modeline", false)

  local height = math.floor(vim.o.lines * 0.4)
  local opts = {
    relative = "editor",
    width = vim.o.columns,
    height = height,
    row = vim.o.lines - height - 1,
    col = 0,
    style = "minimal",
    border = "rounded",
  }
  chat_win = vim.api.nvim_open_win(chat_buf, true, opts)

  -- Keybindings in the chat buffer
  vim.keymap.set("n", "q", function() M.close() end, { buffer = chat_buf })
  vim.keymap.set("i", "<CR>", function() on_submit() end, { buffer = chat_buf })

  add_line("Records chat — /command or message. q to close.")
  add_line("")
end

function M.close()
  if chat_win and vim.api.nvim_win_is_valid(chat_win) then
    vim.api.nvim_win_close(chat_win, true)
  end
  chat_win = nil
  recording = nil
end

local function add_line(text, highlight)
  if not (chat_buf and vim.api.nvim_buf_is_valid(chat_buf)) then
    return
  end
  local line_count = vim.api.nvim_buf_line_count(chat_buf)
  vim.api.nvim_buf_set_lines(chat_buf, line_count, line_count, false, { text })
  if highlight then
    local ns = vim.api.nvim_create_namespace("records")
    vim.api.nvim_buf_add_highlight(
      chat_buf,
      ns,
      highlight,
      line_count,
      0,
      -1
    )
  end
  vim.api.nvim_win_set_cursor(chat_win, { vim.api.nvim_buf_line_count(chat_buf), 0 })
end

local function run_cli(command, opts)
  local args = { command }
  for k, v in pairs(opts or {}) do
    if k == "arguments" then
      table.insert(args, v)
    elseif v == true then
      table.insert(args, "--" .. k)
    elseif v then
      table.insert(args, "--" .. k)
      table.insert(args, tostring(v))
    end
  end

  local result = vim.fn.system(table.concat({ config.bin, table.concat(args, " ") }, " "))
  local ok, parsed = pcall(vim.json.decode, result)
  if not ok then
    error("Invalid CLI response: " .. result)
  end
  if parsed.error then
    error(parsed.error)
  end
  return parsed
end

local function on_submit()
  local line = vim.api.nvim_get_current_line()
  if line:match("^%s*$") then
    return
  end

  add_line("> " .. line, "Comment")
  vim.api.nvim_set_current_line("")

  if line:sub(1, 1) == "/" then
    local parts = vim.split(line:sub(2), "%s+")
    local cmd = parts[1]
    local args = table.concat(vim.list_slice(parts, 2), " ")
    handle_slash(cmd, args)
  else
    if recording then
      handle_message(line)
    else
      add_line("ERROR: No active recording session.", "ErrorMsg")
    end
  end
end

function handle_slash(cmd, args)
  local ok, result
  if cmd == "record" or cmd == "all" or cmd == "me" then
    ok, result = pcall(start_recording, cmd, args)
  elseif cmd == "esc" then
    recording = nil
    add_line("Recording stopped.", "Statement")
    return
  elseif cmd == "stick" then
    ok, result = pcall(stick_record, args)
  elseif cmd == "gc" or cmd == "gcp" or cmd == "cpd" then
    ok, result = pcall(commit, cmd, args)
  elseif cmd == "myname" then
    ok, result = pcall(myname, args)
  elseif cmd == "mucke" then
    ok, result = pcall(mucke)
  elseif cmd == "config" then
    ok, result = pcall(config_cmd)
  else
    add_line("ERROR: Unknown command: " .. cmd, "ErrorMsg")
    return
  end

  if not ok then
    add_line("ERROR: " .. tostring(result), "ErrorMsg")
  else
    add_line("OK", "Statement")
  end
end

function handle_message(text)
  if not recording then
    add_line("ERROR: No active recording session.", "ErrorMsg")
    return
  end
  local ok, result = pcall(run_cli, "append", { file = recording.file, text = text })
  if not ok then
    add_line("ERROR: " .. tostring(result), "ErrorMsg")
  end
end

function start_recording(mode, args)
  local draft = mode == "me"
  local result = run_cli("new", { arguments = args, draft = draft and "true" or nil })
  recording = { file = result.path, draft = draft }
  add_line("Recording (" .. mode .. "): " .. result.path, "Function")
end

function stick_record(slug)
  local result = run_cli("stick", { slug = slug })
  add_line("Featured: " .. result.path, "Function")
end

function commit(mode, message)
  if message == "" then
    message = vim.fn.input("Commit message: ")
  end
  if message == "" then
    add_line("ERROR: Commit message required.", "ErrorMsg")
    return
  end

  local push = mode ~= "gc"
  local deploy = mode == "cpd"
  local result = run_cli("commit", {
    message = message,
    push = push and "true" or nil,
    deploy = deploy and "true" or nil,
  })
  add_line(string.format("Commit %s: %s", push and "(pushed)" or "(staged)", message), "Function")
end

function myname(name)
  if name == "" then
    name = vim.fn.input("Your name: ")
  end
  if name == "" then
    return
  end
  local result = run_cli("myname", { name = name })
  add_line("Saved your name: " .. name, "Function")
end

function mucke()
  local result = run_cli("mucke", { file = vim.fn.expand("%:p") })
  add_line("Mucke: " .. result.title .. " • " .. result.artist, "Function")
end

function config_cmd()
  local result = run_cli("config", {})
  add_line("Records dir: " .. result.records_dir, "Function")
end

vim.api.nvim_create_user_command("Records", M.open, {})

return M
