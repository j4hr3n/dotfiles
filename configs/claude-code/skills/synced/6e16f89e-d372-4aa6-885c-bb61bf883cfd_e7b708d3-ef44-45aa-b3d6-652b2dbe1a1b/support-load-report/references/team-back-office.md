# Preset: Team Back Office (Aidn)

The default team. Config lives in `assets/config.team-back-office.json`; copy it
to the working directory and set `period_start`, `period_end` and `period_label`
for the run.

## Where the load comes from

| Source id | Where | How to find the support threads |
|---|---|---|
| `support-tickets` | Slack `#support-tickets`, channel `C04DG8XNXRV` | Threads tagging `@BO-support` (`<@S0B4JPKPXPT>`). This is the main channel. CX routes municipality questions here. |
| `error-tickets` | Slack `#error-tickets`, channel `C02KQUVA411` | Same `@BO-support` tag. Bot messages starting `Ny tilbakemelding fra…` are HubSpot relays; read the thread for the real question. |
| `team-back-office` | Slack `#team-back-office` | No tag convention here, so read every thread in the window and keep the ones that are a real customer or municipality request for help. Standups, planning chatter, release notes and internal banter are not support load. Say in the run report how many you discarded. |
| `email` | Gmail | Mari Gloppen Hunnes holds most municipality dialogue and cc's Jens, so only Jens' mailbox is searchable. Counted in the same totals as Slack, with the split visible in the method footer. |

Gmail queries (run sequentially, never in parallel with Slack calls, parallel
Gmail/Slack reliably fails with "Stream closed"):

```
from:mari.gloppen@aidn.no (to:kommune.no OR cc:kommune.no) after:<start> before:<end>
from:kommune.no (to:mari.gloppen@aidn.no OR cc:mari.gloppen@aidn.no) after:<start> before:<end>
from:jens.malm@aidn.no (to:kommune.no OR cc:kommune.no) after:<start> before:<end>
from:kommune.no (to:jens.malm@aidn.no OR cc:jens.malm@aidn.no) after:<start> before:<end>
```

Also try `.herad.no`, a few municipalities (Voss herad) use it instead of
`.kommune.no`.

## Sectioning

Four domains plus a catch-all, as in the config:

1. **Egenbetaling / Copay**, overall, then three named subthemes: the
   calculators (split long-term stay / short-term stay / practical aid), yearly
   reconciliation (etteroppgjør), and invoicing and export.
2. **Prisregister / Price register**, overall load only. No fixed subthemes;
   add emergent ones if a clear theme carries several threads.
3. **Helfo-refusjon / Helfo reimbursements**, overall, then *lack of
   functionality* as a named subtheme, plus any other theme that stands out.
4. **Sengeadministrasjon / Bed management**, overall, then allocation of stays
   and the overview screen.
5. **Øvrig back office / Other back office**, everything in the team's domain
   that isn't one of the four. Keeps the quarter total honest.

## Feature chips

Each group in the config carries a `features` list that renders as a chip row on
that domain's page. The current lists were mapped from the topic sections of the
team's support knowledge base (vederlagsberegning, NAV-trekk, etteroppgjør,
sengeplasser og romadministrasjon, HELFO-refusjon, fakturagrunnlag,
saksbehandlingsmaler og betalingsvedtak, mors-rutine, KOSTRA, prisregister,
Visma-eksport, migrering), which is a good approximation and not a feature
inventory. Get the PM to correct them on the first real run and edit the config,
since the chips tell readers what the domain covers and a wrong chip redefines
the domain by accident.

## Municipalities

The config's `municipalities` list holds the kommuner the team serves, and the
build warns on anything outside it. The current list came from the email domains
appearing in `#support-tickets`: Trysil, Ullensvang, Bodø, Øygarden, Hamarøy,
Kinn and Vågan. It is observed rather than authoritative, so confirm it with the
PM on the first real run and correct it here. A name outside the list almost
always means a thread was misread, not that Aidn signed a new customer.

Normalise from the email domain: `bodo.kommune.no` becomes `Bodø`,
`ullensvang.kommune.no` becomes `Ullensvang`. Watch for `.herad.no` (Voss herad).

## Norwegian search vocabulary

Keywords are a net for finding candidate threads and a tie-breaker when a
thread's wording is ambiguous. They are not the classifier. A thread that never
uses any of these words still counts if it's about the thing.

**Egenbetaling:** egenandel, egenbetaling, vederlag, vederlagsberegning,
langtidsopphold, korttidsopphold, praktisk bistand, hjemmetjeneste,
inntektsgrunnlag, skattegrunnlag, fribeløp, etteroppgjør, faktura,
fakturagrunnlag, fakturaeksport, kreditnota, betalingsvedtak, NAV-trekk

**Prisregister:** prisregister, prisliste, satser, sats, grunnbeløp, 1G,
maksimalsats, prisjustering, migrering av priser

**Helfo:** Helfo, refusjon, oppgjør, oppgjørskrav, KUHR, takst, takstkort,
frikort, egenandelsregisteret, avvist krav, kontrollmelding, oppgjørsrapport

**Sengeadministrasjon:** sengepost, sengeplass, tildeling av opphold, opphold,
plassering, sengeoversikt, belegg, beleggsoversikt, romoversikt, romadministrasjon,
inn- og utflytting, flytting, avdelingsoversikt

**Generic support markers:** hjelp, feil, bug, fungerer ikke, hvordan gjør jeg,
haster, kritisk, sak, ticket, avvik

Two open questions worth confirming with the PM the first time this runs, and
worth recording here afterwards: whether Aidn's own UI says *vederlag* or
*egenbetaling* (search both until settled), and whether any named external
invoicing system (Visma, Agresso) should be a search term for the invoicing and
export subtheme.

## Out of scope

Drop, without counting: pasientjournal, skjema and lab, oppgaver and maler,
mobilapp and arbeidsdag, medikamenthåndtering, ruteplanlegging, CPR,
case-handling and collaboration threads with no financial, bed or reporting
angle. If a thread is genuinely borderline, that's a clarifying question for the
PM rather than a guess. Batch those into one question at the end rather than
asking as you go.

## Who to expect in the threads

Mari Gloppen Hunnes and Kjersti Berg carry most Team Back Office support. Their
presence in a thread is a good signal it *is* support load; it is not needed for
a thread to count.
