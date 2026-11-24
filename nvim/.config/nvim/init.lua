-- fui // NEOVIM
-- A small, complete setup on the console palette: files (oil, telescope), git signs, a status
-- line, completion and language servers (mason installs them: :Mason). Plugins install
-- themselves on the first start (lazy.nvim). Space is the leader; Space alone shows the keys.

vim.g.mapleader = " "
vim.g.maplocalleader = " "
local o = vim.opt
o.number, o.relativenumber, o.cursorline = true, true, true
o.signcolumn = "yes"
o.termguicolors = true
o.mouse = "a"
o.clipboard = "unnamedplus"
o.ignorecase, o.smartcase = true, true
o.expandtab, o.shiftwidth, o.tabstop = true, 4, 4
o.splitright, o.splitbelow = true, true
o.scrolloff = 6
o.undofile = true
o.updatetime = 250
o.laststatus = 3
o.fillchars = { eob = " " }
pcall(vim.cmd.colorscheme, "fui")

-- lazy.nvim, cloned on the first start
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", "https://github.com/folke/lazy.nvim.git", lazypath })
end
vim.opt.rtp:prepend(lazypath)
local ok, lazy = pcall(require, "lazy")
if not ok then return end

-- the edition's console palette, from colors/fui.lua (a cyan fallback if it didn't load)
local con = vim.g.fui_palette or { bg = "#07090C", fg = "#E6EBF0", dim = "#7A8590", signal = "#00C2D1", blue = "#7AA7FF",
                                   yellow = "#F2A93B", red = "#FF5C6C", magenta = "#B78CFF", raised = "#181C21" }
local function section(b) return { a = { fg = con.bg, bg = b, gui = "bold" }, b = { fg = con.fg, bg = con.raised }, c = { fg = con.dim, bg = con.bg } } end

lazy.setup({
  { "stevearc/oil.nvim", opts = { view_options = { show_hidden = true } },
    keys = { { "-", "<cmd>Oil<cr>", desc = "files: the folder of this file" } } },
  { "nvim-telescope/telescope.nvim", dependencies = { "nvim-lua/plenary.nvim" }, cmd = "Telescope",
    keys = {
      { "<leader>f", "<cmd>Telescope find_files<cr>", desc = "find a file" },
      { "<leader>g", "<cmd>Telescope live_grep<cr>", desc = "search in files" },
      { "<leader>b", "<cmd>Telescope buffers<cr>", desc = "open buffers" },
      { "<leader>h", "<cmd>Telescope help_tags<cr>", desc = "help" },
    } },
  { "lewis6991/gitsigns.nvim", event = "BufReadPre", opts = {} },
  { "nvim-lualine/lualine.nvim", opts = {
      options = { theme = { normal = section(con.signal), insert = section(con.blue), visual = section(con.magenta),
                            replace = section(con.red), command = section(con.yellow), inactive = section(con.dim) },
                  section_separators = "", component_separators = "│", globalstatus = true },
      sections = { lualine_a = { "mode" }, lualine_b = { "branch", "diff" }, lualine_c = { { "filename", path = 1 } },
                   lualine_x = { "diagnostics", "filetype" }, lualine_y = { "progress" }, lualine_z = { "location" } } } },
  { "folke/which-key.nvim", event = "VeryLazy", opts = { win = { border = "single" } } },
  { "saghen/blink.cmp", version = "1.*", event = "InsertEnter", opts = { keymap = { preset = "default" },
      completion = { menu = { border = "single" }, documentation = { auto_show = true, window = { border = "single" } } } } },
  { "mason-org/mason.nvim", opts = { ui = { border = "single" } } },
  { "mason-org/mason-lspconfig.nvim", dependencies = { "mason-org/mason.nvim", "neovim/nvim-lspconfig" },
    opts = { automatic_enable = true } },
}, {
  install = { colorscheme = { "fui" } },
  lockfile = vim.fn.stdpath("data") .. "/lazy-lock.json",   -- not in ~/.config: that folder is the git repo
  ui = { border = "single" },
  change_detection = { notify = false },
  rocks = { enabled = false },
})

-- language server keys
vim.api.nvim_create_autocmd("LspAttach", { callback = function(ev)
  local map = function(k, f, d) vim.keymap.set("n", k, f, { buffer = ev.buf, desc = d }) end
  map("gd", vim.lsp.buf.definition, "go to definition")
  map("K", vim.lsp.buf.hover, "hover")
  map("<leader>r", vim.lsp.buf.rename, "rename")
  map("<leader>a", vim.lsp.buf.code_action, "code action")
  map("<leader>d", vim.diagnostic.open_float, "diagnostic")
end })
vim.diagnostic.config({ float = { border = "single" }, virtual_text = { prefix = "▪" } })
