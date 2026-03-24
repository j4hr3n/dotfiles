#!/usr/bin/env bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOTFILES_DIR="$HOME/dev/dotfiles"
STASHED=false

echo "=========================================="
echo "  Dotfiles Update"
echo "=========================================="
echo ""

cd "$DOTFILES_DIR"

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}You have uncommitted changes:${NC}"
    git status --short
    echo ""
    read -p "Stash changes and continue? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git stash push -m "dotfiles-update auto-stash $(date +%Y-%m-%d)"
        STASHED=true
    else
        echo "Aborting update."
        exit 1
    fi
fi

# Pull latest
echo -e "${YELLOW}Pulling latest changes...${NC}"
git pull --rebase origin main

# Re-run setup
echo -e "${YELLOW}Re-running setup...${NC}"
bash "$DOTFILES_DIR/setup-mac.sh"

# Pop stash if we stashed
if [ "$STASHED" = true ]; then
    echo -e "${YELLOW}Restoring stashed changes...${NC}"
    git stash pop
fi

echo ""
echo -e "${GREEN}Dotfiles updated successfully!${NC}"
echo "Restart your shell or run: source ~/.zshrc"
