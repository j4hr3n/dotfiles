---
name: support-load-report
description: "Bi-weekly support load report for a product team, as a chart-first bilingual (Norwegian/English) HTML dashboard. Sweeps the team's Slack support channels and customer email over a period, classifies every thread into the team's own sections, counts threads and messages, and surfaces repeat questions, bug/gap splits, per-customer load and an analysis of how the work behaves, so planning can see where support time goes and which features need hardening. Use whenever someone asks for a support load report, supportlast, support volume, a bi-weekly or quarterly support summary, support themes for planning, 'what is support spending time on', 'where does our support time go', 'which features need hardening', or wants support data for quarter planning. Ships a Team Back Office preset (copay, price register, Helfo, bed management), and onboards any other team through a short interview: which domains to report on, how to section the load, which @support handle marks a thread, and where customer email arrives."
---

# Support load report

Produces one deliverable: a self-contained HTML dashboard, charts first, with a
Norwegian/English toggle. The front page opens with one hero chart, a stacked
area of the whole period with a band per domain, so the top edge is total load
and the bands show who is carrying it. Then one page per domain. The team reads
the numbers together and draws the conclusions, so the report shows and does not
explain. Resist the urge to fill it with prose, and keep it free of KPI tiles:
totals belong in one plain line, the charts do the rest.

The report closes with an analysis page that holds area constant and looks at
the shape of the work instead: how long threads run, how long they stay open,
how concentrated the load is in a few heavy threads, which kinds and channels
cost more, and how much of it went into questions asked before. That page is
generated from the same records, so it needs no extra classification work.

Each domain page carries a chip row naming the features it covers, taken from
the config. It exists so nobody has to ask what a domain includes before
trusting its numbers, which means the list has to be right. Confirm it with the
PM rather than inferring it from the keywords.

Load is two counts, both lifted straight from the threads: how many threads came
in, and how many messages they took. Days open and people per thread sit
alongside as plain averages. There is deliberately no weighted score, because a
number nobody can reconstruct gets argued about instead of acted on.

The pipeline is deliberately split. You read threads and decide what each one is
about, because that needs judgement. `scripts/build_report.py` does the
arithmetic and the drawing, because that needs to be identical every edition or
the trend charts lie.

```
gather threads  ->  classify each one  ->  threads.json  ->  build_report.py  ->  HTML
```

## Step 0: settle the run

You need five things before touching any data: team, period, sections, sources,
and where the report lands.

Work out which situation you are in before asking anything:

1. **A config already exists** for this team, in the working directory or the
   outputs folder (`config.<team>.json`). Read it, confirm the period, and go.
   Re-running the interview on a team that already has a config wastes the
   person's time and risks quietly changing the sections between editions, which
   breaks comparability.
2. **Team Back Office**, with no config to hand. Everything is preset: read
   `references/team-back-office.md`, copy `assets/config.team-back-office.json`,
   confirm the period.
3. **Anything else.** Run the onboarding interview below.

Copy the config to the working directory and set `period_start`, `period_end`
and `period_label`. Keep `bucket_days` at 14 so editions stay comparable.

## Step 0b: onboarding a new team

Run this when the skill triggers with no config and no preset that fits. The
output is a saved config, so this happens once per team and never again.

**Discover before you ask.** Nobody enjoys being interviewed about things you
could have looked up. Before the first question, spend a few calls establishing
what you can:

- `slack_search_channels` for the team name, plus obvious candidates like
  `#support-tickets` and `#error-tickets`, to get real channel names and ids.
- Read 20 or so recent messages in the most likely support channel and note
  which `@`-handles or subteams keep appearing on incoming requests. That gives
  you a proposed support handle rather than an open question.
- Note the recurring customer email domains you can see, so the municipality or
  customer question becomes a confirmation.

Then ask. Use `AskUserQuestion` for anything with a small set of answers, and
plain prose questions for the open ones, because a domain list will not fit into
four options. Keep it to two rounds at most.

**Round one, the shape of the report.** Batch these:

- **Which domains?** This is the spine of the whole report, so ask it openly:
  "Which parts of the product should the report be cut into?" Three to six
  domains works; more than six and every page gets thin. If they hesitate, offer
  the areas you saw recurring in the channel as a starting list, clearly marked
  as your reading rather than theirs.
- **Which support channels, and what marks a thread as support in each?** Offer
  the channels you found. For each, establish the marker: a subteam handle, a
  tag, a bot relay, or nothing at all. A channel with no marker convention means
  you read everything there and classify by hand, so flag that as the slower
  option rather than discovering it mid-crawl.
- **Customer email.** Whose mailbox, and which domains identify a customer.
  Offer what you saw. If nobody's mailbox is reachable, say so now: email load
  will be missing from the report and that belongs in the method note, not in a
  footnote after the fact.
- **Period and purpose.** What window, and what the report feeds. Quarter
  planning wants the quarter to date; a triage habit wants the last two weeks.
  The purpose also settles the cadence to offer at the end.

**Round two, the inside of each domain.** Only ask this once the domains are
settled, and only where it earns a question:

- **Subthemes.** For each domain, does the team plan its parts separately? A
  domain splits only when the split would change a decision. Where a domain is
  genuinely one thing, leave it as "overall load" with no subthemes and let
  emergent themes appear from the data instead (three or more threads on the
  same theme earns a subtheme, as in Step 2).
- **Features.** The chip row on each domain page. Ask for the names the team
  says out loud, and take the list as given rather than deriving it from
  keywords: the chips are a scope claim about what the domain covers.
- **Search vocabulary.** The words the team's customers actually use, in their
  language. For Norwegian municipal healthcare, `references/team-back-office.md`
  shows the shape and density to aim for. Keywords are a net for finding
  candidate threads, not the classifier.
- **Customers.** The list of customers or municipalities the team serves, which
  becomes the `municipalities` allow-list. A name outside it in the data almost
  always means a misread thread, which is exactly what makes the guard useful.

**Then write the config** to `config.<team>.json` following
`references/data-format.md`, show the person the sectioning you captured in a
few lines of plain text, and let them correct it before the crawl starts. A
wrong section costs a whole crawl to fix.

Tell them where the config is saved and that future runs will reuse it, so the
interview happens once. If the team is likely to run this often, offer to keep
the config in a stable place they choose rather than a session outputs folder.

Two things not to do in onboarding: do not invent domains from what you saw in
the channel and present them as the team's own structure, and do not start the
crawl while any of the five things above are still open. Both cost far more to
undo than to ask about.

Before gathering, say how big the sweep is: number of days, channels, and
roughly how many threads you expect. A full quarter is a long pass, and the
person should know that up front rather than wondering why you went quiet.

**Check for a previous edition first.** If a `threads.json` from an earlier run
covers part of this period, load it and classify only what is new, matching on
thread `id`. Re-classifying old threads from scratch makes the same thread drift
between sections and turns the trend chart into noise. Reuse beats recompute.

## Step 1: gather

Fetch sources **sequentially**. Parallel Slack and Gmail calls fail with "Stream
closed", and a failed call halfway through a quarter sweep costs more than the
time saved.

For every thread that counts, capture:

- `id`, `source`, `url`, and `date` (the date the thread **started**)
- `replies`: messages after the parent
- `participants`: distinct humans, bots excluded
- `span_days`: first message to last, same day is 0
- `municipality`: the kommune, normalised to a bare name (`Bodø`, never
  `bodo kommune` or `Bodø Kommune`), omitted for internal threads
- enough of the content to classify it and to write one short title

Count `replies`, `participants` and `span_days` off the thread rather than
estimating them. They are the whole load measure, and a thread you skimmed and
guessed at is worse than one you left out, because it lands in a chart looking
like a fact.

The config carries the list of kommuner the team serves, and the build warns on
any name outside it. A municipality Aidn does not serve turning up in the data
means a thread was misread, not that the list is too narrow.

**What is not support load:** standups, planning chatter, release notes,
internal banter, calendar logistics, pure acknowledgements, and threads where
someone said they would look into it and nothing followed. Count the discards so
you can report them.

**If a source fails or is unavailable**, do not quietly proceed. Record it, put
it in the report's `method_note`, and lead with it when you hand the report over.
A dashboard that silently omits a channel will be read as complete, and someone
will plan a quarter on it.

## Step 2: classify

One thread gets exactly one section. Double-counting inflates the totals and the
totals are the point of the report.

Assign, per thread:

**`group` / `subtheme` / `child`** from the config. Use the section that the
person actually needed help with, not the screen they happened to be on. When a
thread spans two sections, pick the one that consumed the conversation. When it
belongs to a domain but no named subtheme, leave `subtheme` off and it lands in
that group's `other` bucket, which is exactly what that bucket is for.

**Emergent subthemes.** Some sections are defined as "overall load, plus
whatever stands out" (price register, and Helfo beyond lack of functionality).
When three or more threads in a group's `other` bucket are clearly the same
theme, add a subtheme to the config with an id you invent and move them into it.
Three is the floor because two threads is a coincidence, and a chart of
coincidences is what makes people distrust the whole report.

**`kind`**, which is the hardening signal:

- `question`: the product worked, the person did not know how. Points at docs,
  training, or a confusing screen.
- `bug`: the product did the wrong thing. Points at hardening.
- `gap`: the product cannot do the thing at all. Points at the roadmap.

The split between these three per section is what turns "we spend a lot of time
on etteroppgjør" into a decision, so be strict about it. A question caused by a
misleading label is still a `question`, but say so in the title.

**`cluster`**: the canonical question this thread is an instance of. Reuse the
identical string across every thread asking it, because the repeat-question chart
groups on exact text. Threads that stand alone get no cluster, and an empty
repeat chart is a finding rather than something to pad.

**`title`**: one short line in Norwegian and English. Nothing renders it today,
but it is what makes the JSON reviewable when someone challenges a number.

Batch any genuinely borderline calls into one clarifying question at the end.
Do not ask as you go, and do not ask about anything you can decide.

Write it all to `threads.json` per `references/data-format.md`.

## Step 3: build

```bash
python3 scripts/build_report.py \
  --config config.json \
  --data threads.json \
  --out <outputs>/support-load-<period>-<team>.html \
  --kit <path to the aidn-design skill folder>
```

The script inlines the Aidn CSS and fonts so the file works anywhere. Without
`--kit` it tries to find the kit itself and warns loudly if it cannot, in which
case the output is unstyled and not shippable. Find the kit with
`ls ~/.claude/skills/aidn-design` or a glob for `**/aidn-design/aidn.css`.

Add `--sample` whenever the numbers are invented, which stamps a banner on every
page. Never show a chart-shaped page built on made-up numbers without it: charts
read as fact, and an unlabelled demo comes back quoted as real.

Read the totals and warnings the script prints. A group at zero, a large
`Unclassified`, or a municipality outside the config's allow-list means the
classification pass needs another look before anyone sees the report.

The layout is fixed on purpose. Editions have to be comparable at a glance, so
do not hand-edit the generated HTML. If a chart is wrong or missing, change the
script so every future edition gets the fix.

## Step 4: hand it over

Save the HTML to the outputs folder and present it with `present_files`. Then
publish it with the `Artifact` tool so the team has a link to open in the
planning session, and so the next edition can replace it at the same URL.

Keep the chat message short. Three or four lines at most: the headline numbers,
anything that failed or is incomplete, and two or three things worth a look in
the session. The team interprets the charts together, and a wall of
interpretation in chat competes with that instead of feeding it.

Keep `threads.json` and `config.json` next to the report. They are the input for
the next edition and the answer to "where did that number come from".

## Running it bi-weekly

Each run rebuilds the full quarter-to-date picture rather than only the last two
weeks, so the report is always the whole quarter and stays usable as planning
input at any point. Offer to schedule it every second Monday with
`create_scheduled_task`. At a quarter boundary, roll `period_start`,
`period_end` and `period_label` forward and start a fresh `threads.json`.

## Guardrails

- Never invent a number. Every figure in the report traces to a thread in
  `threads.json`.
- Flag anything stale or missing: a channel that failed, a mailbox you could not
  read, a period only partly covered. Say it in the report footer and in chat.
- Do not guess at Norwegian product vocabulary. If it is unclear whether the UI
  says one term or another, search both and ask rather than assuming.
- The report is not the place for recommendations. Sections, splits and repeats
  point at the work; the team decides what to do about it.

## Files

- `SKILL.md` Step 0b: the onboarding interview for a team with no config yet.
- `references/team-back-office.md`: the Team Back Office preset. Channel ids,
  Gmail queries, sectioning, Norwegian search vocabulary, what is out of scope.
- `references/data-format.md`: config and threads schemas, field by field, plus
  the effort formula and how clustering works.
- `assets/config.team-back-office.json`: ready-made config to copy and date.
- `scripts/build_report.py`: aggregation and rendering. Charts, effort model,
  bilingual toggle, Aidn bundling.
