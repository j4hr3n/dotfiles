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
    export PATH="/opt/homebrew/sbin:$PATH"
    eval $(/opt/homebrew/bin/brew shellenv)
fi

eval "$(fnm env --use-on-cd --shell zsh)"

. "$HOME/.local/bin/env"

# bun completions
[ -s "/Users/christofferjahren/.bun/_bun" ] && source "/Users/christofferjahren/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
