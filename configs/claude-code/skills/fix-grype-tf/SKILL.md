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
| `npm` | Node | If `pnpm-lock.yaml` exists: `pnpm up <pkg>@<fixed_in>`. Else if `package-lock.json`: `npm install <pkg>@<fixed_in> --package-lock-only`. Else `yarn upgrade <pkg>@<fixed_in>`. |
| `python` | Python | Update `pyproject.toml` / `requirements*.txt`; re-lock with `uv lock` / `poetry lock --no-update <pkg>` / `pip-compile` as appropriate. |
| `java-archive` / `maven` | Java | Update version in `pom.xml` / `build.gradle`. |

If the `fixed_in` version is unavailable on the registry (rare), drop back to the highest available fix version that still resolves all listed advisories. Verify on the registry before failing the run.

## Step 4: Apply the fix

For each affected repo:

1. **Locate or clone**: prefer `~/dev/<repo>` if it exists. Otherwise clone to a tempdir:
   ```bash
   REPO_DIR=$(mktemp -d)/<repo>
   gh repo clone Techfolk-AS/<repo> "$REPO_DIR"
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
- doffin-bot: opened #N — bump go.opentelemetry.io/otel/sdk → v1.43.0
- techfolk-cms: skipped (PR #M already open)
- some-repo: FAILED build verification — see logs above
```

## Guardrails

- **Never** commit changes outside the package bump (no formatter sweeps, no unrelated `go mod tidy` reflows from a different Go version unless required by the dep itself).
- **Never** disable the Grype check, lower `severity-cutoff`, or add suppressions to silence findings — only fix the vulnerable package.
- If a fix requires a Go directive bump (e.g. otel v1.43 needs Go 1.25), include it but call it out in the PR body. If the repo's deploy target (Cloud Functions runtime, Dockerfile base image) won't support that Go version, **stop and report** rather than ship a fix that breaks deploy.
- Don't push to `main`. Don't force-push. Don't merge PRs — leave merge to humans.
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
