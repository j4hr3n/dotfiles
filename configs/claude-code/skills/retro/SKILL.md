# /retro — Process improvement after any work session

## Trigger

The user runs `/retro` (no arguments). Reviews the most recent work in the current session and proposes improvements to skills, config, and memory.

## Inputs

None — context is gathered automatically from the conversation, git history, and session artifacts.

## Instructions

You are executing the `/retro` skill. Follow these steps strictly in order.

---

### Step 1: Gather context

Collect information about the most recent work. Not all sources will be relevant every time — adapt to what actually happened in the session.

1. **Conversation context:**
   Review the current conversation to understand what was done. This may include:
   - Code implementation (feature work, bug fixes, refactoring)
   - Code reviews (PR reviews, feedback)
   - Research and exploration
   - Issue creation or triage
   - Configuration changes
   - Any other workflow

   This is the primary source of truth for what happened — git history alone may not capture review-only or research-only sessions.

2. **Git history** (if code was changed):
   ```bash
   git log --oneline -20
   git diff main...HEAD --stat
   ```
   Understand what changed and on which branch. Skip if the session didn't involve code changes.

3. **Plan files:** Check `.claude/plans/` in the project root for any plan files from the session.

4. **Project memory:** Read `~/.claude/projects/<project>/memory/MEMORY.md` for existing learnings.

5. **Current skills and config:**
   - Scan `~/.claude/skills/*/SKILL.md` for all active skills.
   - Read `~/.claude/CLAUDE.md` (global) and any project-level `CLAUDE.md`.

---

### Step 2: Evaluate process

For each area, assess what worked and what caused friction during the recent work:

- **Skills** (`~/.claude/skills/*/SKILL.md`) — Did the workflow instructions match reality? Were steps missing, wrong, unnecessary, or in the wrong order?
- **CLAUDE.md** (global + project) — Are there new conventions, patterns, or constraints that should be documented? Are existing instructions outdated?
- **Project memory** — Are there learnings missing from `MEMORY.md` that would help future work? Are existing entries still accurate?
- **Settings & config** — Did permissions, env vars, model settings, or sandbox configuration cause friction?

---

### Step 3: Propose changes

Present a summary to the user with these sections:

1. **What worked well** — Keep these as-is.
2. **What caused friction** — Describe the problem and its impact.
3. **Proposed edits** — For each proposed change, show:
   - The target file path
   - What to add, modify, or remove
   - Why this change helps

**Do NOT apply any changes yet.** Wait for the user to approve, modify, or reject each proposal.

If there are no meaningful improvements to suggest, say so — not every session warrants changes.

---

### Step 4: Apply approved changes

Edit the relevant files based on user approval:

- Skill files (`~/.claude/skills/*/SKILL.md`)
- Config files (`CLAUDE.md`, global or project-level)
- Memory files (`MEMORY.md`)
- Any other config files the user approves

Commit changes if they are non-trivial, using branch prefix `chore/` (e.g., `chore/retro-update-solve-skill`).

---

### Step 5: Log the retro

Append a dated entry to `~/.claude/retro/log.md` (create the file and directory if they don't exist):

```markdown
## YYYY-MM-DD — <short description>
- **Trigger**: What work prompted this retro
- **Changes made**: Which files were updated and why
- **Deferred**: Ideas noted but not acted on yet
```
