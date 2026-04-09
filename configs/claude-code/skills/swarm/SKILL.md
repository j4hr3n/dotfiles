---
name: swarm
description: Fully autonomous multi-issue solver using agent teams. Takes issue URLs/numbers, fetches issues assigned to you, or accepts query shortcuts like --mine. Supports GitHub and Azure DevOps. Analyzes dependencies, spawns parallel worker agents, implements all issues, and creates PRs — all without user intervention.
disable-model-invocation: true
---

# /swarm — Autonomous Multi-Issue Solver

## Trigger

The user runs `/swarm <issue-references>` or asks to swarm on issues (e.g., "swarm my assigned issues", "grab all issues assigned to me and swarm them").

Examples:
- `/swarm 42 43 44`
- `/swarm https://github.com/org/repo/issues/42 https://dev.azure.com/org/project/_workitems/edit/99`
- `/swarm --mine` or `/swarm mine`
- "swarm all my github issues"
- "grab my assigned issues and swarm them"

## Inputs

- `$ARGUMENTS`: One or more issue references **or** a query shortcut. Accepted formats:
  - Plain numbers: `42`, `43`
  - GitHub URLs: `https://github.com/<owner>/<repo>/issues/<N>`
  - Azure DevOps URLs: `https://dev.azure.com/<org>/<project>/_workitems/edit/<N>`
  - `--mine` / `mine`: Fetch all open issues assigned to the current user
  - `--mine --repo <owner/repo>`: Fetch assigned issues from a specific repo
  - `--mine --label <label>`: Filter assigned issues by label

If `$ARGUMENTS` is empty or not provided, also treat this as `--mine` (fetch all assigned issues for the current repo).

## Instructions

You are executing the `/swarm` skill. This is a **fully autonomous** workflow — proceed through all phases without waiting for user approval. Follow these phases strictly in order.

---

### Phase 1: Intake

1. **Detect platform** from current git remote:
   ```bash
   git remote get-url origin
   ```
   - If remote contains `github.com` → GitHub (extract owner/repo)
   - If remote contains `dev.azure.com` or `visualstudio.com` → Azure DevOps (extract org/project)

2. **Parse `$ARGUMENTS`** to extract issue references:

   **If `--mine`, `mine`, empty, or the user asked to "grab my issues" / "assigned to me":**
   - GitHub — fetch all open issues assigned to the current user:
     ```bash
     # Current repo (default):
     gh issue list --assignee @me --state open --json number,title,body,labels --limit 50
     # Specific repo (if --repo provided):
     gh issue list --assignee @me --state open --repo <owner/repo> --json number,title,body,labels --limit 50
     # With label filter (if --label provided):
     gh issue list --assignee @me --state open --label "<label>" --json number,title,body,labels --limit 50
     ```
   - Azure DevOps — fetch assigned work items:
     ```bash
     az boards query --wiql "SELECT [System.Id],[System.Title],[System.State] FROM workitems WHERE [System.AssignedTo] = @Me AND [System.State] <> 'Closed' AND [System.State] <> 'Done'" --org https://dev.azure.com/<org> --project <project>
     ```
   - Collect all returned issues as the input set.
   - If the query returns 0 issues, report "No open issues assigned to you" and stop.
   - If the query returns >15 issues, print the full list and ask the user to confirm or narrow down with `--label` before proceeding.

   **If explicit references are provided:**
   - GitHub URL (`https://github.com/<owner>/<repo>/issues/<N>`): extract owner, repo, number
   - Azure DevOps URL (`https://dev.azure.com/<org>/<project>/_workitems/edit/<N>`): extract org, project, number
   - Plain numbers: use the platform detected in step 1

3. **Determine platform per issue** and store as metadata (platform, owner/org, repo/project, number).

4. **Fetch issue details** (skip for `--mine` issues already fetched with full JSON):
   - GitHub:
     ```bash
     gh issue view <N> --repo <owner/repo> --json number,title,body,labels,assignees
     ```
   - Azure DevOps:
     ```bash
     az boards work-item show --id <N> --org https://dev.azure.com/<org> --project <project>
     ```

5. **Assign self to each issue** (skip for `--mine` — already assigned):
   - GitHub:
     ```bash
     gh issue edit <N> --repo <owner/repo> --add-assignee @me
     ```
   - Azure DevOps: (assign via update if supported, otherwise skip)

6. **Print summary table** in chat with columns: Issue #, Title, Platform, Labels.

---

### Phase 2: Dependency Analysis & Planning

1. **Scan issue bodies** for dependency patterns:
   - `depends on #N`, `blocked by #N`, `requires #N`, `after #N`
   - Cross-repo references: `owner/repo#N`

2. **Classify each issue** by target repo (from labels, body keywords, or URL).

3. **Sort into execution waves** (DAG topological sort):
   - Wave 1: issues with no dependencies within the batch
   - Wave 2: issues that depend only on Wave 1 issues
   - Wave N: issues that depend only on waves < N
   - Circular dependencies: group the cycle into one sequential wave, print a warning

4. **Use Explore agents** (up to 3 in parallel via `Task` with `subagent_type=Explore`) to understand relevant codebase areas for all issues.

5. **Consult project memory** at `~/.claude/projects/*/memory/MEMORY.md` for past learnings.

6. **Write master plan** to `.claude/plans/swarm-<timestamp>.md` with per-issue sections:
   ```markdown
   # Swarm Plan — <timestamp>

   ## Issue #<N>: <title>
   ### Goal
   What this achieves.
   ### Changes
   Each file to create/modify, with description of what changes and why.
   ### Tests
   What tests to write or modify.
   ### Verification
   Commands to run (test, typecheck, lint).
   ```
   For multi-repo issues: include shared API contract + separate backend/frontend sections.

7. **Print wave plan summary** in chat — then **proceed immediately** (no approval gate).

---

### Phase 3: Execute (wave-based parallel)

For each wave (1 through N), execute the following:

#### 3a. Create the team

```
TeamCreate with name: "swarm-wave-<N>"
```

#### 3b. Create tasks

Use `TaskCreate` for each issue in this wave. Each task description must embed:

- Full issue details (title, body, labels)
- The implementation plan from Phase 2
- Target repo + working directory
- Branch name: `feat/issue-<N>-<slug>` or `fix/issue-<N>-<slug>` (based on issue type)
- Commit format: meaningful message with `Refs <owner/repo>#<N>`
- Verification commands:
  ```bash
  # Run tests, typecheck, lint as appropriate for the project
  ```
- PR creation instructions (platform-specific):
  - GitHub:
    ```bash
    git push -u origin <branch-name>
    gh pr create --repo <owner/repo> --title "<title>" --body "$(cat <<'EOF'
    ## Summary
    - <changes>

    Refs <owner/repo>#<N>

    ## Test plan
    - [ ] Tests pass
    - [ ] <verification steps>
    EOF
    )"
    ```
  - Azure DevOps:
    ```bash
    git push -u origin <branch-name>
    az repos pr create --title "<title>" --description "<body>" \
      --source-branch <branch-name> --target-branch main \
      --repository <repo> --org https://dev.azure.com/<org> --project <project>
    ```
- Dependency context from prior waves (what was already implemented, branch names, PR URLs)

#### 3c. Spawn workers

Use `Task` with `subagent_type="general-purpose"`, `team_name="swarm-wave-<N>"`, and `isolation="worktree"` for each task.

Each worker's prompt must include:

```
You are a swarm worker. Work fully autonomously — do not ask for approval.

1. Create branch from main:
   git checkout -b <branch-name> main
2. Implement all changes from the plan below
3. Write tests (minimum: happy path + edge case)
4. Run verification (test + lint + typecheck), fix any failures
5. Commit with issue refs:
   git add <files> && git commit -m "<message>

   Refs <owner/repo>#<N>

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
6. Push branch:
   git push -u origin <branch-name>
7. Create PR using the platform-specific command provided below
8. Report back: branch name, PR URL, commit list, test results

If tests fail after one retry, report the failure — don't loop endlessly.

[PLAN]
<full implementation plan for this issue>

[PR COMMAND]
<platform-specific PR creation command>
```

Worker naming:
- Single-repo issues: `worker-<N>` (where N is the issue number)
- Multi-repo issues: `worker-<N>-backend` (spawned first) and `worker-<N>-frontend` (blocked by backend task)

#### 3d. Monitor

Poll `TaskList` until all tasks in the wave are completed.

#### 3e. Handle failures

- If a worker fails: log the failure, mark dependent issues in later waves as **skipped**
- Do not retry failed workers — record the error for the final report

#### 3f. Tear down

1. `SendMessage(type="shutdown_request")` to all workers in the wave
2. `TeamDelete`
3. Proceed to next wave

---

### Phase 4: Cross-reference & Project Board

After all waves complete:

1. **Cross-reference companion PRs** (for multi-repo issues that produced PRs in both repos):
   - Edit each PR description to append: `Companion PR: <URL-of-the-other-PR>`
   - GitHub: `gh pr edit <number> --repo <owner/repo> --body "<updated-body>"`
   - Azure DevOps: `az repos pr update --id <pr-id> --description "<updated-body>" --org <org-url>`

2. **Update project board status** if applicable:
   - Detect board from repo settings
   - Move items to "In Review" status

Failures in this phase are **non-blocking** — report but continue.

---

### Phase 5: Report & Learnings

1. **Save learnings** to project memory at `~/.claude/projects/<project>/memory/MEMORY.md`:
   - Build quirks, architecture patterns, gotchas, debugging insights discovered
   - Keep entries concise with a date header (`## YYYY-MM-DD`)
   - Don't duplicate existing entries

2. **Print final report:**

   #### Summary
   - Issues processed: X
   - PRs created: Y
   - Failures: Z

   #### PRs Created
   | Issue | Branch | PR URL | Status |
   |-------|--------|--------|--------|
   | #N    | feat/issue-N-slug | <url> | Merged/Open |

   #### Failures (if any)
   | Issue | Error | Impacted Dependents |
   |-------|-------|---------------------|
   | #N    | <error> | #M, #O |

   #### Skipped Issues (if any)
   | Issue | Reason |
   |-------|--------|
   | #M    | Dependency #N failed |

3. **Suggest running `/retro`** to review whether skills, config, or workflows need updating.

---

### Error Handling

- **Auth failures**: Report and suggest:
  - GitHub: `gh auth status` / `gh auth login`
  - Azure DevOps: `az account show` / `pnpm azure-login`
- **Branch conflicts**: If branch already exists, append `-v2`, `-v3`, etc.
- **Worker hangs**: Managed by team infrastructure (automatic idle detection)
- **Circular dependencies**: Group into one sequential wave, print warning
- **External dependencies** (issues not in the batch): Note in the plan but don't block execution
- **Network issues**: Suggest checking sandbox settings via `/sandbox` to allow `github.com` and `dev.azure.com`
