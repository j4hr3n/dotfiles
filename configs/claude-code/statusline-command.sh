#!/bin/bash

# Read JSON input from Claude Code
input=$(cat)

# Extract current directory from JSON
cwd=$(echo "$input" | jq -r '.workspace.current_dir')

# Get basename of current directory
dir_name=$(basename "$cwd")

# Extract model information
model_name=$(echo "$input" | jq -r '.model.display_name // .model.id')

# Extract output style (mode/plan)
output_style=$(echo "$input" | jq -r '.output_style.name // empty')

# Format model info with output style
if [ -n "$output_style" ]; then
  model_info=$(printf "\033[0;35m%s\033[0m \033[0;33m[%s]\033[0m " "$model_name" "$output_style")
else
  model_info=$(printf "\033[0;35m%s\033[0m " "$model_name")
fi

# Check if we're in a git repository and get branch info
if git -C "$cwd" rev-parse --git-dir > /dev/null 2>&1; then
  branch=$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null)

  # Check if there are uncommitted changes (skip locks for performance)
  if ! git -C "$cwd" diff --quiet --no-ext-diff 2>/dev/null || \
     ! git -C "$cwd" diff --cached --quiet --no-ext-diff 2>/dev/null; then
    # Dirty: show branch with ✗
    git_info=$(printf "\033[1;34mgit:(\033[0;31m%s\033[1;34m) \033[0;33m✗\033[0m " "$branch")
  else
    # Clean: just show branch
    git_info=$(printf "\033[1;34mgit:(\033[0;31m%s\033[1;34m)\033[0m " "$branch")
  fi
else
  git_info=""
fi

# Print the prompt (model + mode + green arrow + cyan directory + git info)
printf "%s\033[1;32m➜\033[0m  \033[0;36m%s\033[0m %s" "$model_info" "$dir_name" "$git_info"
