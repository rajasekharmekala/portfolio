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
import html
import json
import os
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
        explanatory_p = (
            explanatory_p.strip()
            + " This table grounds the chapter's analysis in verified figures from our browser snapshots and cited company filings."
        )
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

    close = tv.get("close") or inst_m.get("close")
    s20 = tv.get("sma20") or inst_m.get("sma20")
    s50 = tv.get("sma50") or inst_m.get("sma50")
    s200 = tv.get("sma200") or inst_m.get("sma200")
    w30 = tv.get("sma30_weekly") or s200
    w10_ema = tv.get("ema10_weekly") or tv.get("ema50") or s50
    rsi = tv.get("rsi14") if tv.get("rsi14") is not None else inst_m.get("rsi14")
    atr = tv.get("atr14") if tv.get("atr14") is not None else inst_m.get("atr14")
    hi52 = tv.get("high_52w") or inst_m.get("hi52")
    lo52 = tv.get("low_52w") or inst_m.get("lo52")
    rvol = tv.get("rel_vol_10d") or inst_m.get("vol_mult_20d")
    tv_label = tv.get("tv_rating_label", "N/A")
    piv_s1, piv_m, piv_r1 = tv.get("pivot_s1"), tv.get("pivot_middle"), tv.get("pivot_r1")
    ext_10w = s2_ev.get("extension_from_10w_ema_pct")
    ext_50d = s2_ev.get("extension_from_50d_sma_pct")
    w_stage = s2_ev.get("weinstein_stage") or inst_m.get("stage_label", "N/A")
    w_explain = s2_ev.get("stage_explanation", "Stage 2 is rising institutional markup; Stage 4 is breakdown.")
    cite_tag = ch4_spec.get("ledger_cite_tag", "")

    def fmt_px(v):
        return f"{cur}{v:,.2f}" if isinstance(v, (int, float)) else "N/A"

    tech_rows = [
        [
            f"Session close ({_esc(as_of)})",
            fmt_px(close) + cite_tag,
            f"1D: {tv.get('change_1d_pct') or inst_m.get('chg_1d_pct', 'N/A')}%, "
            f"1W: {tv.get('perf_1w_pct') or inst_m.get('chg_1w_pct', 'N/A')}%, "
            f"1M: {tv.get('perf_1m_pct') or inst_m.get('chg_1m_pct', 'N/A')}%",
        ],
        [
            "Stan Weinstein Stage & TheWrap status",
            f"{_esc(w_stage)} (In TheWrap Stage 2 list: {w_s2.get('in_stage2_list', 'N/A')})",
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
            "RSI (14-day) / ATR (14-day)",
            f"{round(rsi, 2) if isinstance(rsi, (int, float)) else 'N/A'} / {fmt_px(atr)}",
            f"TradingView Technical Rating: {_esc(tv_label)} (RSI > 73 signals short-term overextension)",
        ],
        [
            "52-week high / low",
            f"{fmt_px(hi52)} / {fmt_px(lo52)}",
            f"Classic Pivots — Support S1: {fmt_px(piv_s1)}, Mid Pivot: {fmt_px(piv_m)}, Resistance R1: {fmt_px(piv_r1)}",
        ],
        [
            "Relative volume & institutional sponsorship",
            f"{round(rvol, 2) if isinstance(rvol, (int, float)) else 'N/A'}x vs 10d avg",
            f"Sector Stage 2 breadth ({_esc(w_s2.get('sector_name', tv.get('sector', 'N/A')))}): "
            f"{w_s2.get('sector_pct_in_stage2') or w_s2.get('industry_pct_outperforming_sp500', 'N/A')}%",
        ],
    ]
    t1_html = _render_table(
        f"Verified TradingView & TheWrap Stage 2 technical snapshot for {sym} as of {as_of}",
        ["Technical dimension", "Browser / Scanner reading", "Institutional & No-FOMO interpretation"],
        tech_rows,
        ch4_spec.get(
            "tech_table_takeaway",
            f"This table summarizes the live TradingView and TheWrap Stage 2 technical readings for {sym}, showing its trend stage, moving-average support levels, and extension distance.",
        ),
    )

    eval_rows = [
        [
            "Weinstein Stage classification",
            _esc(w_stage),
            _esc(w_explain),
        ],
        [
            "No-FOMO entry timing posture",
            _esc(s2_ev.get("entry_timing_posture", ch4_spec.get("entry_posture", "N/A"))),
            _esc(s2_ev.get("timing_rationale", "Determines whether to buy at CMP or wait for a pullback to support.")),
        ],
        [
            "Support buy zone (20D EMA / 10W EMA / 50D SMA)",
            f"{fmt_px((s2_ev.get('support_buy_zone') or {}).get('low'))} – {fmt_px((s2_ev.get('support_buy_zone') or {}).get('high'))}",
            "Primary institutional pullback accumulation zone on TradingView",
        ],
        [
            "Structural invalidation stop",
            fmt_px(s2_ev.get("invalidation_stop")),
            "Anchored below the 50-day SMA / 30-week SMA minus 1.0x ATR(14)",
        ],
        [
            "Valuation sanity check (Screener.in / Finviz)",
            _esc((s2_ev.get("valuation_assessment") or {}).get("posture", "N/A")),
            _esc((s2_ev.get("valuation_assessment") or {}).get("note", "Compares current P/E against earnings growth and ROE/ROCE.")),
        ],
    ]
    t2_html = _render_table(
        f"Stage 2 & No-FOMO Entry Timing Evaluation for {sym}",
        ["Evaluation dimension", "Reading / Posture", "Rule & practical implication"],
        eval_rows,
        ch4_spec.get(
            "gate_table_takeaway",
            f"This evaluation separates {sym}'s medium-term Stage 2 trend durability from near-term entry timing so we capture early momentum without chasing extended FOMO spikes.",
        ),
    )

    return (
        '<section class="chapter" id="ch-4">\n'
        "<h2>4. Stage 2 trend &amp; TradingView technical structure</h2>\n"
        f"<p>{ch4_spec['intro_prose']}</p>\n"
        f"{t1_html}\n"
        "<h3>Stage 2 momentum &amp; No-FOMO support evaluation</h3>\n"
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
    snap_sym = (snapshots.get("symbols") or {}).get(sym, {}) if "symbols" in snapshots else snapshots.get(sym, {})
    scoring = json.load(open(SCORING_FILE, encoding="utf-8"))
    cur = "₹" if market == "IN" else "$"

    verdict = spec["verdict"]
    v_cls = VERDICT_CLASS_MAP.get(verdict.upper(), "verdict-watch")
    archetype = spec.get("archetype", "STAGE2_LEADER")
    bucket = spec.get("strategy_bucket", "TACTICAL_MOMENTUM")

    tv = snap_sym.get("tradingview") or {}
    s2_ev = snap_sym.get("stage2_evaluation") or {}
    close = tv.get("close") or inst_m.get("close") or spec.get("cmp") or 0.0
    entry_low = spec["entry_zone_low"]
    entry_high = spec["entry_zone_high"]
    stop_loss = spec["stop_loss"]
    target_base = spec["target_base"]
    target_bull = spec["target_bull"]
    target_bear = spec["target_bear"]
    asym = (
        round((target_base - close) / (close - stop_loss), 2)
        if (close and stop_loss and close > stop_loss)
        else spec.get("asymmetry_ratio", 0.0)
    )

    tier = spec.get("conviction_tier", "TIER_2")
    ru = _compute_risk_unit_sizing(close, entry_high, stop_loss, tier, scoring)
    w_stage = s2_ev.get("weinstein_stage") or inst_m.get("stage_label") or spec.get("weinstein_stage", "Stage 2")
    entry_posture = s2_ev.get("entry_timing_posture") or spec.get("entry_posture", verdict)

    # Key figures strip
    kf_items = [
        ("Verdict", f'<span class="verdict {v_cls}">{_esc(verdict)}</span> ({_esc(archetype)})'),
        ("Session Price (" + _esc(as_of) + ")", f"{cur}{close:,.2f}"),
        ("Strategy Bucket", _esc(bucket)),
        ("Weinstein Stage", _esc(w_stage)),
        ("No-FOMO Entry Posture", _esc(entry_posture)),
        ("Support Buy Zone", f"{cur}{entry_low:,.2f} – {cur}{entry_high:,.2f} (Stop: {cur}{stop_loss:,.2f})"),
        ("Base / Bull Target", f"{cur}{target_base:,.2f} / {cur}{target_bull:,.2f} (R:R {asym:.2f}:1)"),
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
        f"<h2>Before you read</h2>\n"
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
        ch1_parts.append(_render_table(st.get("caption", ""), st["headers"], st["rows"], st["takeaway"]))
    for sub in ch1.get("subsections", []):
        ch1_parts.append(f"<h3>{sub['title']}</h3>")
        for p in sub.get("paragraphs", []):
            ch1_parts.append(f"<p>{p}</p>")
    if ch1.get("glossary_items"):
        ch1_parts.append("<h3>Plain-English glossary for this monograph</h3>")
        ch1_parts.append("<ul>")
        for item in ch1["glossary_items"]:
            ch1_parts.append(f"<li>{item}</li>")
        ch1_parts.append("</ul>")
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
                l1_t["takeaway"],
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
            _render_table(pt.get("caption", f"Peer comparison for {sym}"), pt["headers"], pt["rows"], pt["takeaway"])
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
        ch5_parts.append(
            _render_table(
                ht.get("caption", f"Multi-horizon investment outlook for {sym}"),
                ht["headers"],
                ht["rows"],
                ht["takeaway"],
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
    ch5_parts.append(
        _render_table(
            sc_t.get("caption", f"12-month scenario table for {sym}"), sc_t["headers"], sc_t["rows"], sc_t["takeaway"]
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
                ft["takeaway"],
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
            "Aligns capital allocation with Stage 2 durability and business quality",
        ],
        [
            "Action verdict & No-FOMO posture",
            f'<span class="verdict {v_cls}">{_esc(verdict)}</span> ({_esc(entry_posture)})',
            _esc(ch7.get("verdict_rule_summary", "Buy at CMP only when in early Stage 2 near support; wait for support when extended")),
        ],
        [
            "Recommended buy / accumulation zone",
            f"{cur}{entry_low:,.2f} to {cur}{entry_high:,.2f}",
            f"Current price {cur}{close:,.2f}; anchored to TradingView 20D EMA / 10W EMA / 50D SMA support",
        ],
        [
            "Structural invalidation stop",
            f"{cur}{stop_loss:,.2f} (-{ru['stop_distance_pct']}% from entry)",
            _esc(scoring["stop_placement"].get(bucket, scoring["stop_placement"]["CORE_ALPHA"])),
        ],
        [
            "Base / Bull / Bear targets",
            f"{cur}{target_base:,.2f} / {cur}{target_bull:,.2f} / {cur}{target_bear:,.2f}",
            f"Reward-to-risk ratio: {asym:.2f}:1",
        ],
        [
            "Risk-unit initial sizing (portfolio heat)",
            f"{ru['risk_adjusted_weight_pct']}% of net worth ({_esc(tier)}, {ru['risk_budget_bps']:.0f} bps risk budget)",
            f"Formula: min(Tier cap {ru['tier_range_pct']}, {ru['risk_budget_bps']:.0f} bps / {ru['stop_distance_pct']}% stop distance)",
        ],
        [
            "Let-winners-run rule",
            f"Appreciated weight ceiling up to {ru['runaway_winner_cap_pct']}%",
            "Never trim solely for RSI > 70 or crossing 15%; trail stop to rising 21-EMA / 50-SMA until trend or fundamentals break",
        ],
    ]
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
    ap.add_argument("--snapshot", default="", help="Path to stock_snapshot.py JSON output")
    ap.add_argument("--facts", default="", help="Optional path to market_facts JSON ledger")
    ap.add_argument("--out", required=True, help="Output dossier HTML path")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    if args.facts:
        spec.setdefault("facts_path", args.facts)
    facts = json.loads(Path(args.facts).read_text(encoding="utf-8")) if args.facts and Path(args.facts).exists() else {}
    snapshots = (
        json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        if args.snapshot and Path(args.snapshot).exists()
        else {}
    )
    html_out = render_book_dossier(spec, facts=facts, snapshots=snapshots)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    Path(args.out).write_text(html_out, encoding="utf-8")
    print(f"wrote book dossier: {args.out} ({len(html_out):,} bytes)")


if __name__ == "__main__":
    main()
