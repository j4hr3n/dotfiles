# /review — Review an Azure DevOps pull request

## Trigger

The user runs `/review <PR-URL-or-number>` or asks to review a specific PR.

## Inputs

- `$ARGUMENTS`: An Azure DevOps PR URL (e.g., `https://dev.azure.com/dips/DIPS/_git/Pilar/pullrequest/182006`) or a PR number (e.g., `182006`).

## Instructions

You are executing the `/review` skill. Act as a **senior developer** focused on code quality. Follow these steps strictly in order.

---

### Step 1: Fetch PR metadata

Extract the PR number from `$ARGUMENTS` (parse from URL if needed).

```bash
az repos pr show --id <number> --organization https://dev.azure.com/dips --output json
```

Note: `az repos pr show` only needs `--organization` — do NOT pass `--project` or `--repository`.

Extract and display: title, author, description, source branch, target branch, status.

---

### Step 2: Get the diff

```bash
git fetch origin <source-branch> main
git log --oneline origin/main..origin/<source-branch>
git diff origin/main...origin/<source-branch> --stat
git diff origin/main...origin/<source-branch>
```

Understand the scope: how many files changed, which packages are affected, how large is the change.

---

### Step 3: Read affected files in full

For every file touched by the PR, read the **full file** (not just the diff hunks) to understand the surrounding context. This is critical for catching issues the diff alone won't reveal — broken assumptions, missed call sites, incomplete refactors.

Also check for:
- Co-located test files (`*.test.tsx`, `*.test.ts`) — do they exist? Were they updated?
- Related files that consume or are consumed by the changed code

---

### Step 4: Review as a senior developer

Evaluate the changes against these criteria, referencing the project's code-review checklist (`.claude/skills/code-review/SKILL.md`):

**Blocking issues** (must fix before merge):
- Bugs, logic errors, incorrect behavior
- Security vulnerabilities (XSS, injection, exposed secrets)
- Type safety violations (`any`, missing null checks, unsound casts)
- Breaking changes to public APIs or shared contracts
- Silent error swallowing

**Suggestions** (should fix, but not blocking):
- Missing or insufficient test coverage for changed code
- Incorrect architectural layer placement
- Code duplication where an abstraction exists
- Naming inconsistencies with codebase conventions
- Missing edge case handling (empty states, error states, loading)
- Accessibility gaps

**Nitpicks** (minor, optional):
- Style preferences not enforced by tooling
- Minor naming improvements
- Documentation gaps

**Also verify:**
- Named exports only (no default exports)
- Puls semantic tokens used (no raw Tailwind colors or hex values)
- Correct data fetching pattern (server client vs browser client)
- No raw `fetch` calls
- Biome-compatible formatting and import ordering

---

### Step 5: Present findings

Organize the review clearly:

```
## PR #<number>: <title>
**Author:** <name> | **Files changed:** <count> | **Scope:** <packages affected>

### Blocking
- <issue with file:line reference and explanation>

### Suggestions
- <suggestion with file:line reference and explanation>

### Nitpicks
- <nitpick>

### Verdict
<APPROVE / APPROVE WITH COMMENTS / REQUEST CHANGES>
<Brief rationale>
```

If there are no blocking issues or suggestions, say so clearly — don't manufacture feedback.

---

### Step 6: Act on verdict

Ask the user whether to:
1. **Approve** — `az repos pr set-vote --id <number> --vote approve --organization https://dev.azure.com/dips`
2. **Approve with comments** — Post review comments first, then approve
3. **Request changes** — `az repos pr set-vote --id <number> --vote reject --organization https://dev.azure.com/dips`
4. **Do nothing** — Leave the review as informational only

Note: `az repos pr set-vote` only needs `--organization` — do NOT pass `--project` or `--repository`.

Execute the chosen action. If posting comments, use:
```bash
az repos pr comment create --id <number> --content "<comment>" --organization https://dev.azure.com/dips
```

---

### Review principles

- **Be honest.** If the code is good, say so. Don't invent problems.
- **Be specific.** Reference file paths and line numbers. Explain *why* something is an issue, not just *what*.
- **Be proportionate.** A 4-line utility change doesn't need the same scrutiny as an architectural refactor.
- **Respect intent.** Understand what the author was trying to achieve before suggesting alternatives.
- **Stay in scope.** Review what changed. Don't suggest refactoring untouched code.
