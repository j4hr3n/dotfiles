#!/bin/bash
# PreToolCall hook for Claude Code
# Prevents commits to main/master and force pushes

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

[ -z "$command" ] && exit 0

# Block commits directly to main/master
if echo "$command" | grep -qE '\bgit\s+commit\b'; then
  # Resolve the directory the commit actually runs in: prefer the last `cd <dir>` in
  # the command (chained with && or ;), or `git -C <dir>`, otherwise use $PWD.
  target_dir=""
  cd_target=$(echo "$command" | grep -oE '(^|[;&]|&&)[[:space:]]*cd[[:space:]]+[^[:space:];&|]+' | tail -1 | sed -E 's/^[^c]*cd[[:space:]]+//')
  git_c_target=$(echo "$command" | grep -oE '\bgit[[:space:]]+-C[[:space:]]+[^[:space:]]+' | tail -1 | awk '{print $NF}')
  if [ -n "$git_c_target" ]; then
    target_dir="$git_c_target"
  elif [ -n "$cd_target" ]; then
    target_dir="$cd_target"
  fi
  # Expand ~ if present
  target_dir="${target_dir/#\~/$HOME}"
  if [ -n "$target_dir" ] && [ -d "$target_dir" ]; then
    branch=$(git -C "$target_dir" rev-parse --abbrev-ref HEAD 2>/dev/null)
  else
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  fi
  if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
    echo "Blocked: committing directly to $branch. Create a feature branch first." >&2
    exit 2
  fi
fi

# Block force pushes
if echo "$command" | grep -qE '\bgit\s+push\b.*(-f|--force)\b'; then
  echo "Blocked: force push requires explicit user approval." >&2
  exit 2
fi

# Block git reset --hard
if echo "$command" | grep -qE '\bgit\s+reset\b.*--hard\b'; then
  echo "Blocked: git reset --hard discards uncommitted work. Use git stash or confirm with user." >&2
  exit 2
fi

# Block git checkout . / git checkout -- . (discard all changes)
if echo "$command" | grep -qE '\bgit\s+checkout\s+(--\s+)?\.'; then
  echo "Blocked: git checkout . discards all uncommitted changes. Confirm with user first." >&2
  exit 2
fi

# Block git clean -f (delete untracked files)
if echo "$command" | grep -qE '\bgit\s+clean\b.*-[a-zA-Z]*f'; then
  echo "Blocked: git clean -f permanently deletes untracked files. Confirm with user first." >&2
  exit 2
fi

# Block git stash drop/clear (lose stashed work)
if echo "$command" | grep -qE '\bgit\s+stash\s+(drop|clear)\b'; then
  echo "Blocked: git stash drop/clear permanently discards stashed work. Confirm with user first." >&2
  exit 2
fi

exit 0
