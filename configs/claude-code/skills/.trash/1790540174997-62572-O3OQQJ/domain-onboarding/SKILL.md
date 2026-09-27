---
name: domain-onboarding
description: Use this skill whenever someone at Aidn wants to get up to speed on a product or technical domain — such as CPR, Collab, Treatment, Case Handling, IAM, or Data Migrations. Triggers include requests like "onboard me to X", "help me understand the Y domain", "I'm new to Z, where do I start", or "give me a domain overview for X". Always use this skill when the goal is to investigate and synthesise onboarding material about an Aidn domain, regardless of the person's role. The skill drives a structured investigation across GitHub, Notion, and Slack before producing tailored output. Use this for any role — including Directors, C-level, and individual contributors.
---

# Domain Onboarding

## Purpose

Help any Aidn employee — regardless of role or seniority — get oriented in a domain faster. This skill drives an investigation across GitHub, Notion, and Slack, then synthesises what it finds into a tailored onboarding output based on the person's role and depth preference.

Do not assume any existing documentation is complete or well-structured. Investigate from first principles.

---

## Step 1: Gather context from the user

Before investigating, ask the following. Keep it conversational — ask all at once.

1. **Domain**: Which domain do you want to learn? (e.g. CPR, Collab, Treatment, Case Handling, IAM, Data Migrations)
2. **Role**: What is your role? Choose one:
   - Director (responsible for an area, e.g. Platform, Clinical, Product)
   - C-level (CTO, CPO, CCO, CEO)
   - Product (PM, PO)
   - Design (UX/Product Designer)
   - Engineering — Frontend
   - Engineering — Backend
   - Engineering — Fullstack
   - Engineering — Platform/Infrastructure
3. **Depth**:
   - For **leadership roles** (Director, C-level): default to strategic overview. Ask: *"Do you want to stay at strategic level, or also drill into technical or product detail?"* — and note which area to drill into if so.
   - For **engineering roles**: ask how deep they want to go technically:
     - Surface: architecture overview and key concepts, enough to navigate and contribute
     - Deep: actual services, data models, key files, integration patterns, and where things live in code
   - For **product/design roles**: depth is not asked — output is always calibrated to their function.
4. **Output format**: How do you want the output? Suggest these options but stay open to what the user asks for:
   - Notion page (structured document written to a Notion page for future reference)
   - Conversation (Claude walks you through it and you can ask follow-up questions)
   - Markdown summary (a shareable document in chat, easy to copy or paste elsewhere)
   - Or describe what you need — the format can be adapted

If the user does not specify a domain, ask before proceeding.

---

## Step 2: Investigate

Run the investigation across the relevant sources in parallel where possible. Use the connected MCP tools for Notion and Slack, and for engineering roles also GitHub.

**Source selection by role:**
- **Leadership (Director, C-level)**: Notion and Slack by default. Only include GitHub if they explicitly asked to drill into technical detail — and even then, stay at architecture and decision level (READMEs, ADRs, recent PR activity) rather than code-level detail.
- **Product / Design**: Notion and Slack only. Do not investigate GitHub, and do not ask the user about GitHub access — these roles do not need a GitHub account to onboard to a domain.
- **Engineering (any discipline)**: Notion, Slack, and GitHub.

### 2a. GitHub investigation (engineering roles, or leadership drilling into technical detail)

Skip this section entirely for Product, Design, and leadership roles who stayed at strategic depth.

Start with the `health` repo. Then decide whether other repos are relevant based on what you find (common candidates: infra repos, shared libraries, integration repos). If it's unclear, ask the user: *"I found these repos that look relevant: [list]. Should I include them all, or focus on specific ones?"*

Look for:
- Repo/folder structure relevant to the domain
- README files
- Key service entry points (e.g. main application files, API definitions)
- Data models (database schemas, entity definitions)
- Recent PRs mentioning the domain — useful for understanding what's changing
- Any architecture decision records (ADRs) or technical docs in the repo

**Adapt depth to role:**
- Engineering Surface: services, how they connect, where to find things, recent activity.
- Engineering Deep: data models, integration patterns, key files, service boundaries, how the domain interacts with IAM/shared infra.

### 2b. Notion investigation

Search Notion for documents related to the domain. Prioritise:
- Product specs and feature documentation
- Domain or team-specific pages
- Architecture or design documents
- Any onboarding or intro pages that already exist (even partial ones)

Do not rely on these being complete. Use what you find as context and as pointers — tell the user which Notion pages are worth reading and why, rather than reproducing their content.

### 2c. Slack investigation

Aidn's Slack channel naming follows two conventions: product-related channels include "product" in the name (e.g. `#product`, `#product-announcements`), and tech-related channels include "tech" (e.g. `#tech`, `#tech-leads`). Use this to guide which channels to search based on the user's role and the domain.

**Channel strategy by role and domain:**

- **Product roles**: Search `#product`, `#product-announcements`, `#okr`, and any channel with "product" in the name. Also search tender-related channels (look for channels with "tender", "anbud", or municipality names) — these surface what Munis are asking for and any commitments made, which are directly relevant to roadmap and prioritisation context.
- **Engineering roles**: Search `#tech`, `#tech-leads`, and any channel with "tech" in the name. For platform/infra, also check for infra or platform-specific channels.
- **Design roles**: Search both product and tech channels for the domain — design context tends to live in both.

For all roles, also search for any channel named after or closely associated with the domain itself (e.g. a `#cpr` or `#data-migrations` channel if it exists).

Look for:
- Recent feature launches or changes
- Known issues or active decisions
- Municipal asks or tender commitments relevant to the domain (especially useful for product roles)
- Anything that signals the domain's current state or near-term direction

Use this to add recency and ground-truth context that documentation rarely captures. If you find something significant in Slack that contradicts or updates what you found in Notion or GitHub, flag it explicitly.

---

## Step 3: Synthesise

After investigation, produce the onboarding output. Tailor it to the user's role and depth preference.

### Output structure by role

**Leadership — Director or C-level (strategic overview)**

This is the default output for leadership roles. Lead with what matters at a strategic level; do not default into engineering or PM depth unless they asked for it.

- **What this domain does and why it matters** — one paragraph, no jargon. Who are the users, what problem does it solve, where does it sit in Aidn's product?
- **Current state and momentum** — what's shipped, what's actively in progress, what's stalled or at risk. Draw from Slack and recent Notion/GitHub activity to give a current-as-of-today read, not just what documentation says.
- **Open decisions and active bets** — what is being debated or decided right now? What are the key unknowns? Anything that a Director or C-level should have a view on.
- **Risks and areas to watch** — known technical debt, delivery risk, team gaps, or external dependencies that could affect outcomes.
- **Team and ownership** — who owns this domain, what's the team structure, who are the key people (Tech Lead, PM, domain owner)?
- **Relevant OKRs or roadmap commitments** — how does this domain connect to current company OKRs or external commitments (e.g. municipality go-lives, tenders)?
- **Where documentation is weak** — be honest. If key information wasn't found or is clearly out of date, say so.
- **Where to go next** — 3–5 actions: who to talk to, what to read, what decisions to form a view on.

If the Director or C-level also asked to drill down into a specific area (technical, product, etc.), add a follow-on section using the appropriate role template below (Engineering, Product, etc.), clearly labelled as "Going deeper: [area]".

---

**Product**
- What this domain does and who uses it (the patient, clinician, admin, etc.)
- The core workflows or jobs-to-be-done the domain supports
- Key concepts and terminology you need to know
- Where the product currently stands (what's shipped, what's in progress)
- Relevant Notion pages to read (link and one-line description of each)
- Open questions or areas of active change

**Design**
- What this domain does and who the users are
- The main screens or flows the domain covers
- Key design considerations or known UX challenges
- Where the product currently stands
- Relevant Notion pages and any existing design references
- Open questions

**Engineering — Frontend**
- Domain overview: what it does, who uses it
- Frontend services or modules that belong to this domain
- Key screens and their location in the codebase
- How the frontend connects to backend services for this domain
- Relevant Notion pages and GitHub links
- Things to watch out for or known complexity areas

**Engineering — Backend**
- Domain overview
- Backend services that belong to this domain (with repo/folder pointers)
- Key data models and where they live
- Integration points (other services, external systems, IAM boundaries)
- Recent PRs or changes worth understanding
- Relevant Notion pages and GitHub links

**Engineering — Fullstack**
Combine frontend and backend sections above, scaled to depth preference.

**Engineering — Platform/Infrastructure**
- How this domain's services are deployed
- Infra dependencies (databases, queues, external integrations)
- IAM boundaries and access patterns relevant to the domain
- Data migration considerations if applicable
- Relevant RFCs or infra-level docs
- GitHub and Notion pointers

---

## Step 4: Deliver output

Deliver in the format the user chose. If they asked for something not listed here, adapt accordingly — the structure below is a guide, not a constraint.

### Notion page
Write the onboarding content as a new Notion page. Use clear headings, keep it scannable. Include direct links to related pages found during investigation. At the top, include:
- Domain name
- Role this was generated for
- Date generated
- A one-paragraph orientation: what this domain is and why it matters

End with a "Where to go next" section — 3–5 suggested actions or reads.

### Conversation
Walk the user through the content section by section. After each section, pause and ask: *"Does that make sense? Anything you want to go deeper on before I continue?"*

At the end, offer to:
- Go deeper on any area
- Generate a Notion page or markdown summary from the conversation
- Summarise the key things they should do in their first week in this domain

### Markdown summary
Write a clean, well-structured markdown document directly in chat. Use the same structure as the Notion page output. Easy to copy, paste, or share. At the end, offer to write it to Notion if they want a persistent version.

### Other formats
If the user asked for something else (a checklist, a slide outline, a one-pager, etc.), use the synthesised content and adapt the format to what they described.

---

## Quality checks

Before delivering output:
- For leadership roles: is the output focused on state, decisions, risks, and ownership — not a tutorial on how the domain works technically?
- For leadership roles who asked to drill deeper: have you clearly separated the strategic overview from the deeper section?
- For engineering roles: have you actually looked in GitHub, not just Notion?
- Have you surfaced links to real pages/repos rather than describing them vaguely?
- Is the depth appropriate to the role? A PM should not be reading about database schemas. A Director should not be getting a developer onboarding guide unless they asked for it.
- If something important was missing or unclear from the investigation, say so — don't paper over gaps.

If you could not find meaningful information about a domain in the sources available for the user's role, tell the user directly: *"I found limited documentation for this domain. Here's what I could find, but you may want to loop in [suggest: tech lead, PM, or domain owner] to fill the gaps."*

---

## Notes

- This skill does not require good existing documentation to work — it builds from source.
- Investigation depth is the most important variable in output quality. Take time on Step 2 before writing anything.
- The output is meant to get someone to productive independence, not to be a complete reference document. Keep it actionable.
