# .zshrc

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# Path to your dotfiles.
export DOTFILES=$HOME/.dotfiles

# Setup required env var for oh-my-zsh plugins
export ZSH="$(antibody home)/https-COLON--SLASH--SLASH-github.com-SLASH-robbyrussell-SLASH-oh-my-zsh"

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH
export PATH=/opt/homebrew/bin:$PATH
export PATH=/usr/local/bin:$PATH
export PATH=./vendor/bin:$PATH
export PATH=~/.bin:$PATH
export PATH=/opt:$PATH

# ~/.antigen
source "$DOTFILES/antigen/antigen.zsh"

antigen init ~/.antigenrc

# Load the Antibody plugin manager for zsh.
# source <(antibody init)

# Configuration {{{
# ==============================================================================

HYPHEN_INSENSITIVE="true"
ENABLE_CORRECTION="false"
COMPLETION_WAITING_DOTS="true"
HIST_STAMPS="yyyy-mm-dd"

typeset -U path cdpath fpath

# Vim mode
bindkey -v
export KEYTIMEOUT=1

# Kitty bindings
bindkey "\e[1;3D" backward-word # ⌥←
bindkey "\e[1;3C" forward-word # ⌥→

export GIT_EDITOR=vim

path=(
    $HOME/.local/bin
    $HOME/.bin
    $HOME/bin
    $HOME/.composer/vendor/bin
    $HOME/.go/bin
    ./vendor/bin
    ${ANDROID_HOME}tools/
    ${ANDROID_HOME}platform-tools/
    $path
)

setopt auto_cd
cdpath=(
    $HOME/Code
)

zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format %d
zstyle ':completion:*:descriptions' format %B%d%b
zstyle ':completion:*:complete:(cd|pushd):*' tag-order \
    'local-directories named-directories'

export EDITOR='vim'
export NVIM_LISTEN_ADDRESS='/tmp/nvimsocket'
# export FZF_DEFAULT_COMMAND='ag -u -g ""'

unsetopt sharehistory

# Open vim with z argument
v() {
    if [ -n "$1" ]; then
    z $1
    fi

    nvim
}

# cd() {
#     cd $1 && eval ls
# }
# alias cd="cdls"
open () {
    xdg-open $* > /dev/null 2>&1
}

if (( $+commands[tag] )); then
    tag() { command tag "$@"; source ${TAG_ALIAS_FILE:-/tmp/tag_aliases} 2>/dev/null }
    alias ag=tag
fi


# }}}

# Interactive shell startup scripts {{{
# ==============================================================================

if [[ $- == *i* && $0 == '/bin/zsh' ]]; then
    ~/.dotfiles/scripts/login.sh
fi

# }}}

[ -f ~/.zsh_envs ] && source ~/.zsh_envs
[ -f ~/.zsh_aliases ] && source ~/.zsh_aliases
[ -f ~/.zsh_functions ] && source ~/.zsh_functions
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh