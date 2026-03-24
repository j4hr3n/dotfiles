# /retro — Improve skills and config after a work session

## Trigger

The user runs `/retro`. Reviews the current session and proposes improvements to skills and configuration so future sessions go smoother.

## Inputs

None — context comes from the conversation, git history, and project files.

## Instructions

You are executing the `/retro` skill. The goal is continuous improvement: each session should leave the tooling slightly better than it was. Follow these steps in order.

---

### Step 1: Gather context

Build a picture of what happened this session. Adapt to what's relevant — not every source matters every time.

1. **Conversation history** (primary source): Review what was done — implementation, reviews, research, config changes, debugging, etc. Git history alone misses review-only or research-only sessions.

2. **Git history** (if code changed):
   ```bash
   git log --oneline -20
   git diff main...HEAD --stat
   ```

3. **Plan files**: Check `.claude/plans/` for any plans created this session.

4. **Current skills and config**: Read all `SKILL.md` files in the skills directories, plus global and project-level `CLAUDE.md` files. You need to know what exists before you can improve it.

---

### Step 2: Identify friction and gaps

Compare what actually happened against what the skills and config expected. Focus on:

- **Skills**: Did instructions match reality? Were steps missing, wrong, redundant, or ordered badly? Did a skill fail to trigger when it should have?
- **CLAUDE.md** (global + project): Are there new conventions or constraints that should be captured? Are existing rules outdated or contradicted by practice?
- **Settings & config**: Did permissions, sandbox, or environment cause unnecessary friction?

The point is to find the delta between how work *should* flow and how it *actually* flowed.

---

### Step 3: Propose changes

Present a summary:

1. **What worked well** — Reinforce what doesn't need changing.
2. **What caused friction** — Describe the problem and its impact.
3. **Proposed edits** — For each change, show:
   - Target file path
   - What to add, modify, or remove
   - Why this improves future sessions

If nothing meaningful needs changing, say so. Not every session warrants edits.

**Do NOT apply changes yet.** Wait for the user to approve, modify, or reject each proposal.

---

### Step 4: Apply approved changes

Edit the approved files (skill files, `CLAUDE.md`, etc.).

Commit using branch prefix `chore/` (e.g., `chore/retro-improve-review-skill`).
