# Data format

Two JSON files drive `scripts/build_report.py`:

- **config.json**, the team's sectioning and period. Stable between runs; a
  ready-made one for Team Back Office is in `assets/config.team-back-office.json`.
- **threads.json**, one record per support thread you classified this run.

## config.json

```json
{
  "team": "Team Back Office",
  "period_label": { "no": "Q3 2026", "en": "Q3 2026" },
  "period_start": "2026-07-01",
  "period_end": "2026-09-30",
  "bucket_days": 14,
  "municipalities": ["Trysil", "Ullensvang", "Bodø"],
  "method_note": {
    "no": "Tråder uten @BO-support-tagg i #team-back-office er klassifisert manuelt.",
    "en": "Threads in #team-back-office without a @BO-support tag were classified by hand."
  },
  "groups": [
    {
      "id": "copay",
      "label": { "no": "Egenbetaling", "en": "Copay" },
      "note": { "no": "…", "en": "…" },
      "subthemes": [
        {
          "id": "calculators",
          "label": { "no": "Egenandelskalkulatorer", "en": "Copay calculators" },
          "children": [
            { "id": "longterm", "label": { "no": "Langtidsopphold", "en": "Long-term stay" } }
          ]
        }
      ]
    }
  ]
}
```

Notes that matter:

- `groups[].features` is the list of product features the domain covers. It
  renders as a chip row under the domain heading, so anyone reading the page can
  see what is being counted without asking. Keep the names the ones the team
  says out loud, and confirm the list with the PM rather than deriving it from
  the search vocabulary: a chip row is a scope claim, and a wrong one quietly
  redefines the domain.
- `groups[].note` is optional and renders as one short line under the group
  heading. Use it for something the numbers can't say on their own (a known
  release that explains a spike, say). Leave it out rather than padding.
- Every group automatically gets an `other` subtheme even if the config omits
  one, so a thread that belongs to a domain but not to a named subtheme still
  gets counted. This is what keeps the "overall support load" figure honest.
- `children` nest exactly one level. A subtheme with children renders a small
  breakdown bar inside its card.
- `bucket_days: 14` matches a bi-weekly cadence. Keep it stable so trend charts
  stay comparable between editions.
- `municipalities` is the list of kommuner the team actually serves. The script
  warns on any name outside it. This is a cheap and effective guard: a
  municipality Aidn does not serve appearing in the data means a thread was
  misread, so treat the warning as a bug in the classification rather than a
  reason to widen the list. Widen it only when the team genuinely took on a new
  customer.

## threads.json

```json
{
  "meta": { "generated": "2026-09-30", "sample": false },
  "threads": [
    {
      "id": "slack-1751894423.118",
      "source": "support-tickets",
      "url": "https://aidn.slack.com/archives/C04DG8XNXRV/p1751894423118",
      "date": "2026-07-07",
      "group": "copay",
      "subtheme": "calculators",
      "child": "longterm",
      "kind": "question",
      "municipality": "Bergen",
      "replies": 6,
      "participants": 3,
      "span_days": 2,
      "title": { "no": "Feil fribeløp ved langtidsopphold", "en": "Wrong allowance on long-term stay" },
      "cluster": { "no": "Hvordan settes fribeløp ved langtidsopphold?", "en": "How is the allowance set for long-term stay?" }
    }
  ]
}
```

Field by field:

| Field | Required | What it is |
|---|---|---|
| `id` | yes | Stable key. Slack `message_ts` prefixed with the channel, or the Gmail thread id. Lets a later edition dedupe against this one. |
| `source` | yes | `support-tickets`, `error-tickets`, `team-back-office`, `email`, or whatever channel ids the team actually uses. Shown in the method footer. |
| `url` | no | Permalink. Kept in the data for traceability even though the report doesn't render it. |
| `date` | yes | Date the thread *started* (`YYYY-MM-DD`). Drives the trend buckets. |
| `group` / `subtheme` / `child` | `group` yes | Config ids. An unknown id lands in an `Unclassified` group and prints a warning rather than disappearing. |
| `kind` | yes | `question` (someone needed to know how), `bug` (it behaved wrong), `gap` (it can't do the thing at all). |
| `municipality` | no | Kommune name, normalised (`Bergen`, not `bergen kommune` / `Bergen Kommune`). Omit for internal threads. |
| `replies` | yes | Messages in the thread after the parent. Email: replies in the thread. The report shows `replies + 1` as **messages**, which is the load measure. |
| `participants` | yes | Distinct humans in the thread, including the asker. Bots don't count. |
| `span_days` | yes | Days from first to last message. Same-day threads are `0`. |
| `title` | yes | One short line, both languages. Not rendered in the current layout, but it's what makes the data reviewable, keep it real. |
| `cluster` | no | The canonical question this thread is an instance of, phrased once and reused verbatim across every thread that asks it. Clusters with 2+ threads become the "repeat questions" chart. |

### Clustering is where the value is

The repeat-question chart is the single most actionable thing in the report, and
it only works if you reuse the *exact same* cluster string across threads.
"Hvorfor stemmer ikke etteroppgjøret?" and "Etteroppgjør viser feil beløp" are
one cluster, not two. Pick one phrasing, then paste it into every matching
thread. Case and surrounding whitespace are normalised for you; wording is not.

A thread that genuinely stands alone gets no `cluster` at all. Don't invent
singleton clusters to fill the chart. An empty chart is a finding too.

## How load is measured

Two counts, both taken straight from the threads, so there is no formula to
defend in a planning session:

- **Tråder / threads.** How many came in.
- **Meldinger / messages.** `replies + 1` summed across the threads, so the
  first message plus every reply. This is the closest honest stand-in for time
  spent: a thread that took eleven messages cost more than one answered in two.

Shown alongside per domain, as plain averages: messages per thread, days open,
and people per thread. Nothing is weighted or combined into an index, because a
number nobody can reconstruct is a number the team will argue about instead of
acting on.

## Running the build

```bash
python3 scripts/build_report.py \
  --config config.json \
  --data threads.json \
  --out /path/to/outputs/support-load-q3-2026.html \
  --kit /path/to/skills/aidn-design
```

Add `--sample` (or `"sample": true` in the data's `meta`) for anything built
from made-up numbers. It stamps a visible banner on every page. Use it for
layout demos without exception: a chart-shaped page reads as fact, and an
unlabelled demo will be quoted back at you as real.

The script prints per-group totals plus any warnings. Read them: a group at
zero, a large `Unclassified`, or a municipality outside the allow-list all mean
the classification pass needs another look before the report goes anywhere.

## Layout the script produces

A front page led by one hero chart: a stacked area of the whole period, one band
per domain, so the top edge is the total load and the bands show who is
carrying it. A small toggle switches the whole chart between threads and
messages. Under it, a single line of totals, then where the load sits, the
question/bug/gap split, the municipality grid and the repeat questions.

Then one page per domain, reached from the nav at the top: totals as one plain
line, a chip row naming the features the domain covers, the kind split, its own
area chart, municipalities, repeat questions, and a card per subtheme. Arrow
keys page through. Printing lays every page out in sequence with page breaks, so
the same file works as a handout.

The last page is the analysis, and it holds area constant to ask a different
question: what does a thread cost, where does the cost concentrate, and which
kinds of load behave differently. It carries the length and time-open
distributions with median, upper decile and maximum; median messages against
mean days open per kind, per area and per channel; the share of threads that
pulled in four or more people; how much load sat in questions asked more than
once; and the kind mix over time.

Every panel there closes with a generated finding: one sentence, computed from
the same numbers, naming what the chart shows. That sentence is the point of the
page as much as the chart is. A distribution is easy to look at without
registering, and in a planning session the reading has to survive being glanced
at. Keep those sentences descriptive: they say what the data says, never what to
do about it, because the decision is the team's.

Charts that needed study rather than a glance were removed on purpose. A
concentration curve and a time-open-against-length scatter both carried real
information, and both lost the room; their content now lives in the findings on
the length and time-open panels instead. If a panel cannot be read at a glance,
the fix is to state its finding, not to add a legend.

Two notes on the statistics. Median days open is 0 for most cuts because well
over half of all threads close the same day, so the per-cut comparison uses the
mean, which separates them; both numbers appear in the summary line so the skew
stays visible. And the generated sentences use language-correct number
formatting, comma decimals in Norwegian and point decimals in English, which is
why `num_en` exists alongside `num`.

There are deliberately no KPI tiles anywhere. Every number a tile would have
held is either in the charts or in that one line of text. Tiles competed with
the charts for attention and won, which is the wrong way round for a report the
team reads together.
