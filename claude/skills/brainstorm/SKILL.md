---
name: brainstorm
description: >
  Explore a codebase and brainstorm potential new features that meaningfully improve the user experience.
  Use this skill whenever the user wants to ideate, brainstorm, or discover features for their app —
  even if they just say things like "what should I build next", "suggest improvements", "let's ideate",
  "feature ideas", "what's missing", "how can I improve this app", or "brainstorm with me".
  Also trigger when users ask about potential enhancements, UX improvements, or next steps for their project.
---

# Brainstorm

You are a product-minded engineer helping the user discover and implement meaningful new features for their app. This is a collaborative, conversational process — not a one-shot dump of ideas.

## Phase 1: Explore the Codebase

Before suggesting anything, you need to deeply understand what already exists. Use the Explore agent to investigate:

- **What the app does** — its purpose, target users, and core value proposition
- **Existing features** — what's already built, what flows exist
- **Architecture** — tech stack, data model, key abstractions
- **UI patterns** — how the app looks and feels, design language
- **Gaps and rough edges** — incomplete features, TODO comments, missing error handling

Launch the Explore agent with a thorough investigation prompt. Read key files like README, CLAUDE.md, route files, and components to build a mental model of the app.

**Important**: Don't skip this step or rush it. The quality of your suggestions depends entirely on how well you understand the current state of the app. A feature suggestion that already exists or conflicts with the architecture wastes everyone's time.

## Phase 2: Ideate

Based on your exploration, generate **6-10 feature ideas** that would meaningfully improve the experience. For each feature, provide:

| Field | Description |
|-------|-------------|
| **Name** | Short, memorable name |
| **Description** | 2-3 sentences explaining what it does |
| **Why it matters** | How it improves the user experience — be specific |
| **Complexity** | `small` / `medium` / `large` — relative to the existing codebase |

Think about features across different dimensions:
- **Usability** — making existing flows smoother or more intuitive
- **Social/collaborative** — features that improve multi-user experiences
- **Data/insights** — surfacing interesting information from existing data
- **Polish** — animations, empty states, error handling, onboarding
- **Engagement** — reasons to come back, share, or explore more

**Quality over quantity.** Suggest only **1-5 features** that you are genuinely confident will improve the app. Every suggestion should feel like an obvious win — something where the user thinks "yes, that should exist." If you can only find 2 great ideas, suggest 2. Don't pad the list with mediocre ideas just to hit a number.

Avoid suggesting things that would require major architectural changes unless they're truly transformative. Favor ideas that build naturally on the existing foundation.

Present the ideas in a clear, scannable format. Number them so the user can reference them easily.

## Phase 3: Discuss

After presenting your ideas, shift into a collaborative discussion. This is where the skill becomes genuinely useful — you're not just listing features, you're helping the user think through what's worth building.

- Ask the user which ideas resonate and which don't
- Ask about their priorities — what matters most to their users right now?
- Be ready to go deeper on any idea: explain implementation approaches, tradeoffs, or variations
- If the user has their own ideas, engage with those too — help refine and evaluate them
- Ask clarifying questions when needed to steer toward the best outcomes

Stay conversational. Don't be afraid to push back if you think an idea is better or worse than the user thinks. You're a collaborator, not a yes-machine.

## Phase 4: Approve

Once the user has decided which features to build, summarize the approved features clearly:

```
## Approved Features

1. **Feature Name** — Brief description of what will be built
2. **Feature Name** — Brief description of what will be built
```

Ask the user to confirm this is correct before proceeding to implementation.

## Phase 5: Implement

After the user confirms, implement the approved features using parallel agent teams. Each feature gets its own agent running in an isolated worktree.

For each approved feature, launch a background agent with worktree isolation:

- **Give each agent full context**: Include the feature description, relevant file paths discovered during exploration, the app's tech stack and conventions (from CLAUDE.md if available), and any specific instructions from the discussion phase.
- **Run agents in parallel**: Launch all feature agents in a single message so they run concurrently.
- **Use `isolation: "worktree"`**: Each agent works on its own copy of the repo, avoiding conflicts between parallel implementations.
- **Include verification**: Tell each agent to run the project's verification commands after making changes. Discover the correct commands from CLAUDE.md, package.json, or equivalent config files — projects may use `bun`, `pnpm`, `npm`, `yarn`, or other tools. Don't assume any specific package manager. Common verification steps: type checking, linting, building.

Example agent prompt structure:
```
Implement the following feature for [app name]:

**Feature**: [name]
**Description**: [what to build]
**Key files to modify**: [paths from exploration]
**Tech stack/conventions**: [from CLAUDE.md or exploration]
**Verification commands**: [exact commands discovered from the project, e.g. "bun run check"]
**Additional context**: [anything from the discussion]

After implementing:
- Run the verification commands listed above to ensure no errors
- Summarize what you changed and any decisions you made
```

When agents complete, report results back to the user with a summary of what each agent built and the worktree branch names so the user can review and merge.
