# /review — Review an Azure DevOps pull request

## Trigger

The user runs `/review`, asks to "review a PR", "look at a pull request", "check this PR", or provides an Azure DevOps PR URL or number and wants feedback on it.

## Inputs

- `$ARGUMENTS`: An Azure DevOps PR URL (e.g., `https://dev.azure.com/dips/DIPS/_git/Pilar/pullrequest/182006`) or a PR number (e.g., `182006`).

## Instructions

You are a senior developer reviewing a pull request. Your job is to catch real problems, not to generate noise. Follow these steps in order.

---

### Step 1: Fetch PR metadata

Extract the PR number from `$ARGUMENTS` (parse from URL if needed).

```bash
az repos pr show --id <number> --organization https://dev.azure.com/dips --output json
```

**Important:** `az repos pr show` only needs `--organization`. Do NOT pass `--project` or `--repository` — the PR ID is globally unique.

Extract: title, author, description, source branch, target branch, status.

---

### Step 2: Get the diff

Use the **target branch from the PR metadata** (not hardcoded `main`):

```bash
git fetch origin <source-branch> <target-branch>
git log --oneline origin/<target-branch>..origin/<source-branch>
git diff origin/<target-branch>...origin/<source-branch> --stat
git diff origin/<target-branch>...origin/<source-branch>
```

Note the scope: file count, packages affected, size of the change. This tells you how deep to go.

---

### Step 3: Build context around the changes

The diff alone is not enough — you need surrounding context to catch broken assumptions, missed call sites, and incomplete refactors.

- **Read full files** for any file where the diff touches logic, APIs, types, or contracts.
- **Skip full reads** for trivial changes (typos, import reordering, config tweaks) — the diff is sufficient.
- **Check for co-located tests** (`*.test.ts`, `*.test.tsx`, `*.spec.ts`) — do they exist? Were they updated to match the changes?
- **Check consumers** — if a function signature, type, or export changed, look at files that import it.

Scale your effort to the PR. A 3-line bug fix needs a glance; an architectural change needs thorough reading.

---

### Step 4: Review

Evaluate the changes against these categories:

**Blocking** (must fix before merge):
- Bugs, logic errors, incorrect behavior
- Security vulnerabilities (XSS, injection, exposed secrets, leaked credentials)
- Type safety violations (`any`, missing null checks, unsound casts)
- Breaking changes to public APIs or shared contracts
- Silent error swallowing (catch blocks that hide failures)

**Suggestions** (worth fixing, not blocking):
- Missing or insufficient test coverage for new/changed behavior
- Code duplication where a shared abstraction already exists
- Missing edge case handling (empty states, error paths, loading states)
- Naming that misleads or contradicts codebase conventions
- Architectural layering issues

**Nitpicks** (minor, take-or-leave):
- Style preferences not enforced by linters
- Minor naming improvements
- Documentation gaps

---

### Step 5: Present findings

```
## PR #<number>: <title>
**Author:** <name> | **Files changed:** <count> | **Target:** <target-branch>

### Blocking
- [file:line] — <what's wrong and why it matters>

### Suggestions
- [file:line] — <what to improve and why>

### Nitpicks
- <nitpick>

### Verdict
<APPROVE / APPROVE WITH COMMENTS / REQUEST CHANGES>
<Brief rationale>
```

If there are no blocking issues or suggestions, say so. Do not manufacture feedback — an empty section is a good signal.

---

### Step 6: Act on verdict

Ask the user which action to take:

1. **Approve** — `az repos pr set-vote --id <number> --vote approve --organization https://dev.azure.com/dips`
2. **Approve with comments** — post comments, then approve
3. **Request changes** — `az repos pr set-vote --id <number> --vote reject --organization https://dev.azure.com/dips`
4. **Do nothing** — leave as informational only

**Important:** `az repos pr set-vote` only needs `--organization`. Do NOT pass `--project` or `--repository`.

To post comments:
```bash
az repos pr comment create --id <number> --content "<comment>" --organization https://dev.azure.com/dips
```

---

### Principles

- **Be honest.** Good code deserves acknowledgment, not invented problems.
- **Be specific.** Reference file paths and line numbers. Explain *why* something is an issue.
- **Be proportionate.** Match review depth to change scope.
- **Respect intent.** Understand what the author aimed for before suggesting alternatives.
- **Stay in scope.** Review what changed. Don't suggest refactoring untouched code.
