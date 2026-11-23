# HUD // ZSH

# ── history ─────────────────────────────────────────────────────────────
HISTFILE=~/.zsh_history
HISTSIZE=50000
SAVEHIST=50000
setopt HIST_IGNORE_ALL_DUPS HIST_IGNORE_SPACE SHARE_HISTORY INC_APPEND_HISTORY
setopt AUTO_CD INTERACTIVE_COMMENTS

# ── completion ──────────────────────────────────────────────────────────
autoload -Uz compinit && compinit
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

bindkey -e
bindkey '^[[A' history-search-backward
bindkey '^[[B' history-search-forward

# ── aliases ─────────────────────────────────────────────────────────────
if command -v eza >/dev/null; then
  alias ls='eza --group-directories-first'
  alias ll='eza -la --group-directories-first --git'
  alias tree='eza --tree'
fi
command -v bat >/dev/null && alias cat='bat --paging=never'
alias dots='cd ~/.dotfiles'
alias update='yay -Syu'

# ── tools ───────────────────────────────────────────────────────────────
export EDITOR=nvim
# colours for ls/eza/grep/less/man/fzf/jq/gcc/bat come from the theme tokens
[ -r ~/.config/fui/env.sh ] && source ~/.config/fui/env.sh

command -v fzf >/dev/null && source <(fzf --zsh)
command -v starship >/dev/null && eval "$(starship init zsh)"

for plugin in \
  /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh \
  /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh; do
  [ -r "$plugin" ] && source "$plugin"
done
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="${FUI_AUTOSUGGEST:-fg=#2A3A40}"   # set per mode in env.sh

# machine-specific settings, not tracked
[ -r ~/.zshrc.local ] && source ~/.zshrc.local
