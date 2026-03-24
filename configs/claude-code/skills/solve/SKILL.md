# /solve — Solve GitHub issues end-to-end

## Trigger

The user runs `/solve <issue-numbers>` (e.g., `/solve 42` or `/solve 42 43 44`).
Also triggered by phrases like "solve issue 42", "work on #42", "implement issue 42", "fix #42 and #43".

## Inputs

- `$ARGUMENTS`: One or more GitHub issue numbers separated by spaces.

## Instructions

You are executing the `/solve` skill. Follow these phases in order. Each phase gates the next — don't skip ahead.

---

### Phase 1: Read issues

For each issue number in `$ARGUMENTS`:

```bash
gh issue view <number> --repo DIPSAS/agent-platform
```

Collect the title, body, labels, and any linked issues. Assign yourself:
```bash
gh issue edit <number> --repo DIPSAS/agent-platform --add-assignee @me
```

---

### Phase 2: Explore and classify

For each issue, determine the target repo:

| Scope | Target |
|-------|--------|
| Frontend/UI only | **Pilar** |
| Backend/agent logic only | **agent-platform** |
| Both (new API + UI) | **both** |

Use Explore agents (Task tool, `subagent_type=Explore`) to understand the relevant codebase areas. When classified as **both**, explore both repos. Identify key files, patterns, dependencies, and constraints.

---

### Phase 3: Design plan

Write an implementation plan for each issue as a markdown file in `.claude/plans/<slug>.md` (create the directory if needed).

Each plan should cover:
- **Goal** — What this achieves (1-2 sentences)
- **Changes** — Each file to create/modify, what changes and why
- **Tests** — What tests to write or modify
- **Verification** — Commands or steps to confirm it works

**Trace data flow before assuming limitations.** Components often receive richer data than their direct input type suggests — check parent components, context providers, and sibling outputs before concluding data is unavailable.

#### Multi-repo issues (classified as "both")

Produce **three** plan files:

1. **`<slug>-contract.md`** — The shared API contract: endpoints, methods, request/response shapes, DTOs, error codes. This is the sync point between repos and must be approved first.
2. **`<slug>-pilar.md`** — Frontend plan, referencing the contract.
3. **`<slug>-agent-platform.md`** — Backend plan, referencing the contract.

When the issue includes a Figma URL, extract both visual styling and **interaction patterns** (button placements, action row layouts, component positioning).

**Present a concise summary of all plans.** Highlight key decisions and open questions.

**Wait for explicit approval** ("go", "do it", "looks good") before proceeding.

---

### Phase 4: Execute

Once approved, implement each issue:

1. **Branch from main:**
   ```bash
   git checkout -b feat/issue-<number>-<short-slug> main
   ```
   Use prefixes: `feat/`, `fix/`, `refactor/`, `docs/` as appropriate.

2. **Implement the plan.**

3. **Write tests** per AGENTS.md requirements — at minimum one happy path + one edge case.

4. **Commit with issue references:**
   ```
   Refs DIPSAS/agent-platform#<number>
   ```
   Use `Refs` (not `Closes`) so the issue stays open until PR merge.

5. **Verify:**
   ```bash
   turbo run test --filter=<affected-packages>
   pnpm biome check <changed-files>
   turbo run typecheck --filter=<affected-packages>
   ```
   Fix any failures before proceeding.

#### Multiple issues

After collective plan approval, use the **Task tool** to create parallel agents (`subagent_type=general-purpose`), one per issue. Each agent gets its own branch. If any issue targets both repos, use the agent team flow below for that issue instead.

Wait for all agents to complete before Phase 5.

#### Multi-repo execution (issues classified as "both")

Use an **agent team** for cross-repo issues:

1. Confirm the shared contract (`<slug>-contract.md`) is finalized.
2. **Create team** via `TeamCreate` — name: `solve-issue-<N>`.
3. **Create tasks** via `TaskCreate` — one per repo. Include the full contract content and plan path in each task description so teammates have all context at spawn.
4. **Spawn teammates** (Task tool, `subagent_type=general-purpose`, `team_name`):
   - `pilar-dev` — Pilar task, working directory set to Pilar repo
   - `agent-platform-dev` — agent-platform task, working directory set to agent-platform repo
   - Assign tasks via `TaskUpdate`.
5. **Wait** for both to complete (monitor via `TaskList`).
6. **Shut down** teammates via `SendMessage` (`type: "shutdown_request"`).
7. **Clean up** team via `TeamDelete`.

---

### Phase 5: Report and hand off

After implementation:

1. Report to the user: branch name(s), commit list, test results, any issues encountered.

**STOP.** Do not push or create PRs. The user verifies manually and decides when to ship.

---

### Phase 6: PR and project board (only when user asks)

**Only run this when the user explicitly asks** ("create the PR", "push it", "ship it").

For each solved issue:

1. **Push:**
   ```bash
   git push -u origin <branch-name>
   ```

2. **Create PR:**

   - **Pilar (Azure DevOps):**
     ```bash
     az repos pr create --title "<title>" --description "<body>" \
       --source-branch <branch-name> --target-branch main \
       --repository Pilar --org https://dev.azure.com/dips --project DIPS
     ```

   - **agent-platform (GitHub):**
     ```bash
     gh pr create --repo DIPSAS/agent-platform --title "<title>" --body "<body>"
     ```

   PR body format:
   ```markdown
   ## Summary
   - <bullet points>

   Refs DIPSAS/agent-platform#<number>

   ## Test plan
   - [ ] Tests pass locally
   - [ ] <specific verification steps>
   ```

3. **Update project board status to "In Review":**

   Look up IDs dynamically — project number is `5`, owner is `DIPSAS`:
   ```bash
   # Get project node ID
   gh api graphql -f query='{ organization(login: "DIPSAS") { projectV2(number: 5) { id } } }'
   # Get field IDs (find Status field and "In Review" option)
   gh project field-list 5 --owner DIPSAS --format json
   # Get item ID
   gh project item-list 5 --owner DIPSAS --limit 200 --format json | jq '.items[] | select(.content.number == <issue-number>)'
   # Update status
   gh project item-edit --project-id <project-node-id> --id <item-id> --field-id <status-field-id> --single-select-option-id <in-review-option-id>
   ```
   If project board commands fail, report but don't block — the PR is what matters.

4. **Cross-reference companion PRs (multi-repo only):**
   Edit each PR description to append `Companion PR: <URL>` using `gh pr edit` or `az repos pr update`.

---

### Error handling

- **Auth/network failures**: Tell the user to check `gh auth status` / `az account show`, adjust sandbox network settings via `/sandbox`, or run `gh auth login` / `pnpm azure-login`.
- **Test failures**: Fix before creating PR. If the fix isn't obvious, report and ask for guidance.
- **Branch conflicts**: Append `-v2` rather than force-deleting.
