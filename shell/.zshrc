# Path to oh-my-zsh installation
export ZSH=$HOME/.oh-my-zsh

# Path to your dotfiles.
export DOTFILES=$HOME/.dotfiles

# Theme
ZSH_THEME="robbyrussell"

# Aliases
[ -f ~/.zsh_aliases ] && source ~/.zsh_aliases

# zsh completions
fpath=(path/to/zsh-completions/src $fpath)

# Enable history
HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
setopt appendhistory

# set up zsh plugins
plugins=(git)

# start oh-my-zsh
source $ZSH/oh-my-zsh.sh

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

# set up fnm
eval "$(fnm env --use-on-cd)"

# Load brew on macOS
if [[ "$OSTYPE" =~ ^darwin ]]; then
    export PATH="/opt/homebrew/sbin:$PATH"
    eval $(/opt/homebrew/bin/brew shellenv)
fi
# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/christoffer.jahren@schibsted.com/Downloads/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/christoffer.jahren@schibsted.com/Downloads/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/christoffer.jahren@schibsted.com/Downloads/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/christoffer.jahren@schibsted.com/Downloads/google-cloud-sdk/completion.zsh.inc'; fi
