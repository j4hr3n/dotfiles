---
name: fix-grype-tf
description: Auto-fix Techfolk-AS Grype org scan failures. Use this skill whenever the user says "/fix-grype-tf", "fix grype", "fix grype failures", "fix the grype scan", "patch grype vulns", "fix the security scan", mentions the Techfolk-AS Grype Org Scan being red/failing, or pastes a Techfolk-AS/.github Actions run URL with failed Grype jobs. Also triggers when the user wants to plan or dry-run the fix ("what would you fix from this scan?"). Pulls the latest failing run (or a given run ID), parses each affected repo's vulnerable packages and fix versions from the Grype log, bumps dependencies in the right ecosystem (Go / npm / pnpm / Python / Java), verifies the build, pushes a fix branch, and opens one PR per repo — skipping any repo that already has an open fix PR. Specific to the Techfolk-AS GitHub organization.
---

# Fix Grype Org Scan — Techfolk-AS

Auto-fixes vulnerabilities surfaced by the daily **Grype Org Scan** workflow in `Techfolk-AS/.github`. Produces one PR per affected repo bumping the vulnerable dependency to the fixed version Grype recommends.

## When to use

- The user mentions a failing Grype run / "the grype scan is red" / pastes a run URL like `https://github.com/Techfolk-AS/.github/actions/runs/<id>`.
- A `/loop` invocation after each daily scan (see "Running on a loop locally" at the end).
- "/fix-grype-tf" or any "fix grype" phrasing.
- The user asks to **plan / dry-run** what would be fixed (don't push or open PRs in that case — see "Dry-run mode").

## Dry-run mode

If the user says "dry run", "plan only", "don't push", "don't open PRs", "what would you do", or similar, run Steps 1–3 fully and Step 4 only up to the verification (don't push, don't `gh pr create`). End with the same final report (Step 6) but mark each repo as `would-open` instead of `opened`. This is the right mode for evaluating the skill or sanity-checking before letting it run unattended.

## Inputs

Accepts an optional run ID or run URL. If not given, find the most recent **failed** run of the `Grype Org Scan` workflow on the default branch of `Techfolk-AS/.github`:

```bash
gh run list --repo Techfolk-AS/.github --workflow "Grype Org Scan" \
  --status failure --limit 1 --json databaseId,headBranch,conclusion,createdAt
```

If none failed recently, **stop and report success** — there's nothing to fix.

## Step 1: Identify failing repos

For the chosen run, list jobs and filter to failed ones whose name starts with `Scan: `:

```bash
gh run view <run_id> --repo Techfolk-AS/.github --json jobs \
  --jq '.jobs[] | select(.conclusion=="failure" and (.name | startswith("Scan: "))) | {name, databaseId}'
```

The repo name is the suffix after `Scan: `.

## Step 2: Extract vulnerabilities per repo

For each failing job, pull only the Grype output table from the log:

```bash
gh run view --job <job_id> --repo Techfolk-AS/.github --log 2>/dev/null \
  | grep -E "NAME |[A-Za-z0-9./_-]+ +v?[0-9]+\.[0-9]+\.[0-9]+ +[0-9]+\.[0-9]+\.[0-9]+ +.*GHSA-" \
  | sed -E 's/^[^\t]*\t[^\t]*\t[0-9TZ:.\+-]+ +//'
```

Parse each row into `{package, installed, fixed_in, ecosystem (TYPE column), advisory (GHSA/CVE)}`. Pick the **highest** `fixed_in` per package (covers all advisories in one bump).

If parsing yields nothing, dump more of the log and re-parse — don't proceed with empty data.

## Step 3: Plan the fix per repo

For each affected repo, decide the ecosystem and the bump command. Common cases for Techfolk-AS:

| TYPE column | Ecosystem | Bump approach |
| --- | --- | --- |
| `go-module` | Go | `cd <module-dir> && go get <pkg>@<fixed_in> && go mod tidy` (in every directory containing a `go.mod`). Add as explicit indirect requirement if it was transitive. |
| `npm` | Node | See "Transitive npm deps" below — direct `pnpm up` rarely works because almost all Grype findings are transitive. |
| `python` | Python | Update `pyproject.toml` / `requirements*.txt`; re-lock with `uv lock` / `poetry lock --no-update <pkg>` / `pip-compile` as appropriate. |
| `java-archive` / `maven` | Java | Update version in `pom.xml` / `build.gradle`. |

If the `fixed_in` version is unavailable on the registry (rare), drop back to the highest available fix version that still resolves all listed advisories. Verify on the registry before failing the run.

### Transitive npm deps (the common case)

In practice almost every Grype npm finding in this org is a **transitive** dependency, so plain `pnpm up <pkg>` / `npm install <pkg>` is a no-op. Use the package manager's override mechanism instead:

- **pnpm** (`pnpm-lock.yaml`): edit `pnpm.overrides` in `package.json`, then `pnpm install`.
- **npm** (`package-lock.json`): edit top-level `overrides`, then `npm install --package-lock-only`.
- **yarn classic** (`yarn.lock`): edit top-level `resolutions`, then `yarn install`.

Use **version-scoped selectors** to avoid bumping unrelated copies of the same package across major lines. Examples actually used in this org:

```jsonc
{
  "pnpm": {
    "overrides": {
      "uuid@>=11.0.0 <11.1.1": "11.1.1",   // only bumps uuid v11 — leaves v9 transitives alone
      "fast-xml-parser@<5.7.0": "5.7.0",
      "fast-uri@<3.1.2": "3.1.2",
      "dompurify@>=3.0.0 <3.4.0": "3.4.0"
    }
  }
}
```

Without the selector (e.g. `"uuid": ">=11.1.1"`), pnpm will force every uuid resolution — including v8/v9 used by Google SDKs — into a new major, which can break consumers. Always scope by version range when the same package exists at multiple majors in the lockfile (`pnpm why <pkg>` to check).

A direct dep listed in `dependencies` / `devDependencies` should still be bumped directly (edit the version, then install) — overrides are for transitives.

### Multi-package repos

Some repos (e.g. `helen.ai` with `helenai/` + `mcp-server/`) have multiple workspaces with separate lockfiles, and sometimes different package managers per workspace. The Grype scan runs at the repo root and reports findings across all of them.

- Identify every `package.json` / lockfile pair (`find . -maxdepth 3 -name "package.json" -not -path "*/node_modules/*"`).
- Locate each vulnerable package in the right lockfile (`grep <pkg> <each lockfile>`).
- Fix each workspace independently with its own override mechanism, then stage all touched lockfiles in a single commit.

## Step 4: Apply the fix

For each affected repo:

1. **Locate or clone**: prefer `~/dev/<repo>` if it exists. Otherwise clone to a tempdir:
   ```bash
   REPO_DIR=$(mktemp -d)/<repo>
   gh repo clone Techfolk-AS/<repo> "$REPO_DIR"
   ```
   If the local clone has uncommitted work, stash it with a tagged name and remember the original branch so you can restore both at the end:
   ```bash
   ORIG_BRANCH=$(git -C ~/dev/<repo> branch --show-current)
   git -C ~/dev/<repo> stash push -u -m "grype-fix-autostash-<YYYY-MM-DD>"
   # ... do the fix on a fresh branch ...
   git -C ~/dev/<repo> checkout "$ORIG_BRANCH"
   git -C ~/dev/<repo> stash pop  # only pops the matching stash if it's still on top
   ```
2. **Sync main**:
   ```bash
   git -C "$REPO_DIR" fetch origin && git -C "$REPO_DIR" checkout main && git -C "$REPO_DIR" pull --ff-only
   ```
3. **Branch**: `fix/grype-<short-pkg>-<YYYY-MM-DD>` (slugify package name; e.g. `fix/grype-otel-sdk-2026-04-29`).
4. **Bump** using the ecosystem-appropriate command from Step 3.
5. **Verify** locally:
   - Go: `go build ./...` in each module dir.
   - Node: `pnpm install` (if lockfile changed) and `pnpm -r build` if a build script exists; otherwise just lockfile regeneration.
   - Python: `uv sync` / `poetry install --no-root` to validate the resolution.
   - Java: skip local verification if no JDK is set up; rely on the PR's CI.
   If verification fails, **stop for that repo** and report the error — do not push a broken PR.
6. **Commit** with a descriptive message referencing each advisory:
   ```
   fix: upgrade <pkg> to <fixed_in> (<GHSA-1>, <GHSA-2>)

   Resolves high/critical vulnerabilities flagged by the Techfolk-AS Grype org scan.
   Source run: https://github.com/Techfolk-AS/.github/actions/runs/<run_id>
   ```
7. **Push and PR**:
   ```bash
   git push -u origin <branch>
   gh pr create --repo Techfolk-AS/<repo> \
     --title "fix: bump <pkg> to <fixed_in> (Grype)" \
     --body "$(cat <<'EOF'
   ## Summary
   Bumps `<pkg>` from `<installed>` to `<fixed_in>` to resolve high-severity vulnerabilities flagged by the daily Grype org scan.

   ## Vulnerabilities fixed
   | Advisory | Installed | Fixed in |
   | --- | --- | --- |
   | <GHSA-1> | <installed> | <fixed_in> |

   Source: https://github.com/Techfolk-AS/.github/actions/runs/<run_id>

   ## Test plan
   - [x] Local build / lock regeneration passes
   - [ ] Repo CI passes
   - [ ] Next Grype scan is green
   EOF
   )"
   ```

## Step 5: Skip rules — don't open duplicate PRs

Before opening a PR, check whether an open PR already addresses the same package:

```bash
gh pr list --repo Techfolk-AS/<repo> --state open \
  --search "in:title <pkg>" --json number,title,headRefName
```

If a matching open PR exists, skip and note it in the final report instead.

## Step 6: Final report

Print a single summary at the end:

```
Grype auto-fix run for <run_id> (<created_at>)
- webcrm-mcp: opened #3 — bump hono → 4.12.18 (+3 other deps)
- techfolk-cms: skipped (PR #46 already open)
- some-repo: FAILED build verification — see logs above
```

## Step 7 (optional): Auto-merge mode

**Default: do not merge.** Leave merge to humans.

**Override:** if the user explicitly authorizes merging in the same session ("merge them all", "use my admin rights to merge", "auto-merge with admin", etc.), then after every PR is opened:

1. **Check each PR is green and mergeable:**
   ```bash
   gh pr view --repo Techfolk-AS/<repo> <num> \
     --json mergeable,mergeStateStatus,statusCheckRollup
   ```
   `mergeStateStatus` of `CLEAN` is the happy path. `BLOCKED` usually means branch protection — `--admin` overrides it. `BEHIND`, `DIRTY`, or any failing check should stop the merge for that repo; report and move on.

2. **Squash-merge with admin override and delete the branch:**
   ```bash
   gh pr merge --repo Techfolk-AS/<repo> <num> --squash --admin --delete-branch
   ```

3. **Re-trigger the Grype Org Scan** to confirm the fixes worked end-to-end:
   ```bash
   gh workflow run "Grype Org Scan" --repo Techfolk-AS/.github
   # wait for completion:
   gh run watch <new_run_id> --repo Techfolk-AS/.github --exit-status
   ```
   Include the new run's URL and conclusion (success / which repos still failed) in the final report.

Never use `--admin` without an explicit user instruction in the current session.

## Guardrails

- **Never** commit changes outside the package bump (no formatter sweeps, no unrelated `go mod tidy` reflows from a different Go version unless required by the dep itself).
- **Never** disable the Grype check, lower `severity-cutoff`, or add suppressions to silence findings — only fix the vulnerable package.
- If a fix requires a Go directive bump (e.g. otel v1.43 needs Go 1.25), include it but call it out in the PR body. If the repo's deploy target (Cloud Functions runtime, Dockerfile base image) won't support that Go version, **stop and report** rather than ship a fix that breaks deploy.
- Don't push to `main`. Don't force-push. **Don't merge PRs by default** — see Step 7 for the explicit-authorization path.
- If credentials or `GITHUB_TOKEN` are missing for any step, surface the error and stop; don't paper over it.

## Running on a loop locally

The daily Grype Org Scan runs on weekday mornings. The cleanest way to react to it is `/loop` on the user's machine — that machine has SSH keys, `gh` auth, language toolchains (`go`, `pnpm`, `uv`), and the user's `~/dev/<repo>` clones, all of which a remote scheduled agent does not.

Suggested invocation (let the model pace itself between runs):

```
/loop /fix-grype-tf
```

Each tick of the loop:
1. Looks for the most recent **failed** run of the `Grype Org Scan` workflow in `Techfolk-AS/.github`.
2. If none failed since the previous tick (track via the run's `databaseId`), exit early without doing anything.
3. Otherwise, run Steps 1–6 above, opening at most one PR per affected repo.

Important behavioural rules for loop mode:
- **Idempotency**: never open a duplicate PR — Step 5 already covers this, but be extra strict in loop mode since you may see the same failed run multiple times before a maintainer merges the fix.
- **No work on green**: if the latest run succeeded, do nothing. Don't speculatively bump packages.
- **Backoff on hard failures**: if a repo fails verification (e.g. build break after a bump), report it once per loop tick — don't re-attempt the same broken bump on every iteration. A cheap heuristic: if the same `(repo, package, fixed_in)` triple failed verification on the previous tick and nothing on `main` has changed, skip it and surface a TODO in the report.
- **Quiet on success**: when there's nothing to do, the tick output should be a single-line "no failed runs since <last seen>" rather than re-running parsing.
