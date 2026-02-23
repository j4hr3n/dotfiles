#!/usr/bin/env bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to print results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        return $1
    fi
}

# Helper function to print info
print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Function to create symlink with relink support
create_symlink() {
    local target="$1"
    local source="$2"
    local source_full="$DOTFILES_DIR/$source"
    
    # Expand ~ in target path
    local target_expanded="${target/#\~/$HOME}"
    
    # Check if source exists
    if [ ! -e "$source_full" ]; then
        echo -e "${RED}✗${NC} Source not found: $source_full"
        return 1
    fi
    
    # Create parent directory if it doesn't exist
    local parent_dir=$(dirname "$target_expanded")
    if [ ! -d "$parent_dir" ]; then
        mkdir -p "$parent_dir"
    fi
    
    # Remove existing file/link if it exists and is different
    if [ -e "$target_expanded" ] || [ -L "$target_expanded" ]; then
        if [ -L "$target_expanded" ]; then
            local current_target=$(readlink "$target_expanded")
            if [ "$current_target" = "$source_full" ]; then
                print_result 0 "Symlink already exists: $target"
                return 0
            fi
        fi
        rm -rf "$target_expanded"
    fi
    
    # Create symlink
    ln -s "$source_full" "$target_expanded"
    if [ $? -eq 0 ]; then
        print_result 0 "Created symlink: $target → $source"
        return 0
    else
        print_result 1 "Failed to create symlink: $target"
        return 1
    fi
}

# Function to clean broken symlinks (optional)
clean_broken_symlinks() {
    print_info "Checking for broken symlinks in home directory..."
    local broken_count=0
    while IFS= read -r -d '' link; do
        if [ ! -e "$link" ]; then
            rm "$link"
            echo -e "${YELLOW}  Removed broken symlink: $link${NC}"
            ((broken_count++))
        fi
    done < <(find "$HOME" -maxdepth 1 -type l -print0 2>/dev/null)
    
    if [ $broken_count -eq 0 ]; then
        print_result 0 "No broken symlinks found"
    else
        print_result 0 "Cleaned $broken_count broken symlink(s)"
    fi
}

echo "=========================================="
echo "  Mac Dotfiles Setup"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This script is for macOS only${NC}"
    exit 1
fi

# Detect Apple Silicon
IS_APPLE_SILICON=false
if sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q 'Apple M'; then
    IS_APPLE_SILICON=true
fi

# Step 1: Install Xcode Command Line Tools
print_info "Checking for Xcode Command Line Tools..."
if ! xcode-select --print-path &>/dev/null; then
    print_info "Xcode Command Line Tools not found. Installing..."
    xcode-select --install
    
    # Wait until the XCode Command Line Tools are installed
    until xcode-select --print-path &>/dev/null; do
        sleep 5
    done
    
    print_result $? "Xcode Command Line Tools installed"
    
    # Point xcode-select to the appropriate directory
    if [ -d "/Applications/Xcode.app/Contents/Developer" ]; then
        sudo xcode-select -switch /Applications/Xcode.app/Contents/Developer
        print_result $? "Configured xcode-select developer directory"
    fi
    
    # Prompt user to agree to the terms of the Xcode license
    print_info "You may need to agree to the Xcode license..."
    sudo xcodebuild -license accept 2>/dev/null || sudo xcodebuild -license
    print_result $? "Xcode license accepted"
else
    print_result 0 "Xcode Command Line Tools already installed"
fi

# Step 2: Install Homebrew
print_info "Checking for Homebrew..."
if ! command -v brew &>/dev/null; then
    print_info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Configure Homebrew PATH
    if [ "$IS_APPLE_SILICON" = true ]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$HOME/.zprofile"
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    print_result $? "Homebrew installed and configured"
else
    print_result 0 "Homebrew already installed"
    # Ensure brew is in PATH
    if [ "$IS_APPLE_SILICON" = true ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
    else
        eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null || true
    fi
fi

# Step 3: Clone dotfiles repository
print_info "Setting up dotfiles repository..."

# Check if we're already in a dotfiles repository
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/Brewfile" ] && [ -f "$SCRIPT_DIR/shell/.zshrc" ]; then
    DOTFILES_DIR="$SCRIPT_DIR"
    print_result 0 "Running from existing dotfiles repository: $DOTFILES_DIR"
else
    DOTFILES_DIR="$HOME/dotfiles"
    if [ ! -d "$DOTFILES_DIR" ]; then
        print_info "Cloning dotfiles repository..."
        git clone https://github.com/j4hr3n/dotfiles.git "$DOTFILES_DIR"
        print_result $? "Dotfiles repository cloned"
    else
        print_result 0 "Dotfiles repository already exists"
    fi
fi

# Change to dotfiles directory
cd "$DOTFILES_DIR"

# Step 4: Configure Git
print_info "Configuring Git..."
if ! git config --global user.name &>/dev/null; then
    echo ""
    read -p "Enter your Git name: " GIT_NAME
    git config --global user.name "$GIT_NAME"
    print_result $? "Git user.name configured"
else
    print_result 0 "Git user.name already configured: $(git config --global user.name)"
fi

if ! git config --global user.email &>/dev/null; then
    echo ""
    read -p "Enter your Git email: " GIT_EMAIL
    git config --global user.email "$GIT_EMAIL"
    print_result $? "Git user.email configured"
else
    print_result 0 "Git user.email already configured: $(git config --global user.email)"
fi

# Step 5: Install oh-my-zsh
print_info "Checking for oh-my-zsh..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    print_info "Installing oh-my-zsh..."
    RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
    print_result $? "oh-my-zsh installed"
else
    print_result 0 "oh-my-zsh already installed"
fi

# Step 6: Create necessary directories
print_info "Creating necessary directories..."
mkdir -p ~/.gnupg
mkdir -p ~/Library/Application\ Support/com.mitchellh.ghostty
print_result 0 "Directories created"

# Step 7: Create symlinks and install packages
print_info "Setting up dotfiles..."

# Clean broken symlinks (optional, matches dotbot's clean behavior)
clean_broken_symlinks

# Create symlinks
print_info "Creating symlinks..."
create_symlink "~/.zshrc" "shell/.zshrc"
create_symlink "~/.zsh_aliases" "shell/.zsh_aliases"
create_symlink "~/.vimrc" "shell/.vimrc"
create_symlink "~/Brewfile" "Brewfile"
create_symlink "~/Library/Application Support/com.mitchellh.ghostty/config" "configs/ghostty/config"

# Claude Code
create_symlink "~/.claude/CLAUDE.md" "configs/claude-code/CLAUDE.md"
create_symlink "~/.claude/SKILL.md" "configs/claude-code/SKILL.md"
create_symlink "~/.claude/settings.json" "configs/claude-code/settings.json"
create_symlink "~/.claude/statusline-command.sh" "configs/claude-code/statusline-command.sh"
create_symlink "~/.claude/skills/solve/SKILL.md" "configs/claude-code/skills/solve/SKILL.md"
create_symlink "~/.claude/skills/issue/SKILL.md" "configs/claude-code/skills/issue/SKILL.md"
create_symlink "~/.claude/skills/review/SKILL.md" "configs/claude-code/skills/review/SKILL.md"
create_symlink "~/.claude/skills/retro/SKILL.md" "configs/claude-code/skills/retro/SKILL.md"

# Install Homebrew packages and casks
print_info "Installing Homebrew packages and casks..."
brew bundle install
print_result $? "Homebrew packages installed"

# Update Homebrew packages
print_info "Updating Homebrew packages..."
brew update && brew upgrade
print_result $? "Homebrew packages updated"

echo ""
echo "=========================================="
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "=========================================="
echo ""
print_info "Next steps:"
echo "  1. Restart your terminal or run: source ~/.zshrc"
echo "  2. Configure any additional applications as needed"
echo ""

