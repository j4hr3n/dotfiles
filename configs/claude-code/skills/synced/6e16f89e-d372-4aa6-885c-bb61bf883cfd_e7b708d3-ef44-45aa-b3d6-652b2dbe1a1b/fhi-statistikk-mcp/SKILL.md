---
name: fhi-statistikk-mcp
description: Use when querying Norwegian public health statistics via the fhi-statistikk MCP server. Covers data interpretation, quality caveats, and correct usage of the MCP tools. Triggered by requests for health data, population statistics, vaccination data, cause-of-death data, or any reference to FHI/Folkehelseinstituttet statistics when the fhi-statistikk MCP server is connected.
---

# FHI Statistikk — MCP Companion

You have the `fhi-statistikk` MCP server connected. It exposes 6 tools that wrap the
FHI Statistikk Open API. The tools handle API mechanics (dimension auto-completion, year
format, CSV parsing). **This skill covers what the tools can't do: data interpretation.**

## Available MCP tools

| Tool | Purpose |
|---|---|
| `list_sources` | List all 13 data sources (registries) |
| `list_tables` | Find tables within a source, with keyword search |
| `describe_table` | Get dimensions, metadata, flags — everything about a table |
| `get_dimension_values` | Drill into hierarchical dimensions (GEO tree); supports `parent_value` and accent-insensitive `search` |
| `query_data` | Fetch data with dimension filters, returns labeled rows |
| `get_query_template` | Returns raw API JSON body with all dimension values pre-filled — useful to see all available values at once or debug `query_data` |

## CRITICAL: Read metadata before analyzing data

**ALWAYS call `describe_table` before `query_data`.** The description, flags, and dimension
structure are essential for correct interpretation. Do not skip this step.

## CRITICAL: Always present caveats with results

When presenting data to the user, ALWAYS state:
- **Source and table** — which registry and table ID the data comes from
- **Flags** — whether any values are suppressed (`:`) or missing (`..`), and how many
- **Standardization** — which reference population was used (if applicable)
- **Temporal caveats** — municipality mergers, vaccine program start dates, sentinel vs comprehensive coverage
- **What the numbers mean** — rates vs counts, per 100k vs percentage, age-standardized vs crude

Do NOT present raw numbers without context.

## CRITICAL: Don't interpret beyond what the data supports

This is public health data — overconfident interpretation is worse than no interpretation. When the data is ambiguous or incomplete, be explicit about it rather than pushing to an answer. Common cases:
- Suppressed values (`:`) — don't estimate what the hidden number might be
- Incomplete time series (municipality mergers, program start dates) — don't smooth over breaks
- Missing methodology context — if `describe_table` returns no description, note that interpretation is uncertain
- Unexpected values — flag them, don't rationalize them away

"I can't determine this from the available data" is a correct and useful response. The user can act on stated uncertainty; they cannot act on a confident-sounding answer that's actually a guess.

## Workflow

1. `list_sources` or use known source ID (nokkel, sysvak, daar, msis, etc.)
2. `list_tables(source_id, search="keyword")` — find the right table
3. `describe_table(source_id, table_id)` — **read this carefully before querying**
4. `get_dimension_values(source_id, table_id, "GEO")` — if you need to find geographic codes
5. `query_data(source_id, table_id, dimensions=[...])` — fetch the data

The `query_data` tool auto-includes fixed dimensions and defaults MEASURE_TYPE to all.
You must specify all non-fixed, non-MEASURE_TYPE dimensions or you'll get an error.

## Tool-specific notes

### query_data dimensions

Each dimension needs `code`, `filter`, and `values`:
```json
{"code": "GEO", "filter": "item", "values": ["0301"]}
{"code": "AAR", "filter": "bottom", "values": ["3"]}
{"code": "MEASURE_TYPE", "filter": "all", "values": ["*"]}
```

Filter types: `item` (exact), `all` (wildcard), `top` (first N), `bottom` (last N).

Year values: pass `"2024"` — the tool normalizes to `"2024_2024"` automatically.

Always check `"truncated": true` in the response — if set, you got partial data. Reduce filters or use `max_rows=0` for unlimited.

### get_dimension_values

Use this to drill into large hierarchical dimensions (mainly GEO) or to search for a specific location:

- `parent_value`: return only children of a category — e.g. `"18"` for all municipalities in Nordland
- `search`: accent-insensitive label search — `"tromso"` matches `"Tromsø"`, `"bodo"` matches `"Bodø"`

Returns `[{value, label, child_count}]`. Use `value` in your `query_data` dimension filter.

### describe_table output

Top-level fields:
- `description` — prose from the table metadata; read this for methodology and caveats
- `source_institution` — additional source/methodology notes (not always present)
- `flags` — suppression symbols and their meanings for this table

Per dimension:
- `is_fixed` — auto-included in queries, you don't need to specify these
- `total_categories` — if large (>20), only top-level values are shown; use `get_dimension_values` to explore
- `value_format` — present on year dimensions, e.g. `"YYYY_YYYY (e.g. 2020_2020)"`
- `range` — e.g. `"2002..2024"` on year dimensions
- `top_level_values` — shown instead of `values` for large hierarchical dimensions (GEO)
- `note` — self-documenting hints, e.g. `"Single-valued, auto-included in queries"`

## Data quality and interpretation — MUST READ

These patterns apply across many tables and will cause **silently wrong analysis** if ignored.

### null vs 0 vs `:` — three different things

| Value | Meaning |
|---|---|
| `null`/empty | Data not available (not yet reported, or not applicable) |
| `0` | Measured value is actually zero |
| `":"` | Value exists but is **suppressed** (personvern, typically n < 5) |
| `".."` | Missing data |

**Check the FLAGG column in query_data results.** A suppressed value and a null look identical
in the data column. Treating `:` as zero produces wrong conclusions (e.g. "zero vaccination
coverage" when it's actually suppressed because the municipality is too small).

### Hierarchical dimensions — double-counting risk

Many dimensions have a "Total" category alongside subcategories:
- Cancer types: "Total" = sum of all cancer types
- Drug deaths: "Total" = sum of subcategories

**Never sum "Total" with individual categories.** Use one or the other.

### Time formats differ between tables

| Format | Example | Context |
|---|---|---|
| `YYYY_YYYY` | `"2024_2024"` | Year-based (most common) |
| `YYYY-wNN` | `"2024-w40"` | ISO week (influenza) |
| Plain number | `"40"` | Week number (seasonal comparison) |

Cross-table joins on time require format translation. Always check dimension values.

### Sentinel surveillance data

Some tables (especially MSIS influenza) use **sentinel** data from volunteer reporting sites,
not comprehensive national coverage. This means:
- Rates are for the reporting population, not the general population
- Geographic coverage may be incomplete
- Trends can shift when reporting sites change

Read the table description to determine if data is sentinel-based.
Sentinel data is valid for trend analysis but NOT for prevalence estimates.

### Age standardization — which reference population?

| Code | Meaning | Use when |
|---|---|---|
| `RATE_NO` | Norwegian standard | Comparing within Norway |
| `RATE_EU` | Eurostat standard | Comparing with European countries |

These give **different numbers for identical deaths.** Always state which you used.

### Vaccination data: nulls may mean "program didn't exist"

SYSVAK data has structural gaps that are NOT missing data:
- HPV boys: only from 2022
- Rotavirus: only from 2017
- Hepatitt B: only from 2019
- Kikhoste 16-åringer: only from 2014

Null before introduction = "vaccine not in program yet." Read the table description.

### Municipality mergers break time series

Major mergers in 2020. Old municipality codes vanish, new ones appear. Time series per
municipality WILL have breaks. Use county or national level for unbroken series, or limit
to post-2020 for municipality data.

### Cross-table dimension gaps

Tables with similar names may have different dimensions. If a table lacks the dimension you
need (e.g. gender), search for alternative tables:
`list_tables(source_id, search="keyword")`