# Global Instructions

## Commits & PRs
- Never add `Co-Authored-By` or any Claude/Anthropic attribution to commit messages
- Never mention Claude in PR descriptions, titles, or issue comments

## Learnings workflow

After completing a non-trivial task, write key learnings to the project memory file:

- **Path**: `~/.claude/projects/<project>/memory/MEMORY.md` (where `<project>` matches the project identifier Claude Code uses for the current working directory).
- Create the file and any parent directories if they don't exist.
- Each entry should have a date header (`## YYYY-MM-DD`) and concise bullet points.
- Record things like: build quirks, architecture patterns, debugging insights, gotchas, important commands, non-obvious conventions.
- Keep entries actionable and brief — future you should be able to scan them quickly.
- Don't duplicate entries that already exist in the file.

## Permissions

- During feature implementation, work autonomously — don't ask for approval on file edits, writes, or tool calls. This includes writing to `.claude/` (plans, memory).
- Reading files outside the current working directory (e.g., `~/.claude/`, skill files, memory files) does not require approval.

## Tool preferences

- Use `pnpm dlx` instead of `npx` for running package binaries (e.g., `pnpm dlx vitest`, `pnpm dlx @biomejs/biome check`).
- `pnpm`, `pnpm dlx`, `turbo`, `vitest`, `biome`, `git`, `gh`, and `az` commands should be treated as safe to run without manual approval.

## Branch and commit workflow

Unless the user explicitly says to commit to the current branch or to main:

- **Create a fresh branch** before making changes: `git checkout -b <branch-name>`.
- **Auto-generate descriptive branch names** from the task, using prefixes like `feat/`, `fix/`, `refactor/`, `docs/`, `chore/` (e.g., `feat/add-user-auth`, `fix/login-redirect`).
- **Commit at logical points** with meaningful messages that explain *why*, not just *what*.
- Don't squash all changes into a single commit when multiple logical steps are involved.
