# Grype Org Scan Fix Plan — run 25098697388

**Run:** https://github.com/Techfolk-AS/.github/actions/runs/25098697388
**Trigger:** workflow_dispatch on branch `chore/node-24-action-bumps`
**Run head SHA (in `.github`):** `30f25456ac7d9cccde9b87021d177f1436b071a9`
**Started:** 2026-04-29T08:28:45Z — finished 08:29:53Z

## Scan summary

18 repos scanned. **17 passed, 1 failed.**

| Repo | Result |
|------|--------|
| techfolk-cms | pass |
| techweb-3.0 | pass |
| skill-bench | pass |
| julefolk | pass |
| techfolklekene | pass |
| plugin-marketplace | pass |
| link-tracker | pass |
| helen.ai | pass |
| notion-webcrm-export | pass |
| fagprat | pass |
| tf-events-calendar | pass |
| .github | pass |
| webcrm-bot | pass |
| tfs-little-helper | pass |
| webcrm-mcp | pass |
| **doffin-bot** | **FAIL** |
| klubbhuset | pass |

## Affected repo & vulnerabilities

### `Techfolk-AS/doffin-bot`

Ecosystem: Go (`src/go.mod`, module `github.com/Techfolk-AS/doffin`).

Grype findings at scan-time commit `b9d7505`:

| Package | Installed | Fix version | GHSA | Severity |
|---------|-----------|-------------|------|----------|
| `go.opentelemetry.io/otel/sdk` | v1.39.0 | **1.40.0** | GHSA-9h8m-3fm2-qjrq | High |
| `go.opentelemetry.io/otel/sdk` | v1.39.0 | **1.43.0** | GHSA-hfvc-g4fc-pqhx | High |

Both findings are the same package; bumping to v1.43.0 resolves both.

#### Bump command (run from repo root)

```bash
cd src
go get go.opentelemetry.io/otel/sdk@v1.43.0
go mod tidy
```

Optional consistency bump for siblings to keep the otel module set aligned:

```bash
cd src
go get \
  go.opentelemetry.io/otel@v1.43.0 \
  go.opentelemetry.io/otel/metric@v1.43.0 \
  go.opentelemetry.io/otel/trace@v1.43.0 \
  go.opentelemetry.io/otel/sdk@v1.43.0 \
  go.opentelemetry.io/otel/sdk/metric@v1.43.0
go mod tidy
```

#### Existing-fix-PR check — SKIP

- PR #7 (MERGED 2026-04-27T08:22:26Z) — `fix: upgrade go.opentelemetry.io/otel to v1.41.0 (GHSA-mh2q-q3fh-2475)`
- PR #8 (MERGED 2026-04-29T08:35:20Z) — `fix: upgrade otel/sdk to v1.43.0 (GHSA-hfvc-g4fc-pqhx, GHSA-9h8m-3fm2-qjrq)`

The failing scan ran 08:28:45Z–08:29:53Z. **PR #8 merged ~6 minutes after the scan finished**, so the run captured a stale pre-fix tree. Current `main` HEAD `df7e3bc` already pins `go.opentelemetry.io/otel/sdk v1.43.0` in `src/go.mod`.

No open fix PRs; no new fix PR needed.

## Per-repo summary

| Repo | Status | Action |
|------|--------|--------|
| Techfolk-AS/doffin-bot | **skipped** | Already fixed on `main` via merged PR #8. Re-running the org scan should be green. |
| 17 others | pass | No action. |

## Structured outcome

```yaml
opened: []
would-open: []
skipped:
  - repo: Techfolk-AS/doffin-bot
    reason: >-
      Vulnerability already fixed on main by merged PR #8
      (otel/sdk -> v1.43.0). Scan ran against a pre-fix commit;
      the next scheduled scan should pass.
    finding:
      package: go.opentelemetry.io/otel/sdk
      installed: v1.39.0
      fix-version: v1.43.0
      ghsas: [GHSA-9h8m-3fm2-qjrq, GHSA-hfvc-g4fc-pqhx]
    related-prs:
      - {number: 7, state: MERGED, title: "fix: upgrade go.opentelemetry.io/otel to v1.41.0"}
      - {number: 8, state: MERGED, title: "fix: upgrade otel/sdk to v1.43.0"}
failed: []
```

## Recommendation

1. No new branches/PRs required. Re-trigger the Grype Org Scan workflow_dispatch so the next run picks up `df7e3bc` — it should be green.
2. If a future scan flags `otel/sdk` again, use the bump command above on a fresh branch off `main`.
