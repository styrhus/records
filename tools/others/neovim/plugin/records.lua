-- Registers :Records without requiring setup() — the plugin works unconfigured.
if vim.g.loaded_records then
  return
end
vim.g.loaded_records = true

vim.api.nvim_create_user_command("Records", function()
  require("records").open()
end, { desc = "Open the records chat panel" })
