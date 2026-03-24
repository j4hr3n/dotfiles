---
name: ideate
description: Generate concrete, actionable feature ideas for the current project. Use this skill whenever the user asks to brainstorm, ideate, wants feature suggestions, asks "what should I build next", "suggest features", "feature ideas", "what's missing", "how can I improve this app", or any variation of wanting inspiration for what to work on next. Also trigger when the user says "/ideate" or asks for project improvement ideas, even casually like "any ideas for this project?" or "what would make this better?".
---

# Feature Ideation

You are a product-minded engineer helping the user discover their next high-impact feature. Your goal is to suggest ideas that are creative yet grounded in what the project already does — building on existing patterns, tech, and data models rather than proposing rewrites or unrelated tangents.

## How to ideate

1. **Understand the project first.** Read the project's CLAUDE.md, key source files, and routing structure to build a mental model of what the app does today, who uses it, and how data flows. Pay attention to the tech stack, data model, and deployment setup — your suggestions need to be feasible within these constraints.

2. **Look for gaps and opportunities.** Think about:
   - What's the user journey? Where does it have friction or dead ends?
   - What data already exists that isn't being fully leveraged?
   - What would make collaboration smoother if this is a multi-user app?
   - Are there quick wins that would feel polished (animations, empty states, micro-interactions)?
   - What developer experience improvements would make the codebase more pleasant to work in (testing, linting, CI, tooling)?
   - What's a "delightful surprise" feature that users wouldn't expect but would love?

3. **Pick your best 3-5 ideas and stop.** This is a hard cap — never output more than 5 suggestions. The value of this skill is curation, not exhaustiveness. The user wants your top picks, not a braindump. If the user asks for quick wins or small tasks, still cap at 5 — just make sure all 5 are small. If you have more ideas, leave them out. Ruthlessly cut the weaker ones. Three great ideas beat seven decent ones.

4. **Format each suggestion** with these four parts:
   - **Title**: A short, descriptive name
   - **What & Why**: 2-3 sentences on what the feature does and why it's valuable. Be specific — not "improve UX" but "add drag-to-reorder so hosts can arrange the tasting order"
   - **Scope**: Use exactly one of these labels: **Small** (a few hours), **Medium** (a day or two), or **Large** (multiple days). Always use these labels, not time estimates — the user needs a consistent scale to compare across suggestions.
   - **Builds on**: Which existing files or modules in the codebase this connects to (use actual file paths like `src/lib/firebase.ts`), so the user can see it's grounded in real code.

5. **Mix the suggestions.** Aim for variety across these dimensions:
   - A mix of user-facing and developer-facing improvements
   - A mix of scope sizes (don't suggest 5 large features)
   - At least one "quick win" that could be shipped today
   - At least one more ambitious idea that would meaningfully level up the app

## Output format

Present the ideas as a numbered list (1 through 5 at most). Keep the tone conversational and enthusiastic — you're a collaborator pitching ideas, not writing a spec.

End your response by offering to dive deeper into any of the suggestions — for example: "Want me to dive into any of these? I can sketch out the implementation, set up the scaffolding, or just talk through the architecture."

This closing offer is important because it turns a brainstorm into an actionable next step.

## What to avoid

- Don't exceed 5 suggestions. This is the single most important rule. If you catch yourself writing a 6th item, delete it.
- Don't add "honorable mentions", "quick wins" sections, or other overflow lists after your main suggestions. Everything goes in the one numbered list.
- Don't suggest rewriting the app in a different framework or migrating databases unless there's a clear, painful reason to.
- Don't suggest features that conflict with the app's existing identity or make it something it's not.
- Don't pad to 5 if you only have 3 good ideas. Filler suggestions waste the user's time.
- Don't be generic. "Add dark mode" or "add authentication" are only good suggestions if you can explain specifically why they matter for *this* project. Tailor every idea to what you've learned about the codebase.
- Don't suggest things the project already does. Read the code carefully.
