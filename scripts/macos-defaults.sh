#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "  macOS Defaults"
echo "=========================================="
echo ""

# Dock
echo -e "${YELLOW}Configuring Dock...${NC}"
defaults write com.apple.dock autohide -bool true
defaults write com.apple.dock tilesize -int 48
defaults write com.apple.dock mineffect -string "scale"
defaults write com.apple.dock show-recents -bool false

# Finder
echo -e "${YELLOW}Configuring Finder...${NC}"
defaults write NSGlobalDomain AppleShowAllExtensions -bool true
defaults write com.apple.finder AppleShowAllFiles -bool true
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"
defaults write com.apple.finder ShowPathbar -bool true

# Keyboard
echo -e "${YELLOW}Configuring Keyboard...${NC}"
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15

# Screenshots
echo -e "${YELLOW}Configuring Screenshots...${NC}"
mkdir -p "$HOME/screengrabs"
defaults write com.apple.screencapture location -string "$HOME/screengrabs"

# Trackpad
echo -e "${YELLOW}Configuring Trackpad...${NC}"
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# Apply changes
killall Dock 2>/dev/null || true
killall Finder 2>/dev/null || true
killall SystemUIServer 2>/dev/null || true

echo ""
echo -e "${GREEN}macOS defaults applied.${NC}"
echo -e "${YELLOW}Some changes may require a logout to take effect.${NC}"
