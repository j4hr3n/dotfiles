---
name: notion-ticket
description: End-to-end workflow for working a Notion ticket in the health repo, from exploration and planning through draft PR and team announcement. Use whenever the user pastes a Notion ticket or Notion URL, references a ticket ID like CAT-1234, or says things like "new ticket", "let's take this one", or "here's the next task" — even if they don't mention the workflow explicitly.
---

# Notion Ticket Workflow

Work one Notion ticket end to end. The workflow has hard gates where the user decides — respect them even when the next step seems obvious.

## Phase 1: Understand and plan

1. Fetch the ticket with the Notion MCP (`notion-fetch`). Read linked pages/context it references.
2. Update the ticket in Notion:
   - Assign it to the user (christoffer.jahren@aidn.no — look up the user ID via `notion-get-users` if needed) unless already assigned.
   - Set status to the database's in-progress value. Read the data source schema first; property names and status options vary per database, so never guess them.
3. Explore the codebase (start from CONTEXT-MAP.md). Trace the real flow the ticket touches before proposing anything.
4. Keep the user posted along the way about ambiguities, surprises, or mismatches between the ticket and the code. The goal of this phase is a shared understanding, not just a plan.
5. If the change is too big for one reviewable PR, say so and propose a split into subtasks. Only create Notion subtasks after the user explicitly agrees — never unilaterally.
6. Present the plan and **stop**. Do not implement until the user gives the go-ahead.

## Phase 2: Implement (only after go-ahead)

- Follow doc/git-guidelines.md: branch `j4hr3n/<branch-name>`, one logical change per commit, every commit green.
- Verify before pushing per AGENTS.md, and say which checks were not run.
- No Claude/Anthropic attribution in commits.

## Phase 3: Draft PR and monitor

1. Push the branch and open a **draft** PR: `gh pr create --draft`. Reference the ticket in the description. No Claude mentions in title or body.
2. Start a background monitor for PR checks, e.g. `gh pr checks <number> --watch` with `run_in_background`, and report the outcome (fix failures, re-monitor after pushing fixes).

## Phase 4: Ready for review and announce

- The user marks the PR ready for review **manually**. Never do it, and never assume it happened.
- Only when the user says the PR is ready: post an announcement in #team-case-handling-tech (channel C057BA1B4Q4, aidn-no Slack workspace) via the Slack MCP. Keep it short and blunt in the user's voice: PR link plus a one-line summary. No em-dashes.
