---
name: recon
description: "Codebase reconnaissance using git history analysis. Builds a health report of any codebase before you start working on it — file churn hotspots, contributor bus-factor, bug clusters, project momentum, and firefighting patterns. Use this skill whenever the user asks to get to know a codebase, understand a repo, do a codebase overview, audit a project, onboard to a new codebase, or wants to understand what's going on in a repo before diving in. Also trigger when the user asks about code health, churn, bus factor, hotspots, or codebase risk."
---

# /recon — Codebase reconnaissance

## Trigger

The user wants to understand a codebase before working on it. They might say things like "give me an overview of this repo", "what's going on in this codebase", "help me onboard", "what should I know before working here", or just `/recon`.

## Inputs

- `$ARGUMENTS` (optional): A path to a git repository, or a specific area of focus (e.g., "focus on the backend", "just the last 6 months"). If empty, use the current working directory.

## Instructions

You are running a codebase reconnaissance. The goal is to give the user a clear, honest picture of what they're walking into — where the risk is, who knows what, what's been getting attention, and what's been getting patched over. This is the kind of briefing you'd want on your first day at a new job.

Run the analysis steps below, then synthesize everything into a single report. Do not just dump raw command output — interpret it, connect the dots, and tell the story.

---

### Step 1: Orient

Before running any commands, get the basics:

```bash
# What is this project?
head -80 README.md 2>/dev/null
# How big is the repo?
git rev-list --count HEAD
# How old is the repo?
git log --reverse --format='%ai' | head -1
# What's the primary language?
git ls-files | sed 's/.*\.//' | sort | uniq -c | sort -nr | head -10
```

This gives you the frame for interpreting everything that follows. A 50-commit hobby project and a 50,000-commit enterprise monorepo need very different readings.

### Step 2: File churn — where the risk lives

```bash
git log --format=format: --name-only --since="1 year ago" | sort | uniq -c | sort -nr | head -20
```

The 20 most-changed files in the past year. High churn often means code that's fragile, poorly understood, or doing too much. Research from Microsoft found that churn-based metrics predict defects more reliably than complexity metrics alone.

When interpreting, consider:
- Are these config files (normal churn) or core logic files (potential problem)?
- Do any show up in the bug clustering step too? That's the real danger zone — high churn AND high bugs.
- Are lock files or generated files polluting the list? Filter those out mentally.

### Step 3: Contributor distribution — bus factor

```bash
git shortlog -sn --no-merges
```

Who built this thing, and is that knowledge still around?

Look for:
- **Single-contributor dominance**: One person with 60%+ of commits means critical knowledge lives in one head.
- **Active vs. departed contributors**: Cross-reference with recent activity. Someone with 40% of all-time commits but zero in the last 6 months is a knowledge gap.
- **Squash-merge distortion**: If the team uses squash merges, this list shows who clicks the merge button, not who writes the code. Note this caveat if you see very few contributors in a project that seems too large for a tiny team.

```bash
# Recent activity check — who's been active lately?
git shortlog -sn --no-merges --since="6 months ago"
```

### Step 4: Bug clustering — where things break

```bash
git log -i -E --grep="fix|bug|broken|patch|issue" --name-only --format='' | sort | uniq -c | sort -nr | head -20
```

Files that keep appearing in bug-fix commits are the ones that repeatedly break and get band-aid fixes. Compare this list with the churn list from Step 2 — files appearing on both are maximum risk.

Note: this depends on the team writing decent commit messages. If the log is full of "update" and "wip", say so — the signal is weak.

### Step 5: Project momentum — the trajectory

```bash
git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c
```

Monthly commit counts over the repo's life. This is the heartbeat chart.

Look for:
- **Sudden drops**: Team departures, reorgs, or loss of interest.
- **Seasonal patterns**: Some projects have release cycles — batch-shipping rather than continuous deployment.
- **Recent trend**: Is activity increasing, stable, or declining? This tells you whether you're joining an active effort or inheriting something on life support.

### Step 6: Firefighting — deployment trust

```bash
git log --oneline --since="1 year ago" | grep -iE 'revert|hotfix|emergency|rollback|urgent'
```

How often does the team revert changes or push emergency fixes? Frequent reverts suggest:
- Insufficient testing before deploy
- Missing or unreliable staging environments
- Changes making it to production that shouldn't have

A handful per year is normal. Multiple per month is a systemic issue.

### Step 7: Synthesize the report

Combine everything into a structured report. The format:

```
# Codebase Recon: [project name]

## At a glance
- Age / size / primary language / number of contributors
- One-sentence health summary

## Risk hotspots
Files with high churn AND bug-fix activity. These are the ones to be
most careful around. Explain what they are and why they're hot.

## Team & knowledge
Bus factor assessment. Who are the key contributors, who's still
active, where the knowledge gaps are.

## Momentum
Is this project accelerating, cruising, or declining? Any notable
inflection points and likely explanations.

## Stability
Firefighting frequency. How often do things go wrong in production?

## Recommendations
Based on everything above, what should the user pay attention to?
What should they be careful with? Where might they want to dig deeper?
```

Adapt the sections to what's actually interesting. If the bus factor is fine, keep it brief. If there's a clear danger zone in the churn analysis, spend more time on that. The user wants signal, not ceremony.
