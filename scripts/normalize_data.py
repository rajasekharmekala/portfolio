#!/usr/bin/env python3
"""
W1 — One-shot (idempotent) schema normalization for portfolio data records.

Targets:
    data/shortlist/US.json, data/shortlist/IN.json
    data/watchlist/US.json, data/watchlist/IN.json

What it does (plan section 8, W1):
  1. Maps field names to one shared set across markets
     (US *_usd price fields -> cmp/entry_zone_low/...; strategy_book -> strategy_bucket).
  2. Normalizes action_verdict, weinstein_stage, kpi_health, gate_status,
     strategy_bucket and cap_tier to fixed enums (originals preserved in
     *_detail fields where they carry extra information).
  3. Removes emoji and collapses stray whitespace in all string fields.
  4. Converts non-numeric asymmetry values ("3.4:1" -> 3.4, "N/A" -> null).
  5. Normalizes as_of_date / last_researched_date to ISO dates ("unknown" when
     missing) and adds stale_as_of=true for rows older than 30 days before the
     latest as-of date in the same file, or with an unknown as-of date.
  6. Repoints dossier paths to docs/blogs/.

The script is idempotent: running it twice produces the same output.
Run with the venv interpreter:  .venv/bin/python scripts/normalize_data.py
"""

import datetime
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TODAY = datetime.date.today().isoformat()

SHORTLIST_FILES = ["data/shortlist/US.json", "data/shortlist/IN.json"]
WATCHLIST_FILES = ["data/watchlist/US.json", "data/watchlist/IN.json"]

US_RENAME = {
    "cmp_usd": "cmp",
    "entry_zone_low_usd": "entry_zone_low",
    "entry_zone_high_usd": "entry_zone_high",
    "stop_loss_usd": "stop_loss",
    "target_base_usd": "target_base",
    "target_bull_usd": "target_bull",
    "market_cap_usd_b": "market_cap",
    "strategy_book": "strategy_bucket",
}

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U0001F1E6-\U0001F1FF"
    "\U00002600-\U000027BF\U00002B00-\U00002BFF"
    "\U00002300-\U000023FF\u200d\u20e3\ufe0f]"
)

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
SCORE_RE = re.compile(r"(\d+)\s*(?:PASS)?\s*/\s*(\d+)")

BUCKET_MAP = {
    "CORE": "CORE_ALPHA",
    "CORE_ALPHA": "CORE_ALPHA",
    "CORE_ALPHA_BOOK": "CORE_ALPHA",
    "TACTICAL": "TACTICAL_MOMENTUM",
    "TACTICAL_MOMENTUM": "TACTICAL_MOMENTUM",
    "TACTICAL_GROWTH": "TACTICAL_MOMENTUM",
    "LEVERAGED": "LEVERAGED_SATELLITE",
    "LEVERAGED_SATELLITE": "LEVERAGED_SATELLITE",
    "SATELLITE": "LEVERAGED_SATELLITE",
    "LEAPS": "LEAPS_OPTIONS",
    "LEAPS_OPTIONS": "LEAPS_OPTIONS",
    "REJECTED": "REJECTED",
    "REJECTED_BELOW_HURDLE": "REJECTED",
    "DISQUALIFIED": "REJECTED",
    "PENDING": "PENDING",
    "PENDING_RESEARCH": "PENDING",
}

CAP_TIER_MAP = {
    "LARGE CAP": "Large-Cap",
    "MID CAP": "Mid-Cap",
    "SMALL CAP": "Small-Cap",
    "MICRO CAP": "Micro-Cap",
    "MEGA CAP": "Mega-Cap",
}


# ---------------------------------------------------------------- strings

def clean_str(v):
    """Remove emoji and collapse whitespace; returns '' for None."""
    if v is None:
        return ""
    if not isinstance(v, str):
        return v
    s = EMOJI_RE.sub("", v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------------------------------------------------------------- enums

def norm_action_verdict(v):
    if not isinstance(v, str):
        v = "" if v is None else str(v)
    s = clean_str(v).upper()
    if not s or s in ("NONE", "N/A"):
        return "PENDING"
    s = s.replace("/", " ")
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if s in ("IMMEDIATE_BUY", "BUY", "BUY_NOW", "STRONG_BUY"):
        return "IMMEDIATE_BUY"
    if s.startswith("ACCUMULATE"):
        return "ACCUMULATE_ON_DIP"
    if s in ("KEEP_COMPOUNDING", "HOLD", "KEEP", "COMPOUND"):
        return "KEEP_COMPOUNDING"
    if s in ("WAIT_FOR_SUPPORT", "WAIT", "WAIT_FOR_DIP"):
        return "WAIT_FOR_SUPPORT"
    if s in ("TRIM_PROFIT_BOOKING", "TRIM", "TAKE_PROFIT", "PROFIT_BOOKING"):
        return "TRIM_PROFIT_BOOKING"
    if s.startswith("REPLACE"):
        return "REPLACE_UNDERPERFORMER"
    if s == "RESEARCH_REQUIRED" or s == "RESEARCH_REQD":
        return "RESEARCH_REQUIRED"
    if s in ("PENDING", "PENDING_RESEARCH"):
        return "PENDING"
    if s in ("REJECTED", "REJECT", "AVOID") or s.startswith("AVOID"):
        return "REJECTED"
    if s in ("QUALIFIED_CORE_ALPHA", "QUALIFIED_TACTICAL_MOMENTUM", "QUALIFIED"):
        return "QUALIFIED"
    if s == "QUALIFIED_DEFERRED":
        return "WAIT_FOR_SUPPORT"
    if s in ("SELL_REALLOCATE", "SELL_AND_REALLOCATE"):
        return "TRIM_PROFIT_BOOKING"
    if s in ("ON_HOLD", "HOLD_ENTRY"):
        return "PENDING"
    return s  # unexpected: validation will surface it


VERDICT_ENUM = {"IMMEDIATE_BUY", "ACCUMULATE_ON_DIP", "KEEP_COMPOUNDING", "WAIT_FOR_SUPPORT",
                "TRIM_PROFIT_BOOKING", "REPLACE_UNDERPERFORMER", "REJECTED", "QUALIFIED",
                "PENDING", "RESEARCH_REQUIRED"}


def verdict_detail(raw, normalized):
    """Preserve the original verdict text when it was not already canonical."""
    raw = clean_str(raw)
    if raw and raw.upper() not in VERDICT_ENUM and raw.upper() != normalized:
        return raw
    return None


def norm_weinstein(v):
    """Returns (stage, detail)."""
    if not isinstance(v, str):
        v = "" if v is None else str(v)
    s = clean_str(v)
    if not s or s.upper() in ("NONE", "N/A"):
        return "UNKNOWN", None
    u = s.upper()
    stage = None
    for cand in ("STAGE_4", "STAGE_3", "STAGE_2", "STAGE_1"):
        if cand in u:
            stage = cand
            break
    if stage is None:
        m = re.match(r"^\s*(\d)", u)
        if m and m.group(1) in "1234":
            stage = "STAGE_" + m.group(1)
        else:
            return "UNKNOWN", s
    detail = s if u not in ("1", "2", "3", "4", stage) else None
    return stage, detail


def norm_kpi(v):
    """Returns (kpi_health, kpi_score)."""
    if not isinstance(v, str):
        v = "" if v is None else str(v)
    s = clean_str(v)
    if not s or s.upper() in ("NONE", "N/A"):
        return "UNKNOWN", None
    u = s.upper()
    if "PENDING" in u:
        return "PENDING", None
    score = None
    m = SCORE_RE.search(u)
    if m:
        score = f"{m.group(1)}/{m.group(2)}"
    if "FAIL" in u:
        return "FAIL", score
    if score:
        n, d = int(m.group(1)), int(m.group(2))
        return ("PASS" if n >= d else "PASS_WITH_WATCH"), score
    if "WATCH" in u:
        return "PASS_WITH_WATCH", None
    if any(w in u for w in ("GREEN", "STRONG", "HEALTHY", "PASS")):
        return "PASS", None
    if "AVERAGE" in u:
        return "PASS_WITH_WATCH", None
    return "UNKNOWN", None


def norm_gate(v):
    """Returns (gate_status, detail)."""
    if not isinstance(v, str):
        v = "" if v is None else str(v)
    s = clean_str(v)
    if not s or s.upper() in ("NONE", "N/A"):
        return "UNKNOWN", None
    u = s.upper()
    detail = None if u in ("PASS", "PASSED", "ALL_GATES_PASSED", "PENDING") else s
    if "PENDING" in u:
        return "PENDING", detail
    if u in ("PASS", "PASSED", "ALL_GATES_PASSED"):
        return "PASSED", None
    if u.startswith("ALL_GATES_PASSED"):
        return "PASSED", detail
    if "FAIL" in u:
        return "FAIL", detail
    if "CONDITIONAL" in u:
        return "PASSED_CONDITIONAL", detail
    if u in ("PASS_FINANCIAL", "PARTIAL"):
        return "PARTIAL", detail
    return "UNKNOWN", detail


def norm_bucket(v):
    if not isinstance(v, str):
        v = "" if v is None else str(v)
    s = clean_str(v).upper()
    if not s or s in ("NONE", "N/A", "NULL"):
        return "UNKNOWN"
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return BUCKET_MAP.get(s, "UNKNOWN")


def norm_cap_tier(v):
    if not isinstance(v, str):
        v = "" if v is None else str(v)
    s = clean_str(v).upper()
    if not s or s in ("NONE", "N/A", "NULL"):
        return None
    s = re.sub(r"[\s\-_]+", " ", s).strip()
    return CAP_TIER_MAP.get(s, "UNKNOWN")


# ---------------------------------------------------------------- values

def norm_date(v, default="unknown"):
    if v is None:
        return default
    s = str(v).strip()
    if not s or s.upper() in ("NONE", "N/A", "NULL"):
        return default
    m = DATE_RE.search(s)
    if m:
        y, mo, dd = (int(g) for g in m.groups())
        try:
            return datetime.date(y, mo, dd).isoformat()
        except ValueError:
            return default
    for fmt in ("%d %b %Y", "%d %B %Y", "%b %d %Y", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return default


def norm_asymmetry(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        v = float(v)
        return v if v > 0 else None
    s = clean_str(v)
    if not s or s.upper() in ("NONE", "N/A", "NULL"):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?::\s*1|\bx\b)", s, re.I)
    if m:
        v = float(m.group(1))
        return v if v > 0 else None
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        v = float(s)
        return v if v > 0 else None
    return None


def norm_num(v, pct=False):
    """Coerce a numeric-ish value: '+1.8%' -> 1.8, '1.2 ATR' -> 1.2,
    '3.0x Daily Reset' -> 3.0, 'N/A' -> None, 'Net Cash' -> 0.0."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = clean_str(str(v))
    if not s or s.upper() in ("NONE", "N/A", "NULL", "TBD", "-"):
        return None
    if s.upper() in ("CASH POSITIVE", "NET CASH", "CASH RICH", "NO DEBT"):
        return 0.0
    s2 = re.sub(r"\bATR\b|\bX\b", " ", s, flags=re.I)
    if pct:
        s2 = s2.rstrip("%")
    m = re.search(r"-?\d+(?:\.\d+)?", s2)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def norm_int(v):
    """'CYCLE_1' -> 1, 1 -> 1, 'None' -> None."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    s = clean_str(str(v)).upper()
    if not s or s in ("NONE", "N/A", "NULL"):
        return None
    m = re.search(r"\d+", s)
    return int(m.group(0)) if m else None


def norm_dossier_path(v):
    if v is None:
        return None
    s = clean_str(v)
    if not s or s.upper() in ("NONE", "N/A"):
        return None
    if s.startswith("googledrive/"):
        s = "docs/" + s[len("googledrive/"):]
    elif s.startswith("blogs/"):
        s = "docs/" + s
    return s


# ---------------------------------------------------------------- records

def apply_renames(row, renames):
    row = dict(row)
    for old, new in renames.items():
        if old in row:
            if new not in row:
                row[new] = row.pop(old)
            else:
                row.pop(old)
    return row


def clean_row_strings(row):
    for k, v in list(row.items()):
        if isinstance(v, str):
            row[k] = clean_str(v)
    return row


PCT_FIELDS = ["1d_return_pct", "1w_return_pct", "2w_return_pct", "dist_from_20dma_pct"]
NUM_FIELDS = [
    "distance_from_support_atr", "rs_rating", "p_e", "market_cap", "roe_pct",
    "roic_pct", "roce_pct", "debt_to_equity", "debt_to_ebitda", "gross_margin_pct",
    "fcf_margin_pct", "opm_pct", "cfo_to_pat", "3y_revenue_cagr_pct",
    "3y_sales_cagr_pct", "3y_pat_cagr_pct", "entry_zone_low", "entry_zone_high",
    "stop_loss", "target_base", "target_bull", "cmp", "leverage_multiplier",
]


STAGE_ENUM = {"STAGE_1", "STAGE_2", "STAGE_3", "STAGE_4", "UNKNOWN"}
KPI_ENUM = {"PASS", "PASS_WITH_WATCH", "FAIL", "PENDING", "UNKNOWN"}
GATE_ENUM = {"PASSED", "PASSED_CONDITIONAL", "PARTIAL", "FAIL", "PENDING", "UNKNOWN"}


def normalize_shortlist_row(row):
    row = apply_renames(row, US_RENAME)
    row = clean_row_strings(row)

    # Enum fields are only re-mapped when not already canonical, so re-running
    # the script never loses *_detail / kpi_score information (idempotency).
    raw_verdict = row.get("action_verdict") or ""
    if raw_verdict.upper() not in VERDICT_ENUM:
        row["action_verdict"] = norm_action_verdict(raw_verdict)
        detail = verdict_detail(raw_verdict, row["action_verdict"])
        if detail:
            row["action_verdict_detail"] = detail

    for f in PCT_FIELDS:
        if f in row:
            row[f] = norm_num(row[f], pct=True)
    for f in NUM_FIELDS:
        if f in row:
            row[f] = norm_num(row[f])

    stage = row.get("weinstein_stage")
    if stage not in STAGE_ENUM:
        stage, detail = norm_weinstein(stage)
        row["weinstein_stage"] = stage
        if detail is not None:
            row["weinstein_stage_detail"] = detail
        else:
            row.pop("weinstein_stage_detail", None)
    elif stage == "UNKNOWN" and row.get("weinstein_stage_detail") in (None, "UNKNOWN"):
        row.pop("weinstein_stage_detail", None)

    kh = row.get("kpi_health")
    if kh not in KPI_ENUM:
        kh, score = norm_kpi(kh)
        row["kpi_health"] = kh
        row["kpi_score"] = score

    g = row.get("gate_status")
    if g not in GATE_ENUM:
        g, gdetail = norm_gate(g)
        row["gate_status"] = g
        if gdetail:
            row["gate_status_detail"] = gdetail

    row["strategy_bucket"] = norm_bucket(row.get("strategy_bucket"))

    if "cap_tier" in row and row["cap_tier"] not in (None, ""):
        row["cap_tier"] = norm_cap_tier(row["cap_tier"])

    row["asymmetry_ratio"] = norm_asymmetry(row.get("asymmetry_ratio"))
    row["as_of_date"] = norm_date(row.get("as_of_date"))
    row["last_researched_date"] = norm_date(row.get("last_researched_date"))
    row["research_dossier_path"] = norm_dossier_path(row.get("research_dossier_path"))
    return row


def normalize_watchlist_row(row):
    row = dict(row)
    row = clean_row_strings(row)

    # merge redundant legacy strategy_book into strategy_bucket
    if "strategy_book" in row:
        from_book = norm_bucket(row.get("strategy_book"))
        from_field = norm_bucket(row.get("strategy_bucket"))
        merged = from_field if from_field != "UNKNOWN" else from_book
        row["strategy_bucket"] = merged
        row.pop("strategy_book")

    raw_verdict = row.get("action_verdict") or ""
    if raw_verdict.upper() not in VERDICT_ENUM:
        row["action_verdict"] = norm_action_verdict(raw_verdict)
        detail = verdict_detail(raw_verdict, row["action_verdict"])
        if detail:
            row["action_verdict_detail"] = detail

    if row.get("source_type") in (None, ""):
        row["source_type"] = "unknown"
    row["research_cycle"] = norm_int(row.get("research_cycle"))

    s = clean_str(row.get("status")).upper()
    status_map = {
        "COMPLETED": "COMPLETED",
        "RESEARCH_REQUIRED": "RESEARCH_REQUIRED",
        "REJECTED": "REJECTED",
        "UNDERWRITTEN": "UNDERWRITTEN",
        "ARCHIVED": "ARCHIVED",
        "PENDING": "PENDING",
        "UNKNOWN": "UNKNOWN",
    }
    row["status"] = status_map.get(s, "UNKNOWN")

    kh = row.get("kpi_health")
    if kh not in KPI_ENUM:
        kh, score = norm_kpi(kh)
        row["kpi_health"] = kh
        row["kpi_score"] = score

    g = row.get("gate_status")
    if g not in GATE_ENUM:
        g, gdetail = norm_gate(g)
        row["gate_status"] = g
        if gdetail:
            row["gate_status_detail"] = gdetail

    row["strategy_bucket"] = norm_bucket(row.get("strategy_bucket"))
    row["as_of_date"] = norm_date(row.get("as_of_date"))
    row["last_researched_date"] = norm_date(row.get("last_researched_date"))
    return row


def normalize_swap_row(row):
    row = apply_renames(row, {"strategy_book": "strategy_bucket"})
    row = clean_row_strings(row)
    if "timestamp" in row and row["timestamp"]:
        row["timestamp"] = norm_date(row["timestamp"], default=row["timestamp"])
    return row


# ---------------------------------------------------------------- stale

STALE_DAYS = 30


def flag_stale(rows):
    """rows: list of normalized rows. Sets stale_as_of on each (in place)."""
    dates = [r["as_of_date"] for r in rows if r.get("as_of_date", "unknown") != "unknown"]
    if not dates:
        for r in rows:
            r["stale_as_of"] = True
        return
    latest = max(dates)
    cutoff = (datetime.date.fromisoformat(latest) - datetime.timedelta(days=STALE_DAYS)).isoformat()
    for r in rows:
        d = r.get("as_of_date", "unknown")
        r["stale_as_of"] = d == "unknown" or d < cutoff


# ---------------------------------------------------------------- main

def process_file(path, kind):
    full = REPO / path
    data = json.loads(full.read_text(encoding="utf-8"))
    changed = 0

    if kind == "shortlist":
        all_rows = []
        for sheet, rows in data["sheets"].items():
            norm = []
            for row in rows:
                if sheet == "Swap_Decision_Matrix":
                    norm.append(normalize_swap_row(row))
                else:
                    norm.append(normalize_shortlist_row(row))
            all_rows.extend(norm)
            data["sheets"][sheet] = norm
        flag_stale(all_rows)
        schema_refs = ["scripts/schemas/shortlist_record.schema.json",
                       "scripts/schemas/swap_decision.schema.json"]
    else:
        all_rows = []
        for bucket in ("active", "archive"):
            norm = [normalize_watchlist_row(r) for r in data[bucket]]
            data[bucket] = norm
            all_rows.extend(norm)
        flag_stale(all_rows)
        schema_refs = ["scripts/schemas/watchlist_record.schema.json"]

    data["normalization"] = {
        "schema_version": 2,
        "normalized_at": TODAY,
        "schemas": schema_refs,
        "notes": (
            "Field names unified across markets (cmp, entry_zone_*, stop_loss, "
            "target_*, market_cap, strategy_bucket). Enums normalized: "
            "action_verdict, weinstein_stage, kpi_health, gate_status, "
            "strategy_bucket, cap_tier. Emoji removed. Non-numeric asymmetry "
            "converted to number or null. Dossier paths repointed to docs/blogs/. "
            f"stale_as_of=true for as-of dates older than {STALE_DAYS} days "
            "before the latest as-of date in this file, or unknown."
        ),
    }

    full.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if kind == "shortlist":
        n = sum(len(v) for v in data["sheets"].values())
    else:
        n = len(data["active"]) + len(data["archive"])
    print(f"normalized {path}: {n} records")


def main():
    for path in SHORTLIST_FILES:
        process_file(path, "shortlist")
    for path in WATCHLIST_FILES:
        process_file(path, "watchlist")
    print("done. Re-run scripts/validate_data.py to verify.")


if __name__ == "__main__":
    main()
