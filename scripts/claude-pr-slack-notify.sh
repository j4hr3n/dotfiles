#!/bin/bash
# Claude Code PostToolUse hook (Bash matcher).
# After a successful non-draft `gh pr create` in AidnAS/health, injects an
# instruction for the model to announce the PR in #team-case-handling-tech.
# A shell hook can't reach the claude.ai Slack connector directly, so the
# posting itself is delegated back to the model via additionalContext.

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')

# Match `gh pr create` only in command position (start of line or after ; & | (),
# optionally prefixed by env assignments or the rtk wrapper) so the phrase inside
# a commit message or echo string doesn't trigger a false positive.
printf '%s\n' "$cmd" | grep -qE '(^|[;&|(] *)([A-Za-z_]+=[^ ]* +)*(rtk +)?gh +pr +create' || exit 0

# Skip draft PRs (--draft or -d)
printf '%s' "$cmd" | grep -qE -- '(^| )--draft( |=|$)| -d( |$)' && exit 0

# Only announce PRs for the AidnAS/health repo
git remote get-url origin 2>/dev/null | grep -qi 'aidnas/health' || exit 0

jq -n '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: "A non-draft GitHub PR was just created. Post it to the private Slack channel #team-case-handling-tech (channel_id C057BA1B4Q4 — use this ID directly, no need to search) using the Slack slack_send_message MCP tool, without asking for confirmation. Message format (markdown):\n\n:pull_request: [PR title](PR_URL)\n\nBased on [this ticket](TICKET_URL)\n\nFill in the actual PR URL (from the command output) and PR title. TICKET_URL is the ticket the PR addresses (e.g. Notion task or GitHub issue) — take it from session context or the PR body. If there is no ticket, omit the Based on line."
  }
}'
