# Aliases
[ -f ~/.aliases ] && source ~/.aliases

# Enable history
HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
setopt appendhistory

# Load brew on macOS
if [[ "$OSTYPE" =~ ^darwin ]]; then
    export PATH="/opt/homebrew/sbin:$PATH"
    eval $(/opt/homebrew/bin/brew shellenv)
fi