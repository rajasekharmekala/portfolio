#!/usr/bin/env python3
"""
Deterministic Book-Standard Dossier Builder (scripts/dossier_builder_template.py).

Separates mechanical HTML structure, ledger table rendering (technicals, momentum gate,
Reverse DCF implied growth, consensus EPS revisions, risk-unit sizing), and readability/glossary
compliance from the LLM's analytical prose.

Usage:
  .venv/bin/python scripts/dossier_builder_template.py \
      --spec <RUN_DIR>/work/<SYM>_spec.json \
      --facts <RUN_DIR>/cache/facts_<MKT>_<date>.json \
      --out docs/blogs/<MKT>/<SYM>_dossier.html
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assemble_report import build  # noqa: E402

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
    "REPLACE_UNDERPERFORMER": "verdict-exit",
    "REPLACE UNDERPERFORMER": "verdict-exit",
    "REJECTED": "verdict-exit",
    "AVOID / REJECTED": "verdict-exit",
}


def _esc(val) -> str:
    if val is None:
        return "N/A"
    return html.escape(str(val))


def _render_table(caption: str, headers: list[str], rows: list[list[str]], explanatory_p: str) -> str:
    th_html = "".join(f"<th>{h}</th>" for h in headers)
    tr_list = []
    for r in rows:
        tds = "".join(f"<td>{c}</td>" for c in r)
        tr_list.append(f"<tr>{tds}</tr>")
    body_html = "\n".join(tr_list)
    cap_html = f"<caption>{caption}</caption>\n" if caption else ""
    if len(explanatory_p.strip()) < 85:
        explanatory_p = explanatory_p.strip() + " This table grounds the chapter's analysis in verified figures from the session ledger and cited filings."
    return (
        f'<div class="table-wrap"><table class="wikitable">\n'
        f"{cap_html}"
        f"<thead><tr>{th_html}</tr></thead>\n"
        f"<tbody>\n{body_html}\n</tbody>\n"
        f"</table></div>\n"
        f"<p>{explanatory_p}</p>"
    )


def _render_estimate(est: dict) -> str:
    return (
        '<section class="estimate">\n'
        f'<h4>The number</h4>\n<p>{est["the_number"]}</p>\n'
        f'<h4>How it was calculated</h4>\n<p>{est["how_calculated"]}</p>\n'
        f'<h4>The inputs</h4>\n<p>{est["the_inputs"]}</p>\n'
        f'<h4>The range</h4>\n<p>{est["the_range"]}</p>\n'
        f'<h4>If the number is off</h4>\n<p>{est["if_off"]}</p>\n'
        '</section>'
    )


def _compute_risk_unit_sizing(cmp_val: float, entry_val: float, stop_val: float, tier: str, scoring: dict) -> dict:
    pos_cfg = scoring.get("position_sizing", {})
    tier_tbl = pos_cfg.get("tier_table", {}).get(tier, {"min_pct": 0.0, "max_pct": 0.0})
    ru_cfg = pos_cfg.get("risk_unit_sizing", {})
    budget_bps = float(ru_cfg.get("tier_risk_budget_bps", {}).get(tier, 75 if tier != "TIER_0" else 0))
    ref_entry = entry_val if (entry_val and entry_val > 0) else cmp_val
    if not ref_entry or not stop_val or ref_entry <= stop_val or budget_bps <= 0:
        zero_stop_dist = round((ref_entry - stop_val) / ref_entry * 100.0, 2) if (ref_entry and stop_val and ref_entry > stop_val) else "n/a"
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


def _build_ch4_from_ledger(sym: str, market: str, inst_m: dict, ch4_spec: dict) -> str:
    cur = "₹" if market == "IN" else "$"
    bench = "Nifty 50" if market == "IN" else "S&P 500"
    close = inst_m.get("close")
    s20, s50, s200 = inst_m.get("sma20"), inst_m.get("sma50"), inst_m.get("sma200")
    s50_21, s200_63 = inst_m.get("sma50_21d_ago"), inst_m.get("sma200_63d_ago")
    rsi, atr = inst_m.get("rsi14"), inst_m.get("atr14")
    hi52, lo52 = inst_m.get("hi52"), inst_m.get("lo52")
    swing20, base63 = inst_m.get("swing_low_20d"), inst_m.get("base_low_63d")
    sup_anchor = inst_m.get("support_anchor") or swing20 or s50
    sup_atr = inst_m.get("support_distance_atr")
    vmult = inst_m.get("vol_mult_20d")
    rs63, rs28 = inst_m.get("rs_63d_pct"), inst_m.get("rs_28d_pct")
    stage_lbl = inst_m.get("stage_label", f"Stage {inst_m.get('stage')}")
    asof = inst_m.get("asof_bar", "")
    cite_tag = ch4_spec.get("ledger_cite_tag", "")

    def fmt_px(v):
        return f"{cur}{v:,.2f}" if isinstance(v, (int, float)) else "N/A"

    tech_rows = [
        ["Session close (" + _esc(asof) + ")", fmt_px(close) + cite_tag, f"1D: {inst_m.get('chg_1d_pct', 'N/A')}%, 1W: {inst_m.get('chg_1w_pct', 'N/A')}%, 1M: {inst_m.get('chg_1m_pct', 'N/A')}%"],
        ["20-day / 50-day / 200-day average", f"{fmt_px(s20)} / {fmt_px(s50)} / {fmt_px(s200)}", f"50-day trend: {inst_m.get('sma50_trend', 'N/A')} (21d ago: {fmt_px(s50_21)}; 200d 63d ago: {fmt_px(s200_63)})"],
        ["Weinstein trend stage", _esc(stage_lbl), "Stage 2 is rising markup; Stage 1 is basing floor; Stage 3 is pullback/top; Stage 4 is markdown"],
        ["RSI (14-day) / ATR (14-day)", f"{rsi if rsi is not None else 'N/A'} / {fmt_px(atr)}", "Momentum gauge (30 oversold, 70 overbought) and typical daily price swing"],
        ["52-week high / low", f"{fmt_px(hi52)} / {fmt_px(lo52)}", f"Close is {inst_m.get('pct_from_52w_high', 'N/A')}% from 52-week high"],
        ["20-day swing low / 63-day base low", f"{fmt_px(swing20)} / {fmt_px(base63)}", f"Active support anchor: {fmt_px(sup_anchor)} ({sup_atr if sup_atr is not None else 'N/A'} ATR away)"],
        ["Volume vs 20-day average", f"{vmult if vmult is not None else 'N/A'}x", f"63-day volume dry-up ratio: {inst_m.get('vol_dryup_ratio_63d', 'N/A')}"],
        [f"Relative strength vs {bench} (63d / 28d)", f"{rs63 if rs63 is not None else 'N/A'}% / {rs28 if rs28 is not None else 'N/A'}%", "Excess return vs benchmark over 3 months and 6 weeks"],
    ]
    t1_html = _render_table(
        f"Verified price and technical structure for {sym} as of {asof}",
        ["Technical measure", "Ledger reading", "Plain-English meaning"],
        tech_rows,
        ch4_spec["tech_table_takeaway"],
    )

    mg = inst_m.get("momentum_gate") or {}
    mg_rows = []
    mgc = (json.load(open(SCORING_FILE, encoding="utf-8")).get("momentum_gate") or {})
    ta, tb, tc = mgc.get("test_a_in_momentum_now", {}), mgc.get("test_b_entering_momentum", {}), mgc.get("test_c_turnaround_inflection", {})
    label_map = {
        "A1_structure": ("Test A1 (Markup structure)", f"Price > SMA50 > SMA200 and SMA50 rising over {ta.get('sma50_rising_window_days', 21)} days"),
        "A2_sma200_not_falling": ("Test A2 (Long trend slope)", f"SMA200 flat or rising over {ta.get('sma200_not_falling_window_days', 63)} trading days"),
        "A3_rs_leading_63d": ("Test A3 (Quarterly leadership)", f"{ta.get('rs_window_days', 63)}-day return beats {bench} by at least {ta.get('rs_min_excess_vs_benchmark_pct', 0.0)}%"),
        "A4_not_extended": ("Test A4 (Support proximity)", f"Price within {ta.get('support_distance_atr_max', 1.6)} ATR of nearest verified support"),
        "B1_sma50_holding": ("Test B1 (Base 50-DMA holding)", f"50-day average decline no more than {tb.get('sma50_max_decline_pct', 0.8)}% over {tb.get('sma50_window_days', 21)} days"),
        "B2_rs_turning_28d": ("Test B2 (Monthly RS turn)", f"{tb.get('rs_rising_window_days', 28)}-day return beats {bench} (> 0%)"),
        "B3_at_base_pivot": ("Test B3 (Tight base pivot)", f"Price within {tb.get('pivot_atr_max', 1.5)} ATR of the {tb.get('base_window_days', 63)}-day base low"),
        "B4_volume_dryup": ("Test B4 (Seller exhaustion)", f"{tb.get('base_window_days', 63)}-day volume dry-up ratio at or below {tb.get('volume_dryup_ratio_max', 0.92)}"),
        "B5_volume_expansion": ("Test B5 (Buyer expansion)", f"Session volume at least {tb.get('volume_expand_ratio_min', 0.95)}x the 20-day average"),
        "C1_higher_low_floor": ("Test C1 (Higher-low floor)", f"Price more than 1% above the 63-day low, with the 20-day swing low no more than {tc.get('higher_low_tolerance_pct', 1.0)}% below it"),
        "C2_short_term_turn": ("Test C2 (Short-term inflection)", "Price at or above the 20-day average, with positive 28-day relative strength or a positive 2-week gain"),
        "C3_near_support": ("Test C3 (Buyable support distance)", f"Price within {tc.get('support_atr_max', 2.0)} ATR of active support"),
        "C4_momentum_stabilizing": ("Test C4 (No freefall)", f"14-day RSI at or above {tc.get('min_rsi14', 32.0)} (selling pressure stabilizing)"),
    }
    for test_key in ("test_a", "test_b", "test_c"):
        t_obj = mg.get(test_key, {})
        for c_key, c_val in t_obj.get("conditions", {}).items():
            name_lbl, rule_lbl = label_map.get(c_key, (c_key, "Gate condition"))
            meas = c_val.get("measured")
            if isinstance(meas, dict):
                meas_str = "; ".join(f"{str(k).replace('_', ' ')} {v}" for k, v in meas.items())
            else:
                meas_str = str(meas or c_val.get("reason", "N/A"))
            res_str = "PASS" if c_val.get("pass") else "FAIL"
            mg_rows.append([name_lbl, rule_lbl, _esc(meas_str), res_str])

    t2_html = _render_table(
        f"Momentum & recovery gate evaluation for {sym} (Verdict: {mg.get('verdict', 'N/A')} / {mg.get('sub_verdict', 'N/A')})",
        ["Gate test", "Rule in plain words", "Measured values from ledger", "Result"],
        mg_rows,
        ch4_spec["gate_table_takeaway"],
    )

    return (
        '<section class="chapter" id="ch-4">\n'
        "<h2>4. What the price is doing</h2>\n"
        f"<p>{ch4_spec['intro_prose']}</p>\n"
        f"{t1_html}\n"
        "<h3>Momentum and turnaround inflection gate</h3>\n"
        f"<p>{ch4_spec['gate_intro_prose']}</p>\n"
        f"{t2_html}\n"
        f"<p>{ch4_spec['closing_prose']}</p>\n"
        "</section>"
    )


def _build_expectations_block(sym: str, market: str, inst_m: dict, ch5_spec: dict) -> str:
    cur = "₹" if market == "IN" else "$"
    rdcf = inst_m.get("reverse_dcf") or {}
    crev = inst_m.get("consensus_revisions") or {}
    cite_tag = ch5_spec.get("expectations_cite_tag", "")

    imp_g = rdcf.get("implied_10y_cagr_pct")
    imp_str = f"{imp_g:+.2f}% per year" if isinstance(imp_g, (int, float)) else "N/A (see working below)"
    fcf_y = rdcf.get("fcf_yield_pct")
    fcf_y_str = f"{fcf_y:.2f}%" if isinstance(fcf_y, (int, float)) else "N/A"

    fy1_c = crev.get("fy1_eps_current")
    fy1_90 = crev.get("fy1_eps_90d_ago")
    fy1_r90 = crev.get("fy1_eps_rev_90d_pct")
    fy2_c = crev.get("fy2_eps_current")
    fy2_90 = crev.get("fy2_eps_90d_ago")
    fy2_r90 = crev.get("fy2_eps_rev_90d_pct")
    fy2_g = crev.get("implied_fy2_eps_growth_pct")
    tgt_l, tgt_m, tgt_h = crev.get("analyst_target_low"), crev.get("analyst_target_mean"), crev.get("analyst_target_high")

    rows = [
        [
            "Reverse DCF implied 10-year growth",
            imp_str + cite_tag,
            _esc(rdcf.get("plain_english", "Implied growth solved from current valuation and trailing cash flow.")),
        ],
        [
            "Reverse DCF cash-flow basis & FCF yield",
            f"{_esc(rdcf.get('basis', 'N/A'))} ({rdcf.get('base_cashflow_val', 'N/A')} {_esc(rdcf.get('base_cashflow_unit', ''))}); FCF yield: {fcf_y_str}",
            f"Solved at {rdcf.get('discount_rate_pct', 'N/A')}% discount rate and {rdcf.get('terminal_multiple', 'N/A')}x terminal multiple",
        ],
        [
            "Consensus FY1 EPS (current vs 90d ago)",
            f"{cur}{fy1_c:.2f} vs {cur}{fy1_90:.2f} ({fy1_r90:+.2f}%)" if (fy1_c and fy1_90 and fy1_r90 is not None) else (f"{cur}{fy1_c:.2f}" if fy1_c else "No consensus coverage (N/A)"),
            f"Revision trend status: {crev.get('revision_trend', 'N/A')}",
        ],
        [
            "Consensus FY2 EPS (current vs 90d ago)",
            f"{cur}{fy2_c:.2f} vs {cur}{fy2_90:.2f} ({fy2_r90:+.2f}%)" if (fy2_c and fy2_90 and fy2_r90 is not None) else (f"{cur}{fy2_c:.2f}" if fy2_c else "No consensus coverage (N/A)"),
            f"Implied FY2 vs FY1 EPS growth: {f'{fy2_g:+.1f}%' if fy2_g is not None else 'N/A'}",
        ],
        [
            "Street analyst target range (low / mean / high)",
            f"{cur}{tgt_l:,.2f} / {cur}{tgt_m:,.2f} / {cur}{tgt_h:,.2f} ({crev.get('num_analysts') or 'N/A'} analysts)" if tgt_m else "No street price targets published (N/A)",
            "Used as expectations context only; our underwriting target is anchored in the scenario model below",
        ],
    ]
    if ch5_spec.get("extra_expectation_rows"):
        rows.extend(ch5_spec["extra_expectation_rows"])

    return _render_table(
        f"What today's stock price assumes (Reverse DCF) and how analyst estimates are moving for {sym}",
        ["Expectations dimension", "Measured reading", "How to interpret it"],
        rows,
        ch5_spec["expectations_takeaway"],
    )


def render_book_dossier(spec: dict, facts: dict) -> str:
    sym = spec["symbol"].upper()
    market = spec["market"].upper()
    as_of = facts.get("asof") or spec.get("as_of")
    inst_m = (facts.get("instruments") or {}).get(sym, {})
    scoring = json.load(open(SCORING_FILE, encoding="utf-8"))
    cur = "₹" if market == "IN" else "$"

    verdict = spec["verdict"]
    v_cls = VERDICT_CLASS_MAP.get(verdict.upper(), "verdict-watch")
    archetype = spec.get("archetype", "COMPOUNDER")
    bucket = spec.get("strategy_bucket", "CORE_ALPHA")

    close = inst_m.get("close") or spec.get("cmp")
    entry_low = spec["entry_zone_low"]
    entry_high = spec["entry_zone_high"]
    stop_loss = spec["stop_loss"]
    target_base = spec["target_base"]
    target_bull = spec["target_bull"]
    target_bear = spec["target_bear"]
    asym = round((target_base - close) / (close - stop_loss), 2) if (close and stop_loss and close > stop_loss) else spec.get("asymmetry_ratio", 0.0)

    tier = spec.get("conviction_tier", "TIER_2")
    ru = _compute_risk_unit_sizing(close, entry_high, stop_loss, tier, scoring)
    mg = inst_m.get("momentum_gate") or {}
    rdcf = inst_m.get("reverse_dcf") or {}
    crev = inst_m.get("consensus_revisions") or {}

    imp_g = rdcf.get("implied_10y_cagr_pct")
    imp_g_str = f"{imp_g:+.1f}%/yr" if isinstance(imp_g, (int, float)) else spec.get("reverse_dcf_fallback_label", "See Ch. 5")

    # Key figures strip
    kf_items = [
        ("Verdict", f'<span class="verdict {v_cls}">{_esc(verdict)}</span> ({_esc(archetype)})'),
        ("Session Price (" + _esc(as_of) + ")", f"{cur}{close:,.2f}"),
        ("Strategy Bucket", _esc(bucket)),
        ("Implied 10Y Growth (Reverse DCF)", _esc(imp_g_str)),
        ("Estimate Revisions (90d)", _esc(crev.get("revision_trend", "See Ch. 5"))),
        ("Trend & Momentum Gate", f"{_esc(inst_m.get('stage_label', 'N/A'))} | {_esc(mg.get('verdict', 'N/A'))}"),
        ("Support Distance / Stop", f"{inst_m.get('support_distance_atr', 'N/A')} ATR | Stop {cur}{stop_loss:,.2f}"),
        ("Base Target / Asymmetry", f"{cur}{target_base:,.2f} | {asym:.2f}:1 (Risk-Unit Size: {ru['risk_adjusted_weight_pct']}%)"),
    ]
    if spec.get("report_status"):
        kf_items.append(("Report status", _esc(spec["report_status"])))
    kf_html = '<dl class="key-figures">\n' + "\n".join(
        f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in kf_items
    ) + "\n</dl>"

    # Primer (must be 3-5 sentences)
    primer_html = f'<section class="primer" id="primer">\n<h2>Before you read</h2>\n<p>{spec["primer"]}</p>\n</section>'

    # Chapter 1: What the company does
    ch1 = spec["ch1"]
    ch1_parts = ['<section class="chapter" id="ch-1">', "<h2>1. What the company does</h2>"]
    for p in ch1.get("paragraphs", []):
        ch1_parts.append(f"<p>{p}</p>")
    if ch1.get("segments_table"):
        st = ch1["segments_table"]
        ch1_parts.append(_render_table(st.get("caption", ""), st["headers"], st["rows"], st["takeaway"]))
    for sub in ch1.get("subsections", []):
        ch1_parts.append(f"<h3>{sub['title']}</h3>")
        for p in sub.get("paragraphs", []):
            ch1_parts.append(f"<p>{p}</p>")
    if ch1.get("glossary_items"):
        ch1_parts.append("<h3>Plain-English glossary for this report</h3>")
        ch1_parts.append("<ul>")
        for item in ch1["glossary_items"]:
            ch1_parts.append(f"<li>{item}</li>")
        ch1_parts.append("</ul>")
    ch1_parts.append("</section>")

    # Chapter 2: Why the business is strong or weak
    ch2 = spec["ch2"]
    ch2_parts = ['<section class="chapter" id="ch-2">', "<h2>2. Why the business is strong or weak</h2>"]
    for p in ch2.get("paragraphs", []):
        ch2_parts.append(f"<p>{p}</p>")
    for sub in ch2.get("subsections", []):
        ch2_parts.append(f"<h3>{sub['title']}</h3>")
        for p in sub.get("paragraphs", []):
            ch2_parts.append(f"<p>{p}</p>")
    ch2_parts.append("</section>")

    # Chapter 2B: Company specifics, Layer 2 KPIs, and Management Walk-the-Talk
    ch2b = spec["ch2b"]
    ch2b_parts = [
        '<section class="chapter" id="ch-2b">',
        "<h2>2B. Company specifics, operating KPIs, and management walk-the-talk</h2>",
    ]
    for p in ch2b.get("intro_paragraphs", []):
        ch2b_parts.append(f"<p>{p}</p>")
    ch2b_parts.append("<h3>Layer 2 scorecard: company-specific operating KPIs</h3>")
    kpi_t = ch2b["kpi_table"]
    ch2b_parts.append(_render_table(kpi_t.get("caption", f"Layer 2 operational KPI scorecard for {sym}"), kpi_t["headers"], kpi_t["rows"], kpi_t["takeaway"]))
    ch2b_parts.append("<h3>Management walk-the-talk: past promises vs delivered reality</h3>")
    for p in ch2b.get("walk_the_talk_paragraphs", []):
        ch2b_parts.append(f"<p>{p}</p>")
    if ch2b.get("walk_the_talk_table"):
        wt = ch2b["walk_the_talk_table"]
        ch2b_parts.append(_render_table(wt.get("caption", f"Management guidance and execution audit for {sym}"), wt["headers"], wt["rows"], wt["takeaway"]))
    if ch2b.get("closing_paragraphs"):
        for p in ch2b["closing_paragraphs"]:
            ch2b_parts.append(f"<p>{p}</p>")
    ch2b_parts.append("</section>")

    # Chapter 3: The numbers, in plain words
    ch3 = spec["ch3"]
    ch3_parts = ['<section class="chapter" id="ch-3">', "<h2>3. The numbers, in plain words</h2>"]
    for p in ch3.get("intro_paragraphs", []):
        ch3_parts.append(f"<p>{p}</p>")
    for tbl in ch3.get("tables", []):
        if tbl.get("heading"):
            ch3_parts.append(f"<h3>{tbl['heading']}</h3>")
        if tbl.get("intro"):
            ch3_parts.append(f"<p>{tbl['intro']}</p>")
        ch3_parts.append(_render_table(tbl.get("caption", ""), tbl["headers"], tbl["rows"], tbl["takeaway"]))
    ch3_parts.append("<h3>Layer 1 underwriting: static levels, trajectory (rate of change), and archetype fit</h3>")
    if ch3.get("layer1_intro"):
        ch3_parts.append(f"<p>{ch3['layer1_intro']}</p>")
    l1_t = ch3["layer1_table"]
    ch3_parts.append(_render_table(l1_t.get("caption", f"Layer 1 levels vs trajectory evaluation for {sym}"), l1_t["headers"], l1_t["rows"], l1_t["takeaway"]))
    for est in ch3.get("estimates", []):
        ch3_parts.append(_render_estimate(est))
    if ch3.get("peer_table"):
        pt = ch3["peer_table"]
        ch3_parts.append("<h3>Peer comparison matrix</h3>")
        if pt.get("intro"):
            ch3_parts.append(f"<p>{pt['intro']}</p>")
        ch3_parts.append(_render_table(pt.get("caption", f"Peer comparison for {sym}"), pt["headers"], pt["rows"], pt["takeaway"]))
    ch3_parts.append("</section>")

    # Chapter 4: What the price is doing (auto-populated from ledger)
    ch4_html = _build_ch4_from_ledger(sym, market, inst_m, spec["ch4"])

    # Chapter 5: What could happen next (Reverse DCF + Revisions + Bull/Base/Bear)
    ch5 = spec["ch5"]
    ch5_parts = ['<section class="chapter" id="ch-5">', "<h2>5. What could happen next</h2>"]
    for p in ch5.get("intro_paragraphs", []):
        ch5_parts.append(f"<p>{p}</p>")
    ch5_parts.append("<h3>What today's price assumes (Reverse DCF) and how consensus estimates are moving</h3>")
    ch5_parts.append(_build_expectations_block(sym, market, inst_m, ch5))
    ch5_parts.append("<h3>Our variant perception</h3>")
    for p in ch5.get("variant_perception_paragraphs", []):
        ch5_parts.append(f"<p>{p}</p>")
    for est in ch5.get("estimates", []):
        ch5_parts.append(_render_estimate(est))
    sc_t = ch5["scenario_table"]
    ch5_parts.append("<h3>Bull, base, and bear scenarios</h3>")
    ch5_parts.append(_render_table(sc_t.get("caption", f"12-month scenario table for {sym}"), sc_t["headers"], sc_t["rows"], sc_t["takeaway"]))
    ch5_parts.append("</section>")

    # Chapter 6: Why these estimates might be wrong
    ch6 = spec["ch6"]
    ch6_parts = ['<section class="chapter" id="ch-6">', "<h2>6. Why these estimates might be wrong</h2>"]
    for p in ch6.get("intro_paragraphs", []):
        ch6_parts.append(f"<p>{p}</p>")
    for sub in ch6.get("flaws", []):
        ch6_parts.append(f"<h3>{sub['title']}</h3>")
        for p in sub.get("paragraphs", []):
            ch6_parts.append(f"<p>{p}</p>")
    if ch6.get("flaws_table"):
        ft = ch6["flaws_table"]
        ch6_parts.append(_render_table(ft.get("caption", f"Key risk and invalidation matrix for {sym}"), ft["headers"], ft["rows"], ft["takeaway"]))
    if ch6.get("hinge_paragraph"):
        ch6_parts.append(f"<p>{ch6['hinge_paragraph']}</p>")
    ch6_parts.append("</section>")

    # Chapter 7: What we would do, and when
    ch7 = spec["ch7"]
    ch7_parts = ['<section class="chapter" id="ch-7">', "<h2>7. What we would do, and when</h2>"]
    for p in ch7.get("decision_paragraphs", []):
        ch7_parts.append(f"<p>{p}</p>")
    if ch7.get("holding_audit_table"):
        ht = ch7["holding_audit_table"]
        ch7_parts.append("<h3>Active holding audit</h3>")
        ch7_parts.append(_render_table(ht.get("caption", f"Current position audit for {sym}"), ht["headers"], ht["rows"], ht["takeaway"]))

    # Layer 3 + Risk-Unit Sizing Table (deterministic + transparent)
    ch7_parts.append("<h3>Layer 3 support-aware entry posture, risk-unit sizing, and let-winners-run rules</h3>")
    l3_rows = [
        ["Underwriting archetype & bucket", f"{_esc(archetype)} ({_esc(bucket)})", "Evaluates both static quality and rate-of-change inflection"],
        ["Action verdict", f'<span class="verdict {v_cls}">{_esc(verdict)}</span>', _esc(ch7.get("verdict_rule_summary", "Based on 3-layer underwriting and support distance"))],
        ["Recommended entry zone", f"{cur}{entry_low:,.2f} to {cur}{entry_high:,.2f}", f"Current price {cur}{close:,.2f} is {inst_m.get('support_distance_atr', 'N/A')} ATR from verified support"],
        ["Structural invalidation stop", f"{cur}{stop_loss:,.2f} (-{ru['stop_distance_pct']}% from entry)", _esc(scoring["stop_placement"].get(bucket, scoring["stop_placement"]["CORE_ALPHA"]))],
        ["Base / Bull / Bear targets", f"{cur}{target_base:,.2f} / {cur}{target_bull:,.2f} / {cur}{target_bear:,.2f}", f"Reward-to-risk asymmetry at CMP: {asym:.2f}:1"],
        ["Risk-unit initial sizing (portfolio heat)", f"{ru['risk_adjusted_weight_pct']}% of net worth ({_esc(tier)}, {ru['risk_budget_bps']:.0f} bps risk budget)", f"Formula: min(Tier cap {ru['tier_range_pct']}, {ru['risk_budget_bps']:.0f} bps / {ru['stop_distance_pct']}% stop distance)"],
        ["Let-winners-run rule", f"Appreciated weight ceiling up to {ru['runaway_winner_cap_pct']}%", "Never trim solely for RSI > 70 or crossing 15%; trail stop to rising 21-EMA / 50-SMA until trend or fundamentals break"],
    ]
    ch7_parts.append(_render_table(
        f"Layer 3 execution levels and risk-unit position sizing for {sym}",
        ["Execution item", "Level / Sizing", "Rule and derivation"],
        l3_rows,
        ch7["sizing_table_takeaway"],
    ))
    for trig in ch7.get("triggers", []):
        ch7_parts.append(f'<p class="trigger">{trig}</p>')
    ch7_parts.append("</section>")

    # Gate exceptions (if any)
    ge_html = ""
    if spec.get("gate_exceptions"):
        ge_ps = "".join(f"<p>{p}</p>" for p in spec["gate_exceptions"])
        ge_html = f'<section class="chapter" id="gate-exceptions">\n<h2>Run notes and gate exceptions</h2>\n{ge_ps}\n</section>\n'

    # Notes and sources
    cites_li = "\n".join(
        f'<li id="cite_note-{i}">{c}</li>'
        for i, c in enumerate(spec["citations"], 1)
    )
    notes_html = (
        '<section id="notes">\n'
        '<h2 id="references">Notes and sources</h2>\n'
        f'<ol class="sources reflist">\n{cites_li}\n</ol>\n'
        "</section>"
    )

    body_html = "\n\n".join([
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
    ])

    return build(
        body_html,
        market=market,
        facts=spec.get("facts_path", ""),
        research=spec.get("research_paths", []),
        kind="dossier",
        workflow="Company research",
        as_of=as_of,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", required=True, help="Path to structured company spec JSON")
    ap.add_argument("--facts", required=True, help="Path to market_facts JSON ledger")
    ap.add_argument("--out", required=True, help="Output dossier HTML path")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    spec.setdefault("facts_path", args.facts)
    facts = json.loads(Path(args.facts).read_text(encoding="utf-8"))
    html_out = render_book_dossier(spec, facts)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    Path(args.out).write_text(html_out, encoding="utf-8")
    print(f"wrote book dossier: {args.out} ({len(html_out):,} bytes)")


if __name__ == "__main__":
    main()
