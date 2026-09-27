# Path to oh-my-zsh installation
export ZSH=$HOME/.oh-my-zsh

# Path to your dotfiles.
export DOTFILES=$HOME/dev/dotfiles

# Theme
ZSH_THEME="robbyrussell"

# Aliases
[ -f ~/.zsh_aliases ] && source ~/.zsh_aliases

# zsh completions
fpath=(/opt/homebrew/share/zsh-completions $fpath)

# Enable history
HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
setopt appendhistory

# set up zsh plugins
plugins=(git)

# start oh-my-zsh
source $ZSH/oh-my-zsh.sh

# zsh-syntax-highlighting (must be sourced after oh-my-zsh)
[ -f /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ] && \
    source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# zsh-autosuggestions
[ -f /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh ] && \
    source /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh

printf '
         _                  _     
        /\ \               /\ \   
       /  \ \              \ \ \  
      / /\ \ \             /\ \_\ 
     / / /\ \ \           / /\/_/ 
    / / /  \ \_\ _       / / /    
   / / /    \/_//\ \    / / /     
  / / /         \ \_\  / / /      
 / / /________  / / /_/ / /       
/ / /_________\/ / /__\/ /        
\/____________/\/_______/         
                                  
' | lolcat
printf 'Greetings Christoffer, welcome back!' | lolcat
echo

# Load brew on macOS
if [[ "$OSTYPE" =~ ^darwin ]]; then
    if [[ -x /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
    fi
fi

# mise and native installers place executables here.
export PATH="$HOME/.local/bin:$PATH"

# Dev tools are managed by mise when present; falls back to fnm otherwise.
if command -v mise &>/dev/null; then
    eval "$(mise activate zsh)"
else
    eval "$(fnm env --use-on-cd --shell zsh)"
fi

[ -f "$HOME/.local/bin/env" ] && . "$HOME/.local/bin/env"

# fzf keybindings and completion
command -v fzf &>/dev/null && source <(fzf --zsh)

# bun completions
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# Add ~/bin to PATH (claude-mesh, cmesh)
export PATH="$HOME/bin:$PATH"

# Add Go bin to PATH (tea, other go-installed CLIs)
export PATH="$HOME/go/bin:$PATH"
export PATH="$PATH:$HOME/.jfrog/bin"
# System .NET SDK installation. Keep user-local global tools available.
export DOTNET_ROOT="/usr/local/share/dotnet"
export PATH="$DOTNET_ROOT:$HOME/.dotnet/tools:$PATH"

# Machine-local secrets stay outside the repository.
[[ -f "$HOME/.zshrc.local" ]] && source "$HOME/.zshrc.local"
if [[ -n ${GH_PACKAGES_TOKEN:-} ]]; then
    export NODE_AUTH_TOKEN="$GH_PACKAGES_TOKEN"
    export NuGetPackageSourceCredentials_github_aidnas="Username=j4hr3n;Password=${GH_PACKAGES_TOKEN}"
fi

# Trust the locally exported Zscaler CA when present.
if [[ -f "$HOME/.config/devbox/zscaler-root-ca.pem" ]]; then
    export NODE_EXTRA_CA_CERTS="$HOME/.config/devbox/zscaler-root-ca.pem"
fi

# Vite+ bin (https://viteplus.dev)
[[ -f "$HOME/.vite-plus/env" ]] && source "$HOME/.vite-plus/env"
