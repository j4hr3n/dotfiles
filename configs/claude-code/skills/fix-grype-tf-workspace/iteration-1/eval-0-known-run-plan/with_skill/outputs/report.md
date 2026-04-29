# Grype auto-fix plan (DRY RUN)

- **Source run:** [Techfolk-AS/.github run 25098697388](https://github.com/Techfolk-AS/.github/actions/runs/25098697388)
- **Created at:** 2026-04-29T08:28:45Z (head branch `chore/node-24-action-bumps`)
- **Run conclusion:** failure
- **Mode:** dry-run — no branches pushed, no PRs opened, no commits made.

## Affected repos (Step 1)

Filtered the run's jobs to those whose name starts with `Scan: ` and whose conclusion is `failure`:

| Job | Repo | Job ID |
| --- | --- | --- |
| `Scan: doffin-bot` | `Techfolk-AS/doffin-bot` | 73541933391 |

All other 17 `Scan: *` jobs in this run succeeded. Only one repo is affected.

## Vulnerabilities per repo (Step 2)

### doffin-bot

Parsed from the Grype log table:

| Package | Installed | Fixed in | Type | Advisory | Severity |
| --- | --- | --- | --- | --- | --- |
| `go.opentelemetry.io/otel/sdk` | `v1.39.0` | `1.40.0` | `go-module` | GHSA-9h8m-3fm2-qjrq | High |
| `go.opentelemetry.io/otel/sdk` | `v1.39.0` | `1.43.0` | `go-module` | GHSA-hfvc-g4fc-pqhx | High |

Highest `fixed_in` per package: **`go.opentelemetry.io/otel/sdk` -> `v1.43.0`** (covers both advisories in a single bump).

## Plan per repo (Step 3 + Step 4 plan)

### doffin-bot — SKIP

- **Ecosystem:** Go (`go-module`).
- **Module dir:** `src/` (only `go.mod` is at `~/dev/doffin-bot/src/go.mod`).
- **Branch that would be used:** `fix/grype-otel-sdk-2026-04-29`.
- **Exact bump command (would-run, but skipped):**
  ```bash
  cd ~/dev/doffin-bot/src \
    && go get go.opentelemetry.io/otel/sdk@v1.43.0 \
    && go mod tidy \
    && go build ./...
  ```
  `otel/sdk` is listed as `// indirect` in `go.mod`, so after `go get`/`go mod tidy` it would either remain indirect (pinned via `require ... // indirect`) or be promoted if a direct import was added — no extra steps needed beyond the one-liner above.

- **Skip reason (Step 5):** A merged PR already addresses this exact `(package, fixed_in)` pair, **and** the next scheduled scan after the merge already turned green:
  - PR [Techfolk-AS/doffin-bot#8](https://github.com/Techfolk-AS/doffin-bot/pull/8) — `fix: upgrade otel/sdk to v1.43.0 (GHSA-hfvc-g4fc-pqhx, GHSA-9h8m-3fm2-qjrq)` — branch `fix/otel-sdk-cve-2026-hfvc`, **merged 2026-04-29T08:35:20Z**.
  - PR [Techfolk-AS/doffin-bot#7](https://github.com/Techfolk-AS/doffin-bot/pull/7) — `fix: upgrade go.opentelemetry.io/otel to v1.41.0 (GHSA-mh2q-q3fh-2475)` — merged 2026-04-27 (related parent module bump, not the same package, but on the same advisory cluster).
  - Confirmed locally: `~/dev/doffin-bot/src/go.mod` line 38 reads `go.opentelemetry.io/otel/sdk v1.43.0 // indirect` on `origin/main` (HEAD `df7e3bc`).
  - Confirmed via `gh run list`: the next Grype Org Scan run [`25098987272`](https://github.com/Techfolk-AS/.github/actions/runs/25098987272) at 2026-04-29T08:35:47Z (immediately after PR #8 merged) **succeeded**. The failing run 25098697388 is therefore stale.

  Per Step 5 / loop-mode "Idempotency" rule, do not open a duplicate PR.

- **What I would have committed (diff hint), if no merged fix existed:**
  ```diff
  --- a/src/go.mod
  +++ b/src/go.mod
  @@
  -	go.opentelemetry.io/otel/sdk v1.39.0 // indirect
  +	go.opentelemetry.io/otel/sdk v1.43.0 // indirect
  ```
  …plus the corresponding hash updates in `src/go.sum`. No source-code changes required (indirect bump only).

## Per-repo summary

| Repo | Status | Package | Target version | Reason |
| --- | --- | --- | --- | --- |
| `doffin-bot` | **skipped** | `go.opentelemetry.io/otel/sdk` | `v1.43.0` | Already fixed on `main` by merged PR #8; next scan (run 25098987272) is green. |

### Tally

- opened: 0
- would-open: 0
- skipped: 1 (`doffin-bot`)
- failed: 0

## Notes / verification done

- `gh run view 25098697388 --json jobs` -> exactly one failed `Scan: *` job (`doffin-bot`).
- `gh run view --job 73541933391 --log` -> two GHSA rows for `go.opentelemetry.io/otel/sdk`, fixed_in 1.40.0 and 1.43.0; highest is 1.43.0.
- `gh pr list --repo Techfolk-AS/doffin-bot --state all` -> PR #8 merged 2026-04-29T08:35:20Z bumps the same package to v1.43.0.
- `git log origin/main` in `~/dev/doffin-bot` -> HEAD `df7e3bc` (`fix: upgrade go.opentelemetry.io/otel/sdk to v1.43.0 (#8)`).
- `grep otel src/go.mod` -> `go.opentelemetry.io/otel/sdk v1.43.0 // indirect`.
- `gh run list --workflow "Grype Org Scan"` -> the next run (25098987272) on `main` after the merge passed.

No mutating commands were run. No branches pushed. No PRs created.
