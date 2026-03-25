---
name: security-scan-tf
description: Deep security scan of all active repos in the Techfolk-AS GitHub org, looking for malicious code patterns, hardcoded secrets, obfuscated code, backdoors, and suspicious behavior. Use this skill whenever the user asks to scan Techfolk repos, check org security, audit code for malicious patterns, or mentions "/security-scan-tf". Also triggers for questions like "is our code safe", "any suspicious code in our repos", or "security audit". This is specific to the Techfolk-AS GitHub organization.
---

# Security Scan — Techfolk-AS

Performs a deep scan of all active (non-archived) repositories in the **Techfolk-AS** GitHub organization, looking for malicious code patterns. This is not a dependency vulnerability scan (that runs separately via trivy) — this focuses on code-level threats: backdoors, data exfiltration, obfuscated payloads, hardcoded secrets, and suspicious behavior.

## How It Works

1. List all non-archived repos in Techfolk-AS via `gh repo list`
2. Dispatch one subagent per repo to scan in parallel (use `isolation: "worktree"` is not needed — repos are cloned to temp dirs)
3. Each subagent shallow-clones its repo, scans for malicious patterns, and returns findings
4. Aggregate results into a single report printed to the terminal

## Step 1: List Repos

```bash
gh repo list Techfolk-AS --limit 100 --no-archived --json name,primaryLanguage,pushedAt
```

Only scan non-archived repos.

## Step 2: Dispatch Parallel Scanners

For each repo, spawn a subagent with this prompt structure. Launch all subagents in a single message so they run concurrently.

Each subagent should:

1. **Clone** the repo to a temp directory (shallow clone for speed):
   ```bash
   REPO_DIR=$(mktemp -d)
   gh repo clone Techfolk-AS/<repo-name> "$REPO_DIR" -- --depth 1
   ```

2. **Scan** the codebase for every pattern category below. Use Grep with the patterns listed, scoping to source files only (skip `node_modules/`, `dist/`, `build/`, `.next/`, `vendor/`, `*.min.js`, `*.min.css`, lock files, and binary files). When Grep finds hits, read surrounding context (10-20 lines) to determine if the match is genuinely suspicious or benign.

3. **Return** a structured summary: repo name, findings per category (with file paths and line numbers), and a severity rating.

## Pattern Categories

These are the categories of suspicious patterns to scan for. For each category, the subagent should grep for the listed patterns, then read context around each match to classify it as **suspicious**, **worth noting**, or **benign** (and explain why).

### 1. Dynamic Code Execution
Why it matters: attackers use dynamic execution to run payloads that aren't visible in static source.

Patterns to grep for (scope to source files, not configs):
- `eval(` — dynamic JS/Python execution
- `new Function(` — JS function constructor
- `exec(` / `execSync(` — shell execution in Node
- `child_process` — Node process spawning
- `spawn(` / `spawnSync(` — process spawning
- `vm.runInContext` / `vm.runInNewContext` — Node VM execution
- `import(` with variable arguments (not static string imports)
- `require(` with variable arguments
- `subprocess` / `os.system` / `os.popen` — Python shell execution
- `exec.Command` — Go shell execution

Context that makes these **benign**: build tools (webpack, vite config), test utilities, well-known packages doing expected things, clearly commented developer tooling.

Context that makes these **suspicious**: executed strings constructed from network input, base64-decoded payloads, strings assembled from character codes, obfuscated arguments.

### 2. Obfuscated Code & Encoded Payloads
Why it matters: legitimate code is readable. Obfuscation in source (not minified bundles) hides intent.

Patterns to grep:
- `atob(` / `btoa(` — base64 in browser JS
- `Buffer.from(` with `'base64'` — Node base64 decoding
- `String.fromCharCode` — character code assembly
- `\x[0-9a-f]{2}` sequences (long hex strings)
- `\\u00[0-9a-f]{2}` sequences (unicode escapes in source)
- `decodeURIComponent` with percent-encoded strings
- Very long single-line strings (>500 chars) in source files (not data fixtures)

Red flags: base64 strings decoded and then passed to `eval`/`Function`, character code arrays assembled into executable strings.

### 3. Hardcoded Secrets & Credentials
Why it matters: secrets in source code are both a vulnerability and a signal of poor practices (or intentional backdoor credentials).

Patterns to grep:
- `password\s*[:=]` (case-insensitive)
- `secret\s*[:=]` (case-insensitive)
- `api[_-]?key\s*[:=]` (case-insensitive)
- `token\s*[:=]` (case-insensitive) — but filter out common false positives like CSS tokens
- `PRIVATE KEY` — PEM private keys
- `ghp_[A-Za-z0-9]{36}` — GitHub personal access tokens
- `sk-[A-Za-z0-9]{20,}` — OpenAI/Stripe-style secret keys
- `AKIA[A-Z0-9]{16}` — AWS access key IDs
- Strings matching common secret patterns in `.env.example` files are fine (they're templates), but actual values in committed `.env` files are suspicious

### 4. Suspicious Network Activity
Why it matters: malicious code often exfiltrates data or fetches remote payloads.

Patterns to grep:
- `fetch(` / `axios` / `got(` / `request(` / `http.get` / `https.get` with hardcoded URLs that aren't well-known services
- `webhook` URLs that aren't the project's own (e.g., random Discord/Slack webhooks)
- `ngrok` / `localtunnel` / `serveo` URLs in source (tunnel services)
- IP addresses in source code (not configs): `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`
- DNS-over-HTTPS endpoints
- Connections to uncommon ports

Benign context: API clients calling documented services (Notion, Slack, WebCRM — these are expected for Techfolk projects), test fixtures, configuration templates.

### 5. Backdoor & Persistence Patterns
Why it matters: these patterns indicate intentional unauthorized access mechanisms.

Patterns to grep:
- Reverse shell patterns: `bash -i`, `nc -e`, `/dev/tcp/`
- Cron job creation in application code
- SSH key injection / `authorized_keys` manipulation
- File writes to system directories (`/etc/`, `/usr/`, `/tmp/` with execution)
- Environment variable manipulation that could affect other processes
- `postinstall` / `preinstall` scripts in package.json that do anything beyond build steps

### 6. Data Exfiltration Signals
Why it matters: code that reads sensitive files and sends them somewhere is a clear threat.

Patterns to grep:
- Reading `.env`, `.ssh/`, credentials files combined with network calls
- `fs.readFile` / `os.ReadFile` near network-sending code
- Serializing `process.env` or large environment dumps
- Cookie/session theft patterns: accessing `document.cookie` and sending it somewhere
- Sending data to URLs constructed from environment variables or decoded strings

### 7. Supply Chain Signals
Why it matters: tampered packages or unusual dependencies can be entry points.

Things to check:
- `package.json` install scripts (`preinstall`, `postinstall`, `prepare`) — do they run anything beyond normal build steps?
- Dependencies with typosquatting-like names (names very close to popular packages but slightly different)
- Pinned dependencies pointing to git URLs or tarballs instead of the registry
- `go.mod` replace directives pointing to unexpected locations

## Step 3: Aggregate Report

Collect all subagent results and produce a consolidated report. Structure it like this:

```
# Techfolk-AS Security Scan Report
**Date:** YYYY-MM-DD
**Repos scanned:** N active repos
**Repos skipped:** N archived repos

## Summary
- X repos clean
- Y repos with findings worth noting
- Z repos with suspicious findings

## Findings by Severity

### SUSPICIOUS (requires investigation)
List any genuinely suspicious findings here with repo name, file, line number, pattern category, and explanation of why it's suspicious.

### WORTH NOTING (not necessarily malicious but should be reviewed)
Show at most 3 findings here — pick the most interesting/unusual ones. If there are more,
add a line: "N additional minor findings omitted. Ask me to expand if you want the full list."

### CLEAN
List repos with no findings.

## Scan Details
For each repo with findings, show:
- Repo name and primary language
- Each finding with file path, line number, matched pattern, and context
```

If there are no suspicious findings across all repos, say so clearly — a clean report is a good report. Don't inflate minor things into concerns.

## Important Guidelines

- **False positives are worse than false negatives here.** A report full of noise trains people to ignore it. Only flag things as "suspicious" when context genuinely supports concern. Use the "worth noting" tier for things that are technically matches but probably fine.
- **Known-public keys are not findings.** Firebase client-side API keys, Google Maps API keys, public OAuth client IDs, and similar keys that are designed to be embedded in client code should not be flagged — not even as "worth noting". These are public by design and flagging them is noise. Only flag credentials that are meant to be secret (server-side API keys, private keys, tokens with write access, database passwords).
- **Read context before classifying.** Never flag a pattern match without reading the surrounding code. A `fetch()` call in an API client is normal. A `fetch()` call that sends `process.env` to an IP address is not.
- **Skip generated/vendored code.** Minified bundles, lock files, `node_modules/`, `dist/`, `build/` directories — skip them entirely.
- **Be specific.** "Found eval() in file X" is useless. "Found eval() on line 42 of src/utils.ts that executes a base64-decoded string received from an HTTP request" is actionable.
- **Keep the report scannable.** The "worth noting" section exists to surface things that deserve a second look, not to exhaustively list every pattern match. Cap it at 3 items per report. If there are more, mention the count and offer to expand on request.
