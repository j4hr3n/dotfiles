# /issue — Create a GitHub issue with codebase context

## Trigger

The user runs `/issue <description>`.

## Inputs

- `$ARGUMENTS`: A concise description of the issue or feature request.

## Instructions

You are executing the `/issue` skill. Follow these steps strictly in order.

### Step 1: Understand and explore

- Parse the description from `$ARGUMENTS`.
- Use Explore agents (via the Task tool with `subagent_type=Explore`) to find relevant files, patterns, and context in the codebase that relate to the issue.


### Step 2: Draft the issue

Write a well-structured GitHub issue with these sections:

```markdown
## Context
<!-- Why this matters, what prompted it -->

## Description
<!-- What needs to happen, clearly stated -->

## Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical notes
<!-- Relevant files, patterns, constraints discovered during exploration -->
```

### Step 3: Select labels

Choose appropriate labels from the repository. Common labels include:
- `enhancement` — new feature or improvement
- `bug` — something isn't working
- `documentation` — docs changes
- `refactor` — code restructuring without behavior change

If unsure about available labels, run: `gh label list --repo DIPSAS/agent-platform`

### Step 4: Present for confirmation

Show the user:
1. The full issue title and body (formatted)
2. The selected labels
3. Ask: **"Create this issue? (yes/no)"**

**Do NOT create the issue until the user explicitly confirms.**

### Step 5: Create the issue and link to project board

Once approved:

1. **Create the issue:**
   ```bash
   gh issue create --repo DIPSAS/agent-platform \
     --title "<title>" \
     --body "<body>" \
     --label "<label1>,<label2>"
   ```

2. **Capture the issue URL** from the output.

3. **Add to the project board:**
   ```bash
   gh project item-add 5 --owner DIPSAS --url <issue-url>
   ```

4. **Report back** with the issue number, URL, and confirmation it was added to the project board.

### Error handling

- If `gh` commands fail with authentication or network errors, inform the user they may need to:
  - Run `gh auth status` to check authentication
  - Adjust sandbox network settings via `/sandbox` to allow `github.com`
  - Run `gh auth login` if not authenticated
