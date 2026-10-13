#!/usr/bin/env python3
"""Citation gate for generated reports and dossiers (Stage 9b).

Four checks:
  1. SOURCE FLOOR — a full company report must cite >= --min-sources (default
     25) distinct primary source URLs.
  2. URL IN CACHE — every research record with status "found" must have its
     source_url present in the execution cache (built by scripts/fetch_cache.py).
     If the cache directory does not exist at all, these degrade to warnings
     (the cache is expected to be built in W6); if it exists, a missing entry
     is a hard error.
  3. VALUE IN CACHED TEXT — each scalar value in a found research record must
     appear (tolerant of number/currency/percent formatting) in the cached
     body text for its source_url.
  4. AS-OF — each found record must carry a parseable as_of within
     --max-age-days of the report date.

Usage:
  .venv/bin/python scripts/citation_check.py docs/blogs/US/ADBE_dossier.html
      [--research scripts/.cache/research_US_*.json ...]
      [--cache-dir scripts/.cache/fetched]
      [--min-sources 25] [--max-age-days 60] [--allow-stale-asof]

--allow-stale-asof turns check 4 failures into listed "EXCEPTION AS-OF" lines
(result "PASS WITH EXCEPTIONS"); every exception must then be disclosed in the
report's gate-exceptions section.

Exit 1 on any error.
"""

import argparse
import datetime as _dt
import glob
import json
import os
import re
import sys

HREF_RE = re.compile(r'href="([^"]+)"')
REPORT_DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')
# asset / tracker / search domains are not primary sources
EXCLUDE_DOMAINS = ('googleapis.com', 'gstatic.com', 'duckduckgo.com',
                   'google.com/search', 'bing.com', 'yahoo.com/search',
                   'tradingview.com', 'finviz.com', 'screener.in',
                   'trendlyne.com')
REF_HEAD_RE = re.compile(r'id="[^"]*(references|bibliograph|citations)[^"]*"', re.I)


def external_urls(html):
    """Distinct external source URLs cited in the report (fragments stripped)."""
    seen = []
    for m in HREF_RE.finditer(html):
        u = m.group(1).strip()
        if not u.lower().startswith('http'):
            continue
        if any(d in u.lower() for d in EXCLUDE_DOMAINS):
            continue
        u = u.split('#')[0].split('?')[0].rstrip('/')
        if u not in seen:
            seen.append(u)
    return seen


def ref_list_count(html):
    """Number of <li> entries in the References/Bibliography section, if any.
    Dossiers cite primary sources as bibliography entries (with or without
    URLs); that count is the canonical source count for company reports."""
    m = REF_HEAD_RE.search(html)
    if not m:
        return 0
    tail = html[m.end():]
    end = tail.find('</ol>')
    if end == -1:
        end = tail.find('</ul>')
    if end == -1:
        return 0
    return len(re.findall(r'<li[ >]', tail[:end]))


def source_count(html):
    """(count, urls, ref_items) — bibliography entries when present, else URLs."""
    urls = external_urls(html)
    refs = ref_list_count(html)
    return (refs if refs > 0 else len(urls), urls, refs)


def report_date(path):
    m = REPORT_DATE_RE.search(os.path.basename(path))
    if m:
        try:
            return _dt.date.fromisoformat(m.group(1))
        except ValueError:
            pass
    return _dt.date.today()


def parse_asof(v):
    if not isinstance(v, str):
        return None
    v = v.strip()
    for fmt in ('%Y-%m-%d', '%Y-%m'):
        try:
            return _dt.datetime.strptime(v, fmt).date()
        except ValueError:
            pass
    return None


def load_cache(cache_dir):
    """url -> {retrieved_at, text} from the execution cache (one JSON per URL)."""
    if not cache_dir or not os.path.isdir(cache_dir):
        return None
    cache = {}
    for f in glob.glob(os.path.join(cache_dir, '*.json')):
        try:
            e = json.load(open(f, encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(e, dict) and e.get('url'):
            cache[str(e['url']).split('#')[0].split('?')[0].rstrip('/')] = e
    return cache


def load_research(paths):
    items = []
    for p in paths:
        try:
            d = json.load(open(p, encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue
        rows = d.get('items', d) if isinstance(d, dict) else d
        if isinstance(rows, list):
            items.extend(r for r in rows if isinstance(r, dict))
    return items


def value_variants(v):
    """Tolerant surface forms of a research value for text matching."""
    out = []
    s = str(v).strip()
    out.append(s)
    num = re.sub(r'[^0-9.\-]', '', s)
    if num and num not in ('.', '-', '.-'):
        out.append(num)
        if num.lstrip('-').isdigit():
            out.append(f"{int(num):,}")
            try:
                out.append(f"{float(num):.2f}")
            except ValueError:
                pass
    return out


def check(report, research_paths, cache_dir, min_sources, max_age_days,
          allow_stale_asof=False):
    """Return (errors, warns). With allow_stale_asof, a stale as_of is not an
    error: it is listed in warns with an "EXCEPTION AS-OF" prefix so the
    report can disclose it (see _COMMON.md, Gate exceptions)."""
    errors, warns = [], []
    html = open(report, encoding='utf-8').read()
    count, urls, refs = source_count(html)
    if count < min_sources:
        errors.append(f"SOURCE FLOOR: {count} distinct cited sources "
                      f"({refs} bibliography entries, {len(urls)} distinct "
                      f"source URLs) < {min_sources} (a full company report "
                      f"needs at least {min_sources} distinct primary sources)")

    cache = load_cache(cache_dir)
    no_cache = cache is None
    items = load_research(research_paths)
    if not items:
        if not no_cache:
            errors.append("NO RESEARCH RECORDS: pass --research with the run's "
                          "research JSON (found items must be cache-verified)")
        else:
            warns.append("no research records / no execution cache: "
                         "URL and value verification skipped "
                         "(build the cache with scripts/fetch_cache.py)")
        return errors, warns

    ref = report_date(report)
    for it in items:
        label = it.get('key', '?')
        if it.get('symbol'):
            label = f"{it['symbol']}:{label}"
        status = (it.get('status') or '').lower()
        if status == 'not_found':
            if len(it.get('queries_tried', [])) < 3:
                warns.append(f"NOT_FOUND {label}: fewer than 3 queries_tried "
                             "recorded — not a legitimate negative")
            continue
        if status not in ('found', 'confirmed'):
            continue

        # 4. as-of
        asof = parse_asof(it.get('as_of'))
        if asof is None:
            errors.append(f"AS-OF {label}: missing or unparseable as_of "
                          f"({it.get('as_of')!r})")
        elif (ref - asof).days > max_age_days:
            msg = (f"AS-OF {label}: {it.get('as_of')} is "
                   f"{(ref - asof).days} days older than report date "
                   f"{ref.isoformat()} (max {max_age_days})")
            if allow_stale_asof:
                warns.append("EXCEPTION " + msg)
            else:
                errors.append(msg)

        u = (it.get('source_url') or '').split('#')[0].split('?')[0].rstrip('/')
        if not u.startswith('http'):
            errors.append(f"CITATION {label}: found status but no http "
                          "source_url")
            continue
        if no_cache:
            continue
        entry = cache.get(u)
        if entry is None:
            errors.append(f"URL NOT IN CACHE {label}: {u} — fetch it into the "
                          "execution cache (scripts/fetch_cache.py)")
            continue
        text = str(entry.get('text') or '').lower()
        if not text.strip():
            errors.append(f"CACHE EMPTY {label}: {u} has no cached text")
            continue
        # 3. values in cached text (period is metadata, not a value)
        val = it.get('value')
        scalars = []
        if isinstance(val, dict):
            scalars = [v for k, v in val.items()
                       if k != 'period' and isinstance(v, (str, int, float))]
        elif isinstance(val, (str, int, float)):
            scalars = [val]
        for v in scalars:
            variants = value_variants(v)
            if not any(x.lower() in text for x in variants):
                errors.append(f"VALUE NOT IN CACHED TEXT {label}: {v!r} not "
                              f"found in cached text of {u}")
    return errors, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('report')
    ap.add_argument('--research', action='append', default=[])
    ap.add_argument('--cache-dir', default=os.path.join('scripts', '.cache', 'fetched'))
    ap.add_argument('--min-sources', type=int, default=25)
    ap.add_argument('--max-age-days', type=int, default=60)
    ap.add_argument('--allow-stale-asof', action='store_true',
                    help='list stale as_of dates as disclosed EXCEPTIONs instead of failing '
                         '(use when the latest periodic filing is older than --max-age-days; '
                         'every exception must be disclosed in the report)')
    args = ap.parse_args()

    # auto-detect research files when none given
    research = args.research
    if not research:
        research = sorted(glob.glob(os.path.join('scripts', '.cache', 'research_*.json')))

    errors, warns = check(args.report, research, args.cache_dir,
                          args.min_sources, args.max_age_days,
                          allow_stale_asof=args.allow_stale_asof)
    count, urls, refs = source_count(open(args.report, encoding='utf-8').read())
    print(f"cited distinct sources: {count} ({refs} bibliography, "
          f"{len(urls)} URLs; floor {args.min_sources})")
    for w in warns:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  FAIL  {e}")
    excepted = any(w.startswith("EXCEPTION") for w in warns)
    print("CITATION CHECK: " + ("FAIL" if errors else "PASS WITH EXCEPTIONS" if excepted else "PASS"))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
