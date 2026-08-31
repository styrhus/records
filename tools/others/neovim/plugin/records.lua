-- Registers :Records without requiring setup() — the plugin works unconfigured.
if vim.g.loaded_records then
  return
end
vim.g.loaded_records = true

vim.api.nvim_create_user_command("Records", function()
  require("records").open()
end, { desc = "Open the records chat panel" })

-- hundehus 3: the dog's editor half. `records watch` itself writes no state; these commands run
-- and read their own `records watch --json` process, never touching watch.py.
vim.api.nvim_create_user_command("RecordsWatch", function()
  local ok, msg = require("records").watch_start()
  vim.notify(msg, ok and vim.log.levels.INFO or vim.log.levels.WARN)
end, { desc = "Start records watch in the background" })

vim.api.nvim_create_user_command("RecordsWatchStop", function()
  local ok, msg = require("records").watch_stop()
  vim.notify(msg, ok and vim.log.levels.INFO or vim.log.levels.WARN)
end, { desc = "Stop the background records watch" })

vim.api.nvim_create_user_command("RecordsWatchStatus", function()
  vim.notify(require("records").watch_status(), vim.log.levels.INFO)
end, { desc = "Show records watch status" })
