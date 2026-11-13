#!/usr/bin/env python3
"""
Deterministic Deep Business-Monograph Dossier Builder (scripts/dossier_builder_template.py).

Renders a complete, book-length company monograph and multi-horizon Stage 2 investment dossier
from a structured JSON spec and consumer-tool snapshots (scripts/stock_snapshot.py and/or
scripts/market_facts.py), then wraps it in the Research Desk layout via assemble_report.py.

Usage:
  .venv/bin/python scripts/dossier_builder_template.py \
      --spec <RUN_DIR>/work/<SYM>_spec.json \
      [--snapshot <RUN_DIR>/cache/snapshots_<MKT>_<date>.json] \
      [--facts <RUN_DIR>/cache/facts_<MKT>_<date>.json] \
      --out docs/blogs/<MKT>/<SYM>_dossier.html
"""
from __future__ import annotations

import argparse
import copy
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assemble_report import build  # noqa: E402
from dossier_schema import (  # noqa: E402
    enforce_stop_loss_ratchet,
    load_monograph_spec,
    persist_monograph_spec,
    strip_html,
    validate_monograph_spec,
    word_count,
)
from epub_builder import (  # noqa: E402
    build_pdf_book,
    render_masterclass_book_html,
)
from options_snapshot import render_options_section_html  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORING_FILE = os.path.join(ROOT, ".agents", "config", "scoring.json")

VERDICT_CLASS_MAP = {
    "IMMEDIATE_BUY": "verdict-keep",
    "IMMEDIATE BUY": "verdict-keep",
    "KEEP_COMPOUNDING": "verdict-keep",
    "KEEP COMPOUNDING": "verdict-keep",
    "ACCUMULATE_ON_DIP": "verdict-accumulate",
    "ACCUMULATE ON DIP": "verdict-accumulate",
    "BUY_ON_PULLBACK": "verdict-accumulate",
    "WAIT_FOR_SUPPORT": "verdict-watch",
    "WAIT FOR SUPPORT": "verdict-watch",
    "WATCH": "verdict-watch",
    "WATCHLIST / HOLD": "verdict-watch",
    "HOLD": "verdict-watch",
    "QUALIFIED_DEFERRED": "verdict-watch",
    "TRIM_PROFIT_BOOKING": "verdict-trim",
    "TRIM / HARVEST": "verdict-trim",
    "REJECTED": "verdict-exit",
    "AVOID / REJECTED": "verdict-exit",
    "EXIT_IMMEDIATELY": "verdict-exit",
    "EXIT_ON_BOUNCE": "verdict-exit",
    "TRIM_INTO_STRENGTH": "verdict-trim",
    "TRIM_OVERWEIGHT": "verdict-trim",
    "HOLD_WITH_HARD_STOP": "verdict-watch",
    "NOT_HELD": "verdict-watch",
    "DEFER": "verdict-watch",
}


def _lookup_snapshot(snapshots: dict, sym: str) -> dict:
    """Find one symbol's block in a stock_snapshot.py file (key `snapshots` or `symbols`) or a bare symbol map."""
    for key in ("snapshots", "symbols"):
        block = snapshots.get(key)
        if isinstance(block, dict) and sym in block:
            return block[sym]
        if isinstance(block, list):
            for row in block:
                if isinstance(row, dict) and row.get("symbol") == sym:
                    return row
    return snapshots.get(sym, {}) if isinstance(snapshots.get(sym), dict) else {}


def _zone(zone) -> tuple:
    if isinstance(zone, dict):
        return zone.get("low"), zone.get("high")
    if isinstance(zone, (list, tuple)) and len(zone) == 2:
        return zone[0], zone[1]
    return None, None


def _shortlist_rows(data: dict) -> list[dict]:
    if isinstance(data.get("active"), list):
        return data["active"]
    sheets = data.get("sheets") or {}
    return [row for rows in sheets.values() if isinstance(rows, list) for row in rows if isinstance(row, dict)]


def _position_for_symbol(positions: dict, symbol: str) -> dict | None:
    return next((row for row in positions.get("consolidated", []) if row.get("symbol", "").upper() == symbol), None)


def _decision_panels(spec: dict, market: str, symbol: str, positions: dict,
                     snapshots: dict, shortlist: dict) -> tuple[dict, str, str, str]:
    cur = "₹" if market == "IN" else "$"
    position = _position_for_symbol(positions, symbol)
    action = spec["holding_action"]
    shares_to_sell = spec["holding_shares_to_sell"]
    if position:
        quantity = position.get("quantity", 0)
        if shares_to_sell > quantity:
            raise ValueError(f"holding_shares_to_sell ({shares_to_sell}) exceeds current quantity ({quantity}) for {symbol}")
        if any(alert["shares"] > quantity for alert in spec["holding_alerts"]):
            raise ValueError(f"holding alert sells more than the current quantity for {symbol}")
        if action == "EXIT_IMMEDIATELY" and shares_to_sell != quantity:
            raise ValueError("EXIT_IMMEDIATELY must sell the full current holding")
        value = position.get("market_value")
        cost = position.get("cost_basis")
        gain = position.get("gain")
        net_worth = positions.get("net_worth")
        weight = value / net_worth * 100 if isinstance(value, (int, float)) and net_worth else None
        accounts = ", ".join(
            f"{row.get('account', 'account')}: {row.get('quantity', 0):g} shares"
            for row in position.get("accounts", [])
        ) or "Account split unavailable"
        holding_summary = (
            f"{quantity:g} shares across {accounts}; market value "
            f"{cur}{value:,.2f}" if isinstance(value, (int, float))
            else f"{quantity:g} shares across {accounts}; market value unavailable"
        )
        holding_summary += f"; cost basis {cur}{cost:,.2f}" if isinstance(cost, (int, float)) else "; cost basis unknown"
        if action == "HOLD_WITH_HARD_STOP":
            holding_summary += f"; retain all {quantity:g} shares now; {shares_to_sell:g} shares are subject to the listed conditional trigger(s)"
        elif shares_to_sell:
            holding_summary += f"; recommend selling {shares_to_sell:g} shares and retaining {quantity - shares_to_sell:g} shares"
        else:
            holding_summary += f"; no shares recommended for sale; retain all {quantity:g} shares"
        holding_summary += f"; unrealized P&L {cur}{gain:,.2f}" if isinstance(gain, (int, float)) else "; unrealized P&L unavailable"
        holding_summary += f"; portfolio weight {weight:.2f}%" if weight is not None else "; portfolio weight unavailable"
    else:
        quantity = 0
        value = cost = gain = weight = None
        if shares_to_sell != 0:
            raise ValueError("holding_shares_to_sell must be zero when the company is not held")
        if any(alert["shares"] != 0 for alert in spec["holding_alerts"]):
            raise ValueError("NOT_HELD alerts must not recommend selling shares")
        holding_summary = "NOT HELD (0 shares); no current holding to trim or exit."

    active_shortlist = {row.get("symbol", "").upper(): row for row in _shortlist_rows(shortlist)}
    snapshot_map = snapshots.get("snapshots") or snapshots.get("symbols") or snapshots
    destinations = spec["redeployment_plan"]["destinations"]
    for row in destinations:
        symbol_name = str(row.get("symbol") or "").upper()
        if row["destination_type"] == "SHORTLIST" and row["allocation_pct"] > 0 and symbol_name not in active_shortlist:
            raise ValueError(f"redeployment shortlist symbol {symbol_name} is not in the active shortlist")
        if row["destination_type"] != "CASH" and symbol_name and symbol_name not in snapshot_map:
            raise ValueError(f"redeployment candidate {symbol_name} is missing from the fresh stock snapshot")
        if row["destination_type"] != "CASH" and row["allocation_pct"] > 0:
            live = snapshot_map[symbol_name]
            live_eval = live.get("stage2_evaluation", {})
            live_tv = live.get("tradingview", {})
            if not isinstance(live_tv.get("close"), (int, float)) or not _zone(live_eval.get("support_buy_zone"))[0] or not live_eval.get("invalidation_stop"):
                raise ValueError(f"funded redeployment candidate {symbol_name} lacks a fresh price, support zone, or stop")

    action_label = action.replace("_", " ")
    alerts = spec["holding_alerts"]
    alert_rows = []
    for alert in alerts:
        trigger = str(alert.get("trigger"))
        if isinstance(alert.get("trigger_price"), (int, float)):
            trigger += f" ({cur}{alert['trigger_price']:,.2f})"
        amount = (f"; approx. proceeds {cur}{alert['shares'] * alert['trigger_price']:,.2f}"
                  if isinstance(alert.get("trigger_price"), (int, float)) else "")
        alert_rows.append([_esc(trigger), f"{alert['shares']:g}", _esc(alert.get("instruction") + amount)])
    holding_summary_html = _esc(holding_summary)
    if not holding_summary.rstrip().endswith((".", "!", "?")):
        holding_summary_html += "."
    holding_html = (
        f'<section class="chapter" id="holding-action" data-holding-action="{_esc(action)}">'
        "<h2>Current Portfolio Holding Verdict &amp; Alert Plan</h2>"
        f'<p><strong>{_esc(action_label)}:</strong> {holding_summary_html} {_esc(spec["holding_rationale"])}</p>'
        + _render_table(f"Holding action and broker-alert plan for {symbol}",
                        ["Price / event trigger", "Shares affected", "Recommended alert / action"], alert_rows,
                        "These are advisory alert levels for the stated session, not broker orders; verify current holdings and prices before placing or changing any order.")
        + "</section>"
    )
    redeploy_rows = []
    for row in destinations:
        kind = row["destination_type"]
        fallback_candidate = {"CASH": "Cash reserve", "SHORTLIST": "No selected shortlist name",
                             "OUTSIDE": "No selected outside name"}[kind]
        candidate = str(row.get("symbol") or fallback_candidate)
        detail = row["recommendation"]
        live = snapshot_map.get(str(row.get("symbol") or "").upper(), {})
        eval_data = live.get("stage2_evaluation", {}) if isinstance(live, dict) else {}
        tv_data = live.get("tradingview", {}) if isinstance(live, dict) else {}
        technical = eval_data.get("weinstein_stage") or "Not applicable"
        if kind != "CASH" and live:
            detail += f" — current snapshot stage: {technical}; posture: {eval_data.get('entry_timing_posture', 'not supplied')}"
        low, high = _zone(eval_data.get("support_buy_zone")) if kind != "CASH" else (None, None)
        price_text = f"{cur}{tv_data['close']:,.2f}" if isinstance(tv_data.get("close"), (int, float)) else "N/A"
        zone_text = f"{cur}{low:,.2f}–{cur}{high:,.2f}" if isinstance(low, (int, float)) and isinstance(high, (int, float)) else "Not supplied"
        stop = eval_data.get("invalidation_stop") if kind != "CASH" else None
        redeploy_rows.append([
            _esc(kind), _esc(candidate), f"{row['allocation_pct']:.2f}%",
            _esc(price_text), _esc(zone_text), f"{cur}{stop:,.2f}" if isinstance(stop, (int, float)) else "Not supplied",
            f"{cur}{row['target_base']:,.2f}" if isinstance(row.get("target_base"), (int, float)) else "N/A",
            f"{row['asymmetry_ratio']:.2f}:1" if isinstance(row.get("asymmetry_ratio"), (int, float)) else "N/A",
            _esc(detail), _esc(row["entry_condition"]), _esc(row["rationale"]),
        ])
    base = _esc(spec["redeployment_plan"]["capital_source"])
    redeploy_html = (
        f'<section class="chapter" id="capital-redeployment" data-capital-base="{base}">'
        "<h2>Capital Redeployment &amp; Opportunity Cost</h2>"
        f"<p>Capital under review: {base}. Cash is an active choice. We compare cash with shortlist ideas and outside names. We do not assume every dollar must be invested right away.</p>"
        + _render_table(f"Capital redeployment choices for {symbol}",
                        ["Destination", "Candidate", "Share of capital", "CMP", "Entry zone", "Stop", "Base target", "Asymmetry", "Recommendation", "Entry / activation condition", "Why this use of capital"],
                        redeploy_rows,
                        "The allocation percentages refer to the capital source named above and reconcile to 100%; a cash allocation is deliberate when no equity opportunity clears the evidence and entry hurdles.",
                        row_attrs=[{"data-destination": row["destination_type"]} for row in destinations])
        + "</section>"
    )
    book_summary = [
        f"Current holding decision: {action_label}. {strip_html(holding_summary)}. {strip_html(spec['holding_rationale'])}",
        "Alert plan: " + "; ".join(f"{a['trigger']} — {a['instruction']}" for a in alerts),
        "Capital redeployment: " + "; ".join(
            f"{r['allocation_pct']:.2f}% to {r.get('symbol') or r['destination_type']} ({r['destination_type']}): {r['recommendation']}; {r['entry_condition']}"
            for r in destinations
        ),
    ]
    return {"position": position, "quantity": quantity, "value": value, "cost": cost, "gain": gain,
            "weight": weight, "summary": holding_summary, "action": action, "net_worth": positions.get("net_worth")}, holding_html, redeploy_html, " ".join(book_summary)


def _valuation(val) -> tuple:
    unavailable_note = (
        "Cutoff-compatible current valuation ratios are unavailable or excluded. "
        "Chapter 3 presents filing-based analyst sensitivities, not a current P/E-versus-growth "
        "or ROE/ROCE comparison."
    )
    if isinstance(val, dict):
        note = val.get("note")
        if note:
            return val.get("posture", "N/A"), note
        posture = val.get("posture", "N/A")
        if "unavailable" in str(posture).casefold():
            return posture, unavailable_note
        return posture, "Compares current P/E against earnings growth and ROE/ROCE."
    if isinstance(val, str) and val:
        if "unavailable" in val.casefold():
            return val, unavailable_note
        return val, "Compares current P/E against earnings growth and ROE/ROCE."
    return "N/A", unavailable_note


def _tv_rating_label(score) -> str:
    if not isinstance(score, (int, float)):
        return "N/A"
    label = (
        "Strong Buy" if score >= 0.5 else "Buy" if score >= 0.1 else "Neutral" if score > -0.1
        else "Sell" if score > -0.5 else "Strong Sell"
    )
    return f"{label} ({score:+.2f})"


def _esc(val) -> str:
    if val is None:
        return "N/A"
    return html.escape(str(val))


def _clean_cell(c: str) -> str:
    return str(c).strip()


def _render_table(caption: str, headers: list[str], rows: list[list[str]], explanatory_p: str,
                  row_attrs: list[dict] | None = None) -> str:
    th_html = "".join(f"<th>{_clean_cell(h)}</th>" for h in headers)
    tr_list = []
    for idx, r in enumerate(rows):
        tds = "".join(f"<td>{_clean_cell(c)}</td>" for c in r)
        attrs = "".join(f' {html.escape(str(k), quote=True)}="{html.escape(str(v), quote=True)}"'
                        for k, v in (row_attrs[idx] if row_attrs and idx < len(row_attrs) else {}).items())
        tr_list.append(f"<tr{attrs}>{tds}</tr>")
    body_html = "\n".join(tr_list)
    cap_html = f"<caption>{caption}</caption>\n" if caption else ""
    p_html = f"<p>{explanatory_p.strip()}</p>" if explanatory_p and explanatory_p.strip() else ""
    return (
        f'<div class="table-wrap"><table class="wikitable">\n'
        f"{cap_html}"
        f"<thead><tr>{th_html}</tr></thead>\n"
        f"<tbody>\n{body_html}\n</tbody>\n"
        f"</table></div>\n"
        f"{p_html}"
    )


def _render_estimate(est: dict) -> str:
    return (
        '<section class="estimate">\n'
        f'<h4>The number:</h4>\n<p>{est["the_number"]}</p>\n'
        f'<h4>How it was calculated:</h4>\n<p>{est["how_calculated"]}</p>\n'
        f'<h4>The inputs:</h4>\n<p>{est["the_inputs"]}</p>\n'
        f'<h4>The range:</h4>\n<p>{est["the_range"]}</p>\n'
        f'<h4>If the number is off:</h4>\n<p>{est["if_off"]}</p>\n'
        "</section>"
    )


def _compute_risk_unit_sizing(cmp_val: float, entry_val: float, stop_val: float, tier: str, scoring: dict) -> dict:
    pos_cfg = scoring.get("position_sizing", {})
    tier_tbl = pos_cfg.get("tier_table", {}).get(tier, {"min_pct": 0.0, "max_pct": 0.0})
    ru_cfg = pos_cfg.get("risk_unit_sizing", {})
    budget_bps = float(ru_cfg.get("tier_risk_budget_bps", {}).get(tier, 75 if tier != "TIER_0" else 0))
    ref_entry = entry_val if (entry_val and entry_val > 0) else cmp_val
    if not ref_entry or not stop_val or ref_entry <= stop_val or budget_bps <= 0:
        zero_stop_dist = (
            round((ref_entry - stop_val) / ref_entry * 100.0, 2)
            if (ref_entry and stop_val and ref_entry > stop_val)
            else "n/a"
        )
        return {
            "tier": tier,
            "risk_budget_bps": budget_bps,
            "stop_distance_pct": zero_stop_dist,
            "risk_adjusted_weight_pct": 0.0,
            "tier_range_pct": f"{tier_tbl.get('min_pct', 0)}–{tier_tbl.get('max_pct', 0)}%",
            "runaway_winner_cap_pct": pos_cfg.get("runaway_winner_cap_pct", 22),
        }
    stop_dist_pct = round((ref_entry - stop_val) / ref_entry * 100.0, 2)
    raw_wt_pct = round((budget_bps / 100.0) / (stop_dist_pct / 100.0), 2)
    capped_wt_pct = round(min(float(tier_tbl.get("max_pct", 10.0)), raw_wt_pct), 2)
    return {
        "tier": tier,
        "risk_budget_bps": budget_bps,
        "stop_distance_pct": stop_dist_pct,
        "raw_risk_unit_weight_pct": raw_wt_pct,
        "risk_adjusted_weight_pct": capped_wt_pct,
        "tier_range_pct": f"{tier_tbl.get('min_pct', 0)}–{tier_tbl.get('max_pct', 0)}%",
        "runaway_winner_cap_pct": pos_cfg.get("runaway_winner_cap_pct", 22),
    }


def _build_ch4_from_snapshot_or_ledger(
    sym: str, market: str, snap_sym: dict, inst_m: dict, ch4_spec: dict, as_of: str
) -> str:
    cur = "₹" if market == "IN" else "$"
    bench = "Nifty 50" if market == "IN" else "S&P 500"
    tv = snap_sym.get("tradingview") or {}
    w_s2 = snap_sym.get("thewrap_stage2") or {}
    s2_ev = snap_sym.get("stage2_evaluation") or {}

    # Prefer the market-facts ledger only when this instrument row is actually
    # dated to the requested session. Consumer snapshots are timestamped and
    # can be fresher; allowing an older ledger value to win silently mixes
    # sessions (for example, a Nov 6 close under a Nov 9 report header).
    ledger_is_asof = str(inst_m.get("asof_bar", ""))[:10] == str(as_of)[:10]
    target_bar_date = str(inst_m.get("asof_bar") or as_of)[:10]
    price_label = (
        f"Session Price ({_esc(as_of)})"
        if ledger_is_asof
        else f"Last verified target bar ({_esc(target_bar_date)})"
    )
    primary = inst_m if ledger_is_asof else tv
    secondary = tv if ledger_is_asof else inst_m
    close = primary.get("close") or secondary.get("close")
    s20 = primary.get("sma20") or secondary.get("sma20")
    s50 = primary.get("sma50") or secondary.get("sma50")
    s200 = primary.get("sma200") or secondary.get("sma200")
    w30 = tv.get("sma30_weekly") or s200
    w10_ema = tv.get("ema10_weekly") or tv.get("ema50") or s50
    rsi = next((v for v in (primary.get("rsi14"), tv.get("rsi14_daily"), tv.get("rsi_14_daily"), tv.get("rsi14"), secondary.get("rsi14")) if v is not None), None)
    atr = next((v for v in (primary.get("atr14"), tv.get("atr14"), tv.get("atr_14"), secondary.get("atr14")) if v is not None), None)
    hi52 = primary.get("hi52") or tv.get("high_52w") or secondary.get("hi52")
    lo52 = primary.get("lo52") or tv.get("low_52w") or secondary.get("lo52")
    if tv.get("rel_vol_10d") is not None:
        rvol, rvol_period = tv.get("rel_vol_10d"), "10-day"
    elif tv.get("vol_ratio_vs_30d") not in (None, 0):
        rvol, rvol_period = tv.get("vol_ratio_vs_30d"), "30-day"
    else:
        rvol, rvol_period = inst_m.get("vol_mult_20d"), "20-day"
    tv_label = tv.get("tv_rating_label") or _tv_rating_label(tv.get("tv_rating_overall"))
    piv_s1, piv_m, piv_r1 = tv.get("pivot_s1"), tv.get("pivot_middle"), tv.get("pivot_r1")
    ext_10w = s2_ev.get("extension_from_10w_ema_pct")
    ext_50d = s2_ev.get("extension_from_50d_sma_pct")
    w_stage = ch4_spec.get("stage_override") or (inst_m.get("stage_label") if ledger_is_asof else None) or s2_ev.get("weinstein_stage", "N/A")
    w_explain = ch4_spec.get("stage_explanation") or s2_ev.get("stage_explanation") or s2_ev.get("summary_rationale") or "Trend classification should be read against the market-facts ledger and the latest moving averages."
    dashboard_tag = w_s2.get("breakout_type") or w_s2.get("stage_tag") or "not available"
    dashboard_membership = w_s2.get("in_thewrap_stage2", w_s2.get("in_stage2_list"))
    dashboard_membership = "yes" if dashboard_membership is True else "no" if dashboard_membership is False else "not available"
    breadth_parts = []
    breadth_200 = w_s2.get("industry_pct_above_200d_ema")
    breadth_50 = w_s2.get("industry_pct_above_50d_ema")
    if isinstance(breadth_200, (int, float)):
        breadth_parts.append(f"{breadth_200:g}% above 200-day EMA")
    if isinstance(breadth_50, (int, float)):
        breadth_parts.append(f"{breadth_50:g}% above 50-day EMA")
    breadth_text = ", ".join(breadth_parts) if breadth_parts else "not available"
    sector_rank = w_s2.get("sector_rank")
    sector_rank_text = str(sector_rank) if sector_rank is not None else "unavailable"
    rs_pct = w_s2.get("rs_pct")
    rs_pct_text = f"{rs_pct:g}%" if isinstance(rs_pct, (int, float)) else "unavailable"
    cite_tag = ch4_spec.get("ledger_cite_tag", "")

    def fmt_px(v):
        return f"{cur}{v:,.2f}" if isinstance(v, (int, float)) else "N/A"

    tech_rows = [
        [
            f"Session close ({_esc(as_of)})" if ledger_is_asof else f"Last verified close ({_esc(target_bar_date)})",
            fmt_px(close) + cite_tag,
            f"1D: {tv.get('change_1d_pct') if not ledger_is_asof else (inst_m.get('chg_1d_pct') if inst_m.get('chg_1d_pct') is not None else tv.get('change_1d_pct', 'N/A'))}%, "
            f"1W: {tv.get('perf_1w_pct') if not ledger_is_asof else (inst_m.get('chg_1w_pct') if inst_m.get('chg_1w_pct') is not None else tv.get('perf_1w_pct', 'N/A'))}%, "
            f"1M: {tv.get('perf_1m_pct') if not ledger_is_asof else (inst_m.get('chg_1m_pct') if inst_m.get('chg_1m_pct') is not None else tv.get('perf_1m_pct', 'N/A'))}%",
        ],
        [
            ("Market-facts trend & dashboard tag" if ledger_is_asof else "Current snapshot trend & dashboard tag"),
            f"{_esc(w_stage)} (TheWrap breakout tag: {_esc(dashboard_tag)}; Stage 2 list membership: {dashboard_membership}; weeks tagged: {w_s2.get('weeks_in_stage2', 'not available')})",
            _esc(w_explain),
        ],
        [
            "30-week SMA / 10-week EMA (Weekly)",
            f"{fmt_px(w30)} / {fmt_px(w10_ema)}",
            f"Extension from 10-week EMA: {f'{ext_10w:+.2f}%' if isinstance(ext_10w, (int, float)) else 'N/A'} "
            f"(No-FOMO immediate-buy ceiling: +10.0%)",
        ],
        [
            "20-day / 50-day / 200-day SMA (Daily)",
            f"{fmt_px(s20)} / {fmt_px(s50)} / {fmt_px(s200)}",
            f"Extension from 50-day SMA: {f'{ext_50d:+.2f}%' if isinstance(ext_50d, (int, float)) else 'N/A'} "
            f"(No-FOMO ceiling: +12.0%)",
        ],
        [
            "Momentum oscillator / ATR",
            f"{round(rsi, 2) if isinstance(rsi, (int, float)) else 'N/A'} / {fmt_px(atr)}",
            f"TradingView Technical Rating: {_esc(tv_label)} (high oscillator readings can signal short-term overextension)",
        ],
        [
            "52-week high / low",
            f"{fmt_px(hi52)} / {fmt_px(lo52)}",
            f"Classic Pivots — Support S1: {fmt_px(piv_s1)}, Mid Pivot: {fmt_px(piv_m)}, Resistance R1: {fmt_px(piv_r1)}",
        ],
        [
            "Relative volume & institutional sponsorship",
            f"{round(rvol, 2)}x vs {rvol_period} avg" if isinstance(rvol, (int, float)) else "N/A",
            f"TheWrap industry ({_esc(w_s2.get('thewrap_industry') or w_s2.get('sector_name') or tv.get('industry', 'N/A'))}); "
            f"extracted breadth: {breadth_text}; formal sector rank {sector_rank_text}; "
            f"formal relative-strength percentile {rs_pct_text}",
        ],
    ]
    tech_rows = [[cell if str(cell).rstrip().endswith((".", "!", "?")) else f"{cell}." for cell in row] for row in tech_rows]
    t1_html = _render_table(
        f"Dated market-facts ledger for {sym} as of {as_of}",
        ["Technical dimension", "Observed value (source-specific)", "Institutional & No-FOMO interpretation"],
        tech_rows,
        ch4_spec.get(
            "tech_table_takeaway",
            f"This table summarizes dated market-facts indicators for {sym}; weekly averages and dashboard fields are shown only when supplied for the stated cutoff.",
        ),
    )

    zone_low, zone_high = _zone(ch4_spec.get("support_band_override") or s2_ev.get("support_buy_zone"))
    band_position = (
        "below price" if close is not None and zone_high is not None and zone_high < close
        else "above price" if close is not None and zone_low is not None and zone_low > close
        else "overlapping current price"
    )
    eval_rows = [
        [
            ("Market-facts trend classification" if ledger_is_asof else "Current snapshot trend classification"),
            _esc(w_stage),
            _esc(ch4_spec.get("evaluation_stage_explanation") or w_explain),
        ],
        [
            "Consumer snapshot timing-screen result",
            _esc(ch4_spec.get("posture_override") or s2_ev.get("entry_timing_posture", ch4_spec.get("entry_posture", "N/A"))),
            _esc((ch4_spec.get("posture_explanation") or s2_ev.get("timing_rationale") or "Use price, trend and valuation together before setting an order.") + f" Consumer snapshot result only; the dossier action remains {ch4_spec.get('dossier_verdict', 'the overall dossier verdict')}.") ,
        ],
        [
            "Screen support band (nearest support)",
            f"{fmt_px(zone_low)} – {fmt_px(zone_high)}",
            _esc(ch4_spec.get("support_zone_explanation", "Reference band only; require a trend and valuation review before considering an entry.")),
        ],
        [
            "Structural invalidation stop",
            fmt_px(ch4_spec.get("stop_override", s2_ev.get("invalidation_stop"))),
            ch4_spec.get("stop_placement_explanation", "Below the lower of nearest support and the lower of the 50-day and 30-week averages, less 0.5× ATR14; structural reference, not a tactical entry stop or order."),
        ],
        [
            "Valuation sanity check (Screener.in / Finviz)",
            _esc(_valuation(ch4_spec.get("valuation_assessment") or s2_ev.get("valuation_assessment"))[0]),
            _esc(_valuation(ch4_spec.get("valuation_assessment") or s2_ev.get("valuation_assessment"))[1]),
        ],
    ]
    eval_rows = [[cell if str(cell).rstrip().endswith((".", "!", "?")) else f"{cell}." for cell in row] for row in eval_rows]
    t2_html = _render_table(
        f"Trend and No-FOMO Entry Timing Evaluation for {sym}",
        ["Evaluation dimension", "Reading / Posture", "Rule & practical implication"],
        eval_rows,
        ch4_spec.get(
            "gate_table_takeaway",
            f"This evaluation separates {sym}'s medium-term trend from entry timing, so a screen signal does not become an unsupported order.",
        ),
    )

    tv_symbol_source = tv.get("tv_symbol") or ""
    exchange = (
        tv.get("exchange")
        or tv.get("_exchange_prefix")
        or (tv_symbol_source.split(":", 1)[0] if ":" in tv_symbol_source else None)
        or ("NSE" if market == "IN" else "NASDAQ")
    ).upper()
    tv_symbol = f"{exchange}:{sym}"
    tv_widget_html = (
        f'<div class="tradingview-widget-container" style="height: 520px; width: 100%; margin: 1.25rem 0;">\n'
        f'  <div id="tradingview_{sym.lower()}_chart" role="img" aria-label="Interactive TradingView daily chart for {tv_symbol}" style="height: 100%; width: 100%;"></div>\n'
        f'  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>\n'
        f'  <script type="text/javascript">\n'
        f'  new TradingView.widget({{\n'
        f'    "autosize": true,\n'
        f'    "symbol": "{tv_symbol}",\n'
        f'    "interval": "D",\n'
        f'    "timezone": "Etc/UTC",\n'
        f'    "theme": "light",\n'
        f'    "style": "1",\n'
        f'    "locale": "en",\n'
        f'    "toolbar_bg": "#f4f6f8",\n'
        f'    "enable_publishing": false,\n'
        f'    "hide_top_toolbar": false,\n'
        f'    "allow_symbol_change": true,\n'
        f'    "studies": [\n'
        f'      "MASimple@tv-basicstudies",\n'
        f'      "MAExp@tv-basicstudies"\n'
        f'    ],\n'
        f'    "container_id": "tradingview_{sym.lower()}_chart"\n'
        f'  }});\n'
        f'  </script>\n'
        f'</div>\n'
    )

    return (
        '<section class="chapter" id="ch-4">\n'
        "<h2>4. Trend and TradingView technical structure</h2>\n"
        f"<p>{ch4_spec['intro_prose']}</p>\n"
        f"{tv_widget_html}\n"
        f"{t1_html}\n"
        "<h3>Momentum screen and No-FOMO support evaluation</h3>\n"
        f"<p>{ch4_spec.get('gate_intro_prose', 'We evaluate whether the stock is in an actionable early Stage 2 zone or requires patience for a support retest.')}</p>\n"
        f"{t2_html}\n"
        f"<p>{ch4_spec['closing_prose']}</p>\n"
        "</section>"
    )


def render_book_dossier(spec: dict, facts: dict | None = None, snapshots: dict | None = None) -> str:
    facts = facts or {}
    snapshots = snapshots or {}
    sym = spec["symbol"].upper()
    market = spec["market"].upper()
    as_of = spec.get("as_of") or snapshots.get("as_of") or facts.get("asof") or "latest"
    inst_m = (facts.get("instruments") or {}).get(sym, {})
    snap_sym = _lookup_snapshot(snapshots, sym)
    scoring = json.load(open(SCORING_FILE, encoding="utf-8"))
    cur = "₹" if market == "IN" else "$"

    verdict = spec["verdict"]
    v_cls = VERDICT_CLASS_MAP.get(verdict.upper(), "verdict-watch")
    archetype = spec.get("archetype", "STAGE2_LEADER")
    bucket = spec.get("strategy_bucket", "TACTICAL_MOMENTUM")

    tv = snap_sym.get("tradingview") or {}
    s2_ev = snap_sym.get("stage2_evaluation") or {}
    ledger_is_asof = str(inst_m.get("asof_bar", ""))[:10] == str(as_of)[:10]
    price_label = (
        f"Session Price ({_esc(as_of)})"
        if ledger_is_asof
        else f"Last verified target bar ({_esc(str(inst_m.get('asof_bar') or as_of)[:10])})"
    )
    close = (inst_m.get("close") if ledger_is_asof else None) or tv.get("close") or inst_m.get("close") or spec.get("cmp") or 0.0
    entry_low = spec["entry_zone_low"]
    entry_high = spec["entry_zone_high"]
    stop_loss = spec["stop_loss"]
    band_position = (
        "below price" if close is not None and entry_high < close
        else "above price" if close is not None and entry_low > close
        else "overlapping current price"
    )
    target_base = spec["target_base"]
    target_bull = spec["target_bull"]
    target_bear = spec["target_bear"]
    asym = (
        round((target_base - close) / (close - stop_loss), 2)
        if (target_base is not None and close and stop_loss and close > stop_loss)
        else spec.get("asymmetry_ratio", 0.0)
    )

    tier = spec.get("conviction_tier", "TIER_2")
    w_stage = spec.get("weinstein_stage") or (inst_m.get("stage_label") if ledger_is_asof else None) or s2_ev.get("weinstein_stage", "N/A")
    entry_posture = spec.get("entry_posture") or s2_ev.get("entry_timing_posture") or verdict
    no_new_allocation = verdict.upper() in {"REJECTED", "WAIT_FOR_SUPPORT"} or str(entry_posture).startswith(("WAIT_FOR_SUPPORT", "NO_NEW_ALLOCATION"))
    ru = _compute_risk_unit_sizing(close, entry_high, stop_loss, tier, scoring)
    if no_new_allocation:
        # A monitor-only setup has no live risk budget or initial position size.
        # Keep the conviction tier visible, but do not display a hypothetical entry weight as an allocation.
        ru["risk_adjusted_weight_pct"] = 0.0
        ru["raw_risk_unit_weight_pct"] = 0.0
        ru["risk_budget_bps"] = 0.0

    # Key figures strip
    kf_items = [
        ("Verdict", f'<span class="verdict {v_cls}">{_esc(verdict)}</span> ({_esc(archetype)})'),
        (price_label, f"{cur}{close:,.2f}"),
        ("Strategy Bucket", _esc(bucket)),
        ("Weinstein Stage", _esc(w_stage)),
        ("No-FOMO Entry Posture", _esc(entry_posture)),
        ("Scanner band (monitor only)" if str(entry_posture).startswith("NO_NEW_ALLOCATION") else "Support Buy Zone", f"{cur}{entry_low:,.2f} – {cur}{entry_high:,.2f} (Stop: {cur}{stop_loss:,.2f})"),
        ("Price target", "Not set; valuation bridge is not decision-grade" if target_base is None else (f"{cur}{target_base:,.2f} / {cur}{target_bull:,.2f} (new-entry R:R: N/A)" if no_new_allocation else f"{cur}{target_base:,.2f} / {cur}{target_bull:,.2f} (R:R {asym:.2f}:1)")),
        ("Risk-Unit Sizing", f"{ru['risk_adjusted_weight_pct']}% of net worth ({_esc(tier)})"),
    ]
    if spec.get("report_status"):
        kf_items.append(("Report status", _esc(spec["report_status"])))
    kf_html = (
        '<dl class="key-figures">\n'
        + "\n".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in kf_items)
        + "\n</dl>"
    )

    # Primer (must be 3-5 sentences)
    primer_html = (
        f'<section class="primer" id="primer">\n'
        f"<p>{spec['primer']}</p>\n"
        f"</section>"
    )

    # Chapter 1: What the company does & day-to-day operations across verticals
    ch1 = spec["ch1"]
    ch1_parts = [
        '<section class="chapter" id="ch-1">',
        "<h2>1. What the company does &amp; day-to-day vertical operations</h2>",
    ]
    for p in ch1.get("paragraphs", []):
        ch1_parts.append(f"<p>{p}</p>")
    if ch1.get("segments_table"):
        st = ch1["segments_table"]
        ch1_parts.append(_render_table(st.get("caption", ""), st["headers"], st["rows"], st.get("takeaway", "")))
    for sub in ch1.get("subsections", []):
        ch1_parts.append(f"<h3>{sub['title']}</h3>")
        for p in sub.get("paragraphs", []):
            ch1_parts.append(f"<p>{p}</p>")
    ch1_parts.append("</section>")

    # Chapter 2: External Learning Hub, Competitive Moat & Industry Story
    ch2 = spec["ch2"]
    ch2_parts = [
        '<section class="chapter" id="ch-2">',
        "<h2>2. Competitive moat, industry structure &amp; external learning hub</h2>",
    ]
    for p in ch2.get("paragraphs", []):
        ch2_parts.append(f"<p>{p}</p>")
    for sub in ch2.get("subsections", []):
        ch2_parts.append(f"<h3>{sub['title']}</h3>")
        for p in sub.get("paragraphs", []):
            ch2_parts.append(f"<p>{p}</p>")
    if ch2.get("external_resources_table"):
        ert = ch2["external_resources_table"]
        ch2_parts.append("<h3>External learning hub: websites, videos, factory tours &amp; primary links</h3>")
        ch2_parts.append(
            _render_table(
                ert.get("caption", f"Curated external deep-dive resources and videos for {sym}"),
                ert["headers"],
                ert["rows"],
                ert["takeaway"],
            )
        )
    ch2_parts.append("</section>")

    # Chapter 2B: Business KPIs, Structural Potential & CEO Walk-the-Talk Audit
    ch2b = spec["ch2b"]
    ch2b_parts = [
        '<section class="chapter" id="ch-2b">',
        "<h2>2B. Operational business KPIs, structural potential &amp; CEO walk-the-talk</h2>",
    ]
    for p in ch2b.get("intro_paragraphs", []):
        ch2b_parts.append(f"<p>{p}</p>")
    ch2b_parts.append("<h3>The business KPIs that actually matter</h3>")
    for p in ch2b.get("kpi_intro_paragraphs", []):
        ch2b_parts.append(f"<p>{p}</p>")
    kpi_t = ch2b["kpi_table"]
    ch2b_parts.append(
        _render_table(
            kpi_t.get("caption", f"Operational business KPIs and trajectory for {sym}"),
            kpi_t["headers"],
            kpi_t["rows"],
            kpi_t["takeaway"],
        )
    )
    ch2b_parts.append("<h3>Is the company reaching its potential &amp; are the CEOs walking the talk?</h3>")
    for p in ch2b.get("walk_the_talk_paragraphs", []):
        ch2b_parts.append(f"<p>{p}</p>")
    if ch2b.get("walk_the_talk_table"):
        wt = ch2b["walk_the_talk_table"]
        ch2b_parts.append(
            _render_table(
                wt.get("caption", f"CEO guidance vs delivered reality audit for {sym}"),
                wt["headers"],
                wt["rows"],
                wt["takeaway"],
            )
        )
    if ch2b.get("closing_paragraphs"):
        for p in ch2b["closing_paragraphs"]:
            ch2b_parts.append(f"<p>{p}</p>")
    ch2b_parts.append("</section>")

    # Chapter 3: Financials & Valuation Reality Check (Screener.in / Finviz Grounded)
    ch3 = spec["ch3"]
    ch3_parts = [
        '<section class="chapter" id="ch-3">',
        "<h2>3. Financial trajectory &amp; valuation sanity check</h2>",
    ]
    for p in ch3.get("intro_paragraphs", []):
        ch3_parts.append(f"<p>{p}</p>")
    for tbl in ch3.get("tables", []):
        if tbl.get("heading"):
            ch3_parts.append(f"<h3>{tbl['heading']}</h3>")
        if tbl.get("intro"):
            ch3_parts.append(f"<p>{tbl['intro']}</p>")
        ch3_parts.append(_render_table(tbl.get("caption", ""), tbl["headers"], tbl["rows"], tbl["takeaway"]))
    if ch3.get("layer1_table"):
        ch3_parts.append("<h3>Financial health, rate-of-change trajectory &amp; valuation multiples</h3>")
        if ch3.get("layer1_intro"):
            ch3_parts.append(f"<p>{ch3['layer1_intro']}</p>")
        l1_t = ch3["layer1_table"]
        ch3_parts.append(
            _render_table(
                l1_t.get("caption", f"Financial health and valuation summary for {sym}"),
                l1_t["headers"],
                l1_t["rows"],
                l1_t.get("takeaway", ""),
            )
        )
    for est in ch3.get("estimates", []):
        ch3_parts.append(_render_estimate(est))
    if ch3.get("peer_table"):
        pt = ch3["peer_table"]
        ch3_parts.append("<h3>Peer comparison matrix</h3>")
        if pt.get("intro"):
            ch3_parts.append(f"<p>{pt['intro']}</p>")
        ch3_parts.append(
            _render_table(pt.get("caption", f"Peer comparison for {sym}"), pt["headers"], pt["rows"], pt.get("takeaway", ""))
        )
    ch3_parts.append("</section>")

    # Chapter 4: Stage 2 & TradingView Technical Readout
    ch4_html = _build_ch4_from_snapshot_or_ledger(sym, market, snap_sym, inst_m, spec["ch4"], as_of)

    # Chapter 5: Multi-Horizon View (Short-Term Momentum, Medium-Term Catalysts & Scenarios)
    ch5 = spec["ch5"]
    ch5_parts = [
        '<section class="chapter" id="ch-5">',
        "<h2>5. Multi-horizon investment view: short-term momentum, medium-term catalysts &amp; scenarios</h2>",
    ]
    for p in ch5.get("intro_paragraphs", []):
        ch5_parts.append(f"<p>{p}</p>")
    if ch5.get("horizon_table"):
        ht = ch5["horizon_table"]
        ch5_parts.append("<h3>Short-term, medium-term, and long-term synthesis</h3>")
        if ht.get("intro"):
            ch5_parts.append(f"<p>{ht['intro']}</p>")
        ch5_parts.append(
            _render_table(
                ht.get("caption", f"Multi-horizon investment outlook for {sym}"),
                ht["headers"],
                ht["rows"],
                ht.get("takeaway", ""),
            )
        )
    if ch5.get("variant_perception_paragraphs"):
        ch5_parts.append("<h3>Medium-term catalyst pipeline &amp; variant perception</h3>")
        for p in ch5["variant_perception_paragraphs"]:
            ch5_parts.append(f"<p>{p}</p>")
    for est in ch5.get("estimates", []):
        ch5_parts.append(_render_estimate(est))
    sc_t = ch5["scenario_table"]
    ch5_parts.append("<h3>Bull, base, and bear scenarios</h3>")
    if sc_t.get("intro"):
        ch5_parts.append(f"<p>{sc_t['intro']}</p>")
    ch5_parts.append(
        _render_table(
            sc_t.get("caption", f"12-month scenario table for {sym}"), sc_t["headers"], sc_t["rows"], sc_t.get("takeaway", "")
        )
    )
    ch5_parts.append("</section>")

    # Chapter 6: Risks, Thesis Breakers & Red-Team Bear Case
    ch6 = spec["ch6"]
    ch6_parts = ['<section class="chapter" id="ch-6">', "<h2>6. Key risks, thesis breakers &amp; bear case</h2>"]
    for p in ch6.get("intro_paragraphs", []):
        ch6_parts.append(f"<p>{p}</p>")
    for sub in ch6.get("flaws", []):
        ch6_parts.append(f"<h3>{sub['title']}</h3>")
        for p in sub.get("paragraphs", []):
            ch6_parts.append(f"<p>{p}</p>")
    if ch6.get("flaws_table"):
        ft = ch6["flaws_table"]
        ch6_parts.append(
            _render_table(
                ft.get("caption", f"Key risk and invalidation matrix for {sym}"),
                ft["headers"],
                ft["rows"],
                ft.get("takeaway", ""),
            )
        )
    if ch6.get("hinge_paragraph"):
        ch6_parts.append(f"<p>{ch6['hinge_paragraph']}</p>")
    ch6_parts.append("</section>")

    # Chapter 7: What we would do, and when (No-FOMO Execution Plan)
    ch7 = spec["ch7"]
    ch7_parts = ['<section class="chapter" id="ch-7">', "<h2>7. What we would do, and when (No-FOMO action plan)</h2>"]
    for p in ch7.get("decision_paragraphs", []):
        ch7_parts.append(f"<p>{p}</p>")
    if ch7.get("holding_audit_table"):
        ht = ch7["holding_audit_table"]
        ch7_parts.append("<h3>Active holding audit</h3>")
        ch7_parts.append(
            _render_table(
                ht.get("caption", f"Current position audit for {sym}"), ht["headers"], ht["rows"], ht["takeaway"]
            )
        )

    ch7_parts.append("<h3>No-FOMO support entry zone, stop placement &amp; position sizing</h3>")
    l3_rows = [
        [
            "Strategy bucket & conviction tier",
            f"{_esc(bucket)} ({_esc(tier)})",
            "Aligns new capital with durable trend and business quality",
        ],
        [
            "Action verdict & No-FOMO posture",
            f'<span class="verdict {v_cls}">{_esc(verdict)}</span> ({_esc(entry_posture)})',
            _esc(ch7.get("verdict_rule_summary", "Buy at CMP only when in early Stage 2 near support; wait for support when extended")),
        ],
        [
            "Screen band (monitor only)" if no_new_allocation else "Recommended buy / accumulation zone",
            f"{cur}{entry_low:,.2f} to {cur}{entry_high:,.2f}",
            (f"Current price {cur}{close:,.2f}; band is {band_position}; no entry is recommended" if no_new_allocation else f"Current price {cur}{close:,.2f}; use the support band only after trend and valuation checks"),
        ],
        [
            "Screen stop (monitor only)" if no_new_allocation else "Structural invalidation stop",
            f"{cur}{stop_loss:,.2f} (screen reference)",
            ("Reference only; it is not an order or an instruction to sell" if no_new_allocation else _esc(spec.get("ch4", {}).get("stop_placement_explanation") or scoring["stop_placement"].get(bucket, scoring["stop_placement"]["CORE_ALPHA"]))),
        ],
        [
            "Scenario values",
            ("Not assigned" if target_base is None else f"{cur}{target_base:,.2f} / {cur}{target_bull:,.2f} / {cur}{target_bear:,.2f}"),
            ("Per-share values require a reconciled share count and lease-consistent valuation bridge." if target_base is None else ("Illustrative 12-month values; no entry risk/reward applies" if no_new_allocation else f"Reward-to-risk ratio: {asym:.2f}:1")),
        ],
        [
            "Risk-unit initial sizing (portfolio heat)",
            f"{ru['risk_adjusted_weight_pct']}% of net worth ({_esc(tier)}, {ru['risk_budget_bps']:.0f} bps risk budget)",
            ("No allocation while entry gates are unresolved; recalculate only after a fresh review" if no_new_allocation else f"Formula: min(Tier cap {ru['tier_range_pct']}, {ru['risk_budget_bps']:.0f} bps / {ru['stop_distance_pct']}% stop distance)"),
        ],
        [
            "Let-winners-run rule",
            ("Not applicable; no position is open" if no_new_allocation else f"Appreciated weight ceiling up to {ru['runaway_winner_cap_pct']}%"),
            ("Do not allocate or place an order before the entry gates pass" if no_new_allocation else "Never trim solely for RSI > 70 or crossing 15%; trail stop to rising 21-EMA / 50-SMA until trend or fundamentals break"),
        ],
    ]
    l3_rows = [[cell if str(cell).rstrip().endswith((".", "!", "?")) else f"{cell}." for cell in row] for row in l3_rows]
    ch7_parts.append(
        _render_table(
            f"No-FOMO execution levels and risk-unit position sizing for {sym}",
            ["Execution item", "Level / Sizing", "Rule and derivation"],
            l3_rows,
            ch7["sizing_table_takeaway"],
        )
    )
    for trig in ch7.get("triggers", []):
        ch7_parts.append(f'<p class="trigger">{trig}</p>')
    ch7_parts.append("</section>")

    # Gate exceptions (if any)
    ge_html = ""
    if spec.get("gate_exceptions"):
        ge_ps = "".join(f"<p>{p}</p>" for p in spec["gate_exceptions"])
        ge_html = f'<section class="chapter" id="gate-exceptions">\n<h2>Run notes and gate exceptions</h2>\n{ge_ps}\n</section>\n'

    # Notes and sources
    cites_li = "\n".join(f'<li id="cite_note-{i}">{c}</li>' for i, c in enumerate(spec["citations"], 1))
    notes_html = (
        '<section id="notes">\n'
        '<h2 id="references">Notes and sources</h2>\n'
        f'<ol class="sources reflist">\n{cites_li}\n</ol>\n'
        "</section>"
    )

    body_html = "\n\n".join(
        [
            f"<h1>{_esc(spec['title'])}</h1>",
            kf_html,
            primer_html,
            "\n".join(ch1_parts),
            "\n".join(ch2_parts),
            "\n".join(ch2b_parts),
            "\n".join(ch3_parts),
            ch4_html,
            "\n".join(ch5_parts),
            "\n".join(ch6_parts),
            "\n".join(ch7_parts),
            ge_html + notes_html,
        ]
    )

    sector = (
        spec.get("sector")
        or tv.get("sector")
        or (snap_sym.get("fundamental_card") or {}).get("sector")
        or (snap_sym.get("thewrap_stage2") or {}).get("thewrap_industry")
        or tv.get("industry")
        or ""
    )

    return build(
        body_html,
        market=market,
        facts=spec.get("facts_path", ""),
        research=spec.get("research_paths", []),
        kind="dossier",
        workflow="Company research",
        as_of=as_of,
        sector=sector,
    )


_TAG_TOKEN_RE = re.compile(r"(<(?:a|code|sup|script)\b[^>]*>.*?</(?:a|code|sup|script)>|<[^>]+>)", re.S | re.I)
_BARE_URL_RE = re.compile(r"(https?://[^\s<>)\"']+)", re.I)
_BRACKET_CITE_RE = re.compile(r"\[(\d+(?:\s*[,\u2013\-]\s*\d+)*)\]")


def _linkify_html_fragment(fragment: str, max_cite: int = 0) -> str:
    """Auto-link bare http(s) URLs and inline [N] references without touching existing HTML tags."""
    if not fragment:
        return ""

    def repl_url(m: re.Match) -> str:
        raw_url = m.group(1)
        clean = raw_url.rstrip(".,;:!?")
        tail = raw_url[len(clean):]
        esc_u = html.escape(clean, quote=True)
        return f'<a href="{esc_u}" target="_blank" rel="noopener">{html.escape(clean)}</a>{tail}'

    def repl_cite(m: re.Match) -> str:
        if max_cite <= 0:
            return m.group(0)
        inner = m.group(1)
        parts = [p.strip() for p in inner.split(",")]
        rendered = []
        for part in parts:
            rng = re.split(r"[\u2013\-]", part)
            nums = [int(x.strip()) for x in rng if x.strip().isdigit()]
            if not nums or any(n < 1 or n > max_cite for n in nums):
                return m.group(0)
            if len(nums) == 2:
                rendered.append(
                    f'<a href="#cite_note-{nums[0]}">[{nums[0]}]</a>&ndash;<a href="#cite_note-{nums[1]}">[{nums[1]}]</a>'
                )
            else:
                rendered.append(f'<a href="#cite_note-{nums[0]}">[{nums[0]}]</a>')
        return f'<sup class="reference">{", ".join(rendered)}</sup>'

    tokens = _TAG_TOKEN_RE.split(str(fragment))
    out = []
    for tok in tokens:
        if not tok or tok.startswith("<"):
            out.append(tok)
        else:
            step = _BARE_URL_RE.sub(repl_url, tok)
            if max_cite > 0:
                sub_tokens = _TAG_TOKEN_RE.split(step)
                step = "".join(
                    t if t.startswith("<") else _BRACKET_CITE_RE.sub(repl_cite, t)
                    for t in sub_tokens
                )
            out.append(step)
    return "".join(out)


def _render_waterfall_block(blk: dict, market: str, sym: str, max_cite: int = 0) -> str:
    """Deterministically compute per-100 and % of revenue rows from raw audited figures (Zero LLM Math)."""
    cur = "₹" if market == "IN" else "$"
    rev = float(blk["revenue"])
    unit = blk.get("unit") or ("Cr" if market == "IN" else "M")
    period = blk.get("period") or "Latest Audited FY"

    def fmt_raw(v: float) -> str:
        sign = "-" if v < 0 else ""
        return f"{sign}{cur}{abs(v):,.2f} {unit}".strip()

    rows = []
    if isinstance(blk.get("lines"), list) and blk["lines"]:
        for item in blk["lines"]:
            amt = float(item["amount"])
            per100 = (amt / rev) * 100.0
            note = _linkify_html_fragment(item.get("note") or f"Audited {period}: {fmt_raw(amt)}", max_cite)
            rows.append([
                _esc(item["label"]),
                f"{per100:+.2f}" if item.get("signed", amt < 0) else f"{per100:.2f}",
                f"{per100:+.1f}%" if item.get("signed", amt < 0) else f"{per100:.1f}%",
                note,
            ])
    else:
        cogs = -abs(float(blk.get("cogs", 0.0)))
        emp = -abs(float(blk.get("employee_cost", 0.0)))
        opex = -abs(float(blk.get("other_opex", 0.0)))
        ebitda = rev + cogs + emp + opex if ("cogs" in blk or "employee_cost" in blk or "other_opex" in blk) else float(blk.get("ebitda", 0.0))
        da = -abs(float(blk.get("da", 0.0)))
        ebit = ebitda + da
        interest = -abs(float(blk.get("interest", 0.0)))
        other_inc = float(blk.get("other_income", 0.0))
        pbt = ebit + interest + other_inc
        tax = -abs(float(blk.get("tax", 0.0)))
        pat = float(blk["pat"]) if "pat" in blk else (pbt + tax)
        cfo = float(blk.get("cfo", pat))
        wc_delta = float(blk["working_capital_change"]) if "working_capital_change" in blk else (cfo - pat - abs(da))
        capex = -abs(float(blk.get("capex", 0.0)))
        fcf = cfo + capex
        notes = blk.get("notes") or {}

        spec_lines = [
            ("Gross Billed Revenue", rev, False, notes.get("revenue") or f"{period} audited revenue: {fmt_raw(rev)}."),
            ("Direct Materials / COGS", cogs, True, notes.get("cogs") or f"Direct cost of goods/services: {fmt_raw(cogs)}."),
            ("Employee Expenses", emp, True, notes.get("employee_cost") or f"Payroll & engineering talent: {fmt_raw(emp)}."),
            ("Other Operating Overhead", opex, True, notes.get("other_opex") or f"SG&A, facilities & overhead: {fmt_raw(opex)}."),
            ("Operating EBITDA", ebitda, False, notes.get("ebitda") or f"Core operating profit: {fmt_raw(ebitda)}."),
            ("Depreciation & Amortization", da, True, notes.get("da") or f"Non-cash asset depreciation: {fmt_raw(da)}."),
            ("Operating EBIT", ebit, False, notes.get("ebit") or f"Operating income after D&A: {fmt_raw(ebit)}."),
            ("Finance Costs (Interest)", interest, True, notes.get("interest") or f"Debt service cost: {fmt_raw(interest)}."),
            ("Other Non-Operating Income", other_inc, True, notes.get("other_income") or f"Treasury & non-operating income: {fmt_raw(other_inc)}."),
            ("Profit Before Tax (PBT)", pbt, False, notes.get("pbt") or f"Pre-tax profit: {fmt_raw(pbt)}."),
            ("Income Tax", tax, True, notes.get("tax") or f"Corporate tax expense: {fmt_raw(tax)}."),
            ("Reported Profit After Tax (PAT)", pat, False, notes.get("pat") or f"Bottom-line accounting profit: {fmt_raw(pat)}."),
            ("Working Capital & Non-Cash Bridge", wc_delta, True, notes.get("working_capital") or f"Net working-capital & non-cash operating bridge."),
            ("Cash Flow from Operations (CFO)", cfo, False, notes.get("cfo") or f"Audited operating cash flow: {fmt_raw(cfo)}."),
            ("Capital Expenditures (Capex)", capex, True, notes.get("capex") or f"Fixed-asset & tooling capex: {fmt_raw(capex)}."),
            ("Free Cash Flow (FCF)", fcf, True, notes.get("fcf") or f"Reconciled CFO less Capex: {fmt_raw(fcf)}."),
        ]
        for lbl, val, signed, nt in spec_lines:
            p100 = (val / rev) * 100.0
            rows.append([
                _esc(lbl),
                f"{p100:+.2f}" if signed else f"{p100:.2f}",
                f"{p100:+.1f}%" if signed else f"{p100:.1f}%",
                _linkify_html_fragment(nt, max_cite),
            ])

    caption = blk.get("caption") or f"{sym}: Worked {cur}100 Revenue-to-Free-Cash-Flow Waterfall ({period})"
    takeaway = _linkify_html_fragment(
        blk.get("takeaway")
        or f"Every row above is scaled deterministically to {cur}100.00 of {period} audited revenue ({fmt_raw(rev)}) so accounting profit and cash conversion reconcile without period mixing.",
        max_cite,
    )
    return _render_table(
        _esc(caption),
        ["Financial Line Item", f"Amount per {cur}100 Rev ({cur})", "Share of Revenue (%)", "Audited Reality & Notes"],
        rows,
        takeaway,
    )


def _render_snapshot_financials(blk: dict, snap_sym: dict, sym: str, max_cite: int = 0) -> str:
    stmt = blk.get("statement", "profit_loss")
    tbl = ((snap_sym.get("fundamental_card") or {}).get("tables") or {}).get(stmt) or {}
    headers = list(tbl.get("headers") or [])
    row_map = tbl.get("rows") or {}
    if not headers or not row_map:
        return ""
    max_cols = int(blk.get("max_columns", 10))
    start_idx = max(0, len(headers) - max_cols)
    sel_headers = ["Line Item"] + [_esc(h) for h in headers[start_idx:]]
    wanted = blk.get("rows")
    keys = [k for k in (wanted if isinstance(wanted, list) and wanted else row_map.keys()) if k in row_map]
    rows = [[_esc(k)] + [_esc(v) for v in row_map[k][start_idx:]] for k in keys]
    caption = blk.get("caption") or f"{sym}: Multi-Year {stmt.replace('_', ' ').title()} (Snapshot Extracted)"
    takeaway = _linkify_html_fragment(
        blk.get("takeaway")
        or f"Figures above are extracted directly from the verified {sym} financial snapshot across {len(headers[start_idx:])} reporting periods.",
        max_cite,
    )
    return _render_table(_esc(caption), sel_headers, rows, takeaway)


def _render_peer_snapshot_table(blk: dict, snapshots: dict, sym: str, market: str, max_cite: int = 0) -> str:
    cur = "₹" if market == "IN" else "$"
    mcap_lbl = "Mkt Cap (₹ Cr)" if market == "IN" else "Mkt Cap ($B)"
    peer_syms = list(dict.fromkeys([sym] + [str(s).upper() for s in (blk.get("peers") or blk.get("symbols") or [])]))
    rows = []
    for ps in peer_syms:
        ps_snap = _lookup_snapshot(snapshots, ps)
        tv = ps_snap.get("tradingview") or {}
        fc = ps_snap.get("fundamental_card") or {}
        ev = ps_snap.get("stage2_evaluation") or {}
        close = tv.get("close")
        mcap = tv.get("market_cap")
        pe = tv.get("pe_ttm") if tv.get("pe_ttm") is not None else fc.get("stock_pe")
        pb = tv.get("pb_fq")
        roe = tv.get("roe_pct") if tv.get("roe_pct") is not None else fc.get("roe_pct")
        rev_g = tv.get("revenue_yoy_growth_ttm_pct")
        opm = tv.get("operating_margin_ttm_pct")
        stage = ev.get("weinstein_stage") or "N/A"
        rows.append([
            f"<strong>{_esc(ps)}</strong>" if ps == sym else _esc(ps),
            _esc(tv.get("company_name") or ps),
            f"{cur}{close:,.2f}" if isinstance(close, (int, float)) else "N/A",
            f"{mcap:,.2f}" if isinstance(mcap, (int, float)) else "N/A",
            f"{pe:.1f}x" if isinstance(pe, (int, float)) else "N/A",
            f"{pb:.2f}x" if isinstance(pb, (int, float)) else "N/A",
            f"{roe:.1f}%" if isinstance(roe, (int, float)) else "N/A",
            f"{rev_g:+.1f}%" if isinstance(rev_g, (int, float)) else "N/A",
            f"{opm:.1f}%" if isinstance(opm, (int, float)) else "N/A",
            _esc(stage),
        ])
    caption = blk.get("caption") or f"{sym} vs. Listed Peers: Snapshot Valuation, Profitability & Stage 2 Matrix"
    takeaway = _linkify_html_fragment(
        blk.get("takeaway")
        or f"Peer multiples, growth rates, margins, and Weinstein stages are pulled deterministically from the same-session TradingView and fundamental snapshot.",
        max_cite,
    )
    return _render_table(
        _esc(caption),
        ["Ticker", "Company", "CMP", mcap_lbl, "P/E (TTM)", "P/B", "ROE", "Rev YoY", "OPM", "Stage"],
        rows,
        takeaway,
    )


def _render_parallel_block(blk: dict, sym: str, max_cite: int = 0) -> str:
    role = str(blk.get("role") or "MOAT_SCALING").upper()
    role_lbl = {
        "MOAT_SCALING": "Situational Scaling & Moat Twin",
        "FAILURE_BASE_RATE": "Historical Failure-Mode & Base-Rate Twin",
        "CYCLE_VALUATION": "Historical Cycle & Valuation Twin",
    }.get(role, "Situational Structural Parallel")
    comp = _esc(blk.get("company") or "")
    reg = _esc(blk.get("region_era") or "")
    mech = _linkify_html_fragment(str(blk.get("mechanism") or ""), max_cite)
    nums = _linkify_html_fragment(str(blk.get("outcome_numbers") or ""), max_cite)
    lesson = _linkify_html_fragment(str(blk.get("lesson_for_symbol") or ""), max_cite)
    cls = "callout callout-warn" if role == "FAILURE_BASE_RATE" else "case-note"
    if cls == "case-note":
        return (
            '<div class="case-note">\n'
            f'<div class="case-note-head"><h4 class="case-note-title">{_esc(role_lbl)}: {comp}</h4>'
            f'<span class="case-note-sub">{reg}</span></div>\n'
            f"<p><strong>Shared Mechanism:</strong> {mech}</p>\n"
            f"<p><strong>Historical Numbers &amp; Outcome:</strong> {nums}</p>\n"
            f"<p><strong>Direct Implication for {_esc(sym)}:</strong> {lesson}</p>\n"
            "</div>"
        )
    return (
        '<div class="callout callout-warn">\n'
        f'<p class="callout-title">{_esc(role_lbl)}: {comp} ({reg})</p>\n'
        f"<p><strong>Shared Vulnerability:</strong> {mech}</p>\n"
        f"<p><strong>Historical Numbers &amp; Base Rate:</strong> {nums}</p>\n"
        f"<p><strong>How {_esc(sym)} Compares Today:</strong> {lesson}</p>\n"
        "</div>"
    )


def _render_callout_block(blk: dict) -> str:
    variant = blk.get("variant", "primer")
    title = blk.get("title", "")
    ps = "".join(f"<p>{p}</p>" for p in blk.get("paragraphs", []))
    if variant == "case":
        sub = blk.get("subtitle", "")
        sub_html = f'<span class="case-note-sub">{sub}</span>' if sub else ""
        return (
            '<div class="case-note">\n'
            f'<div class="case-note-head"><h4 class="case-note-title">{title}</h4>{sub_html}</div>\n'
            f"{ps}\n"
            "</div>"
        )
    cls_map = {
        "primer": "callout",
        "rule": "callout callout-rule",
        "warn": "callout callout-warn",
    }
    cls = cls_map.get(variant, "callout")
    title_html = f'<p class="callout-title">{title}</p>\n' if title else ""
    return f'<div class="{cls}">\n{title_html}{ps}\n</div>'


def _build_edition_switcher(sym: str, active: str, web_words: int, book_words: int, audio_mins: int) -> str:
    dossier_cls = "edition-tab is-active" if active == "dossier" else "edition-tab"
    return (
        '<div class="edition-switcher" role="navigation" aria-label="Dossier Editions">\n'
        '  <div class="edition-tabs">\n'
        f'    <a class="{dossier_cls}" href="{sym}_dossier.html">Web Research Dossier ({web_words:,} words • Tables &amp; Charts)</a>\n'
        '  </div>\n'
        '  <div class="edition-downloads">\n'
        f'    <a class="edition-dl-link" href="{sym}_book.pdf" download="{sym}_book.pdf">Download PDF ({book_words:,} words)</a>\n'
        '  </div>\n'
        '</div>'
    )


def render_10chapter_monograph_editions(
    spec: dict,
    facts: dict | None = None,
    snapshots: dict | None = None,
    positions: dict | None = None,
    shortlist: dict | None = None,
    out_dossier_path: str | Path = "",
    persist_spec_dir: str | Path | None = None,
) -> dict:
    """Compile the Web Dossier HTML and the companion PDF from a 10-chapter spec."""
    facts = facts or {}
    snapshots = snapshots or {}
    if positions is None:
        raise ValueError("10-chapter dossiers require a fresh positions ledger via --positions")
    shortlist = shortlist or {}
    sym = spec["symbol"].upper()
    market = spec["market"].upper()
    as_of = spec.get("as_of") or snapshots.get("as_of") or facts.get("asof") or "latest"
    inst_m = (facts.get("instruments") or {}).get(sym, {})
    snap_sym = _lookup_snapshot(snapshots, sym)
    scoring = json.load(open(SCORING_FILE, encoding="utf-8"))
    cur = "₹" if market == "IN" else "$"

    schema_errors, stats = validate_monograph_spec(spec, min_total_words=0)
    if schema_errors:
        raise ValueError("Invalid 10-chapter dossier spec: " + "; ".join(schema_errors))

    verdict = spec["verdict"]
    v_cls = VERDICT_CLASS_MAP.get(verdict.upper(), "verdict-watch")
    archetype = spec.get("archetype", "STAGE2_LEADER")
    bucket = spec.get("strategy_bucket", "TACTICAL_MOMENTUM")

    tv = snap_sym.get("tradingview") or {}
    s2_ev = snap_sym.get("stage2_evaluation") or {}
    ledger_is_asof = str(inst_m.get("asof_bar", ""))[:10] == str(as_of)[:10]
    price_label = (
        f"Session Price ({_esc(as_of)})"
        if ledger_is_asof
        else f"Last verified target bar ({_esc(str(inst_m.get('asof_bar') or as_of)[:10])})"
    )
    close = (inst_m.get("close") if ledger_is_asof else None) or tv.get("close") or inst_m.get("close") or spec.get("cmp") or 0.0
    entry_low = spec["entry_zone_low"]
    entry_high = spec["entry_zone_high"]
    stop_loss = spec["stop_loss"]
    band_position = (
        "below price" if close is not None and entry_high < close
        else "above price" if close is not None and entry_low > close
        else "overlapping current price"
    )
    target_base = spec["target_base"]
    target_bull = spec["target_bull"]
    target_bear = spec["target_bear"]
    asym = (
        round((target_base - close) / (close - stop_loss), 2)
        if (target_base is not None and close and stop_loss and close > stop_loss)
        else spec.get("asymmetry_ratio", 0.0)
    )
    entry_asym = (
        round((target_base - entry_high) / (entry_high - stop_loss), 2)
        if (target_base is not None and entry_high and stop_loss and entry_high > stop_loss)
        else asym
    )

    tier = spec.get("conviction_tier", "TIER_2")
    w_stage = spec.get("weinstein_stage") or (inst_m.get("stage_label") if ledger_is_asof else None) or s2_ev.get("weinstein_stage", "N/A")
    entry_posture = spec.get("entry_posture") or s2_ev.get("entry_timing_posture") or verdict
    tech_gate = str(s2_ev.get("technical_timing_gate") or "").upper()
    if tech_gate == "CAP_REJECTED" and spec["new_capital_verdict"] in {"IMMEDIATE_BUY", "ACCUMULATE_ON_DIP"}:
        raise ValueError(
            f"Technical ceiling violation for {sym}: snapshot technical_timing_gate is CAP_REJECTED ({w_stage}), "
            f"which forbids {spec['new_capital_verdict']}"
        )
    if tech_gate == "CAP_WAIT_FOR_SUPPORT" and spec["new_capital_verdict"] == "IMMEDIATE_BUY":
        raise ValueError(
            f"Technical ceiling violation for {sym}: snapshot technical_timing_gate is CAP_WAIT_FOR_SUPPORT "
            f"({entry_posture}), which caps new capital at WAIT_FOR_SUPPORT or ACCUMULATE_ON_DIP"
        )
    no_new_allocation = (
        verdict.upper() in {"REJECTED", "WAIT_FOR_SUPPORT"}
        or str(entry_posture).startswith(("WAIT_FOR_SUPPORT", "NO_NEW_ALLOCATION", "AVOID", "STAY_AWAY"))
    )
    holding, holding_html, redeploy_html, book_decision = _decision_panels(spec, market, sym, positions, snapshots, shortlist)
    ratchet_errors = enforce_stop_loss_ratchet(spec, holding["quantity"], close if isinstance(close, (int, float)) else None)
    if ratchet_errors:
        raise ValueError("Stop-loss ratchet check failed: " + "; ".join(ratchet_errors))
    ru = _compute_risk_unit_sizing(close, entry_high, stop_loss, tier, scoring)
    if no_new_allocation:
        ru["risk_adjusted_weight_pct"] = 0.0
        ru["raw_risk_unit_weight_pct"] = 0.0
        ru["risk_budget_bps"] = 0.0

    scenario_horizon = str(spec.get("scenario_horizon") or "").strip()
    if target_base is None:
        target_label = f"{scenario_horizon.title()} scenario range" if scenario_horizon else "Scenario targets"
        target_value = "Not set; valuation bridge is not decision-grade"
    else:
        target_label = f"{scenario_horizon.title()} scenario range" if scenario_horizon else "Scenario targets"
        if target_bear is not None:
            target_value = f"Bear {cur}{target_bear:,.2f} / Base {cur}{target_base:,.2f} / Bull {cur}{target_bull:,.2f}"
        else:
            target_value = f"Base {cur}{target_base:,.2f} / Bull {cur}{target_bull:,.2f}"
        if no_new_allocation:
            target_value += " (new-entry R:R: N/A)"
        else:
            target_value += f" (Current R:R {asym:.2f}:1 | Support R:R {entry_asym:.2f}:1)"

    screen_signal_text = _esc(entry_posture)
    if no_new_allocation and str(entry_posture).upper() == "BUY_AT_CMP_NO_FOMO":
        screen_signal_text += " (technical ceiling only — overridden by fundamental/valuation gate)"

    kf_items = [
        ("New Capital Verdict", f'<span class="verdict {v_cls}">{_esc(spec["new_capital_verdict"])}</span> ({_esc(archetype)})'),
        ("Current Holding Action", f'<span class="verdict {VERDICT_CLASS_MAP.get(holding["action"], "verdict-watch")}">{_esc(holding["action"].replace("_", " "))}</span> — {_esc(holding["summary"])}'),
        (price_label, f"{cur}{close:,.2f}"),
        ("Strategy Bucket", _esc(bucket)),
        ("Weinstein Stage", _esc(w_stage)),
        ("Technical Screen Signal", screen_signal_text),
        (
            "Valuation watch zone (conditional)" if no_new_allocation else "Support Buy Zone",
            f"{cur}{entry_low:,.2f} – {cur}{entry_high:,.2f}" + (" (no live stop; recalculate before entry)" if no_new_allocation else f" (Stop: {cur}{stop_loss:,.2f})"),
        ),
        (target_label, target_value),
        ("Risk-Unit Sizing", f"{ru['risk_adjusted_weight_pct']}% of net worth ({_esc(tier)})"),
    ]
    opt_pkg = spec.get("options_package") if isinstance(spec.get("options_package"), dict) else None
    opt_plan = (opt_pkg.get("options_plan") if opt_pkg else None) or {}
    if opt_plan.get("options_verdict"):
        ov = str(opt_plan["options_verdict"])
        ov_cls = "verdict-keep" if ov in {"LONG_CALL_LEAPS", "BULL_CALL_DEBIT_SPREAD"} else "verdict-watch"
        kf_items.append((
            "Options / Call Playbook",
            f'<span class="verdict {ov_cls}">{_esc(ov.replace("_", " "))}</span> — {_esc(opt_plan.get("headline") or "")}',
        ))
    if spec.get("report_status"):
        kf_items.append(("Report status", _esc(spec["report_status"])))
    kf_html = (
        '<dl class="key-figures">\n'
        + "\n".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in kf_items)
        + "\n</dl>"
    )

    web_words = stats.get("web_words", 0)
    book_words = stats.get("book_words", 0)
    audio_mins = max(1, stats.get("estimated_audio_minutes", round(book_words / 155)))

    # Pre-build deterministic technical block (ch4_html) and sizing table (l3_html)
    ch4_spec = spec.get("ch4") or spec.get("technical_spec") or {}
    ch4_full_section = _build_ch4_from_snapshot_or_ledger(
        sym,
        market,
        snap_sym,
        inst_m,
        {
            "intro_prose": ch4_spec.get("intro_prose", f"We evaluate {sym}'s live TradingView moving averages, volume signature, and technical stage posture as of {as_of}."),
            "gate_intro_prose": ch4_spec.get("gate_intro_prose", "We separate medium-term trend durability from immediate No-FOMO entry timing."),
            "closing_prose": ch4_spec.get("closing_prose", "Technical structure and support distance govern when and how capital is deployed."),
            **ch4_spec,
        },
        as_of,
    )
    # Extract inner content of ch4_full_section (without outer <section><h2>) when embedded inside a chapter
    ch4_inner = re.sub(r"^<section[^>]*>\s*<h2>.*?</h2>\s*", "", ch4_full_section, flags=re.S)
    ch4_inner = re.sub(r"</section>\s*$", "", ch4_inner, flags=re.S)

    l3_rows = [
        [
            "Strategy bucket & conviction tier",
            f"{_esc(bucket)} ({_esc(tier)})",
            "Aligns capital allocation with durable trend, business quality, and balance-sheet resilience",
        ],
        [
            "Action verdict & No-FOMO posture",
            f'<span class="verdict {v_cls}">{_esc(verdict)}</span> ({_esc(entry_posture)})',
            _esc(spec.get("verdict_rule_summary", "Buy at CMP only in early Stage 2 near support; wait for support when extended; avoid when Stage 4 or risk-reward fails")),
        ],
        [
            "Screen band (monitor only)" if no_new_allocation else "Recommended buy / accumulation zone",
            f"{cur}{entry_low:,.2f} to {cur}{entry_high:,.2f}",
            (
                f"Current price {cur}{close:,.2f}; band is {band_position}; no immediate allocation is recommended"
                if no_new_allocation
                else f"Current price {cur}{close:,.2f}; accumulate inside the support band after trend and valuation gates pass"
            ),
        ],
        [
            "No live stop (monitor only)" if no_new_allocation else "Structural invalidation stop",
            "Recalculate after an entry is authorized" if no_new_allocation else f"{cur}{stop_loss:,.2f}",
            (
                "Reference level only; not an active order while no position is authorized"
                if no_new_allocation
                else _esc(ch4_spec.get("stop_placement_explanation") or scoring["stop_placement"].get(bucket, scoring["stop_placement"]["CORE_ALPHA"]))
            ),
        ],
        [
            "Scenario values",
            "Not assigned" if target_base is None else f"{cur}{target_base:,.2f} / {cur}{target_bull:,.2f} / {cur}{target_bear:,.2f}",
            ("Per-share values require a reconciled share count and lease-consistent valuation bridge." if target_base is None else
             (
                 f"Probability-weighted {scenario_horizon or '12-month'} scenario values; no live entry reward/risk applies until trend/valuation gates clear"
                if no_new_allocation
                else f"Reward-to-risk ratio: {asym:.2f}:1 at CMP ({entry_asym:.2f}:1 from top of support zone)"
            )),
        ],
        [
            "Risk-unit initial sizing (portfolio heat)",
            f"{ru['risk_adjusted_weight_pct']}% of net worth ({_esc(tier)}, {ru['risk_budget_bps']:.0f} bps risk budget)",
            (
                "Zero live allocation while entry or trend gates remain unresolved; recalculate on trigger confirmation"
                if no_new_allocation
                else f"Formula: min(Tier cap {ru['tier_range_pct']}, {ru['risk_budget_bps']:.0f} bps / {ru['stop_distance_pct']}% stop distance)"
            ),
        ],
        [
            "Let-winners-run rule",
            ("Not applicable while no position is open" if no_new_allocation else f"Appreciated weight ceiling up to {ru['runaway_winner_cap_pct']}%"),
            (
                "Do not allocate or place an order before the entry gates pass"
                if no_new_allocation
                else "Never trim solely for RSI > 70 or crossing 15%; trail stop to rising 21-EMA / 50-SMA until trend or fundamentals break"
            ),
        ],
    ]
    l3_rows = [[cell if str(cell).rstrip().endswith((".", "!", "?")) else f"{cell}." for cell in row] for row in l3_rows]
    l3_html = _render_table(
        f"No-FOMO execution levels and risk-unit position sizing for {sym}",
        ["Execution item", "Level / Sizing", "Rule and derivation"],
        l3_rows,
        spec.get(
            "sizing_table_takeaway",
            f"This execution table translates our {verdict} verdict on {sym} into concrete price levels, invalidation stops, and portfolio risk-budget sizing.",
        ),
    )

    max_cite = len(spec.get("citations") or [])
    if not spec.get("primer"):
        for ch in spec.get("chapters", []):
            if ch.get("id") in {"ch-0", "primer"}:
                for blk in ch.get("web_blocks", []):
                    if blk.get("type") == "p":
                        spec["primer"] = strip_html(blk.get("html") or blk.get("text") or "")
                        break
                if not spec.get("primer") and ch.get("book_paragraphs"):
                    spec["primer"] = ch["book_paragraphs"][0]
                break
        if not spec.get("primer"):
            spec["primer"] = f"Executive investment monograph on {sym} ({company_name}) as of {as_of}."
    primer_text = spec.get("primer") or ""
    primer_html = (
        '<section class="primer" id="primer">\n'
        "<h2>Executive Thesis &amp; Before You Read</h2>\n"
        f"<p>{_linkify_html_fragment(primer_text, max_cite)}</p>\n"
        "</section>"
    ) if primer_text else ""

    web_sections: List[str] = []
    spec_for_build = copy.deepcopy(spec)
    chapters = spec_for_build.get("chapters", [])
    refresh_audit = spec.get("refresh_audit") if isinstance(spec.get("refresh_audit"), dict) else None
    prior_anchor = spec.get("prior_anchor") if isinstance(spec.get("prior_anchor"), dict) else {}
    revision_web_html = ""
    if refresh_audit:
        prior_as_of = prior_anchor.get("as_of") or refresh_audit.get("prior_as_of") or "prior session"
        prior_verdict = prior_anchor.get("verdict") or "N/A"
        prior_stop = prior_anchor.get("stop_loss")
        prior_stop_txt = f"{cur}{prior_stop:,.2f}" if isinstance(prior_stop, (int, float)) else "N/A"
        new_stop_txt = f"{cur}{stop_loss:,.2f}" if isinstance(stop_loss, (int, float)) else "N/A"
        tier_mode = _esc(refresh_audit.get("recommended_tier") or "REFRESH")
        patched = [
            f"<strong>{_esc(b.get('target_chapter', ''))}:</strong> {_linkify_html_fragment(str(b.get('what_was_missed', '')), max_cite)}"
            for b in (refresh_audit.get("blind_spots_discovered") or [])
            if isinstance(b, dict) and b.get("materiality") == "MATERIAL_PATCHED"
        ]
        changed_assumptions = [
            f"<strong>{_esc(a.get('disposition', ''))} ({_esc(a.get('chapter', ''))}):</strong> {_linkify_html_fragment(str(a.get('claim', '')), max_cite)}"
            for a in (refresh_audit.get("assumptions_checked") or [])
            if isinstance(a, dict) and a.get("disposition") in {"WEAKENED", "BROKEN", "CONFIRMED"}
        ]
        rev_ps = [
            f"<strong>Companion Audit ({tier_mode}) — { _esc(prior_as_of) } &rarr; { _esc(as_of) }:</strong> "
            f"Verdict {_esc(prior_verdict)} &rarr; <strong>{_esc(spec['new_capital_verdict'])}</strong>; "
            f"Structural Stop {prior_stop_txt} &rarr; <strong>{new_stop_txt}</strong>."
        ]
        if changed_assumptions:
            rev_ps.append("<strong>Assumptions Re-Tested:</strong> " + " | ".join(changed_assumptions[:4]))
        if patched:
            rev_ps.append("<strong>Blind Spots Newly Underwritten:</strong> " + " | ".join(patched[:4]))
        revision_web_html = (
            '<div class="callout callout-rule" id="revision-audit-summary">\n'
            '<p class="callout-title">Companion Dossier Refresh &amp; Blind-Spot Audit</p>\n'
            + "".join(f"<p>{p}</p>\n" for p in rev_ps)
            + "</div>"
        )
        for chapter in chapters:
            if chapter.get("id") in {"ch-0", "primer"}:
                chapter.setdefault("book_callouts", []).insert(0, {
                    "kind": "mental_model",
                    "title": f"Companion Refresh ({prior_as_of} to {as_of})",
                    "text": strip_html(" ".join(rev_ps)),
                })
                break

    for chapter in chapters:
        for blk in chapter.get("web_blocks", []):
            if blk.get("type") == "parallel":
                chapter.setdefault("book_callouts", []).append({
                    "kind": "parallel",
                    "label": str(blk.get("region_era") or "SITUATIONAL PARALLEL"),
                    "title": f"{blk.get('company', '')} ({blk.get('role', 'PARALLEL')})",
                    "text": strip_html(f"{blk.get('mechanism', '')} {blk.get('outcome_numbers', '')} {blk.get('lesson_for_symbol', '')}"),
                })
        if chapter.get("id") == "ch-9":
            chapter.setdefault("book_paragraphs", []).append(book_decision)
            if opt_plan.get("headline"):
                opt_book_text = f"Options and Call-Convexity Playbook ({opt_plan.get('options_verdict', '').replace('_', ' ')}): {opt_plan['headline']}"
                tr = opt_plan.get("recommended_trade") or {}
                if tr.get("beginner_explainer"):
                    opt_book_text += " " + " ".join(tr["beginner_explainer"])
                chapter.setdefault("book_paragraphs", []).append(strip_html(opt_book_text))
    schema_errors, stats = validate_monograph_spec(spec_for_build)
    if schema_errors:
        raise ValueError("Incomplete 10-chapter dossier spec: " + "; ".join(schema_errors))
    web_words = stats.get("web_words", 0)
    book_words = stats.get("book_words", 0)
    audio_mins = max(1, stats.get("estimated_audio_minutes", round(book_words / 155)))

    for idx, ch in enumerate(chapters):
        raw_cid = ch.get("id") or f"ch-{idx}"
        cid = "ch-0" if (idx == 0 and raw_cid == "primer") else raw_cid
        w_title = ch.get("web_title") or ch.get("book_title") or f"Chapter {idx}"
        question = ch.get("question") or ch.get("kicker") or ""

        w_parts = [f'<section class="chapter" id="{_esc(cid)}">', f"<h2>{_esc(w_title)}</h2>"]
        if question:
            w_parts.append(f'<div class="section-summary"><strong>Core Investor Question:</strong> {_esc(question)}</div>')
        if idx == 0 and revision_web_html:
            w_parts.append(revision_web_html)
        saw_tv = False
        saw_sizing = False
        for blk in ch.get("web_blocks", []):
            btype = blk.get("type", "p")
            if btype == "p":
                w_parts.append(f"<p>{_linkify_html_fragment(blk.get('html') or blk.get('text', ''), max_cite)}</p>")
            elif btype == "h3":
                w_parts.append(f"<h3>{_esc(blk.get('title', ''))}</h3>")
            elif btype == "table":
                linked_rows = [
                    [_linkify_html_fragment(str(c), max_cite) for c in r]
                    for r in blk.get("rows", [])
                ]
                w_parts.append(
                    _render_table(
                        _linkify_html_fragment(blk.get("caption", ""), max_cite),
                        blk.get("headers", []),
                        linked_rows,
                        _linkify_html_fragment(blk.get("takeaway", ""), max_cite),
                    )
                )
            elif btype == "waterfall":
                w_parts.append(_render_waterfall_block(blk, market, sym, max_cite))
            elif btype == "snapshot_financials":
                sf_html = _render_snapshot_financials(blk, snap_sym, sym, max_cite)
                if sf_html:
                    w_parts.append(sf_html)
            elif btype == "peer_snapshot_table":
                w_parts.append(_render_peer_snapshot_table(blk, snapshots, sym, market, max_cite))
            elif btype == "callout":
                linked_blk = {
                    **blk,
                    "title": _linkify_html_fragment(blk.get("title", ""), max_cite),
                    "paragraphs": [_linkify_html_fragment(p, max_cite) for p in blk.get("paragraphs", [])],
                }
                w_parts.append(_render_callout_block(linked_blk))
            elif btype == "parallel":
                w_parts.append(_render_parallel_block(blk, sym, max_cite))
            elif btype == "estimate":
                w_parts.append(_render_estimate(blk))
            elif btype == "tradingview_chart":
                saw_tv = True
                w_parts.append(ch4_inner)
            elif btype == "sizing_table":
                saw_sizing = True
                w_parts.append("<h3>No-FOMO support entry zone, stop placement &amp; position sizing</h3>")
                intro_html = blk.get("intro") or blk.get("html") or blk.get("text")
                if intro_html:
                    w_parts.append(f"<p>{_linkify_html_fragment(intro_html, max_cite)}</p>")
                w_parts.append(l3_html)
            elif btype == "trigger":
                w_parts.append(f'<p class="trigger">{_linkify_html_fragment(blk.get("html") or blk.get("text", ""), max_cite)}</p>')

        if cid == "ch-8" and not saw_tv:
            w_parts.append("<h3>Interactive TradingView Tape &amp; Deterministic Technical Structure Ledger</h3>")
            w_parts.append(ch4_inner)
        if cid == "ch-9" and not saw_sizing:
            w_parts.append("<h3>No-FOMO support entry zone, stop placement &amp; position sizing</h3>")
            w_parts.append(l3_html)

        w_parts.append("</section>")
        web_sections.append("\n".join(w_parts))
        if cid == "ch-9":
            web_sections.extend([holding_html, redeploy_html])
            if opt_pkg and opt_plan:
                web_sections.append(
                    render_options_section_html(
                        opt_plan,
                        opt_pkg.get("multitimeframe_chart"),
                        opt_pkg.get("browser_sessions"),
                    )
                )

    ge_html = ""
    if spec.get("gate_exceptions"):
        ge_ps = "".join(f"<p>{_linkify_html_fragment(p, max_cite)}</p>" for p in spec["gate_exceptions"])
        ge_html = f'<section class="chapter" id="gate-exceptions">\n<h2>Run notes and gate exceptions</h2>\n{ge_ps}\n</section>\n'

    cites_li = "\n".join(
        f'<li id="cite_note-{i}">{_linkify_html_fragment(str(c), 0)}</li>'
        for i, c in enumerate(spec["citations"], 1)
    )
    notes_html = (
        '<section id="notes">\n'
        '<h2 id="references">Notes and sources</h2>\n'
        f'<ol class="sources reflist">\n{cites_li}\n</ol>\n'
        "</section>"
    )

    web_body_html = "\n\n".join(
        [
            f"<h1>{_esc(spec['title'])}</h1>",
            _build_edition_switcher(sym, "dossier", web_words, book_words, audio_mins),
            kf_html,
            primer_html,
            "\n\n".join(web_sections),
            ge_html + notes_html,
        ]
    )

    sector = (
        spec.get("sector")
        or tv.get("sector")
        or (snap_sym.get("fundamental_card") or {}).get("sector")
        or (snap_sym.get("thewrap_stage2") or {}).get("thewrap_industry")
        or tv.get("industry")
        or ""
    )

    dossier_html = build(
        web_body_html,
        market=market,
        facts=spec.get("facts_path", ""),
        research=spec.get("research_paths", []),
        kind="dossier",
        workflow="Company research",
        as_of=as_of,
        sector=sector,
    )
    book_html = render_masterclass_book_html(spec_for_build, chapters, kf_items, web_words, book_words, audio_mins)

    out_d_path = Path(out_dossier_path)
    out_dir = out_d_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf_path = out_dir / f"{sym}_book.pdf"

    out_d_path.write_text(dossier_html, encoding="utf-8")

    # The narrative HTML feeds WeasyPrint only; it is a build intermediate and
    # is never published as a standalone page. Keep it beside the PDF so the
    # print stylesheet's relative asset paths resolve, then remove it.
    tmp_book_html = out_dir / f".{sym}_book_print_source.html"
    tmp_book_html.write_text(book_html, encoding="utf-8")
    try:
        build_pdf_book(tmp_book_html, out_pdf_path)
    finally:
        tmp_book_html.unlink(missing_ok=True)

    # Persist canonical spec under data/dossiers/<MKT>/<SYM>/ when publishing to docs/blogs/ (or explicit dir)
    persisted_dir = None
    docs_blogs_root = (Path(ROOT) / "docs" / "blogs").resolve()
    resolved_out = out_d_path.resolve()
    target_persist = Path(persist_spec_dir) if persist_spec_dir else (
        Path(ROOT) / "data" / "dossiers" / market / sym if docs_blogs_root in resolved_out.parents else None
    )
    if target_persist is not None:
        persisted_dir = str(persist_monograph_spec(spec, target_persist))

    return {
        "dossier_html": str(out_d_path),
        "pdf": str(out_pdf_path) if out_pdf_path.exists() else None,
        "persisted_spec_dir": persisted_dir,
        "web_words": web_words,
        "book_words": book_words,
        "audio_minutes": audio_mins,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", required=True, help="Path to structured company spec JSON or chapter directory")
    ap.add_argument("--snapshot", default="", help="Path to stock_snapshot.py JSON output")
    ap.add_argument("--facts", default="", help="Optional path to market_facts JSON ledger")
    ap.add_argument("--positions", default="", help="Path to the same-session market_facts positions ledger")
    ap.add_argument("--shortlist", default="", help="Path to this market's active shortlist records")
    ap.add_argument("--options-snapshot", default="", help="Optional path to options_snapshot.py JSON output")
    ap.add_argument("--persist-spec-dir", default="", help="Optional directory to persist canonical chapter JSON spec")
    ap.add_argument("--out", required=True, help="Output dossier HTML path")
    args = ap.parse_args()

    spec = load_monograph_spec(args.spec)
    if args.options_snapshot and Path(args.options_snapshot).is_file():
        opt_all = json.loads(Path(args.options_snapshot).read_text(encoding="utf-8"))
        sym_key = str(spec.get("symbol") or "").upper()
        pkg = (opt_all.get("packages") or {}).get(sym_key) or (opt_all if opt_all.get("symbol") == sym_key else None)
        if pkg:
            spec["options_package"] = pkg
    if args.facts:
        spec.setdefault("facts_path", args.facts)
    facts = json.loads(Path(args.facts).read_text(encoding="utf-8")) if args.facts and Path(args.facts).exists() else {}
    snapshots = (
        json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        if args.snapshot and Path(args.snapshot).exists()
        else {}
    )
    positions = json.loads(Path(args.positions).read_text(encoding="utf-8")) if args.positions else None
    shortlist_path = Path(args.shortlist) if args.shortlist else Path(ROOT) / "data" / "shortlist" / f"{spec['market'].upper()}.json"
    shortlist = json.loads(shortlist_path.read_text(encoding="utf-8")) if shortlist_path.exists() else {}
    if isinstance(spec.get("chapters"), list) and spec["chapters"]:
        res = render_10chapter_monograph_editions(
            spec, facts=facts, snapshots=snapshots, positions=positions, shortlist=shortlist,
            out_dossier_path=args.out,
            persist_spec_dir=args.persist_spec_dir or None,
        )
        print(
            f"wrote monograph for {spec['symbol']}:\n"
            f"  - Web Dossier: {res['dossier_html']} ({res['web_words']:,} words)\n"
            f"  - PDF:         {res['pdf'] or 'not built (weasyprint unavailable)'} ({res['book_words']:,} words, ~{res['audio_minutes']} min)"
        )
    else:
        html_out = render_book_dossier(spec, facts=facts, snapshots=snapshots)
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        Path(args.out).write_text(html_out, encoding="utf-8")
        print(f"wrote monograph: {args.out} ({len(html_out):,} bytes)")


if __name__ == "__main__":
    main()
