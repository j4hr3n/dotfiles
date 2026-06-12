# $HOME sweet $HOME

## Setup

To install `dotfiles` on a new Mac, run the setup script. It will automatically:

1. Install Xcode Command Line Tools
2. Install Homebrew (if not present)
3. Clone this repository (if not already cloned)
4. Configure Git (prompts for name/email)
5. Install oh-my-zsh
6. Create symlinks for all configuration files
7. Install all Homebrew packages and casks

### Quick Start

Run the setup script directly from the repository:

```bash
# If you've already cloned the repo
cd ~/dev/dotfiles
./setup-mac.sh

# Or download and run in one command
curl -Ls https://raw.githubusercontent.com/j4hr3n/dotfiles/main/setup-mac.sh | bash
```

The script will guide you through the setup process and prompt for any required information (like Git name and email).

### Manual Setup

If you prefer to set up manually:

1. Clone the repository:

   ```bash
   git clone https://github.com/j4hr3n/dotfiles.git ~/dev/dotfiles
   cd ~/dev/dotfiles
   ```

2. Run the setup script:
   ```bash
   ./setup-mac.sh
   ```

## What Gets Installed

- **Shell**: zsh with oh-my-zsh, custom aliases, tmux
- **Terminal**: Ghostty configuration
- **Development Tools**: Git, GitHub CLI, Node.js (via fnm), pnpm, Bun, Go, uv, Docker (via colima), Azure/Google Cloud CLIs
- **Security Tools**: gitleaks, trufflehog, grype, trivy, agent-browser
- **AI Tools**: Claude Code (with synced config, skills, and hooks), opencode, Codex, rtk
- **Applications**: Arc, Cursor, VS Code, Figma, Notion, Raycast, Slack, Spotify, 1Password, and more
- **Utilities**: fzf, jq, yq, fx, and other productivity tools

See `Brewfile` for the complete list of packages and applications.
