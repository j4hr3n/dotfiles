# Grype auto-fix dry-run report

**Mode:** Dry-run (plan only — no pushes, no PRs created)
**Source run:** [25098697388](https://github.com/Techfolk-AS/.github/actions/runs/25098697388)
**Run created:** 2026-04-29T08:28:45Z
**Workflow head branch:** `chore/node-24-action-bumps`

## Step 1 — Failed `Scan: *` jobs

| Job | Repo | Job ID |
| --- | --- | --- |
| Scan: doffin-bot | `doffin-bot` | 73541933391 |

Only one repo affected.

## Step 2 — Parsed vulnerabilities

From the Grype log of job `73541933391`:

| Package | Installed | Fixed in | Type | Advisory | Severity |
| --- | --- | --- | --- | --- | --- |
| `go.opentelemetry.io/otel/sdk` | `v1.39.0` | `1.40.0` | go-module | GHSA-9h8m-3fm2-qjrq | High |
| `go.opentelemetry.io/otel/sdk` | `v1.39.0` | `1.43.0` | go-module | GHSA-hfvc-g4fc-pqhx | High |

Highest `fixed_in` per package: **`v1.43.0`** (covers both advisories with one bump).

## Step 3 — Planned fix per repo

### `doffin-bot`

- **Ecosystem:** Go module (`src/go.mod` at `/Users/christofferjahren/dev/doffin-bot/src/go.mod`).
- **Current state in `go.mod` on local working tree:** `go.opentelemetry.io/otel/sdk v1.43.0 // indirect` (already at fixed version locally).
- **Planned bump command (would-run if needed):**
  ```bash
  cd /Users/christofferjahren/dev/doffin-bot/src \
    && go get go.opentelemetry.io/otel/sdk@v1.43.0 \
    && go mod tidy
  ```
- **Branch name (would-create):** `fix/grype-otel-sdk-2026-04-29`
- **Verification (would-run):** `go build ./...` from `src/`.
- **Commit message (would-write):**
  ```
  fix: upgrade go.opentelemetry.io/otel/sdk to v1.43.0 (GHSA-hfvc-g4fc-pqhx, GHSA-9h8m-3fm2-qjrq)

  Resolves high-severity vulnerabilities flagged by the Techfolk-AS Grype org scan.
  Source run: https://github.com/Techfolk-AS/.github/actions/runs/25098697388
  ```

## Step 5 — Skip rules check

Open PR scan on `Techfolk-AS/doffin-bot` for the package `otel/sdk`:

- `gh pr list --repo Techfolk-AS/doffin-bot --state open --search "in:title otel"` returned **no open PRs**.

But broader history reveals a **MERGED** PR that already resolves both advisories:

- **PR #8** — `fix: upgrade otel/sdk to v1.43.0 (GHSA-hfvc-g4fc-pqhx, GHSA-9h8m-3fm2-qjrq)`
  - State: MERGED
  - Merged at: 2026-04-29T08:35:20Z
  - Merge commit: `df7e3bc`
  - Head branch: `fix/otel-sdk-cve-2026-hfvc`

The failed Grype run `25098697388` started at 08:28:45Z, ~7 minutes **before** PR #8 merged. The next Grype Org Scan run (`25098987272`, 08:35:47Z, on `main`) is **green**, confirming the fix is already in place upstream.

## Step 6 — Final report

```
Grype auto-fix run for 25098697388 (2026-04-29T08:28:45Z) — DRY RUN
- doffin-bot: skipped (already remediated by merged PR #8 — otel/sdk → v1.43.0; subsequent run 25098987272 on main is green)
```

### Per-repo summary

- **opened:** (none — dry run)
- **would-open:** (none)
- **skipped:**
  - `doffin-bot` — fix already merged in PR #8 (`fix/otel-sdk-cve-2026-hfvc`, merged 2026-04-29T08:35:20Z). The failed run predates the merge; the next scan on `main` succeeded. No further action required.
- **failed:** (none)

## Notes / observations

- This is exactly the "no work on green" / idempotency case the skill's loop-mode guardrails describe: the failure is stale relative to `main`. In non-dry-run mode this would still resolve to a single skip with no PR opened.
- The dry-run did not require cloning — `~/dev/doffin-bot` already exists with the merged fix on `main` (and a leftover local checkout of the now-merged branch `fix/otel-sdk-cve-2026-hfvc`).
- No `git push`, `gh pr create`, or other remote-mutating commands were executed. Only read-only `gh` and `git` queries plus `find`/`grep` over the local clone.
- The Grype log parsing in Step 2 used the skill's recommended grep pattern and parsed cleanly on the first pass.
