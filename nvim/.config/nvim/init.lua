-- fui // NEOVIM
-- A small, complete setup on the CRT palette: files (oil, telescope), git signs, a status
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

local crt = { bg = "#0D0D0D", fg = "#D4D4D4", dim = "#8A8A8A", green = "#5FD75F", blue = "#6AB0FF",
              yellow = "#E5C07B", red = "#FF6B6B", magenta = "#C678DD", panel = "#1A1A1A" }
local function section(b) return { a = { fg = crt.bg, bg = b, gui = "bold" }, b = { fg = crt.fg, bg = crt.panel }, c = { fg = crt.dim, bg = crt.bg } } end

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
      options = { theme = { normal = section(crt.green), insert = section(crt.blue), visual = section(crt.magenta),
                            replace = section(crt.red), command = section(crt.yellow), inactive = section(crt.dim) },
                  section_separators = "", component_separators = "│", globalstatus = true },
      sections = { lualine_a = { "mode" }, lualine_b = { "branch", "diff" }, lualine_c = { { "filename", path = 1 } },
                   lualine_x = { "diagnostics", "filetype" }, lualine_y = { "progress" }, lualine_z = { "location" } } } },
  { "folke/which-key.nvim", event = "VeryLazy", opts = { win = { border = "rounded" } } },
  { "saghen/blink.cmp", version = "1.*", event = "InsertEnter", opts = { keymap = { preset = "default" },
      completion = { menu = { border = "rounded" }, documentation = { auto_show = true, window = { border = "rounded" } } } } },
  { "mason-org/mason.nvim", opts = { ui = { border = "rounded" } } },
  { "mason-org/mason-lspconfig.nvim", dependencies = { "mason-org/mason.nvim", "neovim/nvim-lspconfig" },
    opts = { automatic_enable = true } },
}, {
  install = { colorscheme = { "fui" } },
  lockfile = vim.fn.stdpath("data") .. "/lazy-lock.json",   -- not in ~/.config: that folder is the git repo
  ui = { border = "rounded" },
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
vim.diagnostic.config({ float = { border = "rounded" }, virtual_text = { prefix = "▪" } })
