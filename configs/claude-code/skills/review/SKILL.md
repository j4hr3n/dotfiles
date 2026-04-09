# /review — Review a pull request

## Trigger

The user runs `/review`, asks to "review a PR", "look at a pull request", "check this PR", or provides a PR URL or number and wants feedback on it.

## Inputs

- `$ARGUMENTS`: A PR URL or number. Supports:
  - Azure DevOps: `https://dev.azure.com/dips/DIPS/_git/Pilar/pullrequest/182006` or a number
  - GitHub: `https://github.com/org/repo/pull/123`, `org/repo#123`, or a number

## Instructions

You are a senior developer reviewing a pull request. Your job is to catch real problems, not to generate noise. Follow these steps in order.

---

### Step 1: Detect platform and fetch PR metadata

Parse `$ARGUMENTS` to determine the platform:

- URL contains `github.com` or format is `owner/repo#N` → **GitHub**
- URL contains `dev.azure.com` → **Azure DevOps**
- Just a number → detect from the current repo's remote:

```bash
git remote get-url origin 2>/dev/null
```

If it contains `github.com` → GitHub. If it contains `dev.azure.com` or `visualstudio.com` → Azure DevOps.

**GitHub:**
```bash
gh pr view <number-or-url> --json title,author,body,headRefName,baseRefName,state,number,url
```

Extract: title, author login, body, source branch (`headRefName`), target branch (`baseRefName`), state.

**Azure DevOps:**
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
- **Check for co-located tests** (`*.test.ts`, `*.test.tsx`, `*.spec.ts`, `*_test.py`, `test_*.py`) — do they exist? Were they updated to match the changes?
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

**GitHub:**
1. **Approve** — `gh pr review <number> --approve`
2. **Approve with comments** — `gh pr review <number> --comment --body "<summary>"`, then approve
3. **Request changes** — `gh pr review <number> --request-changes --body "<summary>"`
4. **Do nothing** — leave as informational only

**Azure DevOps:**
1. **Approve** — `az repos pr set-vote --id <number> --vote approve --organization https://dev.azure.com/dips`
2. **Approve with comments** — post comments, then approve
3. **Request changes** — `az repos pr set-vote --id <number> --vote reject --organization https://dev.azure.com/dips`
4. **Do nothing** — leave as informational only

To post comments:

**GitHub:** `gh pr comment <number> --body "<comment>"`

**Azure DevOps:** `az repos pr comment create --id <number> --content "<comment>" --organization https://dev.azure.com/dips`

**Important:** `az repos pr set-vote` only needs `--organization`. Do NOT pass `--project` or `--repository`.

---

### Principles

- **Be honest.** Good code deserves acknowledgment, not invented problems.
- **Be specific.** Reference file paths and line numbers. Explain *why* something is an issue.
- **Be proportionate.** Match review depth to change scope.
- **Respect intent.** Understand what the author aimed for before suggesting alternatives.
- **Stay in scope.** Review what changed. Don't suggest refactoring untouched code.
