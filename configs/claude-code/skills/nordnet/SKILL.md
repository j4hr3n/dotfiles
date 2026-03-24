# /nordnet — Interact with Nordnet trading portfolio

## Trigger

The user runs `/nordnet [command]` or asks about their Nordnet portfolio, accounts, or positions.

## Inputs

- `$ARGUMENTS`: Optional subcommand and flags. Supported commands:
  - (empty) or `portfolio` — Show full portfolio overview
  - `status` — Check configuration and session status
  - `login` — Authenticate and create session
  - `setup` — First-time setup (key generation + API registration guide)
  - `refresh` — Refresh the current session
  - `accounts` — List accounts only
  - `positions` — Show positions only
  - `ledgers` — Show cash balances only

## Instructions

You are executing the `/nordnet` skill to interact with the Nordnet trading API. All scripts are located at `~/.claude/tools/nordnet/`.

The base command to run scripts is:
```
bun run --cwd ~/.claude/tools/nordnet scripts/<name>.ts
```

---

### Determine the command

Parse `$ARGUMENTS` to determine which action to take:

| Input | Action |
|-------|--------|
| (empty), `portfolio` | Run `scripts/portfolio.ts` |
| `status` | Run `scripts/status.ts` |
| `login` | Run `scripts/login.ts` |
| `setup` | Run `scripts/setup.ts` |
| `refresh` | Run `scripts/refresh.ts` |
| `accounts` | Run `scripts/portfolio.ts --accounts` |
| `positions` | Run `scripts/portfolio.ts --positions` |
| `ledgers` | Run `scripts/portfolio.ts --ledgers` |

---

### Before running any command (except `setup` and `status`)

First check if the tool is configured:
```bash
bun run --cwd ~/.claude/tools/nordnet scripts/status.ts
```

- If exit code is **1** and the output says "Not configured": guide the user through setup by running `scripts/setup.ts`
- If exit code is **1** and the output says "no active session": run `scripts/login.ts` first, then proceed
- If exit code is **0**: proceed with the requested command

---

### Running commands

Execute the appropriate script and present the output to the user:

```bash
bun run --cwd ~/.claude/tools/nordnet scripts/portfolio.ts
```

For JSON output (useful for further processing):
```bash
bun run --cwd ~/.claude/tools/nordnet scripts/portfolio.ts --json
```

---

### Error handling

- **Login failures**: Check that the API key is correct and the public key is registered. Suggest running `scripts/setup.ts`.
- **Session expired during command**: The scripts auto-refresh sessions. If it still fails, suggest `scripts/login.ts`.
- **Network errors**: Suggest checking internet connectivity and trying again.
- **"Not configured"**: Guide the user to run setup.

---

### Output formatting

When presenting portfolio data to the user:
- Keep the tabular format from the script output
- Highlight significant gains/losses if the data is clear
- For JSON output mode, you can process and summarize the data as needed
- All monetary values are in the currency returned by the API (typically NOK)
