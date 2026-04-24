#!/bin/bash
# SessionStart hook for Claude Code
# Shows workspace context at the start of each session

# Only run if inside a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  exit 0
fi

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# Warn if on main/master
if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  echo "WARNING: On $branch branch — create a feature branch before committing." >&2
fi

# Check for in-progress plans
plan_count=$(find .claude/plans/ -name '*.md' -newer .git/HEAD 2>/dev/null | wc -l | tr -d ' ')
if [ "$plan_count" -gt 0 ]; then
  echo "Note: $plan_count recent plan file(s) in .claude/plans/" >&2
fi

exit 0
