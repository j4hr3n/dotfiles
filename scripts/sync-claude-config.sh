#!/bin/bash
# Auto-syncs Claude Code config changes to dotfiles repo.
# Triggered by Claude Code's Stop hook after each session.

DOTFILES="$HOME/dev/dotfiles"

cd "$DOTFILES" || exit 1

if ! git diff --quiet configs/claude-code/; then
  git add configs/claude-code/
  git commit -m "auto: sync claude config [$(date +%Y-%m-%d)]"
  git push
fi
