#!/usr/bin/env python3
"""Deterministic post-underwriting pipeline state machine for company dossiers.

Transitions a researched company between Shortlist and Discarded based strictly on
validated monograph evidence, never touching physical brokerage Holdings
(`data/accounts/<MKT>/*.transactions.jsonl`):

  1. DISCARD (`new_capital_verdict == "REJECTED"`, `business_quality_verdict == "FUNDAMENTAL_FAIL"`,
     or `conviction_tier == "TIER_0"`):
       - Removes the symbol from `data/shortlist/<MKT>.json` (`active`) and upserts a
         record into `data/discarded/<MKT>.json` (`items`). The published `_dossier.html`
         remains in `docs/blogs/<MKT>/` as institutional memory.
  2. KEEP_ON_SHORTLIST (all non-rejected underwritten names):
       - Upserts a schema-valid record into `data/shortlist/<MKT>.json` (`active`) with
         `status="COMPLETED"` and `research_cycle=target_cycle` for round-robin scheduling,
         and removes the symbol from `data/discarded/<MKT>.json` (`items`) if present.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import Draft7Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import portal_publish  # noqa: E402
import record_merge  # noqa: E402
from dossier_builder_template import _lookup_snapshot  # noqa: E402
from dossier_schema import load_monograph_spec, strip_html, validate_monograph_spec  # noqa: E402
from run_claims import _row_cycle  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SCHEMAS = REPO / "scripts" / "schemas"

VALID_BUCKETS = {
    "CORE_ALPHA", "TACTICAL_MOMENTUM", "LEVERAGED_SATELLITE",
    "LEAPS_OPTIONS", "REJECTED", "PENDING", "UNKNOWN",
}
VALID_STAGES = {"STAGE_1", "STAGE_2", "STAGE_3", "STAGE_4", "UNKNOWN"}
VALID_KPI = {"PASS", "PASS_WITH_WATCH", "FAIL", "PENDING", "UNKNOWN"}


def _norm_stage(raw: Any) -> str:
    s = str(raw or "").upper()
    for n in ("4", "3", "2", "1"):
        if f"STAGE_{n}" in s or f"STAGE {n}" in s:
            return f"STAGE_{n}"
    return "UNKNOWN"


def _norm_bucket(raw: Any) -> str:
    s = str(raw or "").upper().strip()
    return s if s in VALID_BUCKETS else "CORE_ALPHA"


def _norm_date(raw: Any) -> str:
    s = str(raw or "").strip()[:10]
    return s if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else dt.date.today().isoformat()


def _cap_tier(market: str, mcap: Any) -> str:
    if not isinstance(mcap, (int, float)) or mcap <= 0:
        return "Mid-Cap"
    if market == "IN":
        if mcap >= 100000:
            return "Large-Cap"
        if mcap >= 30000:
            return "Mid-Cap"
        if mcap >= 5000:
            return "Small-Cap"
        return "Micro-Cap"
    if mcap >= 200:
        return "Mega-Cap"
    if mcap >= 10:
        return "Large-Cap"
    if mcap >= 2:
        return "Mid-Cap"
    if mcap >= 0.3:
        return "Small-Cap"
    return "Micro-Cap"


def verify_review_and_quality_gates(
    dossier_path: Path,
    review_dir: Path | None = None,
    research_paths: List[str] | None = None,
    best_effort_after_round2: bool = False,
) -> None:
    """Refuse pipeline promotion/discard until mechanical and reviewer gates pass."""
    if not dossier_path.is_file():
        raise FileNotFoundError(f"Compiled dossier not found: {dossier_path}")
    portal_publish.require_modern_report(dossier_path)

    py = sys.executable
    r_proc = subprocess.run(
        [py, str(REPO / "scripts" / "readability_check.py"), str(dossier_path)],
        capture_output=True, text=True, check=False,
    )
    if r_proc.returncode != 0:
        raise ValueError(f"readability_check failed:\n{r_proc.stdout}{r_proc.stderr}")

    c_cmd = [py, str(REPO / "scripts" / "citation_check.py"), str(dossier_path), "--min-sources", "25", "--allow-stale-asof"]
    for rp in research_paths or []:
        c_cmd += ["--research", rp]
    c_proc = subprocess.run(c_cmd, capture_output=True, text=True, check=False)
    if c_proc.returncode != 0:
        raise ValueError(f"citation_check failed:\n{c_proc.stdout}{c_proc.stderr}")

    if review_dir is not None:
        if not review_dir.is_dir():
            raise ValueError(f"Review directory missing: {review_dir}")
        chosen_round = 2 if (review_dir / "round_2").is_dir() else 1
        r_folder = review_dir / f"round_{chosen_round}"
        rev_file = r_folder / f"round_{chosen_round}_review.json"
        if not rev_file.is_file():
            raise ValueError(f"Missing reviewer verdict file: {rev_file}")
        rev_json = json.loads(rev_file.read_text(encoding="utf-8"))
        rev_verdict = str(rev_json.get("verdict") or "").upper()
        if rev_verdict != "APPROVE" and not (chosen_round == 2 and best_effort_after_round2):
            raise ValueError(f"Reviewer verdict in {rev_file.name} is {rev_verdict!r}, not APPROVE")

        rt_file = r_folder / f"round_{chosen_round}_red_team.json"
        if not rt_file.is_file() and chosen_round == 2:
            # Red team only re-runs in round 2 if round 1 was non-APPROVE
            rt_file = review_dir / "round_1" / "round_1_red_team.json"
        if not rt_file.is_file():
            raise ValueError(f"Missing red_team verdict file: {rt_file}")
        rt_json = json.loads(rt_file.read_text(encoding="utf-8"))
        rt_verdict = str(rt_json.get("verdict") or "").upper()
        if rt_verdict != "APPROVE" and not (chosen_round == 2 and best_effort_after_round2):
            raise ValueError(f"Red-team verdict in {rt_file.name} is {rt_verdict!r}, not APPROVE")


def classify_pipeline_transition(spec: Dict[str, Any], snap_sym: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Determine (DISCARD | KEEP_ON_SHORTLIST, computed_metrics)."""
    verdict = str(spec["new_capital_verdict"]).upper()
    tier = str(spec.get("conviction_tier") or "TIER_2").upper()
    bq_obj = spec.get("business_quality") if isinstance(spec.get("business_quality"), dict) else {}
    bq_verdict = str(
        spec.get("business_quality_verdict")
        or bq_obj.get("business_quality_verdict")
        or ("FUNDAMENTAL_FAIL" if verdict == "REJECTED" else "CYCLICAL_CONDITIONAL" if tier == "TIER_3" else "COMPOUNDER_PASS")
    ).upper()
    kpi_health = str(
        spec.get("kpi_health")
        or bq_obj.get("kpi_health")
        or ("FAIL" if bq_verdict == "FUNDAMENTAL_FAIL" else "PASS_WITH_WATCH" if bq_verdict == "CYCLICAL_CONDITIONAL" else "PASS")
    ).upper()
    if kpi_health not in VALID_KPI:
        kpi_health = "PASS_WITH_WATCH"

    tv = snap_sym.get("tradingview") or {}
    close = tv.get("close") if isinstance(tv.get("close"), (int, float)) else float(spec.get("cmp") or spec.get("entry_zone_high") or 0.0)
    ez_low = float(spec["entry_zone_low"]) if spec.get("entry_zone_low") is not None else close
    ez_high = float(spec["entry_zone_high"]) if spec.get("entry_zone_high") is not None else close
    stop = float(spec["stop_loss"]) if spec.get("stop_loss") is not None else max(0.0, ez_low * 0.9)
    target_base = float(spec["target_base"]) if spec.get("target_base") is not None else close

    support_asym = (
        round((target_base - ez_high) / (ez_high - stop), 2)
        if (target_base > ez_high > stop)
        else 0.0
    )
    cmp_asym = (
        round((target_base - close) / (close - stop), 2)
        if (close > stop and target_base > close)
        else support_asym
    )

    metrics = {
        "verdict": verdict,
        "tier": tier,
        "business_quality_verdict": bq_verdict,
        "kpi_health": kpi_health,
        "close": round(float(close), 2),
        "support_asymmetry": support_asym,
        "cmp_asymmetry": cmp_asym,
    }

    if verdict == "REJECTED" or bq_verdict == "FUNDAMENTAL_FAIL" or tier == "TIER_0":
        return "DISCARD", metrics

    return "KEEP_ON_SHORTLIST", metrics


def apply_pipeline_transition(
    spec: Dict[str, Any],
    snapshots: Dict[str, Any],
    shortlist_data: Dict[str, Any],
    discarded_data: Dict[str, Any] | None = None,
    today_iso: str | None = None,
) -> Dict[str, Any]:
    """Mutate copies of shortlist_data and discarded_data according to deterministic rules and validate schemas."""
    sym = str(spec["symbol"]).upper()
    market = str(spec["market"]).upper()
    snap_sym = _lookup_snapshot(snapshots, sym)
    tv = snap_sym.get("tradingview") or {}
    fc = snap_sym.get("fundamental_card") or {}
    s2 = snap_sym.get("thewrap_stage2") or {}
    ev = snap_sym.get("stage2_evaluation") or {}

    transition, metrics = classify_pipeline_transition(spec, snap_sym)
    sl_rows = list(shortlist_data.get("active") or [])
    dc_rows = list((discarded_data or {}).get("items") or [])

    existing_sl = next((r for r in sl_rows if r.get("symbol") == sym), None)
    existing_dc = next((r for r in dc_rows if r.get("symbol") == sym), None)

    target_cycle = max([_row_cycle(r) for r in sl_rows] or [1])
    as_of = _norm_date(spec.get("as_of"))
    researched_date = _norm_date(today_iso or dt.date.today().isoformat())
    company_name = (
        (existing_sl or {}).get("company_name")
        or (existing_dc or {}).get("company_name")
        or tv.get("company_name")
        or str(spec.get("title") or sym).split("(")[0].split("—")[0].strip()
        or sym
    )
    sector = (
        spec.get("sector")
        or tv.get("sector")
        or fc.get("sector")
        or (existing_sl or {}).get("macro_sector")
        or (existing_dc or {}).get("macro_sector")
        or s2.get("thewrap_industry")
        or tv.get("industry")
    )
    stage = _norm_stage(spec.get("weinstein_stage") or ev.get("weinstein_stage") or (existing_sl or {}).get("weinstein_stage"))
    bucket = _norm_bucket(spec.get("strategy_bucket"))
    verdict = metrics["verdict"]
    gate_status = "PASSED" if verdict in {"IMMEDIATE_BUY", "ACCUMULATE_ON_DIP"} else ("FAIL" if verdict == "REJECTED" else "PASSED_CONDITIONAL")
    primer_summary = strip_html(spec.get("primer") or spec.get("holding_rationale") or "")[:320]

    if transition == "DISCARD":
        sl_rows = [r for r in sl_rows if r.get("symbol") != sym]
        dc_updated: Dict[str, Any] = dict(existing_dc or {})
        dc_updated.update({
            "symbol": sym,
            "company_name": company_name,
            "action_verdict": verdict,
            "discarded_date": researched_date,
            "reason": primer_summary or f"{spec.get('archetype', 'MONOGRAPH')}; {metrics['business_quality_verdict']}.",
            "macro_sector": sector,
            "weinstein_stage": stage,
            "research_dossier_path": f"blogs/{market}/{sym}_dossier.html",
            "as_of_date": as_of,
        })
        if existing_dc is not None:
            dc_rows = [dc_updated if r.get("symbol") == sym else r for r in dc_rows]
        else:
            dc_rows.append(dc_updated)
    else:
        dc_rows = [r for r in dc_rows if r.get("symbol") != sym]
        asym_val = max(
            0.01,
            metrics["cmp_asymmetry"] if verdict == "IMMEDIATE_BUY" and metrics["cmp_asymmetry"] > 0 else metrics["support_asymmetry"],
        )
        rsi_raw = tv.get("rsi_14_daily")
        rsi_clean = float(rsi_raw) if isinstance(rsi_raw, (int, float)) and 0 <= rsi_raw <= 100 else None
        rs_raw = s2.get("rs_pct")
        rs_clean = min(99.0, max(0.0, float(rs_raw))) if isinstance(rs_raw, (int, float)) else None
        mcap = tv.get("market_cap") if isinstance(tv.get("market_cap"), (int, float)) and tv.get("market_cap") >= 0 else None
        pe_val = tv.get("pe_ttm") if isinstance(tv.get("pe_ttm"), (int, float)) else fc.get("stock_pe")

        sl_updated: Dict[str, Any] = dict(existing_sl or {})
        sl_updated.update({
            "symbol": sym,
            "company_name": company_name,
            "source_type": sl_updated.get("source_type") or ("CURRENT_HOLDING" if spec.get("holding_action") != "NOT_HELD" else "UNDERWRITTEN_PIPELINE"),
            "status": "COMPLETED",
            "deep_research_status": "COMPLETED",
            "research_cycle": target_cycle,
            "strategy_bucket": bucket,
            "macro_sector": sector,
            "fine_subsector": tv.get("industry") or fc.get("industry") or sl_updated.get("fine_subsector"),
            "cap_tier": _cap_tier(market, mcap),
            "cmp": metrics["close"],
            "entry_zone_low": float(spec["entry_zone_low"]),
            "entry_zone_high": float(spec["entry_zone_high"]),
            "stop_loss": float(spec["stop_loss"]),
            "target_base": float(spec["target_base"]),
            "target_bull": float(spec["target_bull"]) if isinstance(spec.get("target_bull"), (int, float)) and spec["target_bull"] >= 0 else None,
            "asymmetry_ratio": round(asym_val, 2),
            "rsi_14": rsi_clean,
            "rs_rating": rs_clean,
            "1d_return_pct": tv.get("change_1d_pct"),
            "1w_return_pct": tv.get("perf_1w_pct"),
            "p_e": pe_val if isinstance(pe_val, (int, float)) else None,
            "market_cap": mcap,
            "roe_pct": tv.get("roe_pct") if isinstance(tv.get("roe_pct"), (int, float)) else fc.get("roe_pct"),
            "roce_pct": fc.get("roce_pct") if isinstance(fc.get("roce_pct"), (int, float)) else sl_updated.get("roce_pct"),
            "opm_pct": tv.get("operating_margin_ttm_pct") if isinstance(tv.get("operating_margin_ttm_pct"), (int, float)) else sl_updated.get("opm_pct"),
            "debt_to_equity": tv.get("debt_to_equity") if isinstance(tv.get("debt_to_equity"), (int, float)) else sl_updated.get("debt_to_equity"),
            "action_verdict": verdict,
            "action_verdict_detail": f"{spec.get('archetype', 'COMPOUNDER')}; {verdict.replace('_', ' ').lower()}; support R:R {metrics['support_asymmetry']:.2f}:1.",
            "weinstein_stage": stage,
            "weinstein_stage_detail": ev.get("summary_rationale") or f"Evaluated as {stage} as of {as_of}.",
            "kpi_health": metrics["kpi_health"],
            "gate_status": gate_status,
            "gate_status_detail": primer_summary or f"Underwritten in 10-chapter monograph ({as_of}).",
            "entry_posture": str(spec.get("entry_posture") or ev.get("entry_timing_posture") or verdict),
            "as_of_date": as_of,
            "stale_as_of": False,
            "last_researched_date": researched_date,
            "research_dossier_path": f"blogs/{market}/{sym}_dossier.html",
            "summary_rationale": primer_summary or f"Underwritten as {verdict}.",
            "invalidation_condition": f"Daily/weekly close below {spec['stop_loss']} or fundamental KPI breakdown.",
        })
        if existing_sl is not None:
            sl_rows = [sl_updated if r.get("symbol") == sym else r for r in sl_rows]
        else:
            sl_rows.append(sl_updated)

    shortlist_out = {**shortlist_data, "market": market, "as_of_date": researched_date, "active": sl_rows}
    discarded_out = {**(discarded_data or {}), "market": market, "as_of_date": researched_date, "items": dc_rows}

    sl_validator = Draft7Validator(json.loads((SCHEMAS / "shortlist_record.schema.json").read_text(encoding="utf-8")))
    dc_validator = Draft7Validator(json.loads((SCHEMAS / "discarded_record.schema.json").read_text(encoding="utf-8")))

    schema_errs: List[str] = []
    for idx, row in enumerate(shortlist_out["active"]):
        for err in sl_validator.iter_errors(row):
            schema_errs.append(f"shortlist[{idx}] ({row.get('symbol')}): {err.message}")
    for idx, row in enumerate(discarded_out["items"]):
        for err in dc_validator.iter_errors(row):
            schema_errs.append(f"discarded[{idx}] ({row.get('symbol')}): {err.message}")
    if schema_errs:
        raise ValueError("Pipeline sync produced schema errors: " + "; ".join(schema_errs))

    return {
        "symbol": sym,
        "market": market,
        "transition": transition,
        "metrics": metrics,
        "shortlist": shortlist_out,
        "discarded": discarded_out,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, help="Path to monograph spec directory or JSON file")
    ap.add_argument("--snapshot", required=True, help="Path to same-session snapshots JSON")
    ap.add_argument("--dossier", required=True, help="Path to compiled docs/blogs/<MKT>/<SYM>_dossier.html")
    ap.add_argument("--review-dir", default="", help="Optional <RUN_DIR>/review directory to enforce APPROVE gate")
    ap.add_argument("--research", action="append", default=[], help="Optional research_<MKT>_<date>.json for citation gate")
    ap.add_argument("--shortlist", default="", help="Override path to shortlist JSON")
    ap.add_argument("--discarded", default="", help="Override path to discarded JSON")
    ap.add_argument("--best-effort-after-round2", action="store_true", help="Allow sync after round 2 best-effort completion")
    ap.add_argument("--skip-gates", action="store_true", help="Skip external subprocess gates (unit tests only)")
    ap.add_argument("--dry-run", action="store_true", help="Print transition without writing files")
    args = ap.parse_args()

    spec = load_monograph_spec(args.spec)
    spec_errs, _ = validate_monograph_spec(spec)
    if spec_errs:
        raise SystemExit("Spec validation failed:\n - " + "\n - ".join(spec_errs))

    if not args.skip_gates:
        verify_review_and_quality_gates(
            Path(args.dossier),
            review_dir=Path(args.review_dir) if args.review_dir else None,
            research_paths=args.research,
            best_effort_after_round2=args.best_effort_after_round2,
        )

    market = str(spec["market"]).upper()
    sl_path = Path(args.shortlist) if args.shortlist else REPO / "data" / "shortlist" / f"{market}.json"
    dc_path = Path(args.discarded) if args.discarded else REPO / "data" / "discarded" / f"{market}.json"

    sl_raw = sl_path.read_text(encoding="utf-8") if sl_path.exists() else json.dumps({"market": market, "active": []}) + "\n"
    dc_raw = dc_path.read_text(encoding="utf-8") if dc_path.exists() else json.dumps({"market": market, "items": []}) + "\n"
    snapshots = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))

    res = apply_pipeline_transition(
        spec,
        snapshots=snapshots,
        shortlist_data=json.loads(sl_raw),
        discarded_data=json.loads(dc_raw),
    )

    print(
        f"PIPELINE SYNC [{res['market']}:{res['symbol']}] -> {res['transition']} "
        f"(verdict={res['metrics']['verdict']}, tier={res['metrics']['tier']}, "
        f"business={res['metrics']['business_quality_verdict']}, support_RR={res['metrics']['support_asymmetry']:.2f}:1)"
    )
    if args.dry_run:
        return

    sl_path.write_text(record_merge.dump(res["shortlist"], sl_raw), encoding="utf-8")
    dc_path.parent.mkdir(parents=True, exist_ok=True)
    dc_path.write_text(record_merge.dump(res["discarded"], dc_raw), encoding="utf-8")


if __name__ == "__main__":
    main()
