# Global Instructions

## Commits & PRs
- Never add `Co-Authored-By` or any Claude/Anthropic attribution to commit messages
- Never mention Claude in PR descriptions, titles, or issue comments

## Memory & Persistence

- Do **not** write project-specific memory files (no `MEMORY.md`, no memory directories).
- If a pattern, convention, or learning needs to persist, propose a skill update instead.

## Permissions

- During feature implementation, work autonomously — don't ask for approval on file edits, writes, or tool calls. This includes writing to `.claude/` (plans, skills).
- Reading files outside the current working directory (e.g., `~/.claude/`, skill files) does not require approval.

## Tool preferences

- Use `pnpm dlx` instead of `npx` for running package binaries (e.g., `pnpm dlx vitest`, `pnpm dlx @biomejs/biome check`).
- `pnpm`, `pnpm dlx`, `turbo`, `vitest`, `biome`, `git`, `gh`, and `az` commands should be treated as safe to run without manual approval.

## Branch and commit workflow

Unless the user explicitly says to commit to the current branch or to main:

- **Create a fresh branch** before making changes: `git checkout -b <branch-name>`.
- **Auto-generate descriptive branch names** from the task, using prefixes like `feat/`, `fix/`, `refactor/`, `docs/`, `chore/` (e.g., `feat/add-user-auth`, `fix/login-redirect`).
- **Commit at logical points** with meaningful messages that explain *why*, not just *what*.
- Don't squash all changes into a single commit when multiple logical steps are involved.
