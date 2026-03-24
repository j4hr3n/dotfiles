---
name: issue-dips
description: Create a GitHub issue with codebase context. Trigger when the user wants to file a GitHub issue, report a bug, request a feature, create a ticket, log a task, or open an issue. Covers prompts like "file an issue for ...", "create a ticket", "open a bug report", "I want to track this as an issue", "make an issue", or "/issue".
---

# Create GitHub Issue

You are filing a well-researched GitHub issue. Good issues save future-you hours of context-switching — invest a few minutes now to explore the codebase and write clearly.

## Step 1: Explore the codebase

Parse the description from `$ARGUMENTS`. Before writing anything, search the codebase for files, patterns, and prior art related to the issue. This context makes the difference between a vague ticket and one someone can actually pick up and work on.

## Step 2: Detect the repository

Determine which GitHub repo to target:

```bash
gh repo view --json nameWithOwner -q .nameWithOwner
```

If this fails or the project isn't a GitHub repo, ask the user which repo to use.

## Step 3: Draft the issue

Write a focused GitHub issue:

```markdown
## Context
<!-- Why this matters — what prompted it, what pain it causes -->

## Description
<!-- What needs to happen, stated clearly enough that someone unfamiliar could start working -->

## Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical notes
<!-- Relevant files, patterns, constraints discovered during exploration. Skip this section if there's nothing useful to add. -->
```

Keep it concise. Every sentence should either clarify scope or reduce ambiguity.

## Step 4: Select labels

Pick labels that exist in the repo. When unsure what's available:

```bash
gh label list
```

Common choices: `enhancement`, `bug`, `documentation`, `refactor`.

## Step 5: Present for confirmation

Show the user the full issue (title, body, labels) and ask: **"Create this issue?"**

Do not create it until the user confirms. This is the user's name on the issue — they get final say.

## Step 6: Create the issue

Once approved:

```bash
gh issue create \
  --title "<title>" \
  --body "<body>" \
  --label "<label1>,<label2>"
```

Report back with the issue number and URL.

If the repo uses a GitHub project board, offer to add the issue:

```bash
gh project item-add <project-number> --owner <org> --url <issue-url>
```

## Error handling

If `gh` commands fail, the most common causes are:
- Not authenticated — `gh auth status` to check, `gh auth login` to fix
- Network restrictions — sandbox may need `github.com` allowed
- Wrong repo context — the command ran from a directory without a git remote
