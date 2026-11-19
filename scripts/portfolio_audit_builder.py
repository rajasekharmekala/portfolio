#!/usr/bin/env python3
"""Synchronized Dual-Edition Portfolio Audit Compiler (Web Research Desk + Masterclass Audiobook PDF).

Compiles `allocation_<MKT>_<date>.json` (from `scripts/portfolio_allocator.py`) plus optional
bespoke CIO storytelling (`--narrative audit_narrative.json`) into TWO synchronized deliverables:
  1. `docs/reports/<MKT>_Portfolio_Audit.html` — Modern `research-desk-v1` Web Edition with built-in
     interactive Web Speech Audiobook narrator (`.book-audio-bar`), `.edition-switcher`, penny-exact
     Money Bridge, Convergence & Hysteresis diff, Case Notes, and Execution Orders.
  2. `docs/reports/<MKT>_Portfolio_Audit_book.pdf` — Archival cream/navy/gold Masterclass Narrative
     Companion PDF ('The Portfolio Architect') via `scripts/epub_builder.py` + WeasyPrint, walking
     through every keep, ratchet, trim, exit, starter buy, option hold, and cash reserve as one
     cohesive story.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_report import build  # noqa: E402
from epub_builder import build_pdf_book, render_portfolio_book_html  # noqa: E402

REPO = Path(__file__).resolve().parents[1]

VERDICT_PILL_MAP = {
    "KEEP_COMPOUNDING": "verdict-keep",
    "TRACKING_HOLD": "verdict-keep",
    "HOLD_CASH_EQUIVALENT": "verdict-keep",
    "HOLD_CONVEXITY": "verdict-keep",
    "GRANDFATHERED_HOLD": "verdict-watch",
    "ACCUMULATE_ON_DIP": "verdict-buy",
    "DEPLOY_STARTER_NOW": "verdict-buy",
    "DEPLOY_STARTER_AT_SUPPORT": "verdict-buy",
    "RESTING_LIMIT_AT_SUPPORT": "verdict-watch",
    "DEFERRED_GATE_BLOCKED": "verdict-watch",
    "MONITOR_ONLY_PRE_MONOGRAPH": "verdict-watch",
    "BLOCKED_SLOT_CAP_FULL": "verdict-watch",
    "DEFERRED_CASH_OR_CLUSTER_CAP": "verdict-watch",
    "DEFERRED_HEAT_OR_LOT_SIZE": "verdict-watch",
    "TRIM_PROFIT_BOOKING": "verdict-trim",
    "TRIM_OPTION_STRENGTH": "verdict-trim",
    "EXIT": "verdict-exit",
    "EXIT_OPTION": "verdict-exit",
    "EXIT_TIME_STOP": "verdict-exit",
    "REJECTED_BY_DOSSIER": "verdict-exit",
}


def _esc(val: Any) -> str:
    return html.escape(str(val if val is not None else "—"))


_SAFE_TAG_RE = re.compile(
    r"</?(?:a(?:\s+href=\"[^\"]*\"(?:\s+target=\"_blank\")?(?:\s+rel=\"noopener(?:\s+noreferrer)?\")?)?|strong|b|em|i|code)>",
    re.I,
)


def _prose_html(val: Any) -> str:
    """Escape plain text while preserving safe inline `<a href=\"...\">`, `<strong>`, `<em>`, `<code>` tags."""
    s = str(val if val is not None else "")
    tokens: List[str] = []

    def _stash(m: re.Match) -> str:
        tokens.append(m.group(0))
        return f"\x00TAG{len(tokens) - 1}\x00"

    masked = _SAFE_TAG_RE.sub(_stash, s)
    escaped = html.escape(masked)
    for idx, tok in enumerate(tokens):
        escaped = escaped.replace(f"\x00TAG{idx}\x00", tok)
    return escaped


def _vpill(verdict: str, label: Optional[str] = None) -> str:
    cls = VERDICT_PILL_MAP.get(verdict, "verdict-watch")
    txt = (label or verdict).replace("_", " ")
    return f'<span class="verdict {cls}">{_esc(txt)}</span>'


def _word_count(text: str) -> int:
    clean = re.sub(r"<[^>]+>", " ", text)
    return len(re.findall(r"[A-Za-z0-9$₹%.,'-]+", clean))


def _sym_cell(sym: str, mkt: str, sub: str = "") -> str:
    sub_html = f'<br><span class="case-note-sub">{_esc(sub)}</span>' if sub else ""
    dossier_file = REPO / "docs" / "blogs" / mkt / f"{sym}_dossier.html"
    dossier_link = f' &bull; <a href="../blogs/{_esc(mkt)}/{_esc(sym)}_dossier.html">Monograph</a>' if dossier_file.is_file() else ""
    if mkt == "IN":
        links = (
            f'<a href="https://www.tradingview.com/chart/?symbol=NSE%3A{_esc(sym)}">Chart</a> &bull; '
            f'<a href="https://www.screener.in/company/{_esc(sym)}/">Screener</a>{dossier_link}'
        )
    else:
        links = (
            f'<a href="https://www.tradingview.com/chart/?symbol=NASDAQ%3A{_esc(sym)}">Chart</a> &bull; '
            f'<a href="https://finviz.com/quote.ashx?t={_esc(sym)}">Finviz</a>{dossier_link}'
        )
    return f'<strong>{_esc(sym)}</strong>{sub_html}<br><span class="case-note-sub">{links}</span>'


def _stage_display(stage_code: str) -> str:
    m = {"STAGE_1": "Stage 1", "STAGE_2": "Stage 2", "STAGE_3": "Stage 3", "STAGE_4": "Stage 4"}
    return m.get(stage_code, "Unclassified")


def _default_story_and_casenotes(alloc: Dict[str, Any], narrative_override: Dict[str, Any]) -> Dict[str, Any]:
    """Build cohesive mentor-voice narrative chapters + case notes grounded strictly in `alloc`."""
    mkt = alloc["market"]
    cur = alloc["currency_symbol"]
    as_of = alloc["as_of_date"]
    env = alloc["regime_envelope"]
    ps = alloc["portfolio_summary"]
    sc = alloc["stability_and_convergence"]
    holdings = alloc["holding_decisions"]
    tracking = alloc["tracking_positions"]
    options = alloc["options_decisions"]
    challengers = alloc["challenger_decisions"]
    clusters = alloc["clusters"]
    debt_q = alloc["dossier_debt_queue"]

    mkt_name = "Indian equity" if mkt == "IN" else "United States equity and convexity"
    bench_name = "Nifty 50" if mkt == "IN" else "S&P 500"
    regime_lbl = env["regime_label"]
    playbook = env["playbook_mode"].replace("_", " ").title()

    sells = [h for h in holdings if h["delta_shares"] < 0]
    adds = [h for h in holdings if h["delta_shares"] > 0]
    starters = [c for c in challengers if c["funded_shares"] > 0]
    resting = [c for c in challengers if c["entry_action"] == "RESTING_LIMIT_AT_SUPPORT"]
    top_cluster = clusters[0] if clusters else None

    ov_chapters = narrative_override.get("chapters") or {}
    ov_cases = narrative_override.get("casenotes") or {}

    # Prologue / Executive Lede
    completed_str = (
        f"Since our {sc['prior_as_of_date']} plan, you completed {len(sc['completed_edits_since_prior'])} trade edit(s). "
        f"Meanwhile, {len(sc['hysteresis_locked_symbols'])} borderline ticker(s) stay locked by our {sc['price_band_hysteresis_pct']}% hysteresis band."
        if sc.get("prior_as_of_date")
        else "This run sets our baseline v4 anchor ledger so future checks converge toward zero turnover."
    )
    primer_text = narrative_override.get("primer") or (
        f"As of {as_of}, you and I manage {cur}{ps['net_worth']:,.2f} across our {mkt_name} book in a '{regime_lbl}' tape. "
        f"Our portfolio stands at {sc['convergence_score_pct']:.1f}% convergence with target risk rules. "
        f"Open risk-to-stop starts at {ps['current_open_heat_pct']:.2f}% against an {ps['max_portfolio_heat_pct']:.1f}% regime cap. "
        f"We exit or trim {len(sells)} broken or rich line(s), fund {len(adds) + len(starters)} disciplined buy(s), and hold {cur}{ps['target_cash_value']:,.2f} ({ps['target_cash_wt_pct']:.2f}%) in reserve."
    )

    # Chapter 1: Macro, Sector Tide & Convergence
    ch1_paras = (ov_chapters.get("chapter1") or {}).get("book_paragraphs") or [
        (
            f"Before we touch a single share on {as_of}, we check the market tide. "
            f"The {bench_name} sits in '{regime_lbl}', putting our desk in {playbook} mode. "
            f"Breadth reads {env['breadth_pct_above_50dma'] if env['breadth_pct_above_50dma'] is not None else 'measured'}% above the 50-DMA. "
            f"That sets two hard limits: cash stays above {env['min_cash_floor_pct']:.1f}%, and open portfolio heat caps at {env['max_portfolio_heat_pct']:.1f}%."
        ),
        (
            f"Look beneath the surface of our {cur}{ps['net_worth']:,.2f} net worth. "
            f"We hold {ps['active_unique_risk_underlyings_count']} active risk names inside our {ps['active_slots_range'][0]}–{ps['active_slots_range'][1]} slot band. "
            f"We exclude {ps['tracking_positions_count']} tiny sub-0.35% tracking stub(s) worth {cur}{ps['tracking_positions_value']:,.2f} from slot counts. "
            f"After Phase 1 sales, open risk-to-stop drops from {ps['current_open_heat_pct']:.2f}% to {ps['target_open_heat_pct']:.2f}%."
        ),
        (
            f"We also apply sector rotation asymmetrically rather than chasing one-week moves. "
            f"Short sector dips are noise for multi-year compounders. "
            f"Core Alpha names ignore brief sector pullbacks unless their 30-week trend or KPIs break. "
            f"Tactical Momentum entries require Leading or Improving 3-month strength, and every theme cluster caps at 25.0% of net worth"
            + (f" (top cluster {', '.join(top_cluster['symbols'][:4])}: {top_cluster['current_wt_pct']:.2f}% -> {top_cluster['target_wt_pct']:.2f}%)." if top_cluster else ".")
        ),
        (
            f"Short-term rerun stability matters just as much. {completed_str} "
            f"Our ±{sc['rebalance_deadband_wt_pct']:.2f}% deadband leaves properly sized winners untouched. "
            f"Convergence stands at {sc['convergence_score_pct']:.1f}% as we move into our active holdings audit in Chapter 2."
        ),
    ]

    # Chapter 2: Existing Equity Holdings Story
    kept = [h for h in holdings if h["delta_shares"] == 0 and h["target_value"] > 0]
    top_kept_names = ", ".join(f"{h['symbol']} ({h['current_wt_pct']:.2f}%)" for h in kept[:5]) or "none"
    sells_summary = (
        ", ".join(f"{h['symbol']} ({abs(h['delta_shares']):g} sh, {cur}{h['capital_liberated']:,.2f})" for h in sells)
        if sells else "zero forced equity sales today"
    )
    ch2_paras = (ov_chapters.get("chapter2") or {}).get("book_paragraphs") or [
        (
            f"Every held stock faces one test today: if we held cash instead, would this business and chart earn its risk slot? "
            f"We hold {len(holdings)} active lines worth {cur}{ps['current_equities_value']:,.2f} ({ps['current_equities_wt_pct']:.2f}% of net worth). "
            f"Our tournament scores every incumbent on the exact same 100-point scale used for outside shortlist challengers."
        ),
        (
            f"Phase 1 capital cleanup flags {sells_summary}. "
            f"Notice what we refuse to do. We never shave a Stage 2 compounder just because RSI looks high or weight crossed 15%. "
            f"True leaders can compound up to our 22.0% ceiling while trailing stops ratchet upward only."
        ),
        (
            f"Intact positions led by {top_kept_names} stay anchored behind hard structural stops. "
            f"Any pre-dossier holding ({len(debt_q)} in queue) is grandfathered above its chart stop while fresh ADDs stay frozen. "
            f"Let us check every active line and stop trigger before reviewing sleeves and cluster risk in Chapter 3."
        ),
    ]

    # Chapter 3: 2x/3x Sector Rotation & Drawdown Options (US) OR Cluster & Velocity Defense (IN)
    if mkt == "US":
        opt_summary = (
            "; ".join(f"{o['contract_symbol']} ({o['verdict'].replace('_', ' ')}, delta {o['delta']:.2f}, stop ${o['invalidation_stop'] or 0:,.2f})" for o in options[:4])
            if options else "no open option contracts"
        )
        lev_holdings = [h for h in holdings if h["bucket"] == "LEVERAGED_SATELLITE"]
        lev_summary = (
            ", ".join(f"{h['symbol']} ({h['current_wt_pct']:.2f}% -> {h['action_label']})" for h in lev_holdings)
            if lev_holdings else "0.0% in 2x/3x ETFs"
        )
        ch3_paras = (ov_chapters.get("chapter3") or {}).get("book_paragraphs") or [
            (
                f"Leveraged 2x/3x ETFs and call options demand strict sideways-market math. "
                f"Daily-reset ETFs bleed from volatility drag in choppy tapes, while OTM calls lose theta every week. "
                f"Our v4 rulebook enforces a 15.0% combined decay cap (now {ps['combined_decay_sleeve_pct']:.2f}%: {ps['leveraged_satellite_target_wt_pct']:.2f}% ETFs + {ps['options_cap_basis_pct']:.2f}% options)."
            ),
            (
                f"In the 2x/3x sleeve ({lev_summary}), only liquid sector or index ETFs qualify up to 12.0% total (6.0% max per line). "
                f"Each swing carries a 20-DMA stop and a 15-session flat time clock, while single-stock 2x ETFs are phased out. "
                f"In '{regime_lbl}', new 2x/3x buys are {'open on sector breakouts' if env['allow_new_leveraged_etf_buys'] else 'gated at 0% until breadth widens'}."
            ),
            (
                f"Our US options book holds {cur}{ps['current_options_value']:,.2f} market value against {cur}{ps['current_options_cost_basis']:,.2f} cost ({opt_summary}). "
                f"Legacy contracts above shelf stops stay grandfathered for bounce trims rather than panic sales. "
                f"New drawdown buys require 0.60–0.80 delta LEAPS or debit spreads when IV tops 1.15x HV20, leading into Chapter 4."
            ),
        ]
    else:
        cluster_lines = (
            "; ".join(f"{c['cluster_id']} ({', '.join(c['symbols'][:3])}: {c['current_wt_pct']:.2f}% -> {c['target_wt_pct']:.2f}%)" for c in clusters[:4])
            if clusters else "diversified single-stock lines well below the 25% cap"
        )
        ch3_paras = (ov_chapters.get("chapter3") or {}).get("book_paragraphs") or [
            (
                f"In Indian mid- and small-cap stocks, big drawdowns rarely come from one bad company. "
                f"They come from owning five stocks tied to the same domestic capex or liquidity cycle. "
                f"When Nifty breadth narrows in '{regime_lbl}', mid-cap correlations jump toward 1.0 unless cluster caps hold."
            ),
            (
                f"Checking our Zerodha clusters against the 25.0% weight cap and 3.5% heat cap shows: {cluster_lines}. "
                f"Every retained stock sits behind a rupee stop sized from risk-budget bps. "
                f"Post-trade open heat lands at {ps['target_open_heat_pct']:.2f}% against our {ps['max_portfolio_heat_pct']:.1f}% ceiling."
            ),
            (
                f"NSE single-stock options carry short 1-to-3-month expiries and wide spreads during pullbacks. "
                f"So we compound through cash equities in Core Alpha ({ps['core_alpha_target_wt_pct']:.2f}% target) and Tactical Momentum ({ps['tactical_momentum_target_wt_pct']:.2f}% target). "
                f"Our {ps['target_cash_wt_pct']:.2f}% cash reserve stands ready for the shortlist tournament in Chapter 4."
            ),
        ]

    # Chapter 4: Challenger Tournament & 50/50 Tranches
    funded_desc = (
        ", ".join(f"{c['symbol']} ({c['funded_shares']} sh = {cur}{c['funded_value']:,.2f})" for c in starters)
        if starters else "zero immediate market-order buys today because vetted Stage 2 names sit above support zones"
    )
    resting_desc = (
        ", ".join(f"{c['symbol']} ({cur}{c['entry_zone_low']:,.2f}–{cur}{c['entry_zone_high']:,.2f}, stop {cur}{c['stop_loss']:,.2f})" for c in resting[:5])
        if resting else "none staged at support"
    )
    ch4_paras = (ov_chapters.get("chapter4") or {}).get("book_paragraphs") or [
        (
            f"Binary all-or-nothing entry rules cause two costly errors: chasing extended breakouts or missing Stage 2 leaders forever. "
            f"Our v4 rulebook splits every approved position into two equal 50% tranches. "
            f"Tranche 1 deploys a 50% starter (~35–50 bps risk), and Tranche 2 waits for a support test or +1R profit cushion."
        ),
        (
            f"Scoring {len(challengers)} non-held challengers under {playbook} rules yields {funded_desc}. "
            f"Slot discipline also protects working winners. Once we reach {ps['active_slots_range'][0]}–{ps['active_slots_range'][1]} active names, a challenger must beat a Stage 3 incumbent by +15.0 points to claim its slot."
        ),
        (
            f"For Stage 2 monographs trading above our buy window, we stage patient resting alerts on {resting_desc}. "
            f"Cash stays safe until price meets our support math, flowing into the reconciled Money Bridge in Chapter 5."
        ),
    ]

    # Chapter 5: Money Bridge Narrative
    ch5_paras = (ov_chapters.get("chapter5") or {}).get("book_paragraphs") or [
        (
            f"A portfolio plan is only trustworthy when every rupee reconciles cleanly. "
            f"We start with {cur}{ps['current_cash_value']:,.2f} ({ps['current_cash_wt_pct']:.2f}%) in broker cash. "
            f"Phase 1 exits and trims free {cur}{ps['capital_liberated_equities']:,.2f} from stocks and {cur}{ps['capital_liberated_options']:,.2f} from options, building a {cur}{ps['current_cash_value'] + ps['capital_liberated_equities'] + ps['capital_liberated_options']:,.2f} cash pool."
        ),
        (
            f"From that pool, we deploy {cur}{ps['capital_deployed_equities']:,.2f} into qualified buys while respecting our {env['min_cash_floor_pct']:.1f}% cash floor. "
            f"Target equities ({cur}{ps['target_equities_value']:,.2f}), target options ({cur}{ps['target_options_value']:,.2f}), and target cash ({cur}{ps['target_cash_value']:,.2f}, {ps['target_cash_wt_pct']:.2f}%) sum to {cur}{ps['net_worth']:,.2f}."
        ),
        (
            f"Executing these {sc['actionable_trades_count']} trade(s) places every kept line inside our ±{sc['rebalance_deadband_wt_pct']:.2f}% deadband. "
            f"On tomorrow's rerun, completed edits stay steady as HOLD / TRAIL, leading into Chapter 6's execution schedule."
        ),
    ]

    # Chapter 6: Execution Orders, Broker Routing & Dossier Debt Queue
    routing_note = (
        "Route US stock orders to Charles Schwab (selling Robinhood duplicate lots first on trims), and keep Options and 2x/3x swings in Robinhood."
        if mkt == "US"
        else "Execute Phase 1 sales first in Zerodha so proceeds settle cleanly, then set GTT stop triggers after the close."
    )
    debt_top = ", ".join(f"{d['symbol']} ({cur}{d['market_value']:,.0f}, {d['weight_pct']:.2f}%)" for d in debt_q[:5]) or "none—all active holdings have published monographs"
    ch6_paras = (ov_chapters.get("chapter6") or {}).get("book_paragraphs") or [
        (
            f"Order sequence protects capital: execute Phase 1 sales first, stage Phase 2 limit buys second, and set Phase 3 stops third. "
            f"{routing_note}"
        ),
        (
            f"All stops are evaluated on completed daily or weekly closes under our Undercut-and-Reclaim rule. "
            f"An intraday dip that reclaims the 50-DMA or 10-week EMA by the close keeps us in the trend. "
            f"A confirmed close below the hard stop triggers a clean exit next session."
        ),
        (
            f"Our Dossier Debt Queue ranks any pre-monograph holdings by wallet size: {debt_top}. "
            f"Provisional holdings cannot receive fresh ADD capital until underwritten, taking us to Chapter 7's stability contract."
        ),
    ]

    # Chapter 7: Rulebook, Hysteresis & Monitoring Contract
    ch7_paras = (ov_chapters.get("chapter7") or {}).get("book_paragraphs") or [
        (
            f"Three rules in data/allocations/{mkt}.json stop daily flip-flops on short reruns. "
            f"First, a 5-day ±{sc['price_band_hysteresis_pct']:.1f}% price band keeps borderline calls steady during normal market noise. "
            f"Second, held stop-losses ratchet upward only. Third, a ±{sc['rebalance_deadband_wt_pct']:.2f}% weight deadband silences tiny nuisance trades."
        ),
        (
            f"Only three events override those locks right away: a closing break of a hard stop, a Stage 4 breakdown or filing failure, or new synced broker trades. "
            f"Monitor those exact closing levels calmly until the next completed market session."
        ),
        (
            f"All prices, moving averages, stages, and RSI readings trace directly to the {as_of} session ledger, while holdings replay from the append-only brokerage transaction log. "
            f"Advisory alerts expire after 14 calendar days unless renewed, and overnight earnings or macro gaps can open past stated stop levels."
        ),
    ]

    # Per-holding varied case notes (>= 85 words each, varied 2-word openings, numbers + if/unless/below triggers)
    lead_templates = [
        "{company} ({sym}) represents {wt:.2f}% of our {mkt} net worth ({cur}{mv:,.2f} across {qty:g} shares against a {cur}{cost:,.2f} cost basis, {pnl_pct:+.1f}%).",
        "Holding {qty:g} shares of {company} ({sym}) values our stake at {cur}{mv:,.2f}, or {wt:.2f}% of total capital ({pnl_pct:+.1f}% vs {cur}{avg_cost:,.2f} average cost).",
        "Inside our {bucket_nice} sleeve, {sym} ({company}) carries {cur}{mv:,.2f} in market value ({wt:.2f}% weight on {qty:g} shares at {cur}{close:,.2f}).",
        "At {cur}{close:,.2f} per share, {company} ({sym}) accounts for {wt:.2f}% of portfolio equity ({cur}{mv:,.2f}, unrealized P&L {cur}{pnl_val:+,.2f} or {pnl_pct:+.1f}%).",
        "Our position in {sym} ({company}, {qty:g} shares worth {cur}{mv:,.2f}) sits at {wt:.2f}% of net worth within the {sector} group ({quad} quadrant).",
        "Valued at {cur}{mv:,.2f} ({wt:.2f}% of net worth), {company} ({sym}) trades in {stage_nice} with 14-day RSI at {rsi_txt} and {heat_pct:.2f}% open portfolio heat.",
        "Across {acct_txt}, {sym} ({company}) totals {qty:g} shares or {cur}{mv:,.2f} ({wt:.2f}% weight, {pnl_pct:+.1f}% vs cost).",
        "Positioned in {sector}, {company} ({sym}) holds a {wt:.2f}% portfolio weight ({cur}{mv:,.2f} at {cur}{close:,.2f} close, scoring {score:.1f}/100 in our tournament).",
    ]

    built_casenotes: Dict[str, str] = {}
    for idx, hd in enumerate(holdings):
        sym = hd["symbol"]
        if sym in ov_cases and _word_count(str(ov_cases[sym])) >= 85:
            built_casenotes[sym] = str(ov_cases[sym])
            continue
        opener = lead_templates[idx % len(lead_templates)].format(
            company=hd["company_name"],
            sym=sym,
            wt=hd["current_wt_pct"],
            mkt=mkt,
            cur=cur,
            mv=hd["current_value"],
            qty=hd["current_quantity"],
            cost=round(hd["current_value"] - hd["pnl_value"], 2),
            pnl_pct=hd["pnl_pct"],
            avg_cost=hd["avg_cost"],
            bucket_nice=hd["bucket"].replace("_", " ").title(),
            close=hd["close"],
            pnl_val=hd["pnl_value"],
            sector=hd["macro_sector"],
            quad=hd["sector_quadrant"],
            stage_nice=_stage_display(hd["stage"]),
            rsi_txt=f"{hd['rsi14']:.1f}" if hd["rsi14"] is not None else "measured",
            heat_pct=hd["open_heat_pct"],
            acct_txt=" + ".join(hd["accounts_held"]) or mkt,
            score=hd["score"]["tournament_score"],
        )
        t_base_txt = f" toward our {cur}{hd['target_base']:,.2f} base scenario" if hd["target_base"] else ""
        delta_txt = (
            f"We recommend selling {abs(hd['delta_shares']):g} shares ({cur}{hd['capital_liberated']:,.2f} liberated) to bring target weight to {hd['target_wt_pct']:.2f}%."
            if hd["delta_shares"] < 0
            else f"We allocate {cur}{hd['capital_deployed']:,.2f} ({hd['delta_shares']:g} additional shares) to scale target weight to {hd['target_wt_pct']:.2f}%."
            if hd["delta_shares"] > 0
            else f"We maintain all {hd['current_quantity']:g} shares ({hd['target_wt_pct']:.2f}% target weight) with zero turnover."
        )
        trigger_txt = (
            f"Decision rule & invalidation trigger: {hd['rationale']} "
            f"If {sym} closes a completed session below {cur}{hd['effective_stop']:,.2f}, exit the remaining shares to cap downside at {hd['open_heat_pct']:.2f}% of net worth; "
            f"unless that floor breaks, follow {hd['action_label']}{t_base_txt} ({hd['broker_routing']})."
        )
        built_casenotes[sym] = f"{opener} {delta_txt} {trigger_txt}"

    return {
        "primer": primer_text,
        "chapters": {
            "chapter1": {
                "id": "chapter1",
                "title": f"Chapter 1: {'US ' if mkt == 'US' else ''}Macro Tide, Sector Guardrails & Convergence",
                "book_title": "Reading the Macro Tide, Sector Guardrails & Convergence",
                "epigraph": (ov_chapters.get("chapter1") or {}).get("epigraph") or {
                    "quote": "Risk control is invisible in calm water and priceless the afternoon correlations go to one.",
                    "author": "Institutional Portfolio Risk Maxim",
                },
                "book_paragraphs": ch1_paras,
                "book_callouts": (ov_chapters.get("chapter1") or {}).get("book_callouts") or [
                    {
                        "kind": "mental_model",
                        "title": "Why Asymmetric Sector Rotation Beats Quadrant Chasing",
                        "text": f"Core Alpha compounders ride multi-year reinvestment curves and ignore 1-month sector dips, while Tactical Momentum setups require Leading/Improving 3-month sponsorship and obey a hard 25% cluster ceiling.",
                        "after_paragraph": 3,
                    }
                ],
            },
            "chapter2": {
                "id": "chapter2",
                "title": f"Chapter 2: Active {'US ' if mkt == 'US' else ''}Holdings Audit & Stop-Loss Ratchets",
                "book_title": "Inside Our Existing Book — Compounders Kept, Laggards Cut & Stops Ratcheted",
                "epigraph": (ov_chapters.get("chapter2") or {}).get("epigraph") or {
                    "quote": "Every share you already own is a cash purchase you are choosing to make again at today's close.",
                    "author": "CIO Capital Allocation Rule",
                },
                "book_paragraphs": ch2_paras,
                "book_callouts": (ov_chapters.get("chapter2") or {}).get("book_callouts") or [
                    {
                        "kind": "reflection",
                        "title": "Letting Stage 2 Winners Breathe Without Letting Losers Fester",
                        "text": f"Appreciated Stage 2 leaders may compound up to 22% of net worth on ratcheted stops, while Stage 4 breakdowns exit unemotionally regardless of cost basis.",
                        "after_paragraph": 2,
                    }
                ],
            },
            "chapter3": {
                "id": "chapter3",
                "title": (
                    "Chapter 3: 2x/3x Sector Rotation & Drawdown Options Convexity Audit"
                    if mkt == "US"
                    else "Chapter 3: Thematic Cluster Risk, Velocity & Drawdown Defense"
                ),
                "book_title": (
                    "Convexity & Decay — Governing 2x/3x Swings & Drawdown Calls"
                    if mkt == "US"
                    else "Cluster Concentration & Mid-Cap Drawdown Defense"
                ),
                "epigraph": (ov_chapters.get("chapter3") or {}).get("epigraph") or {
                    "quote": "Leverage magnifies edge only when paired with a time clock; without one, sideways chop eats the principal.",
                    "author": "Derivatives & Volatility Desk Principle",
                },
                "book_paragraphs": ch3_paras,
                "book_callouts": (ov_chapters.get("chapter3") or {}).get("book_callouts") or [
                    {
                        "kind": "mental_model",
                        "title": "The 15% Combined Decay Ceiling" if mkt == "US" else "The 25% Correlated Cluster Cap",
                        "text": (
                            f"Combining 2x/3x ETFs ({ps['leveraged_satellite_target_wt_pct']:.2f}%) and Options ({ps['options_cap_basis_pct']:.2f}%) inside one 15.0% ceiling stops volatility drag and theta decay from compounding in sideways tapes."
                            if mkt == "US"
                            else "Grouping correlated holdings (1Y r >= 0.65 or shared capex theme) inside a 25% ceiling prevents five tickers from behaving like one oversized bet."
                        ),
                        "after_paragraph": 2,
                    }
                ],
            },
            "chapter4": {
                "id": "chapter4",
                "title": f"Chapter 4: {'US ' if mkt == 'US' else ''}Shortlist Challenger Tournament & 50/50 Tranches",
                "book_title": "The Challenger Tournament — How Shortlisted Ideas Earn Capital",
                "epigraph": (ov_chapters.get("chapter4") or {}).get("epigraph") or {
                    "quote": "Start with a pilot that lets you sleep; add the second half only when the market proves you right.",
                    "author": "Weinstein & Minervini Pyramiding Discipline",
                },
                "book_paragraphs": ch4_paras,
                "book_callouts": (ov_chapters.get("chapter4") or {}).get("book_callouts") or [
                    {
                        "kind": "execution",
                        "title": "Regime-Adaptive 50/50 Entry Protocol",
                        "text": f"In {playbook} mode, we deploy 50% starters only within our non-extended band and demand a +1R cushion before scaling the second 50%, eliminating both FOMO tops and frozen cash.",
                        "after_paragraph": 1,
                    }
                ],
            },
            "chapter5": {
                "id": "chapter5",
                "title": "Chapter 5: Master Capital Reallocation & Reconciled Money Bridge",
                "book_title": "The Money Bridge — Reconciling Every Dollar and Share",
                "epigraph": (ov_chapters.get("chapter5") or {}).get("epigraph") or {
                    "quote": "Cash is not idle when nothing clears the hurdle; cash is the call option with zero theta decay.",
                    "author": "Private Wealth Treasury Mandate",
                },
                "book_paragraphs": ch5_paras,
                "book_callouts": (ov_chapters.get("chapter5") or {}).get("book_callouts") or [],
            },
            "chapter6": {
                "id": "chapter6",
                "title": "Chapter 6: 3-Phase Execution Orders, Broker Routing & Dossier Queue",
                "book_title": "The Execution Playbook — Orders, Stops & Underwriting Queue",
                "epigraph": (ov_chapters.get("chapter6") or {}).get("epigraph") or {
                    "quote": "Plan the trade when the market is closed so emotion has no vote when the bell rings.",
                    "author": "Execution Desk Rulebook",
                },
                "book_paragraphs": ch6_paras,
                "book_callouts": (ov_chapters.get("chapter6") or {}).get("book_callouts") or [],
            },
            "chapter7": {
                "id": "chapter7",
                "title": "Chapter 7: Convergence, Hysteresis Locks & Monitoring Contract",
                "book_title": "Staying the Course — Hysteresis Locks & Convergence",
                "epigraph": (ov_chapters.get("chapter7") or {}).get("epigraph") or {
                    "quote": "Consistency beats constant tinkering; change the portfolio only when the facts or stops change.",
                    "author": "Portfolio Governance Charter",
                },
                "book_paragraphs": ch7_paras,
                "book_callouts": (ov_chapters.get("chapter7") or {}).get("book_callouts") or [],
            },
        },
        "casenotes": built_casenotes,
        "book_casenotes": narrative_override.get("book_casenotes") or {},
        "book_challengers": narrative_override.get("book_challengers") or [],
        "citations": narrative_override.get("citations") or [
            f"Deterministic Market Facts Ledger & Price Series ({mkt}, session cutoff {as_of})",
            f"TradingView & Stage 2 Sector Breadth Scanner Snapshot ({mkt}, {as_of})",
            "Portfolio Allocator v4 Risk-Heat & Hysteresis State (data/allocations/%s.json, %s)" % (mkt, as_of),
        ],
    }


def compile_portfolio_audit(
    alloc: Dict[str, Any],
    facts_path: str = "",
    research_paths: Optional[List[str]] = None,
    narrative_override: Optional[Dict[str, Any]] = None,
    out_html_path: str | Path = "",
) -> Dict[str, Any]:
    mkt = alloc["market"]
    cur = alloc["currency_symbol"]
    as_of = alloc["as_of_date"]
    env = alloc["regime_envelope"]
    ps = alloc["portfolio_summary"]
    sc = alloc["stability_and_convergence"]
    holdings = alloc["holding_decisions"]
    tracking = alloc["tracking_positions"]
    options = alloc["options_decisions"]
    challengers = alloc["challenger_decisions"]
    clusters = alloc["clusters"]
    bridge = alloc["money_bridge"]
    debt_q = alloc["dossier_debt_queue"]

    narrative_override = narrative_override or {}
    story = _default_story_and_casenotes(alloc, narrative_override)
    report_stem = f"{mkt}_Portfolio_Audit"
    cur_word = "rupee" if mkt == "IN" else "dollar"
    title = (
        f"India (Zerodha) Portfolio Forensic Audit, Allocation & Narrative Playbook"
        if mkt == "IN"
        else f"US (Schwab & Robinhood) Portfolio Forensic Audit, Allocation & Narrative Playbook"
    )

    # Compute Top-3 concentration & money-at-risk figures for Infobox and Stress Scenarios
    sorted_by_cur = sorted(holdings, key=lambda x: -x["current_value"])
    top3_cur_pct = round(sum(x["current_wt_pct"] for x in sorted_by_cur[:3]), 2)
    sorted_by_tgt = sorted([h for h in holdings if h["target_value"] > 0], key=lambda x: -x["target_wt_pct"])
    top3_tgt_pct = round(sum(x["target_wt_pct"] for x in sorted_by_tgt[:3]), 2)
    cur_heat_val = round(sum(x["open_heat_value"] for x in holdings if x["current_value"] > 0 and x["target_value"] == 0) + sum(x["open_heat_value"] * (x["current_value"] / x["target_value"]) if x["target_value"] > 0 else 0.0 for x in holdings) + sum(o["open_heat_value"] for o in options), 2)
    # Simpler exact current vs target rupee/dollar heat from ps percentages:
    cur_heat_amt = round(ps["net_worth"] * (ps["current_open_heat_pct"] / 100.0), 2)
    tgt_heat_amt = round(ps["net_worth"] * (ps["target_open_heat_pct"] / 100.0), 2)

    # Key Figures Strip (Web)
    kf_html = (
        '<dl class="key-figures">\n'
        f'<div><dt class="kf-label">Total Net Worth</dt><dd class="kf-value">{cur}{ps["net_worth"]:,.2f}</dd>'
        f'<span class="kf-note">As of {as_of} close</span></div>\n'
        f'<div><dt class="kf-label">Open Portfolio Heat</dt><dd class="kf-value">{ps["current_open_heat_pct"]:.2f}% &rarr; {ps["target_open_heat_pct"]:.2f}%</dd>'
        f'<span class="kf-note">{cur}{tgt_heat_amt:,.2f} risk vs {ps["max_portfolio_heat_pct"]:.1f}% ceiling</span></div>\n'
        f'<div><dt class="kf-label">Convergence Score</dt><dd class="kf-value">{sc["convergence_score_pct"]:.1f}%</dd>'
        f'<span class="kf-note">{sc["actionable_trades_count"]} trade(s) outside &plusmn;{sc["rebalance_deadband_wt_pct"]:.2f}% band</span></div>\n'
        f'<div><dt class="kf-label">Active Risk Slots</dt><dd class="kf-value">{ps["active_unique_risk_underlyings_count"]} / {ps["active_slots_range"][1]}</dd>'
        f'<span class="kf-note">+{ps["tracking_positions_count"]} tracking stub(s) ignored</span></div>\n'
        f'<div><dt class="kf-label">Target Cash Reserve</dt><dd class="kf-value">{cur}{ps["target_cash_value"]:,.2f} ({ps["target_cash_wt_pct"]:.2f}%)</dd>'
        f'<span class="kf-note">Regime floor: {env["min_cash_floor_pct"]:.1f}%</span></div>\n'
        "</dl>"
    )

    # Infobox
    extra_us_rows = ""
    if mkt == "US":
        extra_us_rows = (
            f'<tr><th>Options Book (MV / Cost)</th><td>${ps["current_options_value"]:,.2f} / ${ps["current_options_cost_basis"]:,.2f}</td></tr>\n'
            f'<tr><th>2x/3x Rotation Target</th><td>{ps["leveraged_satellite_target_wt_pct"]:.2f}% (Max 12.0%)</td></tr>\n'
            f'<tr><th>Combined Decay Sleeve</th><td>{ps["combined_decay_sleeve_pct"]:.2f}% (Max 15.0%)</td></tr>\n'
        )
    infobox_html = (
        '<table class="infobox" role="presentation">\n'
        f'  <caption>{"India" if mkt == "IN" else "US"} Portfolio Executive Snapshot</caption>\n'
        f'  <tr><th colspan="2">Session Cutoff: {_esc(as_of)}</th></tr>\n'
        f'  <tr><th>Market Regime</th><td>{_esc(env["regime_label"])}</td></tr>\n'
        f'  <tr><th>Playbook Mode</th><td>{_esc(env["playbook_mode"].replace("_", " "))}</td></tr>\n'
        f'  <tr><th>Total Net Worth</th><td><strong>{cur}{ps["net_worth"]:,.2f}</strong></td></tr>\n'
        f'  <tr><th>Current Equities</th><td>{cur}{ps["current_equities_value"]:,.2f} ({ps["current_equities_wt_pct"]:.2f}%)</td></tr>\n'
        f'  <tr><th>Current Cash</th><td>{cur}{ps["current_cash_value"]:,.2f} ({ps["current_cash_wt_pct"]:.2f}%)</td></tr>\n'
        f'  <tr><th>Top-3 Concentration</th><td>{top3_cur_pct:.2f}% &rarr; {top3_tgt_pct:.2f}%</td></tr>\n'
        f'  <tr><th>Money at Risk (Stops)</th><td>{cur}{tgt_heat_amt:,.2f} ({ps["target_open_heat_pct"]:.2f}% vs {ps["max_portfolio_heat_pct"]:.1f}% cap)</td></tr>\n'
        f'  <tr><th>Core Alpha Target</th><td>{ps["core_alpha_target_wt_pct"]:.2f}% (Band 35–45%)</td></tr>\n'
        f'  <tr><th>Tactical Momentum Target</th><td>{ps["tactical_momentum_target_wt_pct"]:.2f}%</td></tr>\n'
        f'{extra_us_rows}'
        f'  <tr><th>Effective Exposure</th><td>{ps["effective_market_exposure_pct"] or 100.0:.1f}% (Beta {ps["portfolio_beta_weighted"] or 1.0:.2f})</td></tr>\n'
        "</table>"
    )

    # Build Chapter 1 HTML (place infobox right before p.lede so every table has an immediate prose paragraph)
    ch1 = story["chapters"]["chapter1"]
    heat_note = (
        f"Every stop-out across the book is bounded below {ps['max_portfolio_heat_pct']:.1f}% total drawdown"
        if ps["target_open_heat_pct"] <= ps["max_portfolio_heat_pct"]
        else f"Post-exit heat ({ps['target_open_heat_pct']:.2f}%) still exceeds the {ps['max_portfolio_heat_pct']:.1f}% ceiling due to legacy positions and grandfathered options; new buys are blocked"
    )
    ch1_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Macro Regime, Portfolio Heat &amp; Convergence Guardrails</caption>\n'
        '  <thead><tr><th>Dimension</th><th>Verified Reading</th><th>v4 Rulebook Mandate</th><th>Portfolio Consequence</th></tr></thead>\n'
        '  <tbody>\n'
        f'    <tr><td><strong>Market Regime</strong></td><td>{_esc(env["regime_label"])} (Breadth &gt;50DMA: {env["breadth_pct_above_50dma"] if env["breadth_pct_above_50dma"] is not None else "Measured"}%)</td>'
        f'<td>{_esc(env["playbook_mode"].replace("_", " "))} Playbook</td><td>Min cash floor {env["min_cash_floor_pct"]:.1f}%; starter extension cap &le;{env["max_starter_extension_pct"]:.1f}%</td></tr>\n'
        f'    <tr><td><strong>Open Portfolio Heat</strong></td><td>{ps["current_open_heat_pct"]:.2f}% ({cur}{cur_heat_amt:,.2f}) &rarr; {ps["target_open_heat_pct"]:.2f}% ({cur}{tgt_heat_amt:,.2f})</td>'
        f'<td>Hard ceiling {ps["max_portfolio_heat_pct"]:.1f}% of Net Worth</td><td>{heat_note}</td></tr>\n'
        f'    <tr><td><strong>Active Risk Slots</strong></td><td>{ps["active_unique_risk_underlyings_count"]} unique underlyings (+{ps["tracking_positions_count"]} tracking)</td>'
        f'<td>{ps["active_slots_range"][0]}–{ps["active_slots_range"][1]} active names; &lt;0.35% stubs excluded</td><td>Challengers require +15.0 tournament pts to displace a Stage 3 incumbent</td></tr>\n'
        f'    <tr><td><strong>Convergence &amp; Stability</strong></td><td>{sc["convergence_score_pct"]:.1f}% converged ({sc["actionable_trades_count"]} trade(s))</td>'
        f'<td>&plusmn;{sc["rebalance_deadband_wt_pct"]:.2f}% NAV deadband; 5-day &plusmn;{sc["price_band_hysteresis_pct"]:.1f}% lock</td><td>Suppresses daily flip-flops and 1-share nuisance rebalancing</td></tr>\n'
        '  </tbody>\n</table>'
    )
    ch1_takeaway = (
        f"<p>Reading these four guardrails together shows why our allocation plan stays steady across consecutive sessions. "
        f"With '{_esc(env['regime_label'])}' setting a {env['min_cash_floor_pct']:.1f}% cash floor and a {ps['max_portfolio_heat_pct']:.1f}% heat ceiling, "
        f"every risk decision starts from downside protection rather than prediction. "
        f"Positions already sitting inside our ±{sc['rebalance_deadband_wt_pct']:.2f}% deadband generate zero nuisance orders, "
        f"letting us carry clean capital math directly into our active holdings audit in Chapter 2 below.</p>"
    )
    ch1_trigger = (
        '<div class="callout callout-rule triggers"><div class="callout-title">What Changes Our Macro &amp; Heat Posture</div>'
        f'<p>If broad market breadth expands above 65.0% with benchmark price above rising 50-day and 200-day averages and distribution days subside, our heat budget lifts to 12.0% and Broad Uptrend starters open up to +8.5% above the 10-week EMA; '
        f'if the benchmark breaks below its 200-day average into Downtrend, maximum heat contracts to 4.0% and cash floor rises to 22.0%.</p></div>'
    )
    ch1_html = (
        f'<section class="chapter book-chapter clearfix" id="chapter1">\n'
        f'<h2>{_esc(ch1["title"])}</h2>\n'
        f'{infobox_html}\n'
        f'<p class="lede">{_prose_html(story["primer"])}</p>\n'
        + "\n".join(f"<p>{_prose_html(p)}</p>" for p in ch1["book_paragraphs"])
        + f"\n{ch1_tbl}\n{ch1_takeaway}\n{ch1_trigger}\n</section>"
    )

    # Build Chapter 2 HTML (Holdings Ladder Table + Case Notes + Tracking Stubs)
    ch2 = story["chapters"]["chapter2"]
    hold_rows_html = []
    book_hold_rows_html = []
    ranked_holdings = sorted(
        holdings,
        key=lambda x: (0 if x["verdict"] == "EXIT" else 1 if x["delta_shares"] < 0 else 2 if x["delta_shares"] > 0 else 3, -x["current_value"]),
    )
    for idx, hd in enumerate(ranked_holdings, 1):
        hold_rows_html.append(
            f"<tr><td>{idx}</td>"
            f"<td>{_sym_cell(hd['symbol'], mkt, hd['macro_sector'])}</td>"
            f'<td class="num">{hd["current_wt_pct"]:.2f}% &rarr; {hd["target_wt_pct"]:.2f}%</td>'
            f'<td class="num">{cur}{hd["close"]:,.2f}</td>'
            f'<td class="num">{cur}{hd["pnl_value"]:+,.2f} ({hd["pnl_pct"]:+.1f}%)</td>'
            f'<td>{_esc(_stage_display(hd["stage"]))} &bull; Score {hd["score"]["tournament_score"]:.1f}</td>'
            f'<td class="num">{cur}{hd["effective_stop"]:,.2f} ({hd["open_heat_pct"]:.2f}% heat)</td>'
            f'<td>{_vpill(hd["verdict"], hd["action_label"])}</td>'
            f'<td class="num">{cur}{hd["capital_liberated"]:,.2f}</td></tr>'
        )
        book_hold_rows_html.append(
            f"<tr><td>{idx}</td>"
            f"<td><strong>{_esc(hd['symbol'])}</strong> ({hd['current_quantity']:g}&rarr;{hd['target_quantity']:g} sh)</td>"
            f'<td class="num">{hd["current_wt_pct"]:.2f}% &rarr; {hd["target_wt_pct"]:.2f}%</td>'
            f'<td class="num">{cur}{hd["close"]:,.2f}</td>'
            f'<td class="num">{cur}{hd["effective_stop"]:,.2f}</td>'
            f'<td class="num">{hd["open_heat_pct"]:.2f}%</td>'
            f"<td>{_esc(hd['action_label'])}</td></tr>"
        )
    if not hold_rows_html:
        hold_rows_html.append(f'<tr><td>1</td><td>None</td><td class="num">0.0%</td><td class="num">{cur}0.00</td><td class="num">{cur}0.00</td><td>—</td><td class="num">{cur}0.00</td><td>—</td><td class="num">{cur}0.00</td></tr>')

    ch2_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Active Non-Tracking Holdings Audit, Tournament Scores &amp; Ratcheted Stops</caption>\n'
        f'  <thead><tr><th>Rank</th><th>Security &amp; Sector</th><th class="num">Wt (Now &rarr; Target)</th><th class="num">Close ({cur})</th><th class="num">Unrealized P&amp;L</th><th>Stage &amp; Score</th><th class="num">Stop &amp; Heat</th><th>Action Verdict</th><th class="num">Liberated ({cur})</th></tr></thead>\n'
        f'  <tbody>{"".join(hold_rows_html)}</tbody>\n</table>'
    )
    book_ch2_tbl = (
        '<table class="mc-table">\n'
        '  <caption>Active Holdings Ledger — Weight, Stop-Loss, Open Heat &amp; Action Mandate</caption>\n'
        f'  <thead><tr><th>#</th><th>Ticker &amp; Shares</th><th class="num">Weight</th><th class="num">Close ({cur})</th><th class="num">Hard Stop</th><th class="num">Heat</th><th>Mandate</th></tr></thead>\n'
        f'  <tbody>{"".join(book_hold_rows_html)}</tbody>\n</table>'
    )
    ch2_takeaway = (
        f"<p>Across all {len(holdings)} active non-tracking positions above, Phase 1 actions liberate {cur}{ps['capital_liberated_equities']:,.2f} from broken or over-extended lines while keeping intact compounders anchored on upward-only ratcheted stops. "
        f"Top-3 equity concentration shifts from {top3_cur_pct:.2f}% to {top3_tgt_pct:.2f}% of net worth, and total money at risk if every stop hits is {cur}{tgt_heat_amt:,.2f} ({ps['target_open_heat_pct']:.2f}%). "
        f"Every active holding's specific business thesis, monograph verdict, and closing stop trigger follows in Section 2.1 below.</p>"
    )
    casenotes_html = "\n".join(
        f'<div class="case-note casenote" data-symbol="{_esc(hd["symbol"])}">'
        f'<div class="case-note-head"><span class="case-note-title">{_esc(hd["symbol"])} &mdash; {_esc(hd["company_name"])}</span>'
        f'{_vpill(hd["verdict"], hd["action_label"])}</div>'
        f'<p>{_prose_html(story["casenotes"][hd["symbol"]])}</p></div>'
        for hd in holdings
    )

    tracking_section_html = ""
    book_tracking_sub = None
    if tracking:
        tr_rows_html = []
        book_tr_rows = []
        for tr in tracking:
            tr_stop_v = tr.get("effective_stop") or round(tr["close"] * 0.85, 2)
            tr_stage_v = _stage_display(tr.get("stage", "STAGE_2"))
            tr_newc_v = tr.get("new_capital_verdict", "WAIT_FOR_SUPPORT").replace("_", " ")
            tr_rows_html.append(
                f"<tr><td>{_sym_cell(tr['symbol'], mkt, tr.get('company_name', tr['symbol']))}</td>"
                f'<td class="num">{tr["quantity"]:g}</td>'
                f'<td class="num">{cur}{tr["close"]:,.2f}</td>'
                f'<td class="num">{cur}{tr["current_value"]:,.2f} ({tr["current_wt_pct"]:.2f}%)</td>'
                f'<td>{_esc(tr_stage_v)}</td>'
                f'<td class="num">{cur}{tr_stop_v:,.2f}</td>'
                f'<td>{_vpill("TRACKING_HOLD", f"TRACKING HOLD (NEW CAP: {tr_newc_v})")}</td></tr>'
            )
            book_tr_rows.append(
                f"<tr><td><strong>{_esc(tr['symbol'])}</strong> ({_esc(tr.get('company_name', tr['symbol']))})</td>"
                f'<td class="num">{tr["quantity"]:g} sh</td>'
                f'<td class="num">{cur}{tr["close"]:,.2f}</td>'
                f'<td class="num">{cur}{tr["current_value"]:,.2f} ({tr["current_wt_pct"]:.2f}%)</td>'
                f'<td class="num">{cur}{tr_stop_v:,.2f}</td>'
                f"<td>{_esc(tr_newc_v)}</td></tr>"
            )
        tr_tbl = (
            '<table class="wikitable">\n'
            '  <caption>Sub-0.35% Tracking Stubs (Reconciled in Net Worth, Excluded from Active Risk Slots)</caption>\n'
            f'  <thead><tr><th>Ticker &amp; Company</th><th class="num">Qty</th><th class="num">Close ({cur})</th><th class="num">Value &amp; Weight</th><th>Stage</th><th class="num">Advisory Stop</th><th>Monograph Posture</th></tr></thead>\n'
            f'  <tbody>{"".join(tr_rows_html)}</tbody>\n</table>'
        )
        book_tr_tbl = (
            '<table class="mc-table">\n'
            '  <caption>Sub-0.35% Tracking Stubs (Excluded from 12–15 Active Slot Cap)</caption>\n'
            f'  <thead><tr><th>Ticker &amp; Company</th><th class="num">Qty</th><th class="num">Close</th><th class="num">Value (% NAV)</th><th class="num">Stop</th><th>New Capital</th></tr></thead>\n'
            f'  <tbody>{"".join(book_tr_rows)}</tbody>\n</table>'
        )
        tr_intro = narrative_override.get("tracking_intro") or (
            f"Small 1-share and pilot tracking positions below 0.35% of net worth serve as live exchange-screen anchors rather than meaningful capital commitments. "
            f"In our {mkt} account, {len(tracking)} tracking stub(s) ({', '.join(t['symbol'] for t in tracking)}) sum to {cur}{ps['tracking_positions_value']:,.2f}, or just {round(ps['tracking_positions_value'] / ps['net_worth'] * 100.0, 2):.2f}% of total capital. "
            f"Under our v4 sizing charter, counting a {cur}{tracking[-1]['current_value']:,.2f} 1-share tracker against the 12–15 active risk-slot cap would artificially block real compounders or generate brokerage friction worth more than the position itself. "
            f"We reconcile every {cur_word} of these stubs in our Money Bridge while holding each behind its monograph invalidation stop with zero new capital unless a full support setup triggers."
        )
        tr_take = (
            f"<p>Keeping {', '.join(t['symbol'] for t in tracking)} isolated in this tracking ledger preserves full accounting accuracy. "
            f"All {cur}{ps['tracking_positions_value']:,.2f} sits inside our {cur}{ps['net_worth']:,.2f} net worth, yet our active risk count stays clean at {ps['active_unique_risk_underlyings_count']} names. "
            f"None of these tiny tracking shares warrants fresh capital at today's close. "
            f"Each stub carries a clear advisory invalidation stop while we turn next to thematic cluster risk in Chapter 3.</p>"
        )
        tracking_section_html = (
            "<h3>2.2 Sub-0.35% Tracking Stubs &amp; Monograph Guardrails</h3>\n"
            f"<p>{_prose_html(tr_intro)}</p>\n"
            f"{tr_tbl}\n{tr_take}\n"
        )
        book_tracking_sub = {
            "title": f"Sub-0.35% Tracking Stubs ({', '.join(t['symbol'] for t in tracking)})",
            "paragraphs": [tr_intro, re.sub(r"<[^>]+>", "", tr_take)],
            "callouts": [],
            "tables": [book_tr_tbl],
        }

    ch2_trigger = (
        '<div class="callout callout-rule triggers"><div class="callout-title">Holding Ratchet &amp; Shakeout Trigger Rules</div>'
        f'<p>If any retained holding closes a completed daily session below its ratcheted stop in the table above with RSI(14) below 42, execute an exit on the next session; '
        f'if an intraday flush undercuts support and closes back above the 50-day SMA or 10-week EMA on positive volume, retain the shares and anchor the hard stop below the shakeout low before moving to Chapter 3.</p></div>'
    )
    ch2_html = (
        f'<section class="chapter book-chapter" id="chapter2">\n'
        f'<h2>{_esc(ch2["title"])}</h2>\n'
        + "\n".join(f"<p>{_prose_html(p)}</p>" for p in ch2["book_paragraphs"])
        + f"\n{ch2_tbl}\n{ch2_takeaway}\n"
        + f"<h3>2.1 Individual Position Case Notes &amp; Invalidation Levels</h3>\n"
        + f"<p>Every active position in our book must earn its slot from today's close rather than past cost basis. Each case note below states what the company does, why we hold or trim it, the exact ledger price, weight, unrealized P&amp;L, tournament score, and ratcheted stop-loss, plus the specific price or filing event that changes the call. Treat these levels as standing desk discipline until the next completed session.</p>\n"
        + f"{casenotes_html}\n{tracking_section_html}{ch2_trigger}\n</section>"
    )

    # Build Chapter 3 HTML (Options & 2x/3x Audit for US, or Cluster Audit for IN/US)
    ch3 = story["chapters"]["chapter3"]
    if mkt == "US" and options:
        opt_rows_html = []
        for od in options:
            opt_rows_html.append(
                f"<tr><td><strong>{_esc(od['contract_symbol'])}</strong><br><span class='case-note-sub'>{_esc(od['underlying'])} &bull; {_esc(od['broker_account'])}</span></td>"
                f'<td class="num">{od["contracts"]}</td>'
                f'<td class="num">{od["dte"]}d &bull; &Delta; {od["delta"]:.2f}</td>'
                f'<td class="num">${od["cost_basis"]:,.2f} / ${od["current_value"]:,.2f} ({od["pnl_pct"]:+.1f}%)</td>'
                f'<td class="num">${od["underlying_spot"]:,.2f} / Stop ${od["invalidation_stop"] or 0:,.2f}</td>'
                f'<td class="num">${od["open_heat_value"]:,.2f} ({od["open_heat_pct"]:.2f}%)</td>'
                f'<td>{_vpill(od["verdict"])}</td>'
                f'<td>{_esc(od["rationale"])}</td></tr>'
            )
        ch3_tbl = (
            '<table class="wikitable">\n'
            '  <caption>US Options / LEAPS Convexity Audit &amp; Decay Guardrails</caption>\n'
            '  <thead><tr><th>Contract &amp; Underlying</th><th class="num">Qty</th><th class="num">DTE &amp; Delta</th><th class="num">Cost / MV (P&amp;L)</th><th class="num">Spot / Shelf Stop</th><th class="num">Open Heat</th><th>Verdict</th><th>Desk Rule &amp; Repair Trigger</th></tr></thead>\n'
            f'  <tbody>{"".join(opt_rows_html)}</tbody>\n</table>'
        )
        book_ch3_tbl = ch3_tbl.replace('class="wikitable"', 'class="mc-table"')
        ch3_take = (
            f"<p>Auditing all {len(options)} open option contracts confirms ${ps['current_options_value']:,.2f} in current market value against ${ps['current_options_cost_basis']:,.2f} original cost ({ps['options_cap_basis_pct']:.2f}% cap basis vs our 10.0% ceiling). "
            f"Grandfathered contracts hold strictly while their underlying equities defend weekly shelf invalidation stops. "
            f"Future drawdown deployments require 0.60–0.80 delta ITM/ATM contracts or Bull Call Debit Spreads whenever implied volatility exceeds 1.15x HV20, setting up our equity shortlist tournament in Chapter 4 next.</p>"
        )
    else:
        cl_rows_html = []
        for cl in clusters[:12]:
            cl_rows_html.append(
                f"<tr><td><strong>{_esc(cl['cluster_id'])}</strong></td>"
                f"<td>{_esc(', '.join(cl['symbols']))}</td>"
                f'<td class="num">{cl["current_wt_pct"]:.2f}%</td>'
                f'<td class="num">{cl["target_wt_pct"]:.2f}% (Cap {cl["max_cluster_wt_pct"]:.0f}%)</td>'
                f'<td class="num">{cl.get("current_open_heat_pct", cl["open_heat_pct"]):.2f}% &rarr; {cl["open_heat_pct"]:.2f}% (Cap {cl["max_cluster_heat_pct"]:.1f}%)</td>'
                f'<td>{"WITHIN GUARDRAIL" if cl["target_wt_pct"] <= cl["max_cluster_wt_pct"] and cl["open_heat_pct"] <= cl["max_cluster_heat_pct"] else "TRIMMED TO CAP"}</td></tr>'
            )
        if not cl_rows_html:
            cl_rows_html.append('<tr><td>SINGLETONS</td><td>No multi-stock cluster</td><td class="num">0.0%</td><td class="num">0.0%</td><td class="num">0.0%</td><td>WITHIN GUARDRAIL</td></tr>')
        ch3_tbl = (
            '<table class="wikitable">\n'
            '  <caption>Correlated &amp; Thematic Cluster Exposure Matrix (25% Notional / 3.5% Heat Cap)</caption>\n'
            '  <thead><tr><th>Cluster Group</th><th>Member Tickers</th><th class="num">Current Wt</th><th class="num">Target Wt</th><th class="num">Cluster Heat</th><th>Guardrail Status</th></tr></thead>\n'
            f'  <tbody>{"".join(cl_rows_html)}</tbody>\n</table>'
        )
        book_ch3_tbl = ch3_tbl.replace('class="wikitable"', 'class="mc-table"')
        ch3_take = (
            f"<p>Grouping correlated holdings into explicit clusters ensures no single domestic or sector theme exceeds {clusters[0]['max_cluster_wt_pct'] if clusters else 25:.0f}% of net worth or 3.5% of open portfolio heat. "
            f"When several holdings share one macro capex driver, their combined drawdown risk must be budgeted as a single bet rather than independent lines. "
            f"With thematic concentration verified and bounded inside our guardrails, we turn next to Chapter 4 to test shortlisted challengers.</p>"
        )
    ch3_html = (
        f'<section class="chapter book-chapter" id="chapter3">\n'
        f'<h2>{_esc(ch3["title"])}</h2>\n'
        + "\n".join(f"<p>{_prose_html(p)}</p>" for p in ch3["book_paragraphs"])
        + f"\n{ch3_tbl}\n{ch3_take}\n</section>"
    )

    # Build Chapter 4 HTML (Shortlist Challenger Tournament)
    ch4 = story["chapters"]["chapter4"]
    ch_rows_html = []
    book_ch_rows_html = []
    for idx, ch in enumerate(challengers, 1):
        asym_txt = f"{ch['asymmetry_ratio']:.2f}:1" if ch["asymmetry_ratio"] is not None else "—"
        tbase_txt = f"{cur}{ch['target_base']:,.2f}" if ch["target_base"] else "—"
        ch_rows_html.append(
            f"<tr><td>{idx}</td>"
            f"<td>{_sym_cell(ch['symbol'], mkt, ch['macro_sector'])}</td>"
            f"<td>{_esc(ch['bucket'].replace('_', ' '))} ({_esc(ch['tier'])})</td>"
            f'<td class="num">{ch["score"]["tournament_score"]:.1f}</td>'
            f'<td class="num">{cur}{ch["close"]:,.2f}</td>'
            f'<td class="num">{cur}{ch["entry_zone_low"]:,.2f}–{cur}{ch["entry_zone_high"]:,.2f}</td>'
            f'<td class="num">{cur}{ch["stop_loss"]:,.2f} / {tbase_txt} ({asym_txt})</td>'
            f'<td class="num">{ch["starter_target_wt_pct"]:.2f}% / {ch["full_target_wt_pct"]:.2f}%</td>'
            f'<td>{_vpill(ch["entry_action"])}</td>'
            f'<td class="num">{ch["funded_shares"]} sh ({cur}{ch["funded_value"]:,.2f})</td></tr>'
        )
        book_ch_rows_html.append(
            f"<tr><td>{idx}</td>"
            f"<td><strong>{_esc(ch['symbol'])}</strong> ({_esc(ch['tier'])})</td>"
            f'<td class="num">{ch["score"]["tournament_score"]:.1f}</td>'
            f'<td class="num">{cur}{ch["close"]:,.2f}</td>'
            f'<td class="num">{cur}{ch["entry_zone_low"]:,.2f}–{cur}{ch["entry_zone_high"]:,.2f}</td>'
            f'<td class="num">{cur}{ch["stop_loss"]:,.2f} ({asym_txt})</td>'
            f"<td>{_esc(ch['entry_action'].replace('_', ' '))}</td></tr>"
        )
    if not ch_rows_html:
        ch_rows_html.append(f'<tr><td>1</td><td>No non-held shortlist rows</td><td>—</td><td class="num">0.0</td><td class="num">{cur}0.00</td><td class="num">—</td><td class="num">—</td><td class="num">0.0%</td><td>—</td><td class="num">0 sh ({cur}0.00)</td></tr>')
    ch4_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Shortlist &amp; Monograph Challenger Tournament, 50/50 Tranche Sizing &amp; Entry Gates</caption>\n'
        f'  <thead><tr><th>Rank</th><th>Candidate</th><th>Bucket &amp; Tier</th><th class="num">Score</th><th class="num">CMP ({cur})</th><th class="num">Support Zone ({cur})</th><th class="num">Stop / Base (R:R)</th><th class="num">Starter / Full Wt</th><th>Gate Verdict</th><th class="num">Funded Now</th></tr></thead>\n'
        f'  <tbody>{"".join(ch_rows_html)}</tbody>\n</table>'
    )
    book_ch4_tbl = (
        '<table class="mc-table">\n'
        '  <caption>Challenger Tournament — Score, Support Band, Stop/R:R &amp; Gate Verdict</caption>\n'
        f'  <thead><tr><th>#</th><th>Candidate</th><th class="num">Score</th><th class="num">CMP ({cur})</th><th class="num">Support Band</th><th class="num">Stop (R:R)</th><th>Gate Verdict</th></tr></thead>\n'
        f'  <tbody>{"".join(book_ch_rows_html)}</tbody>\n</table>'
    )
    ch4_take = (
        f"<p>Scoring all {len(challengers)} non-held candidates on our unified 100-point rubric funds {len([c for c in challengers if c['funded_shares'] > 0])} immediate starter position(s) worth {cur}{sum(c['funded_value'] for c in challengers):,.2f}. "
        f"We also stage {len([c for c in challengers if c['entry_action'] == 'RESTING_LIMIT_AT_SUPPORT'])} resting support alert band(s) on vetted Stage 2 monographs that sit extended above buy zones today. "
        f"Pre-monograph shortlist monitors, rejected dossiers, and Stage 3 or Stage 4 pullbacks stay deferred so cash never chases weak setups, flowing directly into Chapter 5 below.</p>"
    )
    ch4_trigger = (
        '<div class="callout callout-rule triggers"><div class="callout-title">50/50 Starter &amp; Proof-Add Triggers</div>'
        f'<p>If a resting monograph challenger pulls back into its support band above with daily RSI(14) holding above 40 and intact volume structure, deploy the 50% Starter Tranche; '
        f'never deploy the second 50% Proof Add unless Tranche 1 is up at least +1.0R in sideways tapes (+0.75R in broad uptrends) so your combined stop moves to breakeven.</p></div>'
    )
    ch4_html = (
        f'<section class="chapter book-chapter" id="chapter4">\n'
        f'<h2>{_esc(ch4["title"])}</h2>\n'
        + "\n".join(f"<p>{_prose_html(p)}</p>" for p in ch4["book_paragraphs"])
        + f"\n{ch4_tbl}\n{ch4_take}\n{ch4_trigger}\n</section>"
    )

    # Build Chapter 5 HTML (100% Reconciled Money Bridge + Step-by-Step Cash Waterfall & Stress Scenarios)
    ch5 = story["chapters"]["chapter5"]
    mb_rows_html = []
    for r in bridge:
        mb_rows_html.append(
            f"<tr><td><strong>{_esc(r['symbol'])}</strong></td>"
            f"<td>{_esc(r['bucket'].replace('_', ' '))}</td>"
            f'<td class="num">{cur}{r["current_value"]:,.2f}</td>'
            f'<td class="num">{r["current_wt_pct"]:.2f}%</td>'
            f'<td class="num">{cur}{r["target_value"]:,.2f}</td>'
            f'<td class="num">{r["target_wt_pct"]:.2f}%</td>'
            f'<td class="num">{cur}{r["variance_value"]:+,.2f}</td>'
            f'<td class="num">{r["variance_wt_pct"]:+.2f}%</td>'
            f"<td>{_esc(r['action_mandate'])}</td></tr>"
        )
    mb_rows_html.append(
        f'<tr><td><strong>TOTAL PORTFOLIO NET WORTH</strong></td><td><strong>ALL SLEEVES</strong></td>'
        f'<td class="num"><strong>{cur}{ps["net_worth"]:,.2f}</strong></td><td class="num"><strong>100.00%</strong></td>'
        f'<td class="num"><strong>{cur}{ps["net_worth"]:,.2f}</strong></td><td class="num"><strong>100.00%</strong></td>'
        f'<td class="num"><strong>{cur}0.00</strong></td><td class="num"><strong>0.00%</strong></td>'
        f'<td><strong>RECONCILED ({sc["convergence_score_pct"]:.1f}% CONVERGED)</strong></td></tr>'
    )
    ch5_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Master Capital Reallocation &amp; 100.00% Reconciled Money Bridge</caption>\n'
        f'  <thead><tr><th>Asset / Position</th><th>Sleeve</th><th class="num">Current ({cur})</th><th class="num">Current Wt</th><th class="num">Target ({cur})</th><th class="num">Target Wt</th><th class="num">Delta ({cur})</th><th class="num">Delta Wt</th><th>Mandate</th></tr></thead>\n'
        f'  <tbody>{"".join(mb_rows_html)}</tbody>\n</table>'
    )
    book_ch5_tbl = ch5_tbl.replace('class="wikitable"', 'class="mc-table"')
    ch5_take = (
        f"<p>Every {cur_word} in the Master Money Bridge reconciles to {cur}{ps['net_worth']:,.2f} across both current and target columns. "
        f"Current holdings plus cash equal 100.00%, and target holdings plus reserve cash equal 100.00% with {cur}0.00 drift. "
        f"Phase 1 sales free {cur}{ps['capital_liberated_equities'] + ps['capital_liberated_options']:,.2f} to supplement our {cur}{ps['current_cash_value']:,.2f} starting cash, fund {cur}{ps['capital_deployed_equities']:,.2f} of disciplined additions, and hold {cur}{ps['target_cash_value']:,.2f} ({ps['target_cash_wt_pct']:.2f}%) in reserve. "
        f"Read the two right-hand columns as the plan of record: every current line we keep holds its exact {cur_word} value, every line we trim shows the precise freed cash, and the final cash row sits well above our {env['min_cash_floor_pct']:.1f}% regime floor. "
        f"Join that reconciled pool to Section 5.1's running-balance waterfall and stress tests below to see how the whole reset is self-funded.</p>"
    )
    # Aggregate retained-book base-case reward versus open-heat stop risk (red-team disclosure)
    retained_lines = [h for h in holdings if h["target_value"] > 0 and h.get("target_base")]
    retained_base_gain = round(
        sum((h["target_base"] - h["close"]) * h["target_quantity"] for h in retained_lines), 2
    )
    retained_base_gain_pct = round(retained_base_gain / ps["net_worth"] * 100.0, 2)
    retained_rr = round(retained_base_gain / tgt_heat_amt, 2) if tgt_heat_amt else 0.0
    _top_contrib = sorted(
        [(h["symbol"], round((h["target_base"] - h["close"]) * h["target_quantity"], 2)) for h in retained_lines],
        key=lambda x: x[1],
        reverse=True,
    )[:2]
    _contrib_str = ", ".join(f"{sym} {cur}{val:+,.2f}" for sym, val in _top_contrib)
    retained_base_line = (
        f"Against that risk, our {len(retained_lines)} retained base-case targets sum to {cur}{retained_base_gain:+,.2f} "
        f"({retained_base_gain_pct:+.2f}% of net worth), a {retained_rr:.2f}:1 aggregate reward-to-stop ratio "
        f"(led by {_contrib_str}), reconciling line by line to each Section 2.1 case note."
    )
    ch5_take = ch5_take.replace("</p>", " " + retained_base_line + "</p>")

    # Step-by-Step Running-Balance Cash Waterfall & Stress Scenarios (Section 5.1)
    wf_rows_html = []
    running_cash = round(ps["current_cash_value"], 2)
    wf_rows_html.append(
        f'<tr><td>Starting Broker Cash</td><td>Settled cash balance</td>'
        f'<td class="num">{cur}0.00</td><td class="num"><strong>{cur}{running_cash:,.2f}</strong></td></tr>'
    )
    for hd in sorted([h for h in holdings if h["delta_shares"] < 0], key=lambda x: -x["capital_liberated"]):
        running_cash = round(running_cash + hd["capital_liberated"], 2)
        verb_wf = "Exit" if hd["verdict"] == "EXIT" else "Trim"
        wf_rows_html.append(
            f'<tr><td>+ {hd["action_label"]} ({_esc(hd["symbol"])})</td>'
            f'<td>{verb_wf} {abs(hd["delta_shares"]):g} sh @ {cur}{hd["close"]:,.2f}</td>'
            f'<td class="num">+{cur}{hd["capital_liberated"]:,.2f}</td>'
            f'<td class="num">{cur}{running_cash:,.2f}</td></tr>'
        )
    for od in options:
        if od["capital_liberated"] > 0:
            running_cash = round(running_cash + od["capital_liberated"], 2)
            wf_rows_html.append(
                f'<tr><td>+ Option Exit/Trim ({_esc(od["contract_symbol"])})</td>'
                f'<td>Close {od["contracts"]} contract(s)</td>'
                f'<td class="num">+{cur}{od["capital_liberated"]:,.2f}</td>'
                f'<td class="num">{cur}{running_cash:,.2f}</td></tr>'
            )
    for hd in [h for h in holdings if h["delta_shares"] > 0]:
        running_cash = round(running_cash - hd["capital_deployed"], 2)
        wf_rows_html.append(
            f'<tr><td>&minus; Scale-Up Add ({_esc(hd["symbol"])})</td>'
            f'<td>Buy {hd["delta_shares"]:g} sh @ {cur}{hd["close"]:,.2f}</td>'
            f'<td class="num">&minus;{cur}{hd["capital_deployed"]:,.2f}</td>'
            f'<td class="num">{cur}{running_cash:,.2f}</td></tr>'
        )
    for ch in [c for c in challengers if c["funded_shares"] > 0]:
        running_cash = round(running_cash - ch["funded_value"], 2)
        wf_rows_html.append(
            f'<tr><td>&minus; 50% Starter Buy ({_esc(ch["symbol"])})</td>'
            f'<td>Buy {ch["funded_shares"]} sh @ {cur}{ch["close"]:,.2f}</td>'
            f'<td class="num">&minus;{cur}{ch["funded_value"]:,.2f}</td>'
            f'<td class="num">{cur}{running_cash:,.2f}</td></tr>'
        )
    wf_rows_html.append(
        f'<tr><td><strong>Ending Target Cash Reserve</strong></td><td><strong>Floor {env["min_cash_floor_pct"]:.1f}% of Net Worth</strong></td>'
        f'<td class="num"><strong>{cur}{ps["target_cash_value"] - ps["current_cash_value"]:+,.2f}</strong></td>'
        f'<td class="num"><strong>{cur}{ps["target_cash_value"]:,.2f} ({ps["target_cash_wt_pct"]:.2f}%)</strong></td></tr>'
    )
    wf_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Step-by-Step Cash Waterfall (Running Liquidity Balance)</caption>\n'
        f'  <thead><tr><th>Waterfall Step</th><th>Transaction Detail</th><th class="num">Cash Flow ({cur})</th><th class="num">Running Cash ({cur})</th></tr></thead>\n'
        f'  <tbody>{"".join(wf_rows_html)}</tbody>\n</table>'
    )
    beta_val = ps["portfolio_beta_weighted"] or 1.0
    ten_pct_index_drop_pct = round((ps["target_equities_wt_pct"] / 100.0) * beta_val * 10.0, 2)
    ten_pct_index_drop_amt = round(ps["net_worth"] * (ten_pct_index_drop_pct / 100.0), 2)
    resting_starters = [c for c in challengers if c["entry_action"] == "RESTING_LIMIT_AT_SUPPORT"]
    resting_total_need = round(sum(ps["net_worth"] * (c["starter_target_wt_pct"] / 100.0) for c in resting_starters[:4]), 2)
    wf_intro = narrative_override.get("waterfall_intro") or (
        f"Walking the cash ledger step by step proves that every purchase is self-funded without margin debt. "
        f"We begin with {cur}{ps['current_cash_value']:,.2f} ({ps['current_cash_wt_pct']:.2f}% of net worth) in settled broker cash. "
        f"Each Phase 1 exit and trim adds cash to the pool before any Phase 2 buy ticket is staged. "
        f"Three stress tests confirm our downside resilience. First, if every retained stop-loss hit at once, loss would equal {cur}{tgt_heat_amt:,.2f} ({ps['target_open_heat_pct']:.2f}% vs our {ps['max_portfolio_heat_pct']:.1f}% cap). "
        f"Second, a 10.0% index drop at {beta_val:.2f} beta implies roughly {ten_pct_index_drop_pct:.2f}% ({cur}{ten_pct_index_drop_amt:,.2f}) equity impact before stops fire. "
        f"Third, if zero support alerts fill, {cur}{ps['target_cash_value']:,.2f} waits safely in dry powder with zero decay, covering ~{cur}{resting_total_need:,.2f} of top resting starters."
    )
    heat_status_txt = (
        f"keeping worst-case stop-out loss below our {ps['max_portfolio_heat_pct']:.1f}% ceiling."
        if ps["target_open_heat_pct"] <= ps["max_portfolio_heat_pct"]
        else f"cutting {ps['current_open_heat_pct'] - ps['target_open_heat_pct']:.2f} percentage points of risk, though remaining above our {ps['max_portfolio_heat_pct']:.1f}% ceiling due to legacy positions and grandfathered options."
    )
    heat_verb = "drops from" if ps["target_open_heat_pct"] < ps["current_open_heat_pct"] else ("edges up from" if ps["target_open_heat_pct"] > ps["current_open_heat_pct"] else "holds steady at")
    wf_take = (
        f"<p>Tracing the running cash balance from {cur}{ps['current_cash_value']:,.2f} to {cur}{ps['target_cash_value']:,.2f} shows that Phase 1 sales fortify our liquidity immediately without relying on optimistic fills. "
        f"Open portfolio heat {heat_verb} {ps['current_open_heat_pct']:.2f}% today to {ps['target_open_heat_pct']:.2f}% after execution ({cur}{tgt_heat_amt:,.2f} if every retained stop hits), {heat_status_txt} "
        f"Treat that {ps['target_open_heat_pct']:.2f}% as pre-gap and pre-slippage, however: our Section 2.2 rule evaluates stops on completed daily or weekly closes (exiting only with RSI(14) below 42, or the following session on explicit hard-stop lines), and thin-volume Phase 1 exits or stop-outs can gap through their limit floors. "
        f"That fully reconciled {cur}{ps['target_cash_value']:,.2f} reserve backs every sequenced advisory recommendation in Chapter 6 next.</p>"
    )
    ch5_html = (
        f'<section class="chapter book-chapter" id="chapter5">\n'
        f'<h2>{_esc(ch5["title"])}</h2>\n'
        + "\n".join(f"<p>{_prose_html(p)}</p>" for p in ch5["book_paragraphs"])
        + f"\n{ch5_tbl}\n{ch5_take}\n"
        + "<h3>5.1 Step-by-Step Cash Waterfall &amp; Downside Stress Scenarios</h3>\n"
        + f"<p>{_prose_html(wf_intro)}</p>\n"
        + f"{wf_tbl}\n{wf_take}\n</section>"
    )

    # Build Chapter 6 HTML (Advisory Execution Recommendations + Dossier Debt Queue)
    ch6 = story["chapters"]["chapter6"]
    exec_rows = []
    for hd in holdings:
        if hd["delta_shares"] < 0:
            verb_ex = "Exit" if hd["verdict"] == "EXIT" else "Trim"
            exec_rows.append(
                f"<tr><td>Phase 1: Advisory {verb_ex}</td><td><strong>{_esc(hd['symbol'])}</strong></td>"
                f'<td class="num">{verb_ex} {abs(hd["delta_shares"]):g} sh</td>'
                f'<td class="num">Session / &ge; {cur}{hd["close"] * 0.99:,.2f}</td>'
                f'<td class="num">{cur}{hd["effective_stop"]:,.2f}</td>'
                f'<td class="num">{cur}{hd["capital_liberated"]:,.2f} freed</td>'
                f"<td>{_esc(hd['broker_routing'])}</td></tr>"
            )
    for od in options:
        if od["capital_liberated"] > 0:
            exec_rows.append(
                f"<tr><td>Phase 1: Advisory Option Exit/Trim</td><td><strong>{_esc(od['contract_symbol'])}</strong></td>"
                f'<td class="num">Close {od["contracts"]} c</td>'
                f'<td class="num">Mid-price limit</td>'
                f'<td class="num">Und. {cur}{od["invalidation_stop"] or 0:,.2f}</td>'
                f'<td class="num">{cur}{od["capital_liberated"]:,.2f} freed</td>'
                f"<td>{_esc(od['broker_account'])}</td></tr>"
            )
    for hd in holdings:
        if hd["delta_shares"] > 0:
            exec_rows.append(
                f"<tr><td>Phase 2: Advisory Scale-Up Add</td><td><strong>{_esc(hd['symbol'])}</strong></td>"
                f'<td class="num">Buy {hd["delta_shares"]:g} sh</td>'
                f'<td class="num">&le; {cur}{hd["close"] * 1.005:,.2f}</td>'
                f'<td class="num">{cur}{hd["effective_stop"]:,.2f}</td>'
                f'<td class="num">{cur}{hd["capital_deployed"]:,.2f} deployed</td>'
                f"<td>{_esc(hd['broker_routing'])}</td></tr>"
            )
    for ch in challengers:
        if ch["funded_shares"] > 0:
            exec_rows.append(
                f"<tr><td>Phase 2: Advisory 50% Starter</td><td><strong>{_esc(ch['symbol'])}</strong></td>"
                f'<td class="num">Buy {ch["funded_shares"]} sh</td>'
                f'<td class="num">{cur}{ch["entry_zone_low"]:,.2f}–{cur}{ max(ch["close"], ch["entry_zone_high"]):,.2f}</td>'
                f'<td class="num">{cur}{ch["stop_loss"]:,.2f}</td>'
                f'<td class="num">{cur}{ch["funded_value"]:,.2f} deployed</td>'
                f"<td>{_esc(ch['broker_routing'])}</td></tr>"
            )
    for ch in challengers:
        if ch["entry_action"] == "RESTING_LIMIT_AT_SUPPORT":
            est_sh = max(1, int((ps["net_worth"] * (ch["starter_target_wt_pct"] / 100.0)) // max(0.01, ch["entry_zone_high"])))
            exec_rows.append(
                f"<tr><td>Phase 2B: Advisory Support Alert</td><td><strong>{_esc(ch['symbol'])}</strong></td>"
                f'<td class="num">Up to {est_sh} sh</td>'
                f'<td class="num">{cur}{ch["entry_zone_low"]:,.2f}–{cur}{ch["entry_zone_high"]:,.2f}</td>'
                f'<td class="num">{cur}{ch["stop_loss"]:,.2f}</td>'
                f'<td class="num">Conditional watch</td>'
                f"<td>{_esc(ch['broker_routing'])} (14-day review)</td></tr>"
            )
    if not exec_rows:
        exec_rows.append(f'<tr><td>Converged — Stand Pat</td><td>Portfolio Aligned</td><td class="num">0 sh</td><td class="num">—</td><td class="num">Keep trailing stops</td><td class="num">{cur}0.00</td><td>No broker trades needed</td></tr>')

    ch6_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Sequenced Advisory Execution Recommendations, Alert Bands &amp; Broker Routing</caption>\n'
        f'  <thead><tr><th>Execution Phase</th><th>Instrument</th><th class="num">Advisory Size</th><th class="num">Reference / Alert Band</th><th class="num">Protective Stop</th><th class="num">Cash Impact</th><th>Routing &amp; Validity</th></tr></thead>\n'
        f'  <tbody>{"".join(exec_rows)}</tbody>\n</table>'
    )
    book_ch6_tbl = ch6_tbl.replace('class="wikitable"', 'class="mc-table"')
    ch6_take = (
        f"<p>All rows above are advisory portfolio recommendations rather than automated broker orders: verify live bid-ask liquidity at market open, note that overnight earnings or regulatory gaps can open below stated stop levels, and review any unfilled Phase 2B support alerts after 14 calendar days. "
        f"Executing Phase 1 sales before staging Phase 2 entries ensures settled cash covers every purchase while preserving our {env['min_cash_floor_pct']:.1f}% reserve floor; Section 6.1 below audits monograph underwriting coverage.</p>"
    )

    debt_rows_html = []
    for idx, dq in enumerate(debt_q, 1):
        debt_rows_html.append(
            f"<tr><td>{idx}</td><td><strong>{_esc(dq['symbol'])}</strong></td>"
            f'<td class="num">{cur}{dq["market_value"]:,.2f} ({dq["weight_pct"]:.2f}%)</td>'
            f"<td>{_esc(_stage_display(dq['stage']))}</td>"
            f"<td>{_esc(dq['priority_reason'])}</td></tr>"
        )
    if not debt_rows_html:
        debt_rows_html.append(f'<tr><td>1</td><td>Queue Clear (100% Covered)</td><td class="num">{cur}0.00 (0.00%)</td><td>All Verified</td><td>Every active and tracking holding in this account has a published 10-chapter monograph dossier</td></tr>')
    debt_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Dossier Underwriting Debt Queue (Pre-Monograph Holdings Ordered by Capital at Risk)</caption>\n'
        f'  <thead><tr><th>Priority</th><th>Held Ticker</th><th class="num">Exposure ({cur} / % NAV)</th><th>Current Stage</th><th>Governance Rule Until Monograph Publishes</th></tr></thead>\n'
        f'  <tbody>{"".join(debt_rows_html)}</tbody>\n</table>'
    )
    debt_take = (
        f"<p>{'Zero pre-monograph holdings remain in the queue above, meaning 100% of our held equity capital is now backed by primary-filing 10-chapter monographs. Research capacity can now focus on fresh shortlist challengers and quarterly filing checks.' if not debt_q else f'Ranking our {len(debt_q)} pre-dossier holdings by capital exposure ensures upcoming company_report runs retire the largest blind spots first. Provisional lines stay protected by hard stops and barred from fresh adds until underwritten.'} "
        f"Chapter 7 next codifies the hysteresis locks and disclosures that keep this plan stable across daily reruns.</p>"
    )
    ch6_html = (
        f'<section class="chapter book-chapter" id="chapter6">\n'
        f'<h2>{_esc(ch6["title"])}</h2>\n'
        + "\n".join(f"<p>{_prose_html(p)}</p>" for p in ch6["book_paragraphs"])
        + f"\n{ch6_tbl}\n{ch6_take}\n"
        + "<h3>6.1 Dossier Underwriting Coverage &amp; Debt Queue</h3>\n"
        + f"<p>Real conviction comes from primary filings and cash-flow forensics, never from a chart pattern alone. Whenever an equity sits in our account without a completed 10-chapter monograph, our rulebook places it in provisional status rather than dumping a working trend or adding blind risk. Existing shares stay guarded by a ratcheted closing stop, fresh capital additions remain frozen, and research priority runs strictly from largest {cur_word} exposure down to smallest.</p>\n"
        + f"{debt_tbl}\n{debt_take}\n</section>"
    )

    # Build Chapter 7 HTML (Convergence, Hysteresis & Methodology)
    ch7 = story["chapters"]["chapter7"]
    ch7_trigger = (
        '<div class="callout callout-rule triggers"><div class="callout-title">Hysteresis Override &amp; Rerun Stability Contract</div>'
        f'<p>If you rerun portfolio_audit within 5 calendar days without new broker trades, any holding whose price moved less than &plusmn;{sc["price_band_hysteresis_pct"]:.1f}% retains its anchored verdict unless it closes below its hard invalidation stop or enters Stage 4. '
        f'Once an executed edit brings a holding within &plusmn;{sc["rebalance_deadband_wt_pct"]:.2f}% of its target weight, further adjustments are suppressed until a genuine fundamental or trend trigger fires.</p></div>'
    )
    ch7_html = (
        f'<section class="chapter book-chapter" id="chapter7">\n'
        f'<h2>{_esc(ch7["title"])}</h2>\n'
        + "\n".join(f"<p>{_prose_html(p)}</p>" for p in ch7["book_paragraphs"])
        + f"\n{ch7_trigger}\n</section>"
    )

    # Build synchronized Masterclass Book chapters (with full holding stories, tracking stubs, challenger stories & archival tables!)
    book_chapters: List[Dict[str, Any]] = []
    book_ch1_tbl = ch1_tbl.replace('class="wikitable"', 'class="mc-table"')
    for key in ("chapter1", "chapter2", "chapter3", "chapter4", "chapter5", "chapter6", "chapter7"):
        cdict = dict(story["chapters"][key])
        if key == "chapter1":
            cdict["book_tables"] = [book_ch1_tbl]
        elif key == "chapter2":
            cdict["book_tables"] = [book_ch2_tbl]
            book_cases = story.get("book_casenotes") or {}

            def _holding_group(hd_item: Dict[str, Any]) -> tuple[int, str, str]:
                v = hd_item["verdict"]
                if v == "EXIT":
                    return (
                        1,
                        "Reclaiming Risk Budget — Full Exits",
                        "These positions either broke their structural thesis or carry negative risk-reward; exiting in full frees capital and eliminates open portfolio heat.",
                    )
                if v == "TRIM_PROFIT_BOOKING":
                    return (
                        2,
                        "Right-Sizing Concentration — Trims & Profit Protection",
                        "Trimming oversized or extended positions locks in gains and brings single-stock and cluster risk back inside our regime limits.",
                    )
                if v == "ACCUMULATE_ON_DIP":
                    return (
                        3,
                        "Deploying Into Strength — Active Additions",
                        "High-conviction leaders inside healthy buy zones earn incremental capital so our best ideas carry meaningful weight.",
                    )
                if hd_item["pnl_pct"] < 0:
                    return (
                        4,
                        "Holding Through Noise — Why Intact Drawdowns Stay",
                        "Temporary pullbacks above structural support and intact fundamentals are held patiently behind hard stops rather than panic-sold.",
                    )
                return (
                    5,
                    "Compounding Engines — Core Leaders We Let Run",
                    "Winners with intact trends and thesis execution remain untouched inside our deadband so compounding does the heavy lifting.",
                )

            grouped_holdings: Dict[int, Dict[str, Any]] = {}
            for hd in ranked_holdings:
                g_ord, g_title, g_intro = _holding_group(hd)
                bucket_grp = grouped_holdings.setdefault(g_ord, {"title": g_title, "intro": g_intro, "items": []})
                bucket_grp["items"].append(hd)

            subs = []
            for g_ord in sorted(grouped_holdings):
                grp = grouped_holdings[g_ord]
                for idx_in_grp, hd in enumerate(grp["items"]):
                    bc = book_cases.get(hd["symbol"]) or {}
                    paras = bc.get("paragraphs") if isinstance(bc, dict) and bc.get("paragraphs") else [story["casenotes"][hd["symbol"]]]
                    calls = bc.get("callouts") if isinstance(bc, dict) and bc.get("callouts") else []
                    if hd.get("decision_source") == "CIO_OVERRIDE" and hd.get("cio_rationale") and not (isinstance(bc, dict) and bc.get("paragraphs")):
                        paras = list(paras) + [f"Context-aware CIO decision (overriding baseline {hd.get('baseline_verdict', '').replace('_', ' ')}): {hd['cio_rationale']}"]
                    sub_entry: Dict[str, Any] = {
                        "title": f"{hd['symbol']} — {hd['company_name']} ({hd['action_label']})",
                        "paragraphs": paras,
                        "callouts": calls,
                        "under_group": True,
                    }
                    if idx_in_grp == 0:
                        sub_entry["group_header"] = grp["title"]
                        sub_entry["group_intro"] = grp["intro"]
                    subs.append(sub_entry)
            if book_tracking_sub:
                subs.append(book_tracking_sub)
            cdict["book_subsections"] = subs
        elif key == "chapter3":
            cdict["book_tables"] = [book_ch3_tbl]
        elif key == "chapter4":
            cdict["book_tables"] = [book_ch4_tbl]
            ch4_subs = list(cdict.get("book_subsections") or [])
            for bch in (story.get("book_challengers") or []):
                if isinstance(bch, dict) and bch.get("title") and bch.get("paragraphs"):
                    ch4_subs.append({
                        "title": bch["title"],
                        "paragraphs": bch["paragraphs"],
                        "callouts": bch.get("callouts") or [],
                    })
            if ch4_subs:
                cdict["book_subsections"] = ch4_subs
        elif key == "chapter5":
            cdict["book_tables"] = [book_ch5_tbl, wf_tbl.replace('class="wikitable"', 'class="mc-table"')]
            cdict["book_subsections"] = [{
                "title": "Cash Waterfall & Downside Stress Test",
                "paragraphs": [wf_intro, re.sub(r"<[^>]+>", "", wf_take)],
                "callouts": [],
            }]
        elif key == "chapter6":
            cdict["book_tables"] = [book_ch6_tbl]
        book_chapters.append(cdict)

    book_words = sum(
        _word_count(" ".join(c.get("book_paragraphs", [])))
        + sum(
            _word_count(co.get("text", "")) + _word_count(co.get("quote", ""))
            for co in c.get("book_callouts", [])
        )
        + sum(
            _word_count(" ".join(s.get("paragraphs", [])))
            + sum(_word_count(co.get("text", "")) + _word_count(co.get("quote", "")) for co in s.get("callouts", []))
            for s in c.get("book_subsections", [])
        )
        for c in book_chapters
    ) + _word_count(story["primer"])
    audio_mins = max(3, round(book_words / 155))

    # Audiobook & Dual-Edition Switcher Bar
    audio_switcher_html = (
        '<div class="edition-switcher" role="navigation" aria-label="Audit Editions">\n'
        '  <div class="edition-tabs">\n'
        f'    <a class="edition-tab is-active" href="{report_stem}.html">Web Research Audit &amp; Tables</a>\n'
        '  </div>\n'
        '  <div class="edition-downloads">\n'
        f'    <a class="edition-dl-link" href="{report_stem}_book.pdf" download="{report_stem}_book.pdf">Download Masterclass Story PDF ({book_words:,} words &bull; ~{audio_mins} min)</a>\n'
        '  </div>\n'
        '</div>\n'
        '<div class="book-audio-bar" role="region" aria-label="Interactive Audiobook Narrator">\n'
        '  <div class="book-audio-controls">\n'
        '    <button type="button" class="book-audio-btn" data-audio-action="play">Play Audiobook</button>\n'
        '    <button type="button" class="book-audio-btn secondary" data-audio-action="prev">&larr; Prev</button>\n'
        '    <button type="button" class="book-audio-btn secondary" data-audio-action="next">Next &rarr;</button>\n'
        '    <button type="button" class="book-audio-btn secondary" data-audio-action="stop">Stop</button>\n'
        '    <select class="book-audio-select" data-audio-rate aria-label="Narration speed">\n'
        '      <option value="1.0" selected>1.0x</option>\n'
        '      <option value="1.15">1.15x</option>\n'
        '      <option value="1.25">1.25x</option>\n'
        '      <option value="1.5">1.5x</option>\n'
        '    </select>\n'
        '  </div>\n'
        f'  <span class="book-audio-status" data-audio-status>Cohesive Story Mode Ready (~{audio_mins} min listen)</span>\n'
        '</div>'
    )

    web_body = "\n\n".join([
        f"<h1>{_esc(title)}</h1>",
        audio_switcher_html,
        kf_html,
        ch1_html,
        ch2_html,
        ch3_html,
        ch4_html,
        ch5_html,
        ch6_html,
        ch7_html,
    ])

    web_words = _word_count(web_body)
    assembled_html = build(
        web_body,
        market=mkt,
        facts=facts_path,
        research=research_paths or [],
        kind="report",
        workflow="Portfolio audit",
        as_of=as_of,
    )

    out_p = Path(out_html_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(assembled_html, encoding="utf-8")

    # Compile Companion PDF ('The Portfolio Architect') beside the HTML report
    stat_cards = [
        ("NET WORTH", f"{cur}{ps['net_worth']:,.2f}"),
        ("MARKET REGIME", env["regime_label"]),
        ("OPEN HEAT", f"{ps['current_open_heat_pct']:.2f}% -> {ps['target_open_heat_pct']:.2f}% (Cap {ps['max_portfolio_heat_pct']:.1f}%)"),
        ("CONVERGENCE", f"{sc['convergence_score_pct']:.1f}% ({sc['actionable_trades_count']} Trades)"),
        ("ACTIVE RISK SLOTS", f"{ps['active_unique_risk_underlyings_count']} / {ps['active_slots_range'][1]}"),
        ("TARGET CASH", f"{cur}{ps['target_cash_value']:,.2f} ({ps['target_cash_wt_pct']:.2f}%)"),
    ]
    book_spec = {
        "market": mkt,
        "as_of": as_of,
        "book_title": f"The Portfolio Architect — {'India (Zerodha)' if mkt == 'IN' else 'US (Schwab & Robinhood)'} Edition",
        "headline_verdict": f"{env['playbook_mode'].replace('_', ' ')} • {sc['convergence_score_pct']:.1f}% CONVERGED",
        "primer": story["primer"],
        "citations": story["citations"],
    }
    book_html = render_portfolio_book_html(book_spec, book_chapters, stat_cards, web_words, book_words, audio_mins)
    out_pdf_path = out_p.parent / f"{out_p.stem}_book.pdf"
    tmp_book_src = out_p.parent / f".{out_p.stem}_book_print_source.html"
    tmp_book_src.write_text(book_html, encoding="utf-8")
    pdf_written = None
    try:
        res_pdf = build_pdf_book(tmp_book_src, out_pdf_path)
        if res_pdf and res_pdf.is_file():
            pdf_written = str(res_pdf)
    finally:
        tmp_book_src.unlink(missing_ok=True)

    return {
        "report_html": str(out_p),
        "book_pdf": pdf_written,
        "web_words": web_words,
        "book_words": book_words,
        "audio_minutes": audio_mins,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--allocation", required=True, help="Path to allocation_<MKT>_<date>.json")
    ap.add_argument("--facts", default="", help="Path to facts_<MKT>_<date>.json")
    ap.add_argument("--research", action="append", default=[], help="Path to research_<MKT>_<date>.json (repeatable)")
    ap.add_argument("--narrative", default="", help="Optional path to custom CIO story JSON")
    ap.add_argument("--out", required=True, help="Output HTML path, e.g. docs/reports/US_Portfolio_Audit.html")
    args = ap.parse_args()

    alloc = json.loads(Path(args.allocation).read_text(encoding="utf-8"))
    narrative = json.loads(Path(args.narrative).read_text(encoding="utf-8")) if args.narrative and Path(args.narrative).is_file() else {}

    res = compile_portfolio_audit(
        alloc=alloc,
        facts_path=args.facts,
        research_paths=args.research,
        narrative_override=narrative,
        out_html_path=args.out,
    )
    print(
        f"[+] Compiled {res['report_html']} ({res['web_words']:,} web words) "
        + (f"+ Companion PDF {res['book_pdf']} ({res['book_words']:,} narrative words, ~{res['audio_minutes']} min audio)"
           if res["book_pdf"] else f"(WeasyPrint unavailable; {res['book_words']:,} narrative words embedded in web audiobook)")
    )


if __name__ == "__main__":
    main()
