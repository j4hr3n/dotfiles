#!/usr/bin/env bash
# Imperative bootstrap steps that don't fit mise's declarative sections.
# Runs on every `mise bootstrap` via [tasks.bootstrap] in mise.toml — every
# step is idempotent. Mirrors the corresponding parts of setup-mac.sh.
set -euo pipefail

# --- Xcode Command Line Tools (provides git, needed by the repos phase) ---
if ! xcode-select --print-path &>/dev/null; then
    echo "→ Xcode Command Line Tools not found. Installing (approve the GUI dialog)..."
    xcode-select --install
    until xcode-select --print-path &>/dev/null; do
        sleep 5
    done
    echo "✓ Xcode Command Line Tools installed"
    if [ -d "/Applications/Xcode.app/Contents/Developer" ]; then
        sudo xcode-select -switch /Applications/Xcode.app/Contents/Developer
        echo "✓ Configured xcode-select developer directory"
    fi
    echo "→ Accept the Xcode license if prompted..."
    sudo xcodebuild -license accept 2>/dev/null || sudo xcodebuild -license
else
    echo "✓ Xcode Command Line Tools already installed"
fi

# --- Git identity ---
if ! git config --global user.name &>/dev/null; then
    read -r -p "Enter your Git name: " GIT_NAME
    git config --global user.name "$GIT_NAME"
    echo "✓ Git user.name configured"
else
    echo "✓ Git user.name already configured: $(git config --global user.name)"
fi

if ! git config --global user.email &>/dev/null; then
    read -r -p "Enter your Git email: " GIT_EMAIL
    git config --global user.email "$GIT_EMAIL"
    echo "✓ Git user.email configured"
else
    echo "✓ Git user.email already configured: $(git config --global user.email)"
fi

# --- oh-my-zsh ---
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "→ Installing oh-my-zsh..."
    KEEP_ZSHRC=yes RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
    echo "✓ oh-my-zsh installed"
else
    echo "✓ oh-my-zsh already installed"
fi

# --- Claude Code (native installer; the cask breaks auto-updates) ---
export PATH="$HOME/.local/bin:$PATH"
if ! command -v claude &>/dev/null; then
    echo "→ Installing Claude Code via native installer..."
    curl -fsSL https://claude.ai/install.sh | bash
    echo "✓ Claude Code installed"
else
    echo "✓ Claude Code already installed: $(claude --version 2>/dev/null || echo present)"
fi

# Claude Code plugins (installed_plugins.json has machine-local paths, so
# plugins are installed via the CLI rather than synced as config)
if command -v claude &>/dev/null; then
    for plugin in frontend-design figma claude-code-setup skill-creator posthog github typescript-lsp; do
        claude plugins install "${plugin}@claude-plugins-official" 2>/dev/null || true
    done
    echo "✓ Claude Code plugins installed"
fi

# The bootstrap project's mise.toml is not loaded from ordinary working
# directories. Keep these global defaults in sync with its [tools] section.
mise use --global node@lts go@latest uv@latest bun@latest pnpm@latest

echo "✓ bootstrap task done"
