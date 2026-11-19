#!/usr/bin/env python3
"""Deterministic CIO Portfolio Construction, Risk-Heat, Hysteresis & Convergence Engine.

Replaces improvised LLM portfolio math with a single reproducible engine governed by
`.agents/config/scoring.json` (schema v4).

Key guarantees:
  1. Zero-Hallucination Accounting: current values + cash + options == target values + target cash + options
     == net_worth (reconciled to 0.01 precision; integer shares for IN and US orders).
  2. Tracking Position Isolation: stubs < 0.35% of NAV (e.g. 1-share trackers) are excluded from
     the 12-15 active risk-slot count, portfolio averages, and rebalance churn.
  3. Asymmetric Sector Rotation & 25% Cluster Risk Cap: medium-term 3M RS + TheWrap Stage 2 breadth
     gates TACTICAL_MOMENTUM entries and 2x/3x sector swings, while CORE_ALPHA ignores short-term
     sector dips; any correlated/thematic cluster (r >= 0.65) is capped at 25% NAV / 3.5% heat.
  4. Regime-Adaptive 50/50 Tranche Sizing: in Sideways/Narrow tapes, starters require proximity to
     support (<= 4%) and tactical winners harvest 35% at +2R; in Broad Uptrends, starters deploy
     within 8.5% of 10W EMA and let winners run to 22%.
  5. 2x/3x & Drawdown Options Governance: sector-only 2x/3x swings (<= 12% cap, 20D EMA stop,
     15-session time stop, single-stock 2x ETFs phased out); LEAPS/Calls capped at 10% of max(cost, MV)
     with 15% combined decay ceiling, grandfathering existing contracts on chart invalidation stops.
  6. Short-Horizon Stability & Monotonic Convergence: persists anchor plan in `data/allocations/<MKT>.json`
     with a 5-day hysteresis lock (±2.5% price deadband, upward-only stop ratchet, +5pt incumbent buffer)
     and a ±1.25% NAV rebalance deadband so user edits converge cleanly toward zero trades.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
SCORING_PATH = REPO / ".agents" / "config" / "scoring.json"

SINGLE_STOCK_LEVERAGED_ETFS: Dict[str, Tuple[str, float]] = {
    "MSTX": ("MSTR", 2.0), "MSTU": ("MSTR", 2.0), "OCNL": ("ORCL", 2.0),
    "NVDL": ("NVDA", 2.0), "NVDU": ("NVDA", 2.0), "TSLL": ("TSLA", 2.0),
    "CONL": ("COIN", 2.0), "AMDL": ("AMD", 2.0), "MSFU": ("MSFT", 2.0),
    "GGLL": ("GOOG", 2.0), "AAPU": ("AAPL", 2.0), "METU": ("META", 2.0),
}
SECTOR_INDEX_LEVERAGED_ETFS: Dict[str, Tuple[str, float]] = {
    "SOXL": ("Semiconductors", 3.0),
    "FAS": ("Financials", 3.0),
    "KORU": ("South Korea Index", 3.0),
    "TQQQ": ("Nasdaq 100", 3.0),
    "UPRO": ("S&P 500", 3.0),
    "SPXL": ("S&P 500", 3.0),
    "TECL": ("Technology", 3.0),
    "LABU": ("Biotech", 3.0),
    "TNA": ("Small Caps", 3.0),
    "QLD": ("Nasdaq 100", 2.0),
    "SSO": ("S&P 500", 2.0),
    "USD": ("Semiconductors", 2.0),
}
CASH_EQUIV_ETFS = {"NBIL", "SGOV", "BIL", "SHV", "USFR", "TFLO", "LIQUIDBEES", "LIQUIDCASE", "LIQUIDIETF"}


def _num(val: Any, nd: int = 2) -> Optional[float]:
    if val is None or isinstance(val, bool):
        return None
    try:
        f = float(val)
        return round(f, nd) if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _load_json(path: Optional[str | Path]) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalize_stage(raw: Any) -> str:
    if raw is None:
        return "UNKNOWN"
    s = str(raw).upper().strip()
    if s in {"1", "STAGE_1", "STAGE 1"} or "STAGE_1" in s or "STAGE 1" in s:
        return "STAGE_1"
    if s in {"2", "STAGE_2", "STAGE 2"} or "STAGE_2" in s or "STAGE 2" in s:
        return "STAGE_2"
    if s in {"3", "STAGE_3", "STAGE 3"} or "STAGE_3" in s or "STAGE 3" in s:
        return "STAGE_3"
    if s in {"4", "STAGE_4", "STAGE 4"} or "STAGE_4" in s or "STAGE 4" in s:
        return "STAGE_4"
    return "UNKNOWN"


def _days_between(d1: Optional[str], d2: Optional[str]) -> Optional[int]:
    if not d1 or not d2:
        return None
    try:
        return abs((dt.date.fromisoformat(str(d2)[:10]) - dt.date.fromisoformat(str(d1)[:10])).days)
    except ValueError:
        return None


def _account_qty_as_of(market: str, symbol: str, as_of_date: Optional[str]) -> Optional[float]:
    """Replay append-only account transaction logs up to `as_of_date` so dossier TRIM share counts converge cleanly."""
    if not as_of_date:
        return None
    acct_dir = REPO / "data" / "accounts" / market.upper()
    if not acct_dir.is_dir():
        return None
    cutoff = str(as_of_date)[:10]
    target = symbol.upper()
    qty = 0.0
    seen = False
    for p in sorted(acct_dir.glob("*.transactions.jsonl")):
        try:
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if str(row.get("symbol") or "").upper() != target:
                    continue
                seen = True
                rdate = str(row.get("date") or "")[:10]
                if rdate and rdate > cutoff:
                    continue
                typ = str(row.get("type") or "").lower()
                q = float(row.get("quantity") or 0.0)
                if typ in {"opening", "buy", "split"}:
                    qty += q
                elif typ == "sell":
                    qty = max(0.0, qty - q)
        except Exception:
            continue
    return round(qty, 6) if seen else None


def _normalize_tier(raw: Any, default: str = "TIER_3") -> str:
    s = str(raw or "").upper().strip()
    if s in {"TIER_1", "TIER_2", "TIER_3", "TIER_4", "TIER_0"}:
        return s
    if s in {"REJECTED", "AVOID", "FAIL", "NONE"}:
        return "TIER_0"
    return default


def _load_dossier_spine(market: str, symbol: str) -> Dict[str, Any]:
    spine_p = REPO / "data" / "dossiers" / market / symbol / "spine.json"
    bq_p = REPO / "data" / "dossiers" / market / symbol / "business_quality.json"
    html_p = REPO / "docs" / "blogs" / market / f"{symbol}_dossier.html"
    spine = _load_json(spine_p)
    bq = _load_json(bq_p)
    if bq and not spine.get("business_quality_verdict"):
        spine["business_quality_verdict"] = bq.get("business_quality_verdict")
    if bq and not spine.get("kpi_health"):
        spine["kpi_health"] = bq.get("kpi_health")
    spine["_has_published_dossier"] = bool(spine_p.is_file() or html_p.is_file())
    return spine


def _resolve_sector_quadrant(
    sector_hint: str,
    facts_instruments: Dict[str, Any],
    stage2_view: Dict[str, Any],
) -> Tuple[str, Optional[float]]:
    """Match a stock's sector/industry to the facts ledger quadrant and TheWrap Stage 2 %."""
    hint = (sector_hint or "").lower()
    quadrant = "Neutral"
    best_s2_pct: Optional[float] = None

    etf_sector_aliases = {
        "xlk": "tech software cloud semi electronic",
        "xle": "energy oil gas lng",
        "xlf": "financial bank wealth insurance",
        "xlv": "health pharma drug medtech",
        "xli": "industrial manuf capital power defense transport",
        "xlc": "communication media internet",
        "xly": "consumer retail auto discretionary",
        "xlp": "staples fmcg beverage",
        "xlb": "materials chemical metal mining",
        "xlu": "utilities power",
        "xlre": "realty real estate reit",
    }
    for name, m in (facts_instruments or {}).items():
        if not isinstance(m, dict) or m.get("kind") != "sector":
            continue
        q = m.get("quadrant")
        if not q:
            continue
        nl = etf_sector_aliases.get(name.lower(), name.lower())
        if any(tok and len(tok) >= 4 and tok in hint for tok in nl.replace("&", " ").replace("/", " ").split()):
            quadrant = q
            break
        if ("tech" in hint or "software" in hint or "cloud" in hint or "semi" in hint) and ("tech" in nl or "it" in nl):
            quadrant = q
            break
        if ("fin" in hint or "bank" in hint or "wealth" in hint or "insur" in hint) and ("fin" in nl or "bank" in nl):
            quadrant = q
            break
        if ("pharma" in hint or "health" in hint or "drug" in hint or "med" in hint) and ("health" in nl or "pharma" in nl):
            quadrant = q
            break
        if ("indus" in hint or "manuf" in hint or "capital" in hint or "power" in hint or "defense" in hint) and ("indus" in nl or "infra" in nl):
            quadrant = q
            break
        if ("energy" in hint or "oil" in hint or "gas" in hint or "lng" in hint) and "energy" in nl:
            quadrant = q
            break

    for row in (stage2_view.get("strongest_sectors") or []):
        sec_name = str(row.get("sector") or "").lower()
        pct = _num(row.get("pct_in_stage2") if "pct_in_stage2" in row else row.get("pct_outperforming_sp500"), 1)
        if sec_name and pct is not None and (sec_name in hint or any(w in hint for w in sec_name.split() if len(w) >= 5)):
            best_s2_pct = max(best_s2_pct or 0.0, pct)

    return quadrant, best_s2_pct


def _resolve_regime_envelope(
    market: str,
    facts: Dict[str, Any],
    scoring: Dict[str, Any],
) -> Dict[str, Any]:
    regime_obj = facts.get("regime") or {}
    label = str(regime_obj.get("label") or "Uptrend (narrow breadth)")
    breadth50 = _num(regime_obj.get("breadth_pct_above_50dma"), 1)
    vix_key = "India VIX" if market == "IN" else "VIX"
    vix_val = _num(((facts.get("instruments") or {}).get(vix_key) or {}).get("close"), 2)

    cash_cfg = (scoring.get("buckets") or {}).get("CASH") or {}
    regime_floors = cash_cfg.get("regime_floors_pct") or {}
    floor_from_regime = float(regime_floors.get(label, 12.0))
    floor_from_vix = 5.0
    if vix_val is not None:
        for rung in (cash_cfg.get("vix_ladder") or []):
            vb = rung.get("vix_below")
            if vb is None or vix_val < float(vb):
                floor_from_vix = float(rung.get("cash_pct", 5.0))
                break
    min_cash_pct = max(floor_from_regime, floor_from_vix)

    ru_cfg = ((scoring.get("position_sizing") or {}).get("risk_unit_sizing") or {})
    heat_map = ru_cfg.get("regime_heat_budget_pct") or {}
    max_heat_pct = float(heat_map.get(label, 8.5))

    if label == "Uptrend (broad)":
        playbook_mode = "BROAD_TREND"
        allow_new_lev_etf = True
    elif label.startswith("Downtrend"):
        playbook_mode = "CAPITAL_PRESERVATION"
        allow_new_lev_etf = False
    else:
        playbook_mode = "SIDEWAYS_DEFENSIVE"
        allow_new_lev_etf = False

    drawdown_call_window = bool(
        playbook_mode in {"SIDEWAYS_DEFENSIVE", "CAPITAL_PRESERVATION"}
        or (vix_val is not None and vix_val >= 19.0)
        or (breadth50 is not None and breadth50 <= 45.0)
    )

    tranche_cfg = ((scoring.get("position_sizing") or {}).get("tranche_entry") or {})
    t_mode = tranche_cfg.get("broad_uptrend" if playbook_mode == "BROAD_TREND" else "sideways_or_narrow") or {}

    return {
        "regime_label": label,
        "playbook_mode": playbook_mode,
        "breadth_pct_above_50dma": breadth50,
        "vix": vix_val,
        "min_cash_floor_pct": round(min_cash_pct, 2),
        "max_portfolio_heat_pct": round(max_heat_pct, 2),
        "allow_new_leveraged_etf_buys": allow_new_lev_etf,
        "countercyclical_options_window_open": drawdown_call_window,
        "starter_fraction": float(t_mode.get("starter_fraction", 0.5)),
        "proof_add_fraction": float(t_mode.get("proof_add_fraction", 0.5)),
        "proof_min_gain_r": float(t_mode.get("proof_min_gain_r", 1.0 if playbook_mode != "BROAD_TREND" else 0.75)),
        "max_starter_extension_pct": float(
            t_mode.get("max_extension_above_10w_ema_pct", 8.5)
            if playbook_mode == "BROAD_TREND"
            else t_mode.get("support_proximity_max_pct", 4.0)
        ),
        "sideways_profit_trim_active": bool(t_mode.get("sideways_profit_trim_active", playbook_mode != "BROAD_TREND")),
        "partial_profit_trim_r": float(t_mode.get("partial_profit_trim_r", 2.0)),
        "partial_profit_trim_rsi14": float(t_mode.get("partial_profit_trim_rsi14", 74.0)),
        "partial_profit_trim_fraction": float(t_mode.get("partial_profit_trim_fraction", 0.35)),
    }


def _score_candidate(
    sym: str,
    bucket: str,
    has_dossier: bool,
    tier: str,
    bq_verdict: str,
    kpi_health: str,
    roic_or_roce: Optional[float],
    asym_ratio: Optional[float],
    stage: str,
    ext_10w_pct: Optional[float],
    rsi14: Optional[float],
    rs_63d: Optional[float],
    sector_quadrant: str,
    sector_s2_pct: Optional[float],
    cluster_current_wt_pct: float,
    cluster_max_wt_pct: float,
    is_incumbent_or_anchored: bool,
    scoring: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute transparent 100-point tournament score (+ stability bonus when applicable)."""
    # 1. Business Quality & Valuation Asymmetry (0 - 40 pts)
    tier_pts = {"TIER_1": 18.0, "TIER_2": 14.0, "TIER_3": 10.0, "TIER_4": 6.0, "TIER_0": 0.0}.get(tier, 11.0)
    if bq_verdict == "COMPOUNDER_PASS":
        tier_pts += 6.0
    elif bq_verdict == "FUNDAMENTAL_FAIL":
        tier_pts = 0.0
    if kpi_health == "PASS":
        tier_pts += 4.0
    elif kpi_health == "FAIL":
        tier_pts = max(0.0, tier_pts - 8.0)

    ret_pts = 5.0
    if roic_or_roce is not None:
        ret_pts = min(8.0, max(0.0, (roic_or_roce - 8.0) * 0.4))
    asym_pts = 4.0
    if asym_ratio is not None:
        asym_pts = min(8.0, max(0.0, asym_ratio * 2.5))

    qual_val = min(40.0, tier_pts + ret_pts + asym_pts)
    if not has_dossier:
        pen = float(((scoring.get("position_sizing") or {}).get("ununderwritten_holding_policy") or {}).get("provisional_score_penalty_pts", 6.0))
        qual_val = max(0.0, qual_val - pen)

    # 2. Stage 2 Technical Structure (0 - 30 pts)
    stage_base = {"STAGE_2": 18.0, "STAGE_1": 11.0, "STAGE_3": 5.0, "STAGE_4": 0.0}.get(stage, 8.0)
    ext_pts = 4.0
    if ext_10w_pct is not None:
        if -3.0 <= ext_10w_pct <= 6.0:
            ext_pts = 6.0
        elif 6.0 < ext_10w_pct <= 10.0:
            ext_pts = 4.0
        elif ext_10w_pct > 18.0 or ext_10w_pct < -10.0:
            ext_pts = 1.0
    rsi_pts = 3.0
    if rsi14 is not None:
        if 48.0 <= rsi14 <= 68.0:
            rsi_pts = 3.5
        elif rsi14 > 76.0 or rsi14 < 35.0:
            rsi_pts = 1.0
    rs_pts = 1.5
    if rs_63d is not None:
        rs_pts = min(2.5, max(0.0, 1.25 + rs_63d * 0.08))
    tech_pts = 0.0 if stage == "STAGE_4" else min(30.0, stage_base + ext_pts + rsi_pts + rs_pts)

    # 3. Asymmetric Sector Rotation Tailwind (0 - 20 pts)
    quad_pts = {"Leading": 15.0, "Improving": 12.0, "Neutral": 10.0, "Weakening": 7.0, "Lagging": 2.0}.get(sector_quadrant, 10.0)
    s2_bonus = 2.5 if sector_s2_pct is None else min(5.0, max(0.0, (sector_s2_pct - 25.0) * 0.1))
    sec_pts = min(20.0, quad_pts + s2_bonus)
    if bucket == "CORE_ALPHA" and stage != "STAGE_4":
        # Core Alpha ignores short-term sector dips unless its own trend breaks
        sec_pts = max(12.0, sec_pts)
    elif bucket == "TACTICAL_MOMENTUM" and sector_quadrant == "Lagging":
        sec_pts = min(4.0, sec_pts)

    # 4. Portfolio Overlap / Cluster Fit (0 - 10 pts)
    headroom = cluster_max_wt_pct - cluster_current_wt_pct
    if headroom >= 12.0:
        fit_pts = 10.0
    elif headroom >= 5.0:
        fit_pts = 6.5
    elif headroom > 0.0:
        fit_pts = 3.0
    else:
        fit_pts = 0.0

    raw_total = round(qual_val + tech_pts + sec_pts + fit_pts, 1)
    inc_buf = float(((scoring.get("position_sizing") or {}).get("convergence_and_hysteresis") or {}).get("incumbent_score_buffer_pts", 5.0))
    effective_total = round(raw_total + (inc_buf if is_incumbent_or_anchored and stage != "STAGE_4" else 0.0), 1)
    return {
        "quality_valuation_pts": round(qual_val, 1),
        "stage2_technical_pts": round(tech_pts, 1),
        "sector_rotation_pts": round(sec_pts, 1),
        "portfolio_fit_pts": round(fit_pts, 1),
        "raw_score": raw_total,
        "stability_bonus_pts": round(effective_total - raw_total, 1),
        "tournament_score": effective_total,
    }


def _compute_risk_unit_target_wt(
    entry_ref: float,
    stop_loss: Optional[float],
    tier: str,
    scoring: Dict[str, Any],
) -> Dict[str, float]:
    pos_cfg = scoring.get("position_sizing") or {}
    tier_tbl = (pos_cfg.get("tier_table") or {}).get(tier) or {"min_pct": 3.0, "max_pct": 6.0}
    tier_max = float(tier_tbl.get("max_pct", 6.0))
    tier_min = float(tier_tbl.get("min_pct", 2.0))
    ru_cfg = pos_cfg.get("risk_unit_sizing") or {}
    budget_bps = float((ru_cfg.get("tier_risk_budget_bps") or {}).get(tier, 65.0 if tier != "TIER_0" else 0.0))
    if tier == "TIER_0" or budget_bps <= 0 or entry_ref <= 0:
        return {"full_target_wt_pct": 0.0, "risk_budget_bps": 0.0, "stop_distance_pct": 0.0}
    if not stop_loss or stop_loss <= 0 or stop_loss >= entry_ref:
        stop_dist_pct = 12.0
    else:
        stop_dist_pct = max(3.5, (entry_ref - stop_loss) / entry_ref * 100.0)
    raw_wt = (budget_bps / 100.0) / (stop_dist_pct / 100.0)
    full_wt = round(min(tier_max, max(tier_min * 0.5, raw_wt)), 2)
    return {
        "full_target_wt_pct": full_wt,
        "risk_budget_bps": round(budget_bps, 1),
        "stop_distance_pct": round(stop_dist_pct, 2),
    }


def build_from_repo_fallback(market: str, as_of: str = "") -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Lightweight offline builder from `data_layer.py` + `data/views/snapshots_*_latest.json` for CLI/testing."""
    sys.path.insert(0, str(REPO / "scripts"))
    import data_layer  # noqa: E402

    snap_view = _load_json(REPO / "data" / "views" / f"snapshots_{market}_latest.json")
    snaps = snap_view.get("snapshots") or {}
    shortlist = _load_json(REPO / "data" / "shortlist" / f"{market}.json")
    meta_all = ((_load_json(REPO / "data" / "metadata" / "symbols.json").get(market) or {}).get("symbols") or {})
    opts_raw = (_load_json(REPO / "data" / "options" / f"{market}.json").get("positions") or []) if market == "US" else []

    snap_view_date = str(snap_view.get("as_of_date") or snap_view.get("generated_at") or "")[:10]
    price_map: Dict[str, float] = {}
    for row in (shortlist.get("active") or []):
        if isinstance(row, dict) and row.get("symbol") and _num(row.get("cmp")):
            price_map[row["symbol"]] = float(row["cmp"])
    for sym, sp in snaps.items():
        tv = (sp.get("tradingview") if isinstance(sp, dict) else None) or {}
        if _num(tv.get("close")):
            price_map[sym] = float(tv["close"])
        sp_spine = _load_dossier_spine(market, sym)
        if _num(sp_spine.get("cmp")) and str(sp_spine.get("as_of") or "")[:10] > snap_view_date:
            price_map[sym] = float(sp_spine["cmp"])

    accounts_out = []
    per_sym: Dict[str, Dict[str, Any]] = {}
    cash_total = 0.0
    for acct_path in data_layer.accounts_for(market):
        meta_d, pos_dict, cash = data_layer.account_state(acct_path)
        acct_id = Path(acct_path).stem.split(".")[0]
        snap_date = meta_d.get("last_date", "")
        cash_total += cash
        acct_mv = 0.0
        for sym, p in pos_dict.items():
            s = sym.upper()
            spine = _load_dossier_spine(market, s)
            px = price_map.get(s) or _num(spine.get("cmp"))
            if px is None and p["quantity"] > 0 and p["cost_basis"]:
                px = round(p["cost_basis"] / p["quantity"], 2)
            px = px or 0.0
            price_map.setdefault(s, px)
            mv = round(p["quantity"] * px, 2)
            acct_mv += mv
            d = per_sym.setdefault(
                s,
                {
                    "symbol": s,
                    "accounts": [],
                    "quantity": 0.0,
                    "market_value": 0.0,
                    "cost_basis": 0.0,
                    "cost_complete": True,
                    "priced": px > 0,
                    "metadata": meta_all.get(s),
                },
            )
            d["accounts"].append({
                "account": acct_id,
                "quantity": p["quantity"],
                "cost_basis": p["cost_basis"],
                "market_value": mv,
                "realized_pl": p["realized_pl"],
            })
            d["quantity"] = round(d["quantity"] + p["quantity"], 6)
            d["market_value"] = round(d["market_value"] + mv, 2)
            d["cost_basis"] = round(d["cost_basis"] + (p["cost_basis"] or 0.0), 2)
        accounts_out.append({
            "id": acct_id,
            "label": acct_id.title(),
            "last_transaction": snap_date,
            "positions": len(pos_dict),
            "cash": round(cash, 2),
            "market_value": round(acct_mv, 2),
        })

    for d in per_sym.values():
        d["gain"] = round(d["market_value"] - d["cost_basis"], 2)

    options_rows = []
    options_val = 0.0
    for o in opts_raw:
        mv = float(o.get("current_mv_usd") or o.get("market_value") or 0.0)
        options_val += mv
        options_rows.append({**o, "market_value": round(mv, 2)})

    equities_val = round(sum(d["market_value"] for d in per_sym.values()), 2)
    net_worth = round(equities_val + cash_total + options_val, 2)
    for d in per_sym.values():
        wt = round(d["market_value"] / net_worth * 100.0, 2) if net_worth > 0 else 0.0
        d["weight_pct"] = wt
        d["is_tracking"] = bool(0.0 < wt < 0.35)

    inst: Dict[str, Any] = {}
    for sym, px in price_map.items():
        tv = ((snaps.get(sym) or {}).get("tradingview") or {})
        s50_f = _num(tv.get("sma50"))
        s200_f = _num(tv.get("sma200"))
        calc_stage = None
        if px and s50_f and s200_f:
            if px > s50_f and px > s200_f:
                calc_stage = 2
            elif px < s50_f and px < s200_f:
                calc_stage = 4
            elif px >= s200_f:
                calc_stage = 3
            else:
                calc_stage = 1
        inst[sym] = {
            "close": px,
            "sma20": _num(tv.get("sma20")),
            "sma50": s50_f,
            "sma200": s200_f,
            "ema10w_approx": _num(tv.get("ema10_weekly")),
            "rsi14": _num(tv.get("rsi_14_daily")),
            "atr14": _num(tv.get("atr_14")),
            "chg_1m_pct": _num(tv.get("perf_1m_pct")),
            "chg_3m_pct": _num(tv.get("perf_3m_pct")),
            "stage": calc_stage,
            "roles": ["holding"] if sym in per_sym else ["shortlist"],
        }

    resolved_asof = as_of or shortlist.get("as_of_date") or dt.date.today().isoformat()
    facts = {
        "market": market,
        "asof": resolved_asof,
        "regime": {"label": "Uptrend (narrow breadth)", "breadth_pct_above_50dma": 46.0},
        "instruments": inst,
    }
    positions = {
        "accounts": accounts_out,
        "consolidated": sorted(per_sym.values(), key=lambda x: -x["market_value"]),
        "equities_value": equities_val,
        "cash_total": round(cash_total, 2),
        "options_value": round(options_val, 2),
        "options_rows": options_rows,
        "net_worth": net_worth,
        "portfolio_risk_and_overlap": {
            "portfolio_beta_weighted": 1.08,
            "effective_market_exposure_pct": round((equities_val + options_val * 2.5) / net_worth * 100.0, 1) if net_worth else 0.0,
            "effective_market_exposure_value": round(equities_val + options_val * 2.5, 2),
            "expected_move_per_1pct_index": 1.08,
            "expected_dollar_per_1pct_index": round((equities_val + options_val * 2.5) * 0.01, 2),
            "lockstep_clusters": [],
            "high_correlation_pairs": [],
        },
    }
    return facts, positions, snap_view


def allocate_portfolio(
    market: str,
    facts: Dict[str, Any],
    positions: Dict[str, Any],
    snapshots: Optional[Dict[str, Any]] = None,
    shortlist_data: Optional[Dict[str, Any]] = None,
    options_snapshot: Optional[Dict[str, Any]] = None,
    prior_state: Optional[Dict[str, Any]] = None,
    scoring: Optional[Dict[str, Any]] = None,
    cio_decisions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Portfolio construction & convergence function with optional CIO override reconciliation."""
    mkt = market.upper()
    cur = "₹" if mkt == "IN" else "$"
    scoring = scoring or _load_json(SCORING_PATH)
    snapshots = snapshots or {}
    snap_map = (snapshots.get("snapshots") if "snapshots" in snapshots else snapshots) or {}
    shortlist_rows = [
        r for r in ((shortlist_data or {}).get("active") or [])
        if isinstance(r, dict) and r.get("symbol")
    ]
    shortlist_by_sym = {r["symbol"].upper(): r for r in shortlist_rows}
    meta_by_sym = ((_load_json(REPO / "data" / "metadata" / "symbols.json").get(mkt) or {}).get("symbols") or {})
    stage2_view = _load_json(REPO / "data" / "views" / f"stage2_{mkt}_latest.json")
    opt_pkgs = ((options_snapshot or {}).get("packages") or {})

    as_of = str(facts.get("asof") or dt.date.today().isoformat())
    inst_map = facts.get("instruments") or {}
    net_worth = float(positions.get("net_worth") or 0.0)
    cash_total = float(positions.get("cash_total") or 0.0)
    equities_value = float(positions.get("equities_value") or 0.0)
    options_value = float(positions.get("options_value") or 0.0)
    if net_worth <= 0:
        raise ValueError(f"Net worth must be positive for {mkt} allocation (got {net_worth})")

    pos_cfg = scoring.get("position_sizing") or {}
    buckets_cfg = scoring.get("buckets") or {}
    track_max_pct = float((pos_cfg.get("tracking_positions") or {}).get("max_weight_pct", 0.35))
    hyst_cfg = pos_cfg.get("convergence_and_hysteresis") or {}
    lock_days = int(hyst_cfg.get("lock_window_calendar_days", 5))
    deadband_wt_pct = float(hyst_cfg.get("rebalance_deadband_wt_pct", 1.25))
    price_hyst_pct = float(hyst_cfg.get("price_band_hysteresis_pct", 2.5))
    displace_min_pts = float(hyst_cfg.get("slot_displacement_min_advantage_pts", 15.0))
    min_slots, max_slots = (pos_cfg.get("active_slots") or [12, 15])[:2]
    cluster_cfg = pos_cfg.get("cluster_risk") or {}
    max_cluster_wt = float(cluster_cfg.get("max_cluster_notional_pct", 25.0))
    max_cluster_heat = float(cluster_cfg.get("max_cluster_heat_pct", 3.5))
    runaway_cap = float(pos_cfg.get("runaway_winner_cap_pct", 22.0))
    init_cost_cap = float(pos_cfg.get("initial_cost_cap_pct", 10.0))

    prior_positions_by_sym: Dict[str, Dict[str, Any]] = {}
    prior_as_of = (prior_state or {}).get("as_of_date")
    days_since_prior = _days_between(prior_as_of, as_of)
    hysteresis_window_active = bool(days_since_prior is not None and days_since_prior <= lock_days)
    for pr in ((prior_state or {}).get("positions") or []):
        if isinstance(pr, dict) and pr.get("symbol"):
            prior_positions_by_sym[str(pr["symbol"]).upper()] = pr

    envelope = _resolve_regime_envelope(mkt, facts, scoring)

    # Account-level cash map (for US Schwab vs Robinhood routing)
    account_cash: Dict[str, float] = {}
    for a in (positions.get("accounts") or []):
        aid = str(a.get("id") or "default").lower()
        account_cash[aid] = float(a.get("cash") or 0.0)

    # Build correlation cluster lookup from positions.portfolio_risk_and_overlap
    risk_ov = positions.get("portfolio_risk_and_overlap") or {}
    corr_clusters = risk_ov.get("lockstep_clusters") or []
    sym_to_cluster_id: Dict[str, str] = {}
    cluster_members: Dict[str, List[str]] = {}
    for idx, cl in enumerate(corr_clusters, 1):
        cid = f"CORR_CLUSTER_{idx}"
        syms = [str(s).upper() for s in (cl.get("symbols") or [])]
        for s in syms:
            sym_to_cluster_id[s] = cid
        cluster_members[cid] = list(syms)

    consolidated = positions.get("consolidated") or []
    held_by_sym = {str(h["symbol"]).upper(): h for h in consolidated if h.get("symbol")}

    # Assign thematic/underlying clusters when not already in a return-correlation cluster
    def _cluster_for(sym: str, sector_label: str, underlying: str) -> str:
        if sym in sym_to_cluster_id:
            return sym_to_cluster_id[sym]
        if underlying != sym and underlying in sym_to_cluster_id:
            return sym_to_cluster_id[underlying]
        if underlying != sym:
            return f"UNDERLYING_{underlying}"
        sec_clean = (sector_label or "General").split("/")[0].split("—")[0].strip() or "General"
        return f"SECTOR_{sec_clean.upper().replace(' ', '_')[:28]}"

    # Pre-compute current cluster weights across non-tracking holdings
    cluster_wt_map: Dict[str, float] = {}
    cluster_heat_map: Dict[str, float] = {}
    cluster_syms_map: Dict[str, List[str]] = {}

    for h in consolidated:
        sym = str(h["symbol"]).upper()
        mv = float(h.get("market_value") or 0.0)
        wt = round(mv / net_worth * 100.0, 2)
        is_track = bool(0.0 < wt < track_max_pct)
        if is_track or sym in CASH_EQUIV_ETFS:
            continue
        sl = shortlist_by_sym.get(sym) or {}
        meta = h.get("metadata") or meta_by_sym.get(sym) or {}
        spine = _load_dossier_spine(mkt, sym)
        sec_lbl = str(sl.get("macro_sector") or spine.get("sector") or meta.get("sub_theme") or "General")
        und = SINGLE_STOCK_LEVERAGED_ETFS.get(sym, (sym, 1.0))[0]
        cid = _cluster_for(sym, sec_lbl, und)
        sym_to_cluster_id[sym] = cid
        cluster_wt_map[cid] = round(cluster_wt_map.get(cid, 0.0) + wt, 2)
        cluster_syms_map.setdefault(cid, []).append(sym)

    # ------------------------------------------------------------------
    # STEP 1: OPTIONS / LEAPS BOOK AUDIT (US & IN)
    # ------------------------------------------------------------------
    opt_cfg = buckets_cfg.get("LEAPS_OPTIONS") or {}
    if "options_rows" in positions:
        opt_rows = positions.get("options_rows") or []
    elif mkt == "US":
        opt_rows = _load_json(REPO / "data" / "options" / f"{mkt}.json").get("positions") or []
    else:
        opt_rows = []
    opt_rows = [
        o for o in opt_rows
        if not (o.get("expiry_date") and str(o["expiry_date"])[:10] < as_of[:10])
    ]
    options_cost_total = round(sum(float(o.get("cost_basis_usd") or o.get("cost_basis") or o.get("market_value") or 0.0) for o in opt_rows), 2)
    options_mv_total = round(sum(float(o.get("market_value") or o.get("current_mv_usd") or 0.0) for o in opt_rows), 2)
    options_cap_basis_val = max(options_cost_total, options_mv_total)
    options_cap_basis_pct = round(options_cap_basis_val / net_worth * 100.0, 2)
    opt_hard_max_pct = float(opt_cfg.get("hard_max_pct", 10.0))

    options_decisions: List[Dict[str, Any]] = []
    options_open_heat_val = 0.0
    option_underlyings_active: set[str] = set()
    liberated_from_options = 0.0

    for o in opt_rows:
        csym = str(o.get("contract_symbol") or o.get("ticker") or "OPTION")
        und = str(o.get("underlying") or o.get("ticker") or csym).upper()
        mv = float(o.get("market_value") or o.get("current_mv_usd") or 0.0)
        cost = float(o.get("cost_basis_usd") or o.get("cost_basis") or mv)
        dte = int(o.get("dte") or 180)
        delta = float(o.get("delta_delta") or o.get("delta") or 0.45)
        pnl_pct = round((mv / cost - 1.0) * 100.0, 2) if cost > 0 else 0.0
        und_inst = inst_map.get(und) or {}
        spot = _num(und_inst.get("close")) or _num(o.get("underlying_cmp_usd")) or 0.0
        inv_stop = _num(o.get("invalidation_stop_usd")) or _num(o.get("support_anchor_usd"))
        contracts = int(o.get("contracts") or 1)

        live_pkg = opt_pkgs.get(und) or {}
        mtf = live_pkg.get("multitimeframe_chart") or {}
        if _num(mtf.get("close")):
            spot = float(mtf["close"])

        # Estimate option dollar loss if underlying hits invalidation stop
        if inv_stop and spot > 0 and spot > inv_stop:
            und_drop = spot - inv_stop
            est_opt_loss = min(mv, round(contracts * 100.0 * delta * und_drop, 2))
        elif inv_stop and spot > 0 and spot <= inv_stop:
            est_opt_loss = mv
        else:
            est_opt_loss = round(mv * 0.5, 2)

        rule_flags = []
        cost_wt_pct = round(cost / net_worth * 100.0, 2)
        if delta < float(opt_cfg.get("min_leaps_delta", 0.60)):
            rule_flags.append(f"Legacy delta {delta:.2f} below 0.60 ITM/ATM standard")
        if cost_wt_pct > float(opt_cfg.get("per_underlying_cost_max_pct", 2.0)):
            rule_flags.append(f"Cost basis {cost_wt_pct:.2f}% exceeds 2.0% per-underlying cap")

        if inv_stop and spot > 0 and spot < inv_stop:
            verdict = "EXIT_OPTION"
            target_mv = 0.0
            liberated = mv
            liberated_from_options += mv
            rationale = (
                f"{und} closed at {cur}{spot:,.2f}, below its {cur}{inv_stop:,.2f} invalidation stop; "
                f"exit {contracts} contract(s) to salvage {cur}{mv:,.2f} before accelerated decay."
            )
        elif dte < int(opt_cfg.get("roll_or_exit_dte", 120)) and pnl_pct < 0:
            verdict = "EXIT_TIME_STOP"
            target_mv = 0.0
            liberated = mv
            liberated_from_options += mv
            rationale = (
                f"{csym} has {dte} DTE (<120 DTE theta cliff) while underwater ({pnl_pct:+.1f}%); "
                f"close rather than holding OTM extrinsic value into steeper decay."
            )
        elif pnl_pct >= float(opt_cfg.get("profit_trim_pct", 45.0)) and contracts >= 2:
            sell_c = max(1, contracts // 2)
            liberated = round(mv * (sell_c / contracts), 2)
            target_mv = round(mv - liberated, 2)
            liberated_from_options += liberated
            option_underlyings_active.add(und)
            options_open_heat_val += round(est_opt_loss * (target_mv / mv), 2) if mv > 0 else 0.0
            verdict = "TRIM_OPTION_STRENGTH"
            rationale = (
                f"Up {pnl_pct:+.1f}% (>= +45% convexity harvest rule); sell {sell_c} of {contracts} contracts "
                f"and trail stop at {cur}{inv_stop or spot * 0.93:,.2f}."
            )
        else:
            verdict = "GRANDFATHERED_HOLD" if rule_flags else "HOLD_CONVEXITY"
            target_mv = mv
            liberated = 0.0
            option_underlyings_active.add(und)
            options_open_heat_val += est_opt_loss
            flag_note = f" ({'; '.join(rule_flags)}; grandfathered — freeze adds, repair/trim on bounce)" if rule_flags else ""
            rationale = (
                f"{und} ({cur}{spot:,.2f}) holds above invalidation stop {cur}{inv_stop or 0:,.2f} with {dte} DTE{flag_note}."
            )

        options_decisions.append({
            "symbol": f"OPT:{csym}",
            "contract_symbol": csym,
            "underlying": und,
            "contracts": contracts,
            "dte": dte,
            "delta": delta,
            "cost_basis": round(cost, 2),
            "current_value": round(mv, 2),
            "target_value": round(target_mv, 2),
            "capital_liberated": round(liberated, 2),
            "pnl_pct": pnl_pct,
            "underlying_spot": spot,
            "invalidation_stop": inv_stop,
            "current_open_heat_value": round(est_opt_loss, 2),
            "current_open_heat_pct": round(est_opt_loss / net_worth * 100.0, 2),
            "open_heat_value": round(est_opt_loss if target_mv > 0 else 0.0, 2),
            "open_heat_pct": round((est_opt_loss if target_mv > 0 else 0.0) / net_worth * 100.0, 2),
            "verdict": verdict,
            "rule_flags": rule_flags,
            "broker_account": str(o.get("broker_account") or "Robinhood"),
            "rationale": rationale,
        })

    # ------------------------------------------------------------------
    # STEP 2: EVALUATE EVERY EXISTING EQUITY / ETF HOLDING
    # ------------------------------------------------------------------
    cio_decisions = cio_decisions or {}
    holding_overrides = {
        str(k).upper(): v
        for k, v in (cio_decisions.get("holding_overrides") or {}).items()
        if isinstance(v, dict)
    }
    challenger_overrides = {
        str(k).upper(): v
        for k, v in (cio_decisions.get("challenger_overrides") or {}).items()
        if isinstance(v, dict)
    }
    cio_portfolio_thesis = str(cio_decisions.get("portfolio_thesis") or "").strip()

    # Pre-compute current Core Alpha weight so baseline rules avoid starving an underweight Core sleeve
    current_core_alpha_wt = round(
        sum(
            float(h.get("market_value") or 0.0) / net_worth * 100.0
            for h in consolidated
            if (
                (shortlist_by_sym.get(str(h.get("symbol", "")).upper()) or {}).get("bucket") == "CORE_ALPHA"
                or _load_dossier_spine(mkt, str(h.get("symbol", "")).upper()).get("bucket") == "CORE_ALPHA"
            )
        ),
        2,
    )

    holding_decisions: List[Dict[str, Any]] = []
    tracking_rows: List[Dict[str, Any]] = []
    dossier_debt_queue: List[Dict[str, Any]] = []
    equity_liberated_total = 0.0
    lev_etf_current_wt = 0.0

    for h in consolidated:
        sym = str(h["symbol"]).upper()
        qty = float(h.get("quantity") or 0.0)
        mv = float(h.get("market_value") or 0.0)
        cost = float(h.get("cost_basis") or 0.0)
        wt_pct = round(mv / net_worth * 100.0, 2)
        inst_m = inst_map.get(sym) or {}
        snap_sym = (snap_map.get(sym) or {})
        tv = snap_sym.get("tradingview") or {}
        s2_ev = snap_sym.get("stage2_evaluation") or {}
        close = _num(inst_m.get("close")) or _num(tv.get("close")) or (round(mv / qty, 2) if qty > 0 else 0.0) or 0.0
        avg_cost = round(cost / qty, 2) if qty > 0 and cost > 0 else close
        pnl_val = round(mv - cost, 2) if h.get("cost_complete", True) else 0.0
        pnl_pct = round((mv / cost - 1.0) * 100.0, 2) if cost > 0 else 0.0

        spine = _load_dossier_spine(mkt, sym)
        sl = shortlist_by_sym.get(sym) or {}
        meta = h.get("metadata") or meta_by_sym.get(sym) or {}
        prior_row = prior_positions_by_sym.get(sym) or {}

        # Tracking positions (< 0.35% NAV): isolated from active slot count & rebalance churn
        if 0.0 < wt_pct < track_max_pct:
            tr_stop = _num(spine.get("stop_loss")) or _num(sl.get("stop_loss")) or round(close * 0.85, 2)
            tr_stage = _normalize_stage(inst_m.get("stage") or s2_ev.get("weinstein_stage") or spine.get("weinstein_stage"))
            tr_new_cap = str(spine.get("new_capital_verdict") or spine.get("verdict") or sl.get("action_verdict") or "WAIT_FOR_SUPPORT").upper()
            tracking_rows.append({
                "symbol": sym,
                "company_name": str(spine.get("company_name") or sl.get("company_name") or meta.get("company_name") or sym),
                "has_dossier": bool(spine.get("_has_published_dossier") or sl.get("research_dossier_path")),
                "quantity": qty,
                "cost_basis": round(cost, 2),
                "pnl_value": pnl_val,
                "pnl_pct": pnl_pct,
                "close": close,
                "effective_stop": tr_stop,
                "stage": tr_stage,
                "new_capital_verdict": tr_new_cap,
                "current_value": round(mv, 2),
                "current_wt_pct": wt_pct,
                "target_value": round(mv, 2),
                "target_wt_pct": wt_pct,
                "verdict": "TRACKING_HOLD",
                "rationale": (
                    f"Sub-0.35% tracking stub ({qty:g} sh = {cur}{mv:,.2f}, {wt_pct:.2f}% of NAV < {track_max_pct:.2f}% threshold; "
                    f"stop {cur}{tr_stop:,.2f}, new capital {tr_new_cap}); excluded from active slot limits and turnover."
                ),
            })
            continue

        is_cash_equiv = sym in CASH_EQUIV_ETFS
        is_single_lev = sym in SINGLE_STOCK_LEVERAGED_ETFS
        is_sector_lev = sym in SECTOR_INDEX_LEVERAGED_ETFS
        has_dossier = bool(spine.get("_has_published_dossier") or sl.get("research_dossier_path") or is_sector_lev or is_cash_equiv)

        if is_cash_equiv:
            bucket = "CASH_EQUIVALENT"
        elif is_single_lev or is_sector_lev:
            bucket = "LEVERAGED_SATELLITE"
            lev_etf_current_wt += wt_pct
        else:
            bucket_candidates = [
                spine.get("strategy_bucket"),
                sl.get("strategy_bucket"),
                meta.get("strategy_bucket"),
            ]
            bucket = next(
                (str(b).upper() for b in bucket_candidates if str(b or "").upper() in {"CORE_ALPHA", "TACTICAL_MOMENTUM", "LEVERAGED_SATELLITE"}),
                "TACTICAL_MOMENTUM",
            )

        sma20 = _num(inst_m.get("sma20")) or _num(tv.get("sma20"))
        sma50 = _num(inst_m.get("sma50")) or _num(tv.get("sma50"))
        sma200 = _num(inst_m.get("sma200")) or _num(tv.get("sma200"))
        ema10w = _num(tv.get("ema10_weekly")) or _num(inst_m.get("ema10w_approx")) or sma50
        rsi14 = _num(inst_m.get("rsi14")) or _num(tv.get("rsi_14_daily"))
        atr14 = _num(inst_m.get("atr14")) or _num(tv.get("atr_14"))
        rs_63d = _num(inst_m.get("rs_63d_pct"))
        ext_10w = round((close / ema10w - 1.0) * 100.0, 2) if (close and ema10w and ema10w > 0) else None

        if inst_m.get("stage") is not None:
            stage = _normalize_stage(inst_m.get("stage"))
        elif sma50 and close and close < sma50:
            # Recent listing (<200 bars) trading below 50-DMA cannot be classified as Stage 2
            stage = "STAGE_3"
        else:
            stage = _normalize_stage(
                s2_ev.get("weinstein_stage")
                or spine.get("weinstein_stage")
                or sl.get("weinstein_stage")
            )

        # Resolve structural stop & enforce upward-only stop-loss ratchet for held shares
        raw_stop = (
            _num(spine.get("stop_loss"))
            or _num(sl.get("stop_loss"))
        )
        if not raw_stop:
            if is_single_lev or is_sector_lev:
                raw_stop = sma20 or (round(close * 0.90, 2) if close else None)
            elif bucket == "CORE_ALPHA":
                candidates = [x for x in (ema10w, sma50) if x and x < close]
                raw_stop = round((min(candidates) - (atr14 or 0.0) * 0.5), 2) if candidates else round(close * 0.88, 2)
            else:
                candidates = [x for x in (sma20, sma50) if x and x < close]
                raw_stop = round(min(candidates), 2) if candidates else round(close * 0.90, 2)

        prior_stop = _num(prior_row.get("effective_stop"))
        prior_qty = _num(prior_row.get("current_quantity"))
        if prior_stop and prior_qty and qty <= prior_qty and prior_stop < close:
            effective_stop = round(max(raw_stop or 0.0, prior_stop), 2)
            stop_ratcheted = effective_stop > (raw_stop or 0.0)
        else:
            effective_stop = round(raw_stop or close * 0.88, 2)
            stop_ratcheted = False

        # Risk / Heat calculation
        lev_mult = float(
            SINGLE_STOCK_LEVERAGED_ETFS.get(sym, (sym, 1.0))[1]
            if is_single_lev
            else SECTOR_INDEX_LEVERAGED_ETFS.get(sym, (sym, 1.0))[1]
            if is_sector_lev
            else 0.0 if is_cash_equiv else 1.0
        )
        if is_cash_equiv:
            heat_val = 0.0
        elif effective_stop and close > effective_stop:
            stop_drop_frac = (close - effective_stop) / close
            heat_val = round(mv * min(1.0, stop_drop_frac * (1.25 if lev_mult > 1.0 else 1.0)), 2)
        else:
            heat_val = round(mv * 0.12 * max(1.0, lev_mult * 0.6), 2)
        heat_pct = round(heat_val / net_worth * 100.0, 2)

        sec_lbl = str(
            SECTOR_INDEX_LEVERAGED_ETFS[sym][0]
            if is_sector_lev
            else sl.get("macro_sector") or spine.get("sector") or meta.get("sub_theme") or tv.get("sector") or "General"
        )
        und_sym = SINGLE_STOCK_LEVERAGED_ETFS.get(sym, (sym, 1.0))[0]
        cid = sym_to_cluster_id.get(sym) or _cluster_for(sym, sec_lbl, und_sym)
        sym_to_cluster_id[sym] = cid
        cluster_heat_map[cid] = round(cluster_heat_map.get(cid, 0.0) + heat_pct, 2)

        quadrant, s2_ind_pct = _resolve_sector_quadrant(sec_lbl, inst_map, stage2_view)
        tier = _normalize_tier(
            spine.get("conviction_tier") or sl.get("conviction_tier"),
            default="TIER_2" if bucket == "CORE_ALPHA" else "TIER_3",
        )
        bq_verdict = str(spine.get("business_quality_verdict") or ("COMPOUNDER_PASS" if sl.get("gate_status") == "PASSED" else "PROVISIONAL"))
        kpi_health = str(spine.get("kpi_health") or sl.get("kpi_health") or "PASS_WITH_WATCH")
        roic_roce = _num(sl.get("roic_pct")) or _num(sl.get("roce_pct")) or _num(tv.get("roe_pct"))
        t_base = _num(spine.get("target_base")) or _num(sl.get("target_base"))
        asym = (
            round((t_base - close) / (close - effective_stop), 2)
            if (t_base and close > effective_stop)
            else _num(sl.get("asymmetry_ratio"))
        )
        dossier_hold_action = str(spine.get("holding_action") or "").upper().strip()
        dossier_new_cap = str(spine.get("new_capital_verdict") or spine.get("verdict") or "").upper().strip()
        dossier_explicit_hold = bool(
            has_dossier
            and (dossier_hold_action in {"HOLD_WITH_HARD_STOP", "KEEP_COMPOUNDING"} or dossier_hold_action.startswith("TRIM"))
        )

        score_obj = _score_candidate(
            sym=sym,
            bucket=bucket,
            has_dossier=has_dossier,
            tier=tier,
            bq_verdict="FUNDAMENTAL_FAIL" if dossier_hold_action in {"EXIT_IMMEDIATELY", "EXIT", "SELL_ALL"} else bq_verdict,
            kpi_health=kpi_health,
            roic_or_roce=roic_roce,
            asym_ratio=asym,
            stage=stage,
            ext_10w_pct=ext_10w,
            rsi14=rsi14,
            rs_63d=rs_63d,
            sector_quadrant=quadrant,
            sector_s2_pct=s2_ind_pct,
            cluster_current_wt_pct=max(0.0, cluster_wt_map.get(cid, wt_pct) - wt_pct),
            cluster_max_wt_pct=max_cluster_wt,
            is_incumbent_or_anchored=dossier_hold_action not in {"EXIT_IMMEDIATELY", "EXIT", "SELL_ALL"},
            scoring=scoring,
        )

        sizing_ref = _compute_risk_unit_target_wt(close, effective_stop, tier, scoring)
        full_model_wt = sizing_ref["full_target_wt_pct"]

        if not has_dossier and not is_cash_equiv and not is_single_lev and not is_sector_lev:
            dossier_debt_queue.append({
                "symbol": sym,
                "market_value": round(mv, 2),
                "weight_pct": wt_pct,
                "stage": stage,
                "priority_reason": f"Un-underwritten holding ({wt_pct:.2f}% of NAV, {cur}{mv:,.2f}); freeze ADDs until 10-chapter monograph completes.",
            })

        # Resolve any explicit dossier partial-trim mandate (replaying account quantity at dossier as_of so executed trims converge!)
        dossier_trim_sell_sh = 0
        if has_dossier and dossier_hold_action.startswith("TRIM"):
            raw_dossier_sell = _num(spine.get("holding_shares_to_sell")) or 0.0
            if raw_dossier_sell > 0:
                qty_at_dossier = _account_qty_as_of(mkt, sym, spine.get("as_of"))
                base_qty_ref = qty_at_dossier if (qty_at_dossier is not None and qty_at_dossier > 0) else qty
                post_trim_target_qty = max(0.0, round(base_qty_ref - raw_dossier_sell, 6))
                if qty > post_trim_target_qty + 1e-4:
                    dossier_trim_sell_sh = int(round(qty - post_trim_target_qty))

        # Determine raw holding verdict before hysteresis check
        safety_override = False
        hysteresis_applied = False
        dossier_trim_mandate = False
        explicit_sell_shares: Optional[int] = None
        gain_r = (
            round((close - avg_cost) / max(0.01, avg_cost - effective_stop), 2)
            if (avg_cost > effective_stop and close > 0)
            else 0.0
        )

        if is_cash_equiv:
            verdict = "HOLD_CASH_EQUIVALENT"
            action_label = "HOLD / DRY POWDER"
            target_wt = wt_pct
            rationale = f"T-bill / liquid cash-equivalent ETF ({wt_pct:.2f}% NAV, 0.0 beta); acts as interest-bearing dry powder."
        elif is_single_lev:
            overlap_held = und_sym in held_by_sym and not held_by_sym[und_sym].get("is_tracking")
            below_20 = bool(sma20 and close < sma20)
            if overlap_held or stage == "STAGE_4" or below_20:
                safety_override = True
                verdict = "EXIT"
                action_label = "EXIT (SINGLE-STOCK 2X OVERLAP/DECAY)"
                target_wt = 0.0
                why = f"overlaps held {und_sym} (double-stacked beta slippage)" if overlap_held else "broke below 20-day trend / Stage 4"
                rationale = (
                    f"Single-stock 2x ETF ({sym}) {why}. Under the v4 rulebook, single-stock convexity belongs in capped-loss Options, "
                    f"while 2x/3x ETFs are restricted to sector/index swings; exit all {qty:g} shares."
                )
            else:
                verdict = "TRIM_PROFIT_BOOKING"
                action_label = "PHASE OUT ON STRENGTH / 20D STOP"
                target_wt = wt_pct
                rationale = (
                    f"Grandfathered single-stock 2x ETF above 20-DMA ({cur}{sma20 or effective_stop:,.2f}); "
                    f"no adds allowed — exit into +10–15% strength or immediately on a close below {cur}{sma20 or effective_stop:,.2f}."
                )
        elif is_sector_lev:
            lev_cfg = buckets_cfg.get("LEVERAGED_SATELLITE") or {}
            single_max = float(lev_cfg.get("single_position_max_pct", 6.0))
            below_20 = bool(sma20 and close < sma20)
            held_sessions_est = _days_between(prior_row.get("anchor_date"), as_of) or 0
            if stage == "STAGE_4" or below_20 or envelope["playbook_mode"] == "CAPITAL_PRESERVATION":
                safety_override = True
                verdict = "EXIT"
                action_label = "EXIT (20D ROTATION STOP)"
                target_wt = 0.0
                rationale = f"Sector/index 3x ETF ({sym}) broke below its 20-DMA ({cur}{sma20 or 0:,.2f}) or macro downtrend gate; exit immediately to prevent daily leverage decay."
            elif held_sessions_est >= 21 and abs(pnl_pct) < 5.0:
                verdict = "EXIT"
                action_label = "EXIT (15-SESSION TIME STOP)"
                target_wt = 0.0
                rationale = f"{sym} stalled flat ({pnl_pct:+.1f}%) past the 15-trading-day rotation clock; exit to stop sideways volatility drag."
            elif pnl_pct >= float(lev_cfg.get("profit_trim_pct", 15.0)) or wt_pct > single_max + 0.75:
                verdict = "TRIM_PROFIT_BOOKING"
                action_label = "TRIM (ROTATION HARVEST / 6% CAP)"
                target_wt = min(single_max, round(wt_pct * 0.55, 2))
                rationale = f"Sector swing {sym} reached {pnl_pct:+.1f}% ({wt_pct:.2f}% wt vs {single_max:.1f}% cap); lock quick rotation gains and trail 20-DMA {cur}{sma20 or effective_stop:,.2f}."
            else:
                verdict = "KEEP_COMPOUNDING"
                action_label = "HOLD / 20D EMA + 15D TIME STOP"
                target_wt = wt_pct
                rationale = f"Active sector/index rotation swing ({wt_pct:.2f}% wt <= {single_max:.1f}% cap) above 20-DMA; hard exit below {cur}{sma20 or effective_stop:,.2f} or at +15% target."
        elif (
            (effective_stop and close < effective_stop and (rsi14 is None or rsi14 < 42.0 or dossier_explicit_hold))
            or dossier_hold_action in {"EXIT_IMMEDIATELY", "EXIT", "SELL_ALL"}
            or bq_verdict == "FUNDAMENTAL_FAIL"
            or (stage == "STAGE_4" and bucket != "CORE_ALPHA" and not dossier_explicit_hold)
            or (stage == "STAGE_4" and bucket == "CORE_ALPHA" and effective_stop and close < effective_stop)
        ):
            safety_override = True
            verdict = "EXIT"
            action_label = "EXIT"
            target_wt = 0.0
            dossier_exit = dossier_hold_action in {"EXIT_IMMEDIATELY", "EXIT", "SELL_ALL"}
            why_exit = (
                f"published monograph mandates {dossier_hold_action} ({stage}, new capital {dossier_new_cap or 'REJECTED'})"
                if dossier_exit
                else f"hard risk gate triggered ({stage}, bucket={bucket}, close {cur}{close:,.2f} vs stop {cur}{effective_stop:,.2f}, quality={bq_verdict})"
            )
            rationale = f"Capital protection override: {why_exit}; exit full position ({qty:g} shares)."
        elif dossier_trim_sell_sh > 0 and close > 0:
            verdict = "TRIM_PROFIT_BOOKING"
            action_label = f"TRIM ({dossier_hold_action.replace('_', ' ')})"
            explicit_sell_shares = dossier_trim_sell_sh
            dossier_trim_mandate = True
            rem_qty = max(0.0, qty - dossier_trim_sell_sh)
            target_wt = round((rem_qty * close) / net_worth * 100.0, 2)
            rationale = (
                f"Published monograph mandates {dossier_hold_action}: sell {dossier_trim_sell_sh:g} of {qty:g} shares "
                f"({wt_pct:.2f}% -> {target_wt:.2f}% NAV; new capital {dossier_new_cap or 'REJECTED'}) and retain {rem_qty:g} shares behind hard stop {cur}{effective_stop:,.2f}."
            )
        elif wt_pct > runaway_cap:
            verdict = "TRIM_PROFIT_BOOKING"
            action_label = "TRIM"
            target_wt = round(runaway_cap - 2.0, 2)
            rationale = f"Appreciated weight ({wt_pct:.2f}%) breached runaway-winner ceiling ({runaway_cap:.1f}%); trim excess to {target_wt:.1f}% and trail stop at {cur}{effective_stop:,.2f}."
        elif (
            envelope["sideways_profit_trim_active"]
            and bucket == "TACTICAL_MOMENTUM"
            and gain_r >= envelope["partial_profit_trim_r"]
            and ((rsi14 and rsi14 >= envelope["partial_profit_trim_rsi14"]) or (ext_10w and ext_10w >= 18.0))
            and wt_pct >= 3.5
        ):
            verdict = "TRIM_PROFIT_BOOKING"
            action_label = "TRIM (SIDEWAYS +2R HARVEST)"
            target_wt = round(wt_pct * (1.0 - envelope["partial_profit_trim_fraction"]), 2)
            rationale = (
                f"Sideways-market swing harvest: {sym} is up {gain_r:.1f}R with extended tape (RSI {rsi14 or 0:.1f}, +{ext_10w or 0:.1f}% vs 10W EMA); "
                f"harvest 35% into strength and ratchet stop to {cur}{effective_stop:,.2f}."
            )
        elif (
            has_dossier
            and stage == "STAGE_2"
            and bq_verdict != "FUNDAMENTAL_FAIL"
            and dossier_new_cap not in {"REJECTED"}
            and tier != "TIER_0"
            and wt_pct + deadband_wt_pct < min(init_cost_cap, full_model_wt)
            and ext_10w is not None
            and ext_10w <= envelope["max_starter_extension_pct"]
            and gain_r >= envelope["proof_min_gain_r"]
            and (bucket == "CORE_ALPHA" or quadrant in {"Leading", "Improving", "Neutral"})
        ):
            add_step = round(min(init_cost_cap, full_model_wt) - wt_pct, 2)
            target_wt = round(wt_pct + min(add_step, full_model_wt * 0.5), 2)
            verdict = "ACCUMULATE_ON_DIP"
            action_label = "ADD AT SUPPORT"
            rationale = (
                f"Underwritten Stage 2 leader at {wt_pct:.2f}% NAV (below {full_model_wt:.2f}% risk-unit target) trading within "
                f"{ext_10w:+.1f}% of 10W EMA with +{gain_r:.2f}R profit cushion (>= +{envelope['proof_min_gain_r']:.2f}R proof gate); eligible for Tranche-2 scale-up toward {target_wt:.2f}%."
            )
        else:
            verdict = "KEEP_COMPOUNDING"
            action_label = "HOLD / TRAIL" if stage == "STAGE_2" else "HOLD / HARD STOP"
            target_wt = wt_pct
            prov_tag = " [Provisional pre-dossier holding: ADDs frozen until monograph completes]" if not has_dossier else ""
            ratchet_tag = f" (stop ratcheted up from prior plan to {cur}{effective_stop:,.2f})" if stop_ratcheted else ""
            rationale = (
                f"{stage} structure above invalidation stop {cur}{effective_stop:,.2f}{ratchet_tag}; "
                f"retain {wt_pct:.2f}% weight under let-winners-run / deadband rules.{prov_tag}"
            )

        # Short-Timeframe Hysteresis Check (prevents 1-5 day flip-flops on minor price noise)
        if hysteresis_window_active and not safety_override and not dossier_trim_mandate and prior_row:
            p_verdict = prior_row.get("verdict")
            p_close = _num(prior_row.get("close"))
            p_qty = _num(prior_row.get("current_quantity"))
            qty_unchanged = p_qty is not None and abs(qty - p_qty) < 1e-4
            px_move_pct = abs((close / p_close - 1.0) * 100.0) if (p_close and p_close > 0) else 99.0
            if qty_unchanged and px_move_pct <= price_hyst_pct and p_verdict and p_verdict != verdict:
                verdict = p_verdict
                action_label = str(prior_row.get("action_label") or action_label)
                target_wt = float(prior_row.get("target_wt_pct", target_wt))
                explicit_sell_shares = None
                hysteresis_applied = True
                rationale += f" [Hysteresis Lock: kept {verdict} from {prior_as_of} as {px_move_pct:.2f}% price move is within ±{price_hyst_pct:.1f}% deadband.]"

        # Apply Convergence Rebalance Deadband (±1.25% NAV): suppress tiny nuisance trims/adds (except explicit dossier TRIM mandates)
        if not dossier_trim_mandate and verdict in {"TRIM_PROFIT_BOOKING", "ACCUMULATE_ON_DIP"} and abs(target_wt - wt_pct) < deadband_wt_pct:
            verdict = "KEEP_COMPOUNDING"
            action_label = "HOLD / TRAIL (CONVERGED)"
            target_wt = wt_pct
            explicit_sell_shares = None
            rationale += f" [Converged within ±{deadband_wt_pct:.2f}% NAV deadband — zero nuisance trade.]"

        # Apply CIO Context-Aware Override (if supplied via --cio-decisions)
        baseline_verdict = verdict
        decision_source = "BASELINE_RULEBOOK"
        cio_rationale = ""
        if sym in holding_overrides:
            ov = holding_overrides[sym]
            decision_source = "CIO_OVERRIDE"
            verdict = str(ov.get("verdict") or verdict)
            action_label = str(ov.get("action_label") or verdict.replace("_", " "))
            if ov.get("stop_loss") is not None:
                ov_stop = float(ov["stop_loss"])
                effective_stop = max(effective_stop, ov_stop) if ov.get("ratchet_only", True) else ov_stop
                stop_dist = max(0.035, (close - effective_stop) / close) if (close > 0 and effective_stop and close > effective_stop) else 0.10
                heat_val = round(mv * stop_dist, 2)
                heat_pct = round(heat_val / net_worth * 100.0, 2) if net_worth > 0 else 0.0
            if ov.get("target_shares") is not None and close > 0:
                target_wt = round((float(ov["target_shares"]) * close) / net_worth * 100.0, 2)
            elif ov.get("target_wt_pct") is not None:
                target_wt = float(ov["target_wt_pct"])
            elif verdict == "EXIT":
                target_wt = 0.0
            elif verdict == "KEEP_COMPOUNDING":
                target_wt = wt_pct
            explicit_sell_shares = int(ov["sell_shares"]) if ov.get("sell_shares") is not None else None
            cio_rationale = str(ov.get("rationale") or "").strip()
            if cio_rationale:
                rationale = f"[CIO Decision] {cio_rationale}"

        # Convert target_wt into exact whole shares for sells/trims (buys/adds funded in Step 4 waterfall)
        if verdict == "EXIT":
            shares_delta = -qty
            target_qty = 0.0
            target_val = 0.0
            liberated = round(mv, 2)
            equity_liberated_total += liberated
        elif verdict == "TRIM_PROFIT_BOOKING" and target_wt < wt_pct and close > 0:
            if explicit_sell_shares is not None and explicit_sell_shares > 0:
                sell_sh = min(int(math.floor(qty)), int(explicit_sell_shares))
            else:
                desired_val = net_worth * (target_wt / 100.0)
                sell_sh = max(1, int(math.floor((mv - desired_val) / close)))
                sell_sh = min(int(qty) if mkt == "IN" else sell_sh, int(math.floor(qty)))
            if sell_sh <= 0:
                shares_delta = 0.0
                target_qty = qty
                target_val = round(mv, 2)
                liberated = 0.0
            else:
                shares_delta = -float(sell_sh)
                target_qty = round(qty - sell_sh, 6)
                liberated = round(sell_sh * close, 2)
                target_val = round(mv - liberated, 2)
                equity_liberated_total += liberated
        else:
            # Keep or potential ADD (ADD shares are sized against actual cash in Step 4)
            shares_delta = 0.0
            target_qty = qty
            target_val = round(mv, 2)
            liberated = 0.0

        # US Account consolidation guidance on trims/adds
        accounts_held = [str(a.get("account")) for a in (h.get("accounts") or [])]
        preferred_acct = (
            "Zerodha" if mkt == "IN"
            else ("Robinhood" if bucket == "LEVERAGED_SATELLITE" else "Charles Schwab")
        )
        if mkt == "US" and len(accounts_held) > 1 and shares_delta < 0:
            acct_note = "Sell Robinhood duplicate leg first to consolidate equity into Charles Schwab"
        else:
            acct_note = f"Route via {preferred_acct}"

        holding_decisions.append({
            "symbol": sym,
            "company_name": str(sl.get("company_name") or meta.get("company_name") or sym),
            "bucket": bucket,
            "tier": tier,
            "has_dossier": has_dossier,
            "macro_sector": sec_lbl,
            "sector_quadrant": quadrant,
            "sector_stage2_pct": s2_ind_pct,
            "cluster_id": cid,
            "accounts_held": accounts_held,
            "broker_routing": acct_note,
            "current_quantity": qty,
            "target_quantity": target_qty,
            "delta_shares": shares_delta,
            "avg_cost": avg_cost,
            "close": close,
            "effective_stop": effective_stop,
            "stop_ratcheted": stop_ratcheted,
            "target_base": t_base,
            "asymmetry_ratio": asym,
            "stage": stage,
            "rsi14": rsi14,
            "ext_10w_pct": ext_10w,
            "current_value": round(mv, 2),
            "current_wt_pct": wt_pct,
            "desired_wt_pct": target_wt,
            "target_value": target_val,
            "target_wt_pct": round(target_val / net_worth * 100.0, 2),
            "capital_liberated": liberated,
            "capital_deployed": 0.0,
            "pnl_value": pnl_val,
            "pnl_pct": pnl_pct,
            "current_open_heat_value": round(heat_val, 2),
            "current_open_heat_pct": heat_pct,
            "open_heat_value": round(heat_val * (target_val / mv), 2) if mv > 0 else 0.0,
            "open_heat_pct": round((heat_val * (target_val / mv) if mv > 0 else 0.0) / net_worth * 100.0, 2),
            "verdict": verdict,
            "baseline_verdict": baseline_verdict,
            "decision_source": decision_source,
            "cio_rationale": cio_rationale,
            "action_label": action_label,
            "hysteresis_locked": hysteresis_applied,
            "score": score_obj,
            "full_risk_unit_wt_pct": full_model_wt,
            "rationale": rationale,
        })

    # Enforce 25% Cluster Cap across retained holdings if a single cluster still exceeds 25%
    post_cluster_wt: Dict[str, float] = {}
    for hd in holding_decisions:
        if hd["target_value"] > 0 and hd["bucket"] != "CASH_EQUIVALENT":
            post_cluster_wt[hd["cluster_id"]] = post_cluster_wt.get(hd["cluster_id"], 0.0) + hd["target_wt_pct"]

    for cid, cwt in list(post_cluster_wt.items()):
        if cwt > max_cluster_wt + deadband_wt_pct:
            # Trim lowest-scoring member of the breached cluster down to restore <= 25% cap
            members = [hd for hd in holding_decisions if hd["cluster_id"] == cid and hd["target_value"] > 0 and hd["verdict"] != "EXIT"]
            members.sort(key=lambda x: x["score"]["tournament_score"])
            excess_pct = cwt - max_cluster_wt
            for m_hd in members:
                if excess_pct <= 0.25:
                    break
                cut_pct = min(excess_pct, max(0.0, m_hd["target_wt_pct"] - 2.5))
                if cut_pct >= deadband_wt_pct and m_hd["close"] > 0:
                    cut_sh = int(math.floor((net_worth * (cut_pct / 100.0)) / m_hd["close"]))
                    cut_sh = min(cut_sh, int(math.floor(m_hd["target_quantity"])))
                    if cut_sh > 0:
                        freed = round(cut_sh * m_hd["close"], 2)
                        m_hd["target_quantity"] = round(m_hd["target_quantity"] - cut_sh, 6)
                        m_hd["delta_shares"] = round(m_hd["delta_shares"] - cut_sh, 6)
                        m_hd["target_value"] = round(m_hd["target_value"] - freed, 2)
                        m_hd["target_wt_pct"] = round(m_hd["target_value"] / net_worth * 100.0, 2)
                        m_hd["capital_liberated"] = round(m_hd["capital_liberated"] + freed, 2)
                        m_hd["verdict"] = "TRIM_PROFIT_BOOKING"
                        m_hd["action_label"] = "TRIM (25% CLUSTER CAP)"
                        m_hd["rationale"] += f" [Cluster {cid} was {cwt:.1f}% > {max_cluster_wt:.0f}% cap; trimmed {cut_sh} shares.]"
                        equity_liberated_total = round(equity_liberated_total + freed, 2)
                        excess_pct -= round(freed / net_worth * 100.0, 2)
            post_cluster_wt[cid] = sum(
                x["target_wt_pct"] for x in holding_decisions if x["cluster_id"] == cid and x["target_value"] > 0
            )

    # ------------------------------------------------------------------
    # STEP 3: SCORE SHORTLIST & COMPLETED-MONOGRAPH CHALLENGERS (NON-HELD)
    # ------------------------------------------------------------------
    challenger_decisions: List[Dict[str, Any]] = []
    held_active_syms = {hd["symbol"] for hd in holding_decisions if hd["target_value"] > 0}

    combined_challenger_rows: List[Dict[str, Any]] = []
    for sr in shortlist_rows:
        ssym = str(sr["symbol"]).upper()
        sspine = _load_dossier_spine(mkt, ssym)
        s_status = str(sr.get("status") or "").upper()
        s_verdict = str(sspine.get("new_capital_verdict") or sspine.get("verdict") or sr.get("action_verdict") or "").upper()
        if s_verdict == "REJECTED":
            continue
        if s_status == "RESEARCH_REQUIRED" and not sspine.get("_has_published_dossier") and not sr.get("research_dossier_path"):
            continue
        combined_challenger_rows.append(sr)

    for r in combined_challenger_rows:
        sym = str(r["symbol"]).upper()
        if sym in held_by_sym and not held_by_sym[sym].get("is_tracking"):
            continue
        inst_m = inst_map.get(sym) or {}
        snap_sym = snap_map.get(sym) or {}
        tv = snap_sym.get("tradingview") or {}
        s2_ev = snap_sym.get("stage2_evaluation") or {}
        spine = _load_dossier_spine(mkt, sym)
        prior_row = prior_positions_by_sym.get(sym) or {}
        has_monograph = bool(spine.get("_has_published_dossier") or r.get("research_dossier_path"))

        close = _num(inst_m.get("close")) or _num(tv.get("close")) or _num(spine.get("cmp")) or _num(r.get("cmp")) or 0.0
        entry_low = _num(spine.get("entry_zone_low")) or _num(r.get("entry_zone_low")) or round(close * 0.94, 2)
        entry_high = _num(spine.get("entry_zone_high")) or _num(r.get("entry_zone_high")) or round(close * 0.98, 2)
        stop_loss = _num(spine.get("stop_loss")) or _num(r.get("stop_loss")) or round(entry_low * 0.92, 2)
        target_base = _num(spine.get("target_base")) or _num(r.get("target_base"))

        bucket_cands = [spine.get("strategy_bucket"), r.get("strategy_bucket")]
        bucket = next(
            (str(b).upper() for b in bucket_cands if str(b or "").upper() in {"CORE_ALPHA", "TACTICAL_MOMENTUM"}),
            "CORE_ALPHA",
        )
        tier = _normalize_tier(
            spine.get("conviction_tier") or r.get("conviction_tier"),
            default="TIER_2" if bucket == "CORE_ALPHA" else "TIER_3",
        )
        if not spine.get("_has_published_dossier") and "TIER_0" in str(r.get("entry_posture") or ""):
            tier = "TIER_0"

        sma50 = _num(inst_m.get("sma50")) or _num(tv.get("sma50"))
        if inst_m.get("stage") is not None:
            stage = _normalize_stage(inst_m.get("stage"))
        elif sma50 and close and close < sma50:
            stage = "STAGE_3"
        else:
            stage = _normalize_stage(s2_ev.get("weinstein_stage") or spine.get("weinstein_stage") or r.get("weinstein_stage"))

        ema10w = _num(tv.get("ema10_weekly")) or _num(inst_m.get("ema10w_approx")) or sma50 or entry_high
        rsi14 = _num(inst_m.get("rsi14")) or _num(tv.get("rsi_14_daily")) or _num(r.get("rsi_14"))
        rs_63d = _num(inst_m.get("rs_63d_pct"))
        ext_10w = round((close / ema10w - 1.0) * 100.0, 2) if (close and ema10w and ema10w > 0) else 0.0
        dist_above_zone_pct = round((close / entry_high - 1.0) * 100.0, 2) if (close and entry_high and entry_high > 0) else 0.0

        sec_lbl = str(r.get("macro_sector") or spine.get("sector") or tv.get("sector") or "General")
        cid = _cluster_for(sym, sec_lbl, sym)
        quadrant, s2_ind_pct = _resolve_sector_quadrant(sec_lbl, inst_map, stage2_view)
        bq_verdict = str(spine.get("business_quality_verdict") or ("COMPOUNDER_PASS" if r.get("gate_status") == "PASSED" else "CONDITIONAL"))
        kpi_health = str(spine.get("kpi_health") or r.get("kpi_health") or "PASS_WITH_WATCH")
        roic_roce = _num(r.get("roic_pct")) or _num(r.get("roce_pct")) or _num(r.get("roe_pct"))

        ref_px = min(close, entry_high) if close > 0 and entry_high > 0 else close
        asym = (
            round((target_base - ref_px) / (ref_px - stop_loss), 2)
            if (target_base and ref_px > stop_loss)
            else _num(r.get("asymmetry_ratio"))
        )

        raw_verdict_str = str(spine.get("new_capital_verdict") or spine.get("verdict") or r.get("action_verdict") or "").upper()
        posture_str = str(spine.get("entry_posture") or r.get("entry_posture") or "").upper()
        is_rejected = raw_verdict_str == "REJECTED" or str(r.get("gate_status") or "").upper() == "FAIL"
        legacy_orders_disabled = bool(
            not spine.get("_has_published_dossier")
            and (
                r.get("orders_enabled") is False
                or "NO ORDER" in (str(r.get("entry_posture") or "") + " " + str(r.get("notes") or "")).upper()
            )
        )

        score_obj = _score_candidate(
            sym=sym,
            bucket=bucket,
            has_dossier=has_monograph,
            tier="TIER_0" if is_rejected else tier,
            bq_verdict="FUNDAMENTAL_FAIL" if is_rejected else bq_verdict,
            kpi_health=kpi_health,
            roic_or_roce=roic_roce,
            asym_ratio=asym,
            stage=stage,
            ext_10w_pct=ext_10w,
            rsi14=rsi14,
            rs_63d=rs_63d,
            sector_quadrant=quadrant,
            sector_s2_pct=s2_ind_pct,
            cluster_current_wt_pct=post_cluster_wt.get(cid, 0.0),
            cluster_max_wt_pct=max_cluster_wt,
            is_incumbent_or_anchored=bool(prior_row.get("funded_shares", 0) > 0),
            scoring=scoring,
        )

        sizing = _compute_risk_unit_target_wt(close if close > 0 else entry_high, stop_loss, "TIER_0" if is_rejected else tier, scoring)
        full_wt = sizing["full_target_wt_pct"]
        starter_wt = round(full_wt * envelope["starter_fraction"], 2)

        explicit_no_alloc = (
            ("NO_NEW_ALLOCATION" in posture_str or "MONITORING ONLY" in posture_str)
            and raw_verdict_str not in {"WAIT_FOR_SUPPORT", "ACCUMULATE_ON_DIP", "IMMEDIATE_BUY"}
        )
        hard_blocked = (
            is_rejected
            or not has_monograph
            or legacy_orders_disabled
            or tier == "TIER_0"
            or stage in {"STAGE_3", "STAGE_4"}
            or bq_verdict == "FUNDAMENTAL_FAIL"
            or explicit_no_alloc
            or (asym is not None and asym < 1.25)
            or (bucket == "TACTICAL_MOMENTUM" and quadrant == "Lagging")
            or envelope["playbook_mode"] == "CAPITAL_PRESERVATION"
        )

        # Regime-Adaptive 50/50 Starter Eligibility
        if is_rejected:
            entry_action = "REJECTED_BY_DOSSIER"
            eligible_now = False
            why = f"Published monograph rejected new capital ({stage}, R:R={asym if asym is not None else 'N/A'}); zero allocation."
        elif not has_monograph or legacy_orders_disabled:
            entry_action = "MONITOR_ONLY_PRE_MONOGRAPH"
            eligible_now = False
            why = (
                f"Legacy shortlist monitor without a published 10-chapter monograph ({stage}, support {cur}{entry_low:,.2f}–{cur}{entry_high:,.2f}); "
                f"no order enabled until refreshed monograph underwriting completes."
            )
        elif hard_blocked or full_wt <= 0:
            entry_action = "DEFERRED_GATE_BLOCKED"
            eligible_now = False
            why = (
                f"Blocked from immediate deployment ({stage}, tier={tier}, sector={quadrant}, "
                f"asymmetry={asym if asym is not None else 'N/A'}); monitor {cur}{entry_low:,.2f}–{cur}{entry_high:,.2f} and await Stage 2 / R:R confirmation."
            )
        elif envelope["playbook_mode"] == "BROAD_TREND":
            if ext_10w <= envelope["max_starter_extension_pct"] and (rsi14 is None or rsi14 <= 73.0) and raw_verdict_str in {"IMMEDIATE_BUY", "ACCUMULATE_ON_DIP"}:
                entry_action = "DEPLOY_STARTER_NOW"
                eligible_now = True
                why = (
                    f"Broad Uptrend + Stage 2 within {ext_10w:+.1f}% of 10W EMA: deploy 50% Starter Tranche ({starter_wt:.2f}% NAV) "
                    f"now; reserve second 50% for pullback to {cur}{entry_low:,.2f}–{cur}{entry_high:,.2f} or +0.75R pyramid."
                )
            else:
                entry_action = "RESTING_LIMIT_AT_SUPPORT"
                eligible_now = False
                why = (
                    f"Stage 2 monograph with {asym:.2f}:1 support asymmetry, currently {dist_above_zone_pct:+.1f}% vs support top {cur}{entry_high:,.2f}; "
                    f"stage resting limit for 50% Starter ({starter_wt:.2f}% NAV) inside {cur}{entry_low:,.2f}–{cur}{entry_high:,.2f}."
                )
        else:
            # SIDEWAYS_DEFENSIVE: require proximity to support band AND explicit IMMEDIATE_BUY/ACCUMULATE_ON_DIP or in-zone touch
            near_support = (dist_above_zone_pct <= envelope["max_starter_extension_pct"]) or (ext_10w <= envelope["max_starter_extension_pct"])
            if near_support and (rsi14 is None or rsi14 <= 68.0) and (raw_verdict_str in {"IMMEDIATE_BUY", "ACCUMULATE_ON_DIP"} or dist_above_zone_pct <= 1.0):
                entry_action = "DEPLOY_STARTER_AT_SUPPORT"
                eligible_now = True
                why = (
                    f"Sideways-tape support starter: trading inside/near support ({cur}{close:,.2f} vs zone {cur}{entry_low:,.2f}–{cur}{entry_high:,.2f}, "
                    f"{ext_10w:+.1f}% vs 10W EMA); deploy 50% Starter ({starter_wt:.2f}% NAV), add second 50% only after >= +1R proof."
                )
            else:
                entry_action = "RESTING_LIMIT_AT_SUPPORT"
                eligible_now = False
                why = (
                    f"Underwritten Stage 2 candidate trading {dist_above_zone_pct:+.1f}% above support top {cur}{entry_high:,.2f} ({ext_10w:+.1f}% vs 10W EMA); "
                    f"stage resting limit for 50% Starter ({starter_wt:.2f}% NAV) inside {cur}{entry_low:,.2f}–{cur}{entry_high:,.2f} (R:R {asym:.2f}:1)."
                )

        # Hysteresis check on challenger eligibility across 1-5 day reruns
        if hysteresis_window_active and prior_row and not hard_blocked:
            p_action = prior_row.get("entry_action")
            p_close = _num(prior_row.get("close"))
            px_move_pct = abs((close / p_close - 1.0) * 100.0) if (p_close and p_close > 0) else 99.0
            if p_action in {"DEPLOY_STARTER_NOW", "DEPLOY_STARTER_AT_SUPPORT", "RESTING_LIMIT_AT_SUPPORT"} and px_move_pct <= price_hyst_pct:
                if p_action != entry_action:
                    entry_action = p_action
                    eligible_now = entry_action in {"DEPLOY_STARTER_NOW", "DEPLOY_STARTER_AT_SUPPORT"}
                    why += f" [Hysteresis Lock: preserved {entry_action} from {prior_as_of}.]"

        baseline_entry_action = entry_action
        ch_decision_source = "BASELINE_RULEBOOK"
        ch_cio_rationale = ""
        if sym in challenger_overrides:
            ov = challenger_overrides[sym]
            ch_decision_source = "CIO_OVERRIDE"
            if ov.get("entry_action"):
                entry_action = str(ov["entry_action"])
            eligible_now = entry_action in {"DEPLOY_STARTER_NOW", "DEPLOY_STARTER_AT_SUPPORT"}
            if ov.get("starter_wt_pct") is not None:
                starter_wt = float(ov["starter_wt_pct"])
            if ov.get("stop_loss") is not None:
                stop_loss = float(ov["stop_loss"])
            ch_cio_rationale = str(ov.get("rationale") or "").strip()
            if ch_cio_rationale:
                why = f"[CIO Decision] {ch_cio_rationale}"

        challenger_decisions.append({
            "symbol": sym,
            "company_name": str(spine.get("company_name") or r.get("company_name") or sym),
            "has_dossier": has_monograph,
            "bucket": bucket,
            "tier": "TIER_0" if is_rejected else tier,
            "macro_sector": sec_lbl,
            "sector_quadrant": quadrant,
            "sector_stage2_pct": s2_ind_pct,
            "cluster_id": cid,
            "close": close,
            "entry_zone_low": entry_low,
            "entry_zone_high": entry_high,
            "stop_loss": stop_loss,
            "target_base": target_base,
            "asymmetry_ratio": asym,
            "stage": stage,
            "rsi14": rsi14,
            "ext_10w_pct": ext_10w,
            "full_target_wt_pct": full_wt,
            "starter_target_wt_pct": starter_wt,
            "risk_budget_bps": sizing["risk_budget_bps"],
            "entry_action": entry_action,
            "baseline_entry_action": baseline_entry_action,
            "decision_source": ch_decision_source,
            "cio_rationale": ch_cio_rationale,
            "eligible_now": eligible_now,
            "funded_shares": 0,
            "funded_value": 0.0,
            "funded_wt_pct": 0.0,
            "displaced_incumbent": None,
            "broker_routing": "Zerodha" if mkt == "IN" else "Charles Schwab",
            "score": score_obj,
            "rationale": why,
        })

    def _challenger_sort_key(item: Dict[str, Any]) -> tuple:
        act = item["entry_action"]
        prio = (
            0 if item["eligible_now"]
            else 1 if act == "RESTING_LIMIT_AT_SUPPORT"
            else 2 if act == "DEFERRED_GATE_BLOCKED"
            else 3 if act == "MONITOR_ONLY_PRE_MONOGRAPH"
            else 4
        )
        return (prio, -item["score"]["tournament_score"])

    challenger_decisions.sort(key=_challenger_sort_key)

    # ------------------------------------------------------------------
    # STEP 4: SLOT TOURNAMENT (12-15 CAP), HEAT GATE & CASH WATERFALL
    # ------------------------------------------------------------------
    # Count unique active risk underlyings (Equities + 2x/3x ETFs + Active Option Underlyings)
    retained_equity_underlyings = {
        SINGLE_STOCK_LEVERAGED_ETFS.get(hd["symbol"], (hd["symbol"], 1.0))[0]
        for hd in holding_decisions
        if hd["target_value"] > 0 and hd["bucket"] != "CASH_EQUIVALENT"
    }
    active_unique_underlyings = retained_equity_underlyings | option_underlyings_active

    # Check if we exceed max_slots (15) OR if an eligible challenger displaces a weak Stage 3 incumbent (>= +15 pts)
    displaced_pairs: List[Dict[str, Any]] = []
    eligible_challengers = [c for c in challenger_decisions if c["eligible_now"]]

    if len(active_unique_underlyings) >= max_slots and eligible_challengers:
        weak_incumbents = [
            hd for hd in holding_decisions
            if hd["target_value"] > 0
            and hd["bucket"] not in {"CASH_EQUIVALENT"}
            and hd["stage"] in {"STAGE_3", "UNKNOWN"}
        ]
        weak_incumbents.sort(key=lambda x: x["score"]["tournament_score"])
        for ch in eligible_challengers:
            if not weak_incumbents:
                break
            weakest = weak_incumbents[0]
            score_gap = round(ch["score"]["tournament_score"] - weakest["score"]["tournament_score"], 1)
            if score_gap >= displace_min_pts:
                weak_incumbents.pop(0)
                freed = round(weakest["target_value"], 2)
                weakest["verdict"] = "EXIT"
                weakest["action_label"] = f"EXIT (DISPLACED BY {ch['symbol']})"
                weakest["delta_shares"] = -weakest["current_quantity"]
                weakest["target_quantity"] = 0.0
                weakest["target_value"] = 0.0
                weakest["target_wt_pct"] = 0.0
                weakest["capital_liberated"] = round(weakest["current_value"], 2)
                weakest["open_heat_value"] = 0.0
                weakest["open_heat_pct"] = 0.0
                weakest["rationale"] += (
                    f" [Slot Displacement: {ch['symbol']} ({ch['score']['tournament_score']} pts) beat "
                    f"{weakest['symbol']} ({weakest['score']['tournament_score']} pts) by +{score_gap:.1f} pts >= {displace_min_pts:.0f} hurdle.]"
                )
                equity_liberated_total = round(equity_liberated_total + freed, 2)
                ch["displaced_incumbent"] = weakest["symbol"]
                displaced_pairs.append({
                    "exited": weakest["symbol"],
                    "entered": ch["symbol"],
                    "score_advantage_pts": score_gap,
                    "capital_freed": freed,
                })
                active_unique_underlyings.discard(weakest["symbol"])

    # Compute deployable capital above minimum cash floor & remaining portfolio heat budget
    gross_cash_pool = round(cash_total + equity_liberated_total + liberated_from_options, 2)
    min_cash_reserve = round(net_worth * (envelope["min_cash_floor_pct"] / 100.0), 2)
    deployable_cash = max(0.0, round(gross_cash_pool - min_cash_reserve, 2))

    pre_trade_open_heat_pct = round(
        sum(hd["current_open_heat_pct"] for hd in holding_decisions)
        + sum(od["current_open_heat_pct"] for od in options_decisions),
        2,
    )
    post_phase1_open_heat_pct = round(
        sum(hd["open_heat_pct"] for hd in holding_decisions if hd["target_value"] > 0)
        + sum(od["open_heat_pct"] for od in options_decisions if od["target_value"] > 0),
        2,
    )
    remaining_heat_pct = max(0.0, round(envelope["max_portfolio_heat_pct"] - post_phase1_open_heat_pct, 2))

    # Priority 1: Fund any qualified Tranche-2 scale-up ADDs on existing Stage 2 winners
    holding_adds = [
        hd for hd in holding_decisions
        if hd["verdict"] == "ACCUMULATE_ON_DIP" and hd["desired_wt_pct"] > hd["current_wt_pct"] + deadband_wt_pct
    ]
    holding_adds.sort(key=lambda x: -x["score"]["tournament_score"])

    total_deployed_equities = 0.0
    for hd in holding_adds:
        cid = hd["cluster_id"]
        cluster_room_pct = max(0.0, max_cluster_wt - post_cluster_wt.get(cid, 0.0))
        desired_add_pct = min(hd["desired_wt_pct"] - hd["current_wt_pct"], cluster_room_pct)
        if desired_add_pct < deadband_wt_pct or deployable_cash <= 0 or hd["close"] <= 0:
            hd["verdict"] = "KEEP_COMPOUNDING"
            hd["action_label"] = "HOLD / TRAIL"
            continue
        stop_dist_frac = max(0.035, (hd["close"] - hd["effective_stop"]) / hd["close"]) if hd["close"] > hd["effective_stop"] else 0.10
        max_val_by_heat = net_worth * (remaining_heat_pct / 100.0) / stop_dist_frac if remaining_heat_pct > 0 else 0.0
        alloc_cap = min(deployable_cash, net_worth * (desired_add_pct / 100.0), max_val_by_heat)
        buy_sh = int(math.floor(alloc_cap / hd["close"]))
        cost_val = round(buy_sh * hd["close"], 2)
        if buy_sh <= 0 or (cost_val / net_worth * 100.0) < deadband_wt_pct * 0.8:
            hd["verdict"] = "KEEP_COMPOUNDING"
            hd["action_label"] = "HOLD / TRAIL"
            continue
        hd["delta_shares"] = float(buy_sh)
        hd["target_quantity"] = round(hd["current_quantity"] + buy_sh, 6)
        hd["target_value"] = round(hd["current_value"] + cost_val, 2)
        hd["target_wt_pct"] = round(hd["target_value"] / net_worth * 100.0, 2)
        hd["capital_deployed"] = cost_val
        added_heat_pct = round((cost_val * stop_dist_frac) / net_worth * 100.0, 2)
        hd["open_heat_value"] = round(hd["open_heat_value"] + cost_val * stop_dist_frac, 2)
        hd["open_heat_pct"] = round(hd["open_heat_pct"] + added_heat_pct, 2)
        deployable_cash = round(deployable_cash - cost_val, 2)
        total_deployed_equities = round(total_deployed_equities + cost_val, 2)
        remaining_heat_pct = max(0.0, round(remaining_heat_pct - added_heat_pct, 2))
        post_cluster_wt[cid] = round(post_cluster_wt.get(cid, 0.0) + (cost_val / net_worth * 100.0), 2)

    # Priority 2: Fund eligible Shortlist Starter Tranches up to max_slots & heat/cluster caps
    for ch in challenger_decisions:
        if not ch["eligible_now"]:
            continue
        if len(active_unique_underlyings) >= max_slots:
            ch["entry_action"] = "BLOCKED_SLOT_CAP_FULL"
            ch["rationale"] += f" [Slot Cap: {len(active_unique_underlyings)}/{max_slots} active risk slots full; challenger did not clear +{displace_min_pts:.0f}pt displacement hurdle.]"
            continue
        cid = ch["cluster_id"]
        cluster_room_pct = max(0.0, max_cluster_wt - post_cluster_wt.get(cid, 0.0))
        alloc_wt_pct = min(ch["starter_target_wt_pct"], cluster_room_pct)
        if alloc_wt_pct < deadband_wt_pct or deployable_cash <= 0 or ch["close"] <= 0:
            ch["entry_action"] = "DEFERRED_CASH_OR_CLUSTER_CAP"
            continue
        stop_dist_frac = max(0.035, (ch["close"] - ch["stop_loss"]) / ch["close"]) if ch["close"] > ch["stop_loss"] else 0.10
        max_val_by_heat = net_worth * (remaining_heat_pct / 100.0) / stop_dist_frac if remaining_heat_pct > 0 else 0.0
        alloc_cap = min(deployable_cash, net_worth * (alloc_wt_pct / 100.0), max_val_by_heat)
        buy_sh = int(math.floor(alloc_cap / ch["close"]))
        cost_val = round(buy_sh * ch["close"], 2)
        if buy_sh <= 0 or (cost_val / net_worth * 100.0) < 1.0:
            ch["entry_action"] = "DEFERRED_HEAT_OR_LOT_SIZE"
            continue
        ch["funded_shares"] = buy_sh
        ch["funded_value"] = cost_val
        ch["funded_wt_pct"] = round(cost_val / net_worth * 100.0, 2)
        added_heat_pct = round((cost_val * stop_dist_frac) / net_worth * 100.0, 2)
        deployable_cash = round(deployable_cash - cost_val, 2)
        total_deployed_equities = round(total_deployed_equities + cost_val, 2)
        remaining_heat_pct = max(0.0, round(remaining_heat_pct - added_heat_pct, 2))
        post_cluster_wt[cid] = round(post_cluster_wt.get(cid, 0.0) + ch["funded_wt_pct"], 2)
        active_unique_underlyings.add(ch["symbol"])

    # ------------------------------------------------------------------
    # STEP 5: EXACT 100.00% RECONCILED MONEY BRIDGE & CONVERGENCE METRICS
    # ------------------------------------------------------------------
    target_cash = round(gross_cash_pool - total_deployed_equities, 2)
    tracking_total_val = round(sum(t["current_value"] for t in tracking_rows), 2)
    target_options_val = round(sum(o["target_value"] for o in options_decisions), 2)
    target_equities_val = round(
        sum(hd["target_value"] for hd in holding_decisions)
        + tracking_total_val
        + sum(ch["funded_value"] for ch in challenger_decisions),
        2,
    )

    # Guarantee penny-exact reconciliation against net_worth
    reconciliation_drift = round(net_worth - (target_equities_val + target_options_val + target_cash), 2)
    if abs(reconciliation_drift) > 0:
        target_cash = round(target_cash + reconciliation_drift, 2)

    money_bridge_rows: List[Dict[str, Any]] = []
    for hd in sorted(holding_decisions, key=lambda x: -x["current_value"]):
        var_val = round(hd["target_value"] - hd["current_value"], 2)
        var_pct = round(hd["target_wt_pct"] - hd["current_wt_pct"], 2)
        money_bridge_rows.append({
            "symbol": hd["symbol"],
            "kind": "HOLDING",
            "bucket": hd["bucket"],
            "current_value": hd["current_value"],
            "current_wt_pct": hd["current_wt_pct"],
            "target_value": hd["target_value"],
            "target_wt_pct": hd["target_wt_pct"],
            "variance_value": var_val,
            "variance_wt_pct": var_pct,
            "action_mandate": hd["action_label"],
        })

    for ch in challenger_decisions:
        if ch["funded_value"] > 0:
            money_bridge_rows.append({
                "symbol": ch["symbol"],
                "kind": "NEW_STARTER",
                "bucket": ch["bucket"],
                "current_value": 0.0,
                "current_wt_pct": 0.0,
                "target_value": ch["funded_value"],
                "target_wt_pct": ch["funded_wt_pct"],
                "variance_value": ch["funded_value"],
                "variance_wt_pct": ch["funded_wt_pct"],
                "action_mandate": f"STARTER BUY ({ch['funded_shares']} sh)",
            })

    if tracking_rows:
        tw = round(tracking_total_val / net_worth * 100.0, 2)
        money_bridge_rows.append({
            "symbol": f"TRACKING ({len(tracking_rows)} stubs: {', '.join(t['symbol'] for t in tracking_rows)})",
            "kind": "TRACKING_SUMMARY",
            "bucket": "TRACKING",
            "current_value": tracking_total_val,
            "current_wt_pct": tw,
            "target_value": tracking_total_val,
            "target_wt_pct": tw,
            "variance_value": 0.0,
            "variance_wt_pct": 0.0,
            "action_mandate": "IGNORED IN SLOT COUNT",
        })

    if options_decisions:
        cw = round(options_mv_total / net_worth * 100.0, 2)
        tw = round(target_options_val / net_worth * 100.0, 2)
        money_bridge_rows.append({
            "symbol": f"OPTIONS BOOK ({len(options_decisions)} contracts)",
            "kind": "OPTIONS_SUMMARY",
            "bucket": "LEAPS_OPTIONS",
            "current_value": options_mv_total,
            "current_wt_pct": cw,
            "target_value": target_options_val,
            "target_wt_pct": tw,
            "variance_value": round(target_options_val - options_mv_total, 2),
            "variance_wt_pct": round(tw - cw, 2),
            "action_mandate": "HOLD / REPAIR ON STOPS" if liberated_from_options == 0 else "PARTIAL EXIT / TRIM",
        })

    cash_cw = round(cash_total / net_worth * 100.0, 2)
    cash_tw = round(target_cash / net_worth * 100.0, 2)
    money_bridge_rows.append({
        "symbol": "CASH & LIQUID BUFFER",
        "kind": "CASH",
        "bucket": "CASH",
        "current_value": round(cash_total, 2),
        "current_wt_pct": cash_cw,
        "target_value": target_cash,
        "target_wt_pct": cash_tw,
        "variance_value": round(target_cash - cash_total, 2),
        "variance_wt_pct": round(cash_tw - cash_cw, 2),
        "action_mandate": f"RESERVE FLOOR ({envelope['min_cash_floor_pct']:.1f}% MIN)",
    })

    # Compute Sleeve Summary & Combined Decay Check
    target_bucket_totals: Dict[str, float] = {"CORE_ALPHA": 0.0, "TACTICAL_MOMENTUM": 0.0, "LEVERAGED_SATELLITE": 0.0}
    for hd in holding_decisions:
        if hd["bucket"] in target_bucket_totals:
            target_bucket_totals[hd["bucket"]] += hd["target_value"]
        elif hd["bucket"] == "CASH_EQUIVALENT":
            pass
    for ch in challenger_decisions:
        if ch["funded_value"] > 0 and ch["bucket"] in target_bucket_totals:
            target_bucket_totals[ch["bucket"]] += ch["funded_value"]

    target_lev_pct = round(target_bucket_totals["LEVERAGED_SATELLITE"] / net_worth * 100.0, 2)
    target_opt_cap_pct = round(max(options_cost_total - liberated_from_options, target_options_val) / net_worth * 100.0, 2)
    combined_decay_pct = round(target_lev_pct + target_opt_cap_pct, 2)
    combined_decay_limit = float((buckets_cfg.get("COMBINED_DECAY_SLEEVE") or {}).get("hard_max_pct", 15.0))

    # Compute Monotonic Convergence Score & Prior-Run Diff
    total_abs_variance = sum(
        abs(r["variance_value"]) for r in money_bridge_rows if r["kind"] not in {"CASH", "TRACKING_SUMMARY"}
    )
    convergence_score_pct = round(max(0.0, min(100.0, (1.0 - total_abs_variance / net_worth) * 100.0)), 1)

    completed_edits: List[str] = []
    genuine_changes: List[str] = []
    locked_symbols: List[str] = [hd["symbol"] for hd in holding_decisions if hd["hysteresis_locked"]]

    if prior_state:
        for sym, pr in prior_positions_by_sym.items():
            if sym.startswith("OPT:"):
                continue
            p_qty = _num(pr.get("current_quantity")) or 0.0
            p_target_qty = _num(pr.get("target_quantity")) or 0.0
            now_h = held_by_sym.get(sym)
            now_qty = float(now_h["quantity"]) if now_h else 0.0
            if abs(now_qty - p_qty) > 1e-4:
                if abs(now_qty - p_target_qty) <= max(1.0, p_target_qty * 0.15):
                    completed_edits.append(f"{sym}: executed target quantity ({p_qty:g} -> {now_qty:g} shares)")
                else:
                    completed_edits.append(f"{sym}: partial trade executed ({p_qty:g} -> {now_qty:g} shares)")
        for hd in holding_decisions:
            pr = prior_positions_by_sym.get(hd["symbol"])
            if pr and pr.get("verdict") != hd["verdict"] and not hd["hysteresis_locked"]:
                genuine_changes.append(f"{hd['symbol']}: {pr.get('verdict')} -> {hd['verdict']}")

    # Build Persisted State Payload (keyed by unique `symbol` for record_merge.py compatibility)
    persisted_positions: List[Dict[str, Any]] = []
    for hd in holding_decisions:
        persisted_positions.append({
            "symbol": hd["symbol"],
            "anchor_date": prior_positions_by_sym.get(hd["symbol"], {}).get("anchor_date") or as_of,
            "as_of_date": as_of,
            "close": hd["close"],
            "current_quantity": hd["current_quantity"],
            "target_quantity": hd["target_quantity"],
            "current_wt_pct": hd["current_wt_pct"],
            "target_wt_pct": hd["target_wt_pct"],
            "effective_stop": hd["effective_stop"],
            "verdict": hd["verdict"],
            "action_label": hd["action_label"],
            "tournament_score": hd["score"]["tournament_score"],
        })
    for ch in challenger_decisions:
        persisted_positions.append({
            "symbol": ch["symbol"],
            "anchor_date": prior_positions_by_sym.get(ch["symbol"], {}).get("anchor_date") or as_of,
            "as_of_date": as_of,
            "close": ch["close"],
            "current_quantity": 0.0,
            "target_quantity": float(ch["funded_shares"]),
            "current_wt_pct": 0.0,
            "target_wt_pct": ch["funded_wt_pct"],
            "effective_stop": ch["stop_loss"],
            "verdict": ch["entry_action"],
            "entry_action": ch["entry_action"],
            "funded_shares": ch["funded_shares"],
            "tournament_score": ch["score"]["tournament_score"],
        })

    final_open_heat_pct = round(
        sum(hd["open_heat_pct"] for hd in holding_decisions if hd["target_value"] > 0)
        + sum(od["open_heat_pct"] for od in options_decisions if od["target_value"] > 0)
        + sum(
            round(
                (ch["funded_value"] * max(0.035, (ch["close"] - ch["stop_loss"]) / ch["close"])) / net_worth * 100.0,
                2,
            )
            for ch in challenger_decisions
            if ch["funded_value"] > 0 and ch["close"] > 0
        ),
        2,
    )

    post_cluster_heat: Dict[str, float] = {}
    for hd in holding_decisions:
        if hd["target_value"] > 0 and hd["bucket"] != "CASH_EQUIVALENT":
            post_cluster_heat[hd["cluster_id"]] = round(post_cluster_heat.get(hd["cluster_id"], 0.0) + hd["open_heat_pct"], 2)
    for ch in challenger_decisions:
        if ch["funded_value"] > 0 and ch["close"] > 0:
            ch_h = round((ch["funded_value"] * max(0.035, (ch["close"] - ch["stop_loss"]) / ch["close"])) / net_worth * 100.0, 2)
            post_cluster_heat[ch["cluster_id"]] = round(post_cluster_heat.get(ch["cluster_id"], 0.0) + ch_h, 2)

    dossier_debt_queue.sort(key=lambda x: -x["market_value"])

    # Hard Guardrail Enforcement when CIO overrides are active
    target_cash_wt_check = round(target_cash / net_worth * 100.0, 2) if net_worth > 0 else 0.0
    if holding_overrides or challenger_overrides:
        if final_open_heat_pct > envelope["max_portfolio_heat_pct"] + 0.05:
            raise ValueError(
                f"CIO_GUARDRAIL_BREACH: Open portfolio heat {final_open_heat_pct:.2f}% exceeds regime cap {envelope['max_portfolio_heat_pct']:.1f}%."
            )
        if target_cash_wt_check + 0.05 < envelope["min_cash_floor_pct"]:
            raise ValueError(
                f"CIO_GUARDRAIL_BREACH: Target cash {target_cash_wt_check:.2f}% is below regime floor {envelope['min_cash_floor_pct']:.1f}%."
            )
        for cid, ch_heat in post_cluster_heat.items():
            c_wt = post_cluster_wt.get(cid, 0.0)
            if ch_heat > max_cluster_heat + 0.05 or c_wt > max_cluster_wt + 0.25:
                raise ValueError(
                    f"CIO_GUARDRAIL_BREACH: Cluster {cid} breaches cap (weight {c_wt:.2f}%/{max_cluster_wt:.1f}%, heat {ch_heat:.2f}%/{max_cluster_heat:.1f}%)."
                )

    cio_overrides_count = sum(1 for hd in holding_decisions if hd.get("decision_source") == "CIO_OVERRIDE") + sum(
        1 for ch in challenger_decisions if ch.get("decision_source") == "CIO_OVERRIDE"
    )

    sells_and_trims = [hd for hd in holding_decisions if hd["delta_shares"] < 0]
    equity_buys_and_adds = (
        [hd for hd in holding_decisions if hd["delta_shares"] > 0]
        + [ch for ch in challenger_decisions if ch["funded_shares"] > 0]
    )
    resting_limit_orders = [ch for ch in challenger_decisions if ch["entry_action"] == "RESTING_LIMIT_AT_SUPPORT"]

    return {
        "schema_version": 4,
        "market": mkt,
        "currency": "INR" if mkt == "IN" else "USD",
        "currency_symbol": cur,
        "as_of_date": as_of,
        "net_worth": round(net_worth, 2),
        "cio_context": {
            "decision_mode": "CIO_LED" if (cio_overrides_count > 0 or cio_portfolio_thesis) else "BASELINE_ONLY",
            "overrides_applied_count": cio_overrides_count,
            "portfolio_thesis": cio_portfolio_thesis,
        },
        "regime_envelope": envelope,
        "portfolio_summary": {
            "net_worth": round(net_worth, 2),
            "current_equities_value": round(equities_value, 2),
            "current_equities_wt_pct": round(equities_value / net_worth * 100.0, 2),
            "current_options_value": round(options_mv_total, 2),
            "current_options_wt_pct": round(options_mv_total / net_worth * 100.0, 2),
            "current_options_cost_basis": round(options_cost_total, 2),
            "current_cash_value": round(cash_total, 2),
            "current_cash_wt_pct": cash_cw,
            "target_equities_value": target_equities_val,
            "target_equities_wt_pct": round(target_equities_val / net_worth * 100.0, 2),
            "target_options_value": target_options_val,
            "target_options_wt_pct": round(target_options_val / net_worth * 100.0, 2),
            "target_cash_value": target_cash,
            "target_cash_wt_pct": cash_tw,
            "capital_liberated_equities": round(equity_liberated_total, 2),
            "capital_liberated_options": round(liberated_from_options, 2),
            "capital_deployed_equities": round(total_deployed_equities, 2),
            "active_non_tracking_equities_count": sum(1 for hd in holding_decisions if hd["target_value"] > 0 and hd["bucket"] != "CASH_EQUIVALENT")
            + sum(1 for ch in challenger_decisions if ch["funded_value"] > 0),
            "active_unique_risk_underlyings_count": len(active_unique_underlyings),
            "active_slots_range": [min_slots, max_slots],
            "tracking_positions_count": len(tracking_rows),
            "tracking_positions_value": tracking_total_val,
            "current_open_heat_pct": pre_trade_open_heat_pct,
            "target_open_heat_pct": final_open_heat_pct,
            "max_portfolio_heat_pct": envelope["max_portfolio_heat_pct"],
            "core_alpha_target_wt_pct": round(target_bucket_totals["CORE_ALPHA"] / net_worth * 100.0, 2),
            "tactical_momentum_target_wt_pct": round(target_bucket_totals["TACTICAL_MOMENTUM"] / net_worth * 100.0, 2),
            "leveraged_satellite_target_wt_pct": target_lev_pct,
            "options_cap_basis_pct": target_opt_cap_pct,
            "combined_decay_sleeve_pct": combined_decay_pct,
            "combined_decay_hard_max_pct": combined_decay_limit,
            "combined_decay_breached": combined_decay_pct > combined_decay_limit,
            "effective_market_exposure_pct": risk_ov.get("effective_market_exposure_pct"),
            "portfolio_beta_weighted": risk_ov.get("portfolio_beta_weighted"),
        },
        "stability_and_convergence": {
            "convergence_score_pct": convergence_score_pct,
            "prior_as_of_date": prior_as_of,
            "days_since_prior": days_since_prior,
            "hysteresis_window_active": hysteresis_window_active,
            "rebalance_deadband_wt_pct": deadband_wt_pct,
            "price_band_hysteresis_pct": price_hyst_pct,
            "actionable_trades_count": len(sells_and_trims) + len(equity_buys_and_adds) + sum(1 for o in options_decisions if o["capital_liberated"] > 0),
            "completed_edits_since_prior": completed_edits,
            "hysteresis_locked_symbols": locked_symbols,
            "genuine_new_changes": genuine_changes,
            "slot_displacements": displaced_pairs,
        },
        "account_cash_routing": account_cash,
        "clusters": [
            {
                "cluster_id": cid,
                "symbols": cluster_syms_map.get(cid, []),
                "current_wt_pct": round(cluster_wt_map.get(cid, 0.0), 2),
                "target_wt_pct": round(post_cluster_wt.get(cid, 0.0), 2),
                "current_open_heat_pct": round(cluster_heat_map.get(cid, 0.0), 2),
                "open_heat_pct": round(post_cluster_heat.get(cid, 0.0), 2),
                "max_cluster_wt_pct": max_cluster_wt,
                "max_cluster_heat_pct": max_cluster_heat,
            }
            for cid in sorted(cluster_wt_map, key=lambda k: -cluster_wt_map[k])
        ],
        "holding_decisions": holding_decisions,
        "tracking_positions": tracking_rows,
        "options_decisions": options_decisions,
        "challenger_decisions": challenger_decisions,
        "money_bridge": money_bridge_rows,
        "execution_plan": {
            "phase1_sells_and_trims_count": len(sells_and_trims),
            "phase2_funded_buys_and_adds_count": len(equity_buys_and_adds),
            "phase2_resting_support_limits_count": len(resting_limit_orders),
        },
        "dossier_debt_queue": dossier_debt_queue,
        "persisted_state": {
            "market": mkt,
            "schema_version": 4,
            "as_of_date": as_of,
            "convergence_score_pct": convergence_score_pct,
            "positions": persisted_positions,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market", choices=["IN", "US"], required=True)
    ap.add_argument("--facts", default="", help="Path to facts_<MKT>_<date>.json")
    ap.add_argument("--positions", default="", help="Path to positions_<MKT>_<date>.json")
    ap.add_argument("--snapshots", default="", help="Path to snapshots_<MKT>_<date>.json")
    ap.add_argument("--shortlist", default="", help="Path to data/shortlist/<MKT>.json")
    ap.add_argument("--options-snapshot", default="", help="Path to options_snapshot_<MKT>_<date>.json")
    ap.add_argument("--prior-state", default="", help="Path to prior data/allocations/<MKT>.json")
    ap.add_argument("--persist-state", default="", help="Write updated anchor state to data/allocations/<MKT>.json")
    ap.add_argument("--cio-decisions", default="", help="Optional path to cio_decisions_<MKT>.json for CIO-led overrides")
    ap.add_argument("--from-repo", action="store_true", help="Fallback offline build from repo transaction logs + latest views")
    ap.add_argument("--as-of", default="", help="Override as-of date in --from-repo mode")
    ap.add_argument("--out", required=True, help="Output path for allocation_<MKT>_<date>.json")
    args = ap.parse_args()

    mkt = args.market.upper()
    if args.from_repo or not (args.facts and args.positions):
        facts, positions, snap_default = build_from_repo_fallback(mkt, as_of=args.as_of)
    else:
        facts = _load_json(args.facts)
        positions = _load_json(args.positions)
        snap_default = _load_json(REPO / "data" / "views" / f"snapshots_{mkt}_latest.json")

    snapshots = _load_json(args.snapshots) or snap_default
    shortlist = _load_json(args.shortlist or (REPO / "data" / "shortlist" / f"{mkt}.json"))
    options_snap = _load_json(args.options_snapshot)
    prior_path = args.prior_state or str(REPO / "data" / "allocations" / f"{mkt}.json")
    prior_state = _load_json(prior_path)
    cio_decisions = _load_json(args.cio_decisions) if args.cio_decisions else None

    result = allocate_portfolio(
        market=mkt,
        facts=facts,
        positions=positions,
        snapshots=snapshots,
        shortlist_data=shortlist,
        options_snapshot=options_snap,
        prior_state=prior_state,
        cio_decisions=cio_decisions,
    )

    out_p = Path(args.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ps = result["portfolio_summary"]
    sc = result["stability_and_convergence"]
    print(
        f"[+] {mkt} Allocation ({result['as_of_date']}): Net Worth {result['currency_symbol']}{ps['net_worth']:,.2f} | "
        f"Active Risk Names {ps['active_unique_risk_underlyings_count']}/{ps['active_slots_range'][1]} "
        f"(+{ps['tracking_positions_count']} tracking ignored) | "
        f"Heat {ps['current_open_heat_pct']:.2f}% -> {ps['target_open_heat_pct']:.2f}% (cap {ps['max_portfolio_heat_pct']:.1f}%) | "
        f"Convergence {sc['convergence_score_pct']:.1f}% ({sc['actionable_trades_count']} trades)"
    )

    if args.persist_state:
        persist_p = Path(args.persist_state)
        persist_p.parent.mkdir(parents=True, exist_ok=True)
        persist_p.write_text(json.dumps(result["persisted_state"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[+] Persisted anchor state to {persist_p}")


if __name__ == "__main__":
    main()
