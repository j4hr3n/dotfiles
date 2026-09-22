# $HOME sweet $HOME

## Setup

On a new Apple Silicon Mac, `mise.toml` declares the machine setup. Install
Xcode Command Line Tools first (the repository clone needs `git`), then install
mise and bootstrap the repository over HTTPS:

```bash
if ! xcode-select --print-path >/dev/null 2>&1; then
  xcode-select --install
  until xcode-select --print-path >/dev/null 2>&1; do sleep 5; done
fi
curl https://mise.run | sh
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$HOME/.local/bin:$PATH"
mkdir -p "$HOME/dev"
mise bootstrap --from https://github.com/j4hr3n/dotfiles.git --from-dir "$HOME/dev/dotfiles"
```

`mise bootstrap` clones this repo, installs the tools in `[tools]`
(node, go, uv, bun, pnpm — replacing fnm/asdf), pours the Homebrew packages
and casks from `[bootstrap.packages]` without installing Homebrew, links the
shell/ghostty/Claude Code configs from `[dotfiles]`, and runs
`scripts/bootstrap-task.sh` for the imperative steps (Xcode CLT, Git identity,
oh-my-zsh, Claude Code). The task also records the `[tools]` versions in mise's
global config so they remain active outside the bootstrap checkout.

Useful commands:

```bash
mise bootstrap --dry-run    # preview the plan
mise bootstrap status       # drift report
mise bootstrap --yes        # unattended re-apply
mise dot diff               # config file drift
```

Notes:

- Intel Macs: mise's brew package manager is Apple Silicon only. Keep using
  `setup-mac.sh` there.
- Existing dotfiles that conflict with the symlink targets need to be moved or
  explicitly replaced before the first bootstrap; mise protects existing files
  by default.
- `setup-mac.sh` remains available as the Intel Mac fallback. It installs
  Homebrew and uses `Brewfile`; the mise flow does not create `~/Brewfile`.

For an already-cloned checkout, run `mise bootstrap` from the repository root.

## What Gets Installed

- **Shell**: zsh with oh-my-zsh, custom aliases, tmux
- **Terminal**: Ghostty configuration
- **Development Tools**: Git, GitHub CLI, Node.js, pnpm, Bun, Go, uv, Docker (via colima), Google Cloud CLI
- **Security Tools**: gitleaks, trufflehog, grype, trivy, agent-browser
- **AI Tools**: Claude Code (with synced config, skills, and hooks), opencode, Codex, rtk
- **Applications**: Arc, Cursor, VS Code, Figma, Notion, Raycast, Slack, Spotify, 1Password, and more
- **Utilities**: fzf, jq, yq, fx, and other productivity tools

`mise.toml` is the package and tool list for the Apple Silicon bootstrap;
`Brewfile` remains the package list for the Homebrew-based fallback.
