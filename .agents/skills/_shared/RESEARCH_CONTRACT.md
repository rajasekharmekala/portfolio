# Research Contract — the record every research agent returns

One JSON file per market per day: `scripts/.cache/research_<MARKET>_<YYYY-MM-DD>.json`
with top level `{"items": [ ...one record per (symbol, metric) lookup... ]}`.

Every claim that a report will make as fact — a filing number, a pledge percentage,
a segment split, a capacity figure — must trace to exactly **one record** in this
file. No record, no claim. The record is the unit of audit:
`scripts/citation_check.py` (the W3 citation gate) proves each record against the
fetch cache and every report against the research file.

## Record shape

```json
{
  "key": "promoter_pledge",
  "symbol": "AFCOM",
  "status": "found",
  "value": {
    "pledge_pct_of_promoter_holding": "0.0%",
    "period": "2026-06"
  },
  "unit": { "pledge_pct_of_promoter_holding": "percent of promoter holding" },
  "quoted": "Promoter shareholding as on 30-06-2026 ... Pledged: 0",
  "source_url": "https://trendlyne.com/equity/share-holding/2486163/17160453/latest/afcom-holdings-ltd/",
  "retrieved_at": "2026-10-08T14:32:11",
  "as_of": "2026-06",
  "queries_tried": [
    "AFCOM promoter pledge latest shareholding 2026 Screener",
    "site:screener.in/company AFCOM shareholding pledge latest 2026"
  ],
  "sources_tried": ["Screener", "Trendlyne"]
}
```

| field          | required | rules |
|----------------|----------|-------|
| `key`          | yes      | stable metric id, snake_case (e.g. `promoter_pledge`, `net_debt_ebitda`) |
| `symbol`       | yes      | exchange symbol exactly as it appears in the data files |
| `status`       | yes      | `found` or `not_found` — nothing else |
| `value`        | if found | dict of **scalar** metric values (number or string-as-printed, e.g. `"0.0%"`). Keep scalars raw: the citation gate checks each scalar verbatim against the cached page text, so no prose in `value`. Include `period` inside `value` when the metric is point-in-time. |
| `unit`         | if found | dict, metric id → unit ("₹ crore", "percent of promoter holding", "times"). Never let the unit live only in prose. |
| `quoted`       | if found | verbatim passage from the source page that the value is read from. Must appear in the cached text (whitespace-normalised). If the page is a table, quote the row. |
| `source_url`   | if found | one http(s) URL per record. Primary sources only: exchange filings, company IR, the named source the quote is from. Aggregators (screener.in, trendlyne.com, finviz, tradingview) are allowed for shareholding data, never as the sole source for a financial claim. |
| `retrieved_at` | if found | ISO timestamp of the actual fetch — the same value the fetch cache stores. |
| `as_of`        | if found | the period the value describes, `YYYY-MM-DD` or `YYYY-MM`. Must be within 60 days of the report date (enforced). |
| `queries_tried`| yes      | every query actually run, in order. `not_found` records need at least 3 distinct queries (enforced as a warning; 3+ is the floor for an honest not_found). |
| `sources_tried`| yes      | every source actually consulted, in order. |
| `reason`       | if value is null | why no value: `no_filed_data`, `paywall`, `source_unavailable`, `metric_not_published`, or a one-line explanation. A `found` record with `value: null` is invalid. |

## The null rule

A metric the company does not publish is recorded as:

```json
{ "key": "esg_score", "symbol": "XYZ", "status": "found",
  "value": null, "reason": "metric_not_published",
  "source_url": "https://xyz.in/investors", "retrieved_at": "...",
  "as_of": "2026-10-08", "queries_tried": [...], "sources_tried": [...] }
```

A metric nobody publishes anywhere is `status: "not_found"` with `value` absent and
≥3 queries. The report must then say "not published" — it must not substitute an
estimate, and it must not cite a page that does not contain the number.

## The fetch cache

Every `found` record's `source_url` must exist in the execution cache
(`scripts/.cache/fetched/`, one JSON per URL with `url`, `retrieved_at`, `text`).
Fetch with:

```bash
python3 scripts/fetch_cache.py --research scripts/.cache/research_<MARKET>_<date>.json
```

The cache stores the page exactly as fetched, with a sha256 of the stored text.
**Never hand-edit a cache entry or type a value from memory into a record** — the
citation gate's whole job is to fail when a value, a quote, or a page cannot be
matched to what was actually fetched. If a page changed after the fetch, re-fetch
(`--force`) and re-read the value.

## What the citation gate enforces

1. `found` with no http `source_url` → error.
2. `source_url` not in the fetch cache → error (`URL NOT IN CACHE`).
3. any scalar in `value` not present in the cached page text → error (`VALUE NOT IN CACHED TEXT`).
4. `as_of` older than 60 days before the report date → error.
5. `not_found` with fewer than 3 `queries_tried` → warning.
6. report-level source floor (dossiers 25, other reports 12) → error.

A record that passes all of these is admissible. A report citing an inadmissible
record is not finished.
