# /solve — Solve GitHub issues end-to-end

## Trigger

The user runs `/solve <issue-numbers>` (e.g., `/solve 42` or `/solve 42 43 44`).

## Inputs

- `$ARGUMENTS`: One or more GitHub issue numbers separated by spaces.

## Instructions

You are executing the `/solve` skill. Follow these phases strictly in order.

---

### Phase 1: Read issues

For each issue number in `$ARGUMENTS`:

```bash
gh issue view <number> --repo DIPSAS/agent-platform
```

Collect the title, body, labels, and any linked issues for every issue.

For GitHub issues, assign the current user:
```bash
gh issue edit <number> --repo DIPSAS/agent-platform --add-assignee @me
```

---

### Phase 2: Explore and classify

For each issue:

- **Determine target repo**:
  - Frontend/UI only → **Pilar**
  - Backend/agent logic only → **agent-platform**
  - Both (e.g., new API endpoint + UI that calls it) → **both**
- Use Explore agents (via the Task tool with `subagent_type=Explore`) to understand the relevant parts of the codebase. When classified as **both**, explore both repos.
- Identify key files, patterns, dependencies, and constraints.

---

### Phase 3: Design plan

For each issue, write a detailed implementation plan as a markdown file:

- Save to `.claude/plans/<slug>.md` in the project root (e.g., `issue-42-add-logout-button.md`).
- Create the `.claude/plans/` directory if it doesn't exist.

Each plan file should include:

```markdown
# Issue #<number>: <title>

## Goal
What this achieves (1-2 sentences).

## Changes
Each file to create/modify, with a description of what changes and why.

## Tests
What tests to write or modify.

## Verification
How to confirm the implementation works (test commands, manual steps).
```

**Data availability**: Before assuming data is unavailable for a UI component, trace the full data flow — check not just the immediate input type, but also what parent components pass down (e.g., message-level references, context providers, sibling tool outputs). Components often receive richer data than their direct input type suggests.

#### Multi-repo issues (classified as "both")

For issues targeting both repos, produce **three** plan files instead of one:

1. **`<slug>-contract.md`** — Shared API contract: endpoints, HTTP methods, request/response shapes, data DTOs, error codes, and assumptions. This is the sync point between repos.
2. **`<slug>-pilar.md`** — Frontend implementation plan. References the contract file for all API interactions.
3. **`<slug>-agent-platform.md`** — Backend implementation plan. References the contract file for all API shapes.

The contract must be approved first — present it for review before the repo-specific plans.

When the issue includes a Figma URL, extract not just visual styling but also **interaction patterns** — button placements, action row layouts, and component positioning relative to content.

**Present a concise summary of all plans in chat.** Highlight key decisions and open questions.

**Do NOT proceed to implementation until the user explicitly approves** (e.g., "go", "do it", "looks good", "approved").

---

### Phase 4: Execute

Once approved, implement each issue:

1. **Create a branch from main:**
   ```bash
   git checkout -b feat/issue-<number>-<short-slug> main
   ```
   Use prefixes: `feat/`, `fix/`, `refactor/`, `docs/` as appropriate.

2. **Implement the plan:** Make all changes described in the plan file.

3. **Write tests:** Follow the testing requirements from AGENTS.md — at minimum one happy path + one edge case.

4. **Commit with issue references:** Use meaningful commit messages that include:
   ```
   Refs DIPSAS/agent-platform#<number>
   ```
   Use `Refs` (not `Closes`) so the issue stays open until PR merge.

5. **Run verification:**
   ```bash
   turbo run test --filter=<affected-packages>
   pnpm biome check <changed-files>
   turbo run typecheck --filter=<affected-packages>
   ```
   Fix any failures before proceeding.

#### Multiple issues

When solving multiple issues, after collective plan approval:
- Use the **Task tool** to create parallel agents (`subagent_type=general-purpose`), one per issue.
- Each agent gets its own branch and works independently.
- If any individual issue targets both repos, use the agent team flow below for that issue's work items instead of a single subagent. Create one team that covers all multi-repo work items alongside the single-repo subagents.
- Wait for all agents and teammates to complete before proceeding to Phase 5.

#### Multi-repo issues (classified as "both")

For issues that span both repos, use an **agent team** instead of subagents:

1. **Confirm the shared contract** (`<slug>-contract.md`) is finalized and approved.

2. **Create the team** with `TeamCreate`:
   - Team name: `solve-issue-<N>` (e.g., `solve-issue-42`)

3. **Create tasks** with `TaskCreate` — one for each repo:
   - Pilar task: implement `<slug>-pilar.md`, branch `feat/issue-<N>-<slug>-frontend`
   - agent-platform task: implement `<slug>-agent-platform.md`, branch `feat/issue-<N>-<slug>-backend`
   - Include the full contract content and plan file path in each task description so teammates have all context at spawn time.

4. **Spawn two teammates** (via the Task tool with `subagent_type=general-purpose` and `team_name`):
   - **`pilar-dev`** — assigned the Pilar task, working directory set to the Pilar repo
   - **`agent-platform-dev`** — assigned the agent-platform task, working directory set to the agent-platform repo
   - Use `TaskUpdate` to assign each task to its respective teammate by name.

5. **Wait for both teammates** to complete their tasks. Teammates mark tasks completed via `TaskUpdate` and go idle automatically. Monitor via `TaskList`.

6. **Shut down teammates** with `SendMessage` (`type: "shutdown_request"`) once both tasks are completed.

7. **Clean up the team** with `TeamDelete` before proceeding to Phase 5.

---

### Phase 5: Report and hand off

After implementation is complete:

1. **Report to the user:**
   - Branch name(s)
   - Commit list
   - Test results summary
   - Any issues encountered

2. **Suggest running `/retro`** to review whether skills, commands, or config need updating based on this session.

**STOP HERE.** Do NOT push branches or create PRs automatically. The user will verify the implementation manually and decide when to create the PR.

---

### Phase 6: PR and project board (manual trigger only)

**Only execute this phase when the user explicitly asks** (e.g., "create the PR", "push it", "ship it").

For each solved issue:

1. **Push the branch:**
   ```bash
   git push -u origin <branch-name>
   ```

2. **Create a PR:**

   - **For Pilar (Azure DevOps):**
     ```bash
     az repos pr create --title "<title>" --description "<body>" \
       --source-branch <branch-name> --target-branch main \
       --repository Pilar \
       --org https://dev.azure.com/dips --project DIPS
     ```

   - **For agent-platform (GitHub):**
     ```bash
     gh pr create --repo DIPSAS/agent-platform \
       --title "<title>" --body "<body>"
     ```

   PR body format:
   ```markdown
   ## Summary
   - <bullet points of changes>

   Refs DIPSAS/agent-platform#<number>

   ## Test plan
   - [ ] Tests pass locally
   - [ ] <specific verification steps>
   ```

3. **Update project board status to "In Review":**

   First, get the project node ID via GraphQL (required for `item-edit`):
   ```bash
   gh api graphql -f query='{ organization(login: "DIPSAS") { projectV2(number: 5) { id } } }'
   ```

   Then look up field IDs dynamically:
   ```bash
   gh project field-list 5 --owner DIPSAS --format json
   ```
   Find the `Status` field ID and the `In Review` option ID from the output.

   Then get the item ID:
   ```bash
   gh project item-list 5 --owner DIPSAS --limit 200 --format json | jq '.items[] | select(.content.number == <issue-number>)'
   ```

   Finally, update the status:
   ```bash
   gh project item-edit --project-id <project-node-id> --id <item-id> --field-id <status-field-id> --single-select-option-id <in-review-option-id>
   ```

   If project board commands fail, report the failure but don't block the workflow — the PR is the critical deliverable.

4. **Cross-reference companion PRs (multi-repo issues only):**

   When an issue produced PRs in both repos, edit each PR description to append:
   ```
   Companion PR: <URL-of-the-other-PR>
   ```
   Use `gh pr edit` (GitHub) or `az repos pr update` (Azure DevOps) to add the cross-reference.

---

### Error handling

- If `gh` or `az` commands fail with authentication or network errors, inform the user they may need to:
  - Run `gh auth status` / `az account show` to check authentication
  - Adjust sandbox network settings via `/sandbox` to allow `github.com` and `dev.azure.com`
  - Run `gh auth login` or `pnpm azure-login` if not authenticated
- If tests fail, fix the failures before creating the PR. If a fix isn't obvious, report the failure and ask the user for guidance.
- If a branch already exists, append a short suffix (e.g., `-v2`) rather than force-deleting.
