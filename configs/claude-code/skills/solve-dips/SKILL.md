# /solve-dips — Solve DIPS GitHub issues end-to-end

## Trigger

The user runs `/solve <issue-numbers>` (e.g., `/solve 42` or `/solve 42 43 44`).
Also triggered by phrases like "solve issue 42", "work on #42", "implement issue 42", "fix #42 and #43".

## Inputs

- `$ARGUMENTS`: One or more GitHub issue numbers separated by spaces.

## Instructions

You are executing the `/solve` skill. Follow these phases in order. Each phase gates the next — don't skip ahead.

---

### Phase 1: Read issues

First, **resolve `<owner>/<repo>` and the GitHub host** from each input in `$ARGUMENTS`:

| Input form | Repo | Host |
|-----------|------|------|
| Bare number (`42`) | `DIPSAS/agent-platform` (default) | `github.com` |
| Owner-qualified (`DIPSAS/agent-platform#42`) | as given | `github.com` |
| `https://github.com/<owner>/<repo>/issues/<n>` | from URL | `github.com` |
| `https://dips.ghe.com/<owner>/<repo>/issues/<n>` | from URL | `dips.ghe.com` |

When the host is `dips.ghe.com`, **prepend `GH_HOST=dips.ghe.com` to every `gh` call** in this flow (view, edit, pr create, project lookups). `az` commands are unaffected.

> **DIPS GHE sandbox quirk**: `gh` calls to `dips.ghe.com` fail TLS verification inside the sandbox (macOS keychain isolation) and may also surface as "invalid token" / "failed to log in". Pass `dangerouslyDisableSandbox: true` on the first `gh` call rather than chasing a phantom auth issue. If the project's `.claude/settings.local.json` sets `env.SSL_CERT_FILE=/etc/ssl/cert.pem`, sandbox mode works — check there first.

Then for each issue:

```bash
gh issue view <number> --repo <owner>/<repo>
```

Collect the title, body, labels, and any linked issues. Assign yourself:
```bash
gh issue edit <number> --repo <owner>/<repo> --add-assignee @me
```

Use the resolved `<owner>/<repo>` consistently in later phases — `Refs` footers, PR descriptions, and board lookups all key off it.

---

### Phase 2: Explore and classify

For each issue, determine the target repo:

| Scope | Target |
|-------|--------|
| Frontend/UI only | **Pilar** |
| Backend/agent logic only | **agent-platform** |
| Both (new API + UI) | **both** |

Use Explore agents (Task tool, `subagent_type=Explore`) to understand the relevant codebase areas. When classified as **both**, explore both repos. Identify key files, patterns, dependencies, and constraints.

> **Prompt-budget caveat:** keep Explore prompts terse (under ~400 words). The DIPS GHE / Figma / PostHog tool surfaces plus skill reminders consume a meaningful slice of the agent's context budget — verbose prompts get rejected with "Prompt is too long". If you need depth, split into multiple short Explore calls or fall back to direct `Read`/`Bash` instead.

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

**Wait for explicit approval** ("go", "do it", "looks good") before proceeding. **This gate applies even in auto mode** — the user wants a human check on the plan before any code is written, regardless of issue size or perceived risk. Do not skip it.

---

### Phase 4: Execute

Once approved, implement each issue:

1. **Fetch and branch from latest main:**
   ```bash
   git fetch origin main
   git checkout -b feat/issue-<number>-<short-slug> origin/main
   ```
   Always use `origin/main` (not local `main`) to ensure the branch is based on the latest remote state.
   Use prefixes: `feat/`, `fix/`, `refactor/`, `docs/` as appropriate.

2. **Implement the plan.**

3. **Write tests** per AGENTS.md requirements — at minimum one happy path + one edge case.

4. **Commit with issue references:**
   ```
   Refs DIPSAS/agent-platform#<number>
   ```
   Use `Refs` (not `Closes`) so the issue stays open until PR merge.

   > **Lefthook + sandbox**: in Pilar, `git commit` runs lefthook which rewrites `.git/hooks/*`. Sandbox blocks that with "operation not permitted". Pass `dangerouslyDisableSandbox: true` for `git commit` here unless the project's `settings.local.json` allows `.git/hooks/**` writes.

5. **Verify** (adapt to target repo):

   **agent-platform (Python):**
   ```bash
   uv run pytest src/platform/tests/ -v
   uv run ruff check <changed-dirs>
   uv run ruff format --check <changed-dirs>
   ```

   **Pilar (TypeScript):**
   ```bash
   turbo run test --filter=<affected-packages>
   pnpm biome check <changed-files>
   turbo run typecheck --filter=<affected-packages>
   ```

   Fix any failures before proceeding.

   **Typecheck noise caveat:** `turbo run typecheck` runs against the whole package and may surface pre-existing errors from files you didn't touch. Before fixing anything, grep for your changed files:
   ```bash
   turbo run typecheck --filter=<pkg> 2>&1 | grep <changed-file>
   ```
   If your files aren't in the output, the failures are pre-existing on `origin/main` — report and move on, don't fix unless the user asks.

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
2. **Suggest running `/simplify`** as the next step before push. The three review agents (reuse, quality, efficiency) catch issues while commits are still amendable locally — running it *after* push forces a force-push (often blocked by the branch guard) or an extra follow-up commit. Offer it explicitly in the report.
3. **Consolidate noisy history before pushing.** If iterative feedback produced more than ~5 commits for one logical change (or any commit-then-revert pairs), offer to soft-reset to `origin/main` and recommit in 3-5 logical groups. The branch guard blocks `git reset --hard`, but `git reset --soft origin/main` is allowed and preserves all changes as staged work.

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

     **Post the Pilar PR link back to the GitHub issue** — mandatory for Pilar PRs, so the issue surfaces the cross-system PR alongside Azure DevOps. Capture the PR URL from the `az` response (e.g. `--query 'repository.webUrl'` plus `pullRequestId`, or read it from the JSON output) and comment on the issue:
     ```bash
     gh issue comment <number> --repo <owner>/<repo> \
       --body "Pilar PR: <pr-url>"
     # Prepend GH_HOST=dips.ghe.com when the issue lives on DIPS GHE.
     ```

   - **agent-platform / DIPS GHE (GitHub):**
     ```bash
     gh pr create --repo <owner>/<repo> --title "<title>" --body "<body>"
     # Prepend GH_HOST=dips.ghe.com when the issue lives on DIPS GHE.
     ```

   PR body format:
   ```markdown
   ## Summary
   - <bullet points>

   Refs <owner>/<repo>#<number>

   ## Test plan
   - [ ] Tests pass locally
   - [ ] <specific verification steps>
   ```

3. **Update project board status to "In Review" — always, when the issue has a board.**

   This is a mandatory step after every PR, not optional. Don't skip it even if the user didn't explicitly ask. Look up the project from the issue itself so this works across orgs and hosts:

   ```bash
   gh issue view <number> --repo <owner>/<repo> --json projectItems
   # Prepend GH_HOST=dips.ghe.com for DIPS GHE.
   ```

   If `projectItems` is empty, **don't trust it blindly**: the same empty array comes back when the token is missing the `read:project` scope. Run `gh auth status` first — if the host's token lacks `project` / `read:project`, ask the user to run `gh auth refresh -s project,read:project -h <host>` and re-check. Only treat an empty list as "no board" once you've confirmed the scopes are present. (Default `gh auth login` does **not** request these scopes; on `dips.ghe.com` this bites every time.)

   Otherwise, resolve the project's number/owner from the response and drive the Status field:
   ```bash
   gh project field-list <project-number> --owner <project-owner> --format json
   gh project item-list <project-number> --owner <project-owner> --limit 200 --format json \
     | jq '.items[] | select(.content.number == <issue-number>)'
   gh project item-edit --project-id <project-node-id> --id <item-id> \
     --field-id <status-field-id> --single-select-option-id <in-review-option-id>
   ```

   Sandbox mode can block these calls (network/auth). If that happens, re-run with `dangerouslyDisableSandbox: true` once to confirm scopes are the blocker, otherwise fall through. Report the outcome — the PR is what matters; don't block on a failed board update.

4. **Cross-reference companion PRs (multi-repo only):**
   Edit each PR description to append `Companion PR: <URL>` using `gh pr edit` or `az repos pr update`.

---

### Error handling

- **Auth/network failures**: Tell the user to check `gh auth status` / `az account show`, adjust sandbox network settings via `/sandbox`, or run `gh auth login` / `pnpm azure-login`.
- **Test failures**: Fix before creating PR. If the fix isn't obvious, report and ask for guidance.
- **Branch conflicts**: Append `-v2` rather than force-deleting.
