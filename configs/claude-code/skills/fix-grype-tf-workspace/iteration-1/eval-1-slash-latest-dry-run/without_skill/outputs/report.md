# /fix-grype-tf — Dry-Run Plan

**Mode:** Plan only. No branches pushed, no PRs opened, no remote-mutating commands run.

> Note: this report was returned inline by the subagent because its `Write` tool call to the workspace path was blocked by the harness. Captured here verbatim for the eval.

## 1. Latest failed Techfolk-AS Grype Org Scan

| Field | Value |
|---|---|
| Workflow | Grype Org Scan (`Techfolk-AS/.github`) |
| Run ID | `25098697388` |
| Run URL | https://github.com/Techfolk-AS/.github/actions/runs/25098697388 |
| Started | 2026-04-29T08:28:45Z |
| Trigger | `workflow_dispatch` on branch `chore/node-24-action-bumps` |
| Result | failure (1 of 17 repo scans failed) |

The earlier failed runs on `main` were the scheduled scans 2026-04-12 / 13 / 14 (`24301130958`, `24332178206`, `24386419266`). The 2026-04-29 dispatch is the most recent failure overall.

## 2. Affected repos and packages

Only **one** repo failed in this run: `Techfolk-AS/doffin-bot` (job `73541933391`).

Grype output (severity cutoff = high, only-fixed = true):

| Package | Installed | Fixed in | Type | Vulnerability | Severity |
|---|---|---|---|---|---|
| `go.opentelemetry.io/otel/sdk` | v1.39.0 | 1.40.0 | go-module | GHSA-9h8m-3fm2-qjrq | High |
| `go.opentelemetry.io/otel/sdk` | v1.39.0 | 1.43.0 | go-module | GHSA-hfvc-g4fc-pqhx | High |

All other 16 repo scans passed (techfolk-cms, techweb-3.0, skill-bench, julefolk, techfolklekene, plugin-marketplace, link-tracker, helen.ai, notion-webcrm-export, fagprat, tf-events-calendar, .github, webcrm-bot, tfs-little-helper, webcrm-mcp, klubbhuset).

## 3. Important context: the fix is already on `main`

State of `Techfolk-AS/doffin-bot` right now:

- HEAD on `main`: `df7e3bcce40ff4f1eccc71de3e7820434874d7b5` (2026-04-29T08:35:20Z)
- Commit message: `fix: upgrade go.opentelemetry.io/otel/sdk to v1.43.0 (#8)`
- `src/go.mod` requires `go.opentelemetry.io/otel/sdk v1.43.0` (indirect) — covers both fix versions.
- `src/go.sum` carries `v1.43.0` entries only (no `v1.39.0`).
- No open PRs on the repo.
- The next Grype Org Scan run **`25098987272`** (workflow_dispatch on `main`, 2026-04-29T08:35:47Z) completed with status **success**.

The failure flagged by `25098697388` was remediated ~6 minutes after the scan, and the next scan confirmed clean. **No further action required.** The plan below is what the auto-fixer would have done if `main` were still vulnerable.

## 4. Dry-run remediation plan (hypothetical — would only run if main still vulnerable)

### Repo: `Techfolk-AS/doffin-bot` (Go module under `src/`)

1. Pre-flight: `gh pr list --repo Techfolk-AS/doffin-bot --state open` — currently empty, so no skip.
2. Branch: `git checkout -b fix/grype-otel-sdk-v1.43`
3. Bump dependency:
   - `cd src`
   - `go get go.opentelemetry.io/otel/sdk@v1.43.0` (fixes both GHSAs in one shot)
   - `go mod tidy`
4. Verify: `go build ./...`, run `task test` if defined in `Taskfile.yaml` else `go test ./...`. Optionally re-run `grype dir:. --fail-on high --only-fixed`.
5. Commit (conventional): `fix: bump go.opentelemetry.io/otel/sdk to v1.43.0` with body listing GHSA-9h8m-3fm2-qjrq, GHSA-hfvc-g4fc-pqhx, and a link to run `25098697388`.
6. Push + PR (skipped under DRY RUN):
   - Would run: `git push -u origin fix/grype-otel-sdk-v1.43`
   - Would run: `gh pr create --base main --title "fix: bump go.opentelemetry.io/otel/sdk to v1.43.0" --body <…>`
7. Skip rules honoured: would skip if an open PR for this fix already existed; none does.

### Other repos
No other repos failed this run; nothing else planned.

## 5. Summary table — what would be opened

| Repo | Branch | Files touched | PR title | Outcome |
|---|---|---|---|---|
| Techfolk-AS/doffin-bot | `fix/grype-otel-sdk-v1.43` | `src/go.mod`, `src/go.sum` | `fix: bump go.opentelemetry.io/otel/sdk to v1.43.0` | Would open, but already fixed on main → recommend skip |

## 6. Recommendation

- Do **not** open a PR; the vulnerability is already remediated on `main` (`df7e3bc`) and the subsequent scan run `25098987272` is green.
- Optional follow-up: the failed run was triggered from `chore/node-24-action-bumps`. Before merging that branch, rebase it onto fixed `main` so the next scan from it doesn't re-flag the same finding.
