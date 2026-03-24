#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0; WARN=0; FAIL=0

echo "=========================================="
echo "  Dotfiles Doctor"
echo "=========================================="
echo ""

# --- Symlink checks ---
echo "Checking symlinks..."

SYMLINKS=(
    "$HOME/.zshrc|shell/.zshrc"
    "$HOME/.zsh_aliases|shell/.zsh_aliases"
    "$HOME/.vimrc|shell/.vimrc"
    "$HOME/Brewfile|Brewfile"
    "$HOME/Library/Application Support/com.mitchellh.ghostty/config|configs/ghostty/config"
    "$HOME/.claude/CLAUDE.md|configs/claude-code/CLAUDE.md"
    "$HOME/.claude/settings.json|configs/claude-code/settings.json"
    "$HOME/.claude/skills|configs/claude-code/skills"
    "$HOME/.claude/SKILL.md|configs/claude-code/SKILL.md"
    "$HOME/.claude/statusline-command.sh|configs/claude-code/statusline-command.sh"
)

for entry in "${SYMLINKS[@]}"; do
    target="${entry%%|*}"
    expected="$DOTFILES_DIR/${entry##*|}"

    if [ -L "$target" ]; then
        actual=$(readlink "$target")
        if [ "$actual" = "$expected" ]; then
            echo -e "  ${GREEN}OK${NC}     $target"
            ((PASS++))
        else
            echo -e "  ${YELLOW}DRIFT${NC}  $target -> $actual (expected $expected)"
            ((WARN++))
        fi
    elif [ -e "$target" ]; then
        echo -e "  ${RED}FILE${NC}   $target exists but is not a symlink"
        ((FAIL++))
    else
        echo -e "  ${RED}MISS${NC}   $target does not exist"
        ((FAIL++))
    fi
done

# --- Brew bundle check ---
echo ""
echo "Checking Homebrew packages..."

if brew bundle check --file="$DOTFILES_DIR/Brewfile" &>/dev/null; then
    echo -e "  ${GREEN}OK${NC}     All Brewfile entries installed"
    ((PASS++))
else
    echo -e "  ${YELLOW}DRIFT${NC}  Missing packages:"
    brew bundle check --file="$DOTFILES_DIR/Brewfile" 2>&1 | sed 's/^/         /'
    ((WARN++))
fi

extra=$(brew bundle cleanup --file="$DOTFILES_DIR/Brewfile" 2>/dev/null)
if [ -n "$extra" ]; then
    echo -e "  ${YELLOW}EXTRA${NC}  Packages not in Brewfile:"
    echo "$extra" | sed 's/^/         /'
    ((WARN++))
else
    echo -e "  ${GREEN}OK${NC}     No extra packages outside Brewfile"
    ((PASS++))
fi

# --- Summary ---
echo ""
echo "=========================================="
echo -e "  ${GREEN}$PASS passed${NC}  ${YELLOW}$WARN warnings${NC}  ${RED}$FAIL errors${NC}"
echo "=========================================="

[ "$FAIL" -gt 0 ] && exit 1
[ "$WARN" -gt 0 ] && exit 2
exit 0
