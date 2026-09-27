---
name: cycle-insights-digest
description: >
  End-of-cycle Productboard insights digest for any Aidn team. Fetches all feedback (notes/insights)
  linked to the team PM's features in Productboard during the current cycle, summarizes themes and
  patterns in English, and posts the digest to the team's Slack channel. Use this skill whenever
  someone wants a cycle summary, insights recap, or end-of-cycle Productboard digest — even
  if they phrase it casually. Designed to be used by any team: just say the team name, PM email,
  and Slack channel. Works both manually and as a scheduled task. Trigger on: "cycle digest",
  "insights summary for [team]", "post our cycle notes to Slack", "what came into Productboard
  this cycle", "end-of-cycle summary", "what insights did we get this cycle",
  "summarize Productboard for [team]".
---

# Cycle Insights Digest

Generate an end-of-cycle Productboard insights digest for an Aidn team. Runs every other Friday
(the last day of each 2-week Aidn cycle) and gives the PM a clear summary of what feedback came
in during the cycle — so the whole team heads into the next cycle informed.

---

## Onboarding flow

If the user hasn't provided all three required inputs (team name, PM email, Slack channel),
run this onboarding flow before doing anything else. It's a short, friendly setup — walk
through it step by step, one question at a time.

**Step 1 — Welcome**

Greet the user with a short intro:

> 👋 Welcome to the **Cycle Insights Digest**!
>
> This skill pulls all the feedback and notes linked to your features in Productboard at the
> end of each Aidn cycle, summarises the themes and patterns in both Norwegian and English,
> and posts the digest straight to your team's Slack channel — so your whole team goes into
> the next cycle with a shared picture of what users are asking for.
>
> It takes about 30 seconds to set up. I just need three things from you.

**Step 2 — Collect inputs (one at a time)**

Ask each question on its own, wait for the answer, then move to the next:

1. "**What's your team name?** (e.g. CPR, Collab, Treatment, Case Handling)"
2. "**What's the PM's email address?** This needs to be the email of the PM who owns the features in Productboard — notes are assigned to features, and features are owned by the PM. (e.g. firstname.lastname@aidn.no)"
3. "**Which Slack channel should I post the digest to?** (e.g. #team-cpr)"

**Step 3 — Confirm and choose**

Once you have all three, summarise and ask how they want to proceed:

> Got it! Here's what I'll set up:
> - **Team:** [Team Name]
> - **PM email:** [email]
> - **Slack channel:** [#channel]
>
> How would you like to continue?
> **A)** Run the digest now (I'll pull insights from the current cycle and post to Slack)
> **B)** Set up automatic posting (every cycle-end Friday at 08:00 — I'll post automatically without you having to do anything)
> **C)** Both — run now and set up the schedule

**Step 4 — Act on choice**

- **A (run now):** Proceed directly to Step 1 (Determine cycle dates) below.
- **B (schedule only):** Create a scheduled task with the prompt:
  `"Run the cycle insights digest for [Team Name], PM is [email], post to [#channel]"`
  Cron: `0 8 * * 5`, timezone: `Europe/Oslo`.
  Then confirm: "Done! You'll get your first digest next cycle-end Friday. 🎉"
- **C (both):** Run the digest first, then create the scheduled task.

---

## Required inputs (when already provided)

If the user has already given all three in their message, skip the onboarding and go straight
to the steps below:
- **Team name** — for display (e.g., "CPR", "Collab", "Treatment", "IAM")
- **PM email** — the PM's Aidn email address (e.g., "pm.name@aidn.no"), used to filter
  their features in Productboard
- **Slack channel** — where to post (e.g., "#team-cpr")

---

## Step 1 — Determine the cycle dates

Query the Aidn Cycles calendar to find the current or just-ended cycle.

**Calendar ID:** `c_e6f3f1a072f574d499511863d5bafe0a6ae11d2a189cddac432c8bce661df4c7@group.calendar.google.com`

List events spanning today ±3 days. Find the cycle whose end date (exclusive in the calendar,
i.e. the day *after* the last day) equals tomorrow — meaning today is the final Friday of
that cycle.

Extract:
- **Cycle number** (e.g., "Cycle 12")
- **Cycle start date** (Monday, inclusive)
- **Cycle end date** (Friday, inclusive = today)

**If triggered manually and today is NOT a cycle-end Friday:**
Tell the user it's mid-cycle, then ask: "Do you want a digest of insights so far in the
current cycle?" If yes, use that cycle's start date through today.

**If triggered by a scheduled task and today is NOT a cycle-end Friday:**
Exit silently — no Slack post, no error.

**Fallback if calendar is unreachable:** Cycles are 2 weeks long. Cycle 12 = Jun 15–26.
Add multiples of 14 days to find the current cycle.

---

## Step 2 — Fetch the PM's features from Productboard

Use `entities_query_entities` to find features owned by this PM:

```
entityTypes: ["feature"]
filter: {
  type: "simple",
  target: "owner",
  operator: "IN",
  value: ["<pm email>"]
}
fields: ["Teams", "Owner", "Status"]
limit: 50
```

Collect all feature entity IDs. If `totalCount` exceeds 50, repeat with additional pages
(use name-based filtering to narrow if needed — the goal is features actively worked on,
not the entire backlog).

If no features found, check the email is correct before giving up.

---

## Step 3 — Fetch feedback linked to those features

**Important — decode IDs before use:** `entities_query_entities` returns Base64-encoded
GraphQL IDs (e.g. `MzpQbUVudGl0eTpjNDk4MGE0MC0...`). `feedback_list_feedback` requires
plain UUID format. Decode each ID before passing it:

```python
import base64
raw_id = "MzpQbUVudGl0eTpjNDk4MGE0MC0..."  # from entities_query_entities
uuid = base64.b64decode(raw_id).decode().split(":")[-1]
# result: "c4980a40-..."  ← use this
```

If you can't run Python, split on `:` after base64-decoding: the UUID is always the last segment.

Call `feedback_list_feedback` with batches of up to 20 **decoded** UUIDs at a time:

```
ids: [<uuid_1>, <uuid_2>, ...]
```

Follow `nextCursor` to paginate through all feedback. Collect everything returned.

After fetching, verify: log how many feedback items were returned and from how many features.
If zero items for many features, the IDs are likely still in the wrong format — double-check
the decode step.

**Date filtering:** Each feedback item should include a creation/submission timestamp.
Keep only items where the date falls within the cycle (cycle start → cycle end). If no
timestamp is available on the items, include all feedback and note in the Slack message
that date filtering wasn't available.

If zero feedback exists for all features: still post to Slack — "nothing came in this
cycle" is useful signal.

---

## Step 4 — Summarize the feedback

Write the summary in **both Norwegian and English**. Norwegian comes first — it preserves
the original nuance and phrasing from users. English follows as a clean translation. Both
sections cover the same themes and points; don't add new content in one that isn't in the other.

**Structure per theme (both languages):**

1. **Volume** — total count of feedback items in this cycle
2. **Top themes** — group items by topic or pattern. For each theme: a short specific label,
   a count, 1–2 sentences on the core signal, and a list of direct Productboard links for
   the notes in that theme. Aim for 3–6 themes; bundle smaller ones under "Other/Annet".
   Specific labels are more useful than vague ones — "Treg medikamentsøk" / "Slow medication
   search" beats "Ytelse" / "Performance".
3. **Worth watching / Verdt å følge med på** — at most 3 items that are urgent, newly
   emerging, or appear across multiple feedback sources.

Keep it neutral. Do not include customer names (anonymize by default). Target: 200–400 words
per language section.

**Each feedback item has a `displayUrl` field** — use this as the direct link to the note
in Productboard. Group these links under each theme so the PM can click straight through.

---

## Step 5 — Post to Slack

Format using Slack markdown (`*bold*`, `_italic_`, `•` bullets). The message has two
clearly separated sections: Norwegian first, English second.

```
*🔍 Cycle [N] Innsiktsoppsummering — [Team Name]*
[Start date, e.g. Man 15 jun] → [End date, e.g. Fre 26 jun]

*[N] innspill mottatt denne cyclen*

*Topp temaer*
• *[Tema 1]* ([antall]) — [1–2 setninger]
  🔗 <[pb-url-1]|Note 1> · <[pb-url-2]|Note 2>
• *[Tema 2]* ([antall]) — [1–2 setninger]
  🔗 <[pb-url]|Note 1>

*Verdt å følge med på*
• [Signal 1]
• [Signal 2]

---

*🔍 Cycle [N] Insights — [Team Name] (English)*

*[N] feedback items this cycle*

*Top themes*
• *[Theme 1]* ([count]) — [1–2 sentence summary]
  🔗 <[pb-url-1]|Note 1> · <[pb-url-2]|Note 2>
• *[Theme 2]* ([count]) — [1–2 sentence summary]
  🔗 <[pb-url]|Note 1>

*Worth watching*
• [Signal 1]
• [Signal 2]

_Hentet fra Productboard · [Today's date]_
```

Notes on links:
- Use Slack's link format: `<url|display text>` — e.g. `<https://aidn.productboard.com/...|Note 3>`
- Use the note's `name` field as display text where available, otherwise "Note [n]"
- List all notes under their theme, not just a sample

Adjust to fit. If zero feedback: post a short "quiet cycle" note in both languages. If date
filtering wasn't available, note it in both sections.

Post using `slack_send_message` to the team's Slack channel.

Confirm to the user: "Posted the Cycle [N] digest to [#channel]."

---

## Error handling

| Situation | Action |
|---|---|
| No features found for PM email | Ask user to confirm the email matches Productboard |
| Productboard returns an error | Post ⚠️ to Slack so PM knows the digest failed |
| Calendar unreachable | Use date math fallback (see Step 1) |
| Zero feedback | Post "quiet cycle" message — don't skip silently |

---

## Setting up automated scheduling (per team)

Each team sets up their own scheduled task once. The scheduled prompt should be:

> "Run the cycle insights digest for [Team Name], PM is [pm.email@aidn.no], post to [#channel]"

**Schedule:** Every Friday at 08:00 Oslo time → cron `0 8 * * 5` (Europe/Oslo timezone).
The skill checks the calendar on each run and only posts on cycle-end Fridays. Non-cycle
Fridays exit silently — no need to manage a custom schedule per cycle.
