# .zshrc

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# Path to your dotfiles.
export DOTFILES=$HOME/.dotfiles

#############
# Confluent #
#############

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH
export PATH=/opt/homebrew/bin:$PATH
export PATH=/usr/local/bin:$PATH
export PATH=./vendor/bin:$PATH
export PATH=~/.bin:$PATH
export PATH=/opt:$PATH
export PATH=${GOPATH}/bin:${GOROOT}/bin:$PATH
export PATH=/opt/homebrew/opt/node@16/bin:$PATH 

# Flutter setup
export PATH=/opt/homebrew/bin/flutter:$PATH

# Pyenv setup
export PYENV_ROOT="$HOME/.pyenv"

# # Sudo-less gem installs
export GEM_HOME=$HOME/.gem
export PATH=$GEM_HOME/bin:$PATH

export LANG='en_GB.UTF-8'
export LC_ALL='en_GB.UTF-8'

# ~/.antigen
source "$DOTFILES/antigen/antigen.zsh"

antigen init ~/.antigenrc

# Manual zsh completions
fpath=(~/.oh-my-zsh/completions $fpath)

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

unsetopt sharehistory

# Open vim with z argument
v() {
    if [ -n "$1" ]; then
    z $1
    fi

    nvim
}

if (( $+commands[tag] )); then
    tag() { command tag "$@"; source ${TAG_ALIAS_FILE:-/tmp/tag_aliases} 2>/dev/null }
    alias ag=tag
fi

# }}}

# Prompt {{{
# ==============================================================================

source $HOME/.antigen/bundles/jonmosco/kube-ps1/kube-ps1.sh

prompt_kube_ps1() { echo -n $(kube_ps1); }
get_cluster_short() { if [[ "$1" =~ ^arn:aws:eks ]]; then echo "$1" | rev | cut -d'/' -f 1 | rev; fi; }

KUBE_PS1_CLUSTER_FUNCTION=get_cluster_short
KUBE_PS1_SYMBOL_COLOR=white
KUBE_PS1_CTX_COLOR=red
KUBE_PS1_NS_COLOR=cyan
KUBE_PS1_BG_COLOR=null
KUBE_PS1_PREFIX=" "
KUBE_PS1_SEPARATOR=""
KUBE_PS1_SUFFIX=" "
KUBE_PS1_SYMBOL_USE_IMG=true
PROMPT='$(kube_ps1)'$PROMPT
PROMPT_EOL_MARK=''

# Make Python use UTF-8 encoding for output to stdin, stdout, and stderr.
export PYTHONIOENCODING='UTF-8'

# In order for gpg to find gpg-agent, gpg-agent must be running, and there must be an env
# variable pointing GPG to the gpg-agent socket. This little script, which must be sourced
# in your shell's init script (ie, .bash_profile, .zshrc, whatever), will either start
# gpg-agent or set up the GPG_AGENT_INFO variable if it's already running.
if [ -f ~/.gnupg/.gpg-agent-info ] && [ -n "$(pgrep gpg-agent)" ]; then
    source ~/.gnupg/.gpg-agent-info
    export GPG_AGENT_INFO
fi

export GPG_TTY=$(tty) # https://stackoverflow.com/questions/41052538/git-error-gpg-failed-to-sign-data/41054093

[ -f ~/.zsh_envs ] && source ~/.zsh_envs
[ -f ~/.zsh_aliases ] && source ~/.zsh_aliases
[ -f ~/.zsh_functions ] && source ~/.zsh_functions
[ -f ~/.p10k.zsh ] && source ~/.p10k.zsh ||  echo "⚠️  Failed to load powerlevel10k ⚠️"

# # Gradle Setup
export GRADLE_HOME=$(which gradle)

# Flutterfire setup
export PATH="$PATH":"$HOME/.pub-cache/bin"

# Docker through lima-vm
export DOCKER_HOST=unix://$HOME/.lima/docker/sock/docker.sock

# Load pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Python Poetry
export PATH="/Users/anderskirkeby/.local/bin:$PATH"

fpath+=~/.zfunc
autoload -Uz compinit && compinit

# Load nvm 

export NVM_DIR="$HOME/.nvm"
[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
[ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion

#THIS MUST BE AT THE END OF THE FILE FOR SDKMAN TO WORK!!!
export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$SDKMAN_DIR/bin/sdkman-init.sh" ]] && source "$SDKMAN_DIR/bin/sdkman-init.sh" || echo "⚠️  Failed to load sdkman ⚠️"
