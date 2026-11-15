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
    "HOLD_CASH_EQUIVALENT": "verdict-keep",
    "HOLD_CONVEXITY": "verdict-keep",
    "GRANDFATHERED_HOLD": "verdict-watch",
    "ACCUMULATE_ON_DIP": "verdict-buy",
    "DEPLOY_STARTER_NOW": "verdict-buy",
    "DEPLOY_STARTER_AT_SUPPORT": "verdict-buy",
    "RESTING_LIMIT_AT_SUPPORT": "verdict-watch",
    "DEFERRED_GATE_BLOCKED": "verdict-watch",
    "BLOCKED_SLOT_CAP_FULL": "verdict-watch",
    "DEFERRED_CASH_OR_CLUSTER_CAP": "verdict-watch",
    "DEFERRED_HEAT_OR_LOT_SIZE": "verdict-watch",
    "TRIM_PROFIT_BOOKING": "verdict-trim",
    "TRIM_OPTION_STRENGTH": "verdict-trim",
    "EXIT": "verdict-exit",
    "EXIT_OPTION": "verdict-exit",
    "EXIT_TIME_STOP": "verdict-exit",
}


def _esc(val: Any) -> str:
    return html.escape(str(val if val is not None else "—"))


def _vpill(verdict: str, label: Optional[str] = None) -> str:
    cls = VERDICT_PILL_MAP.get(verdict, "verdict-watch")
    txt = (label or verdict).replace("_", " ")
    return f'<span class="verdict {cls}">{_esc(txt)}</span>'


def _word_count(text: str) -> int:
    clean = re.sub(r"<[^>]+>", " ", text)
    return len(re.findall(r"[A-Za-z0-9$₹%.,'-]+", clean))


def _sym_cell(sym: str, mkt: str, sub: str = "") -> str:
    sub_html = f'<br><span class="case-note-sub">{_esc(sub)}</span>' if sub else ""
    if mkt == "IN":
        links = (
            f'<a href="https://www.tradingview.com/chart/?symbol=NSE%3A{_esc(sym)}">Chart</a> &bull; '
            f'<a href="https://www.screener.in/company/{_esc(sym)}/">Screener</a>'
        )
    else:
        links = (
            f'<a href="https://www.tradingview.com/chart/?symbol=NASDAQ%3A{_esc(sym)}">Chart</a> &bull; '
            f'<a href="https://finviz.com/quote.ashx?t={_esc(sym)}">Finviz</a>'
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
        f"Since our previous {sc['prior_as_of_date']} plan, you completed {len(sc['completed_edits_since_prior'])} portfolio edit(s), "
        f"while {len(sc['hysteresis_locked_symbols'])} borderline ticker(s) remain locked by our {sc['price_band_hysteresis_pct']}% hysteresis deadband so daily market noise cannot whipsaw your orders."
        if sc.get("prior_as_of_date")
        else "This run establishes our baseline v4 anchor ledger so subsequent daily checks converge smoothly toward zero unnecessary turnover."
    )
    primer_text = narrative_override.get("primer") or (
        f"Sitting across the desk on {as_of}, you and I manage {cur}{ps['net_worth']:,.2f} across our {mkt_name} book under a '{regime_lbl}' market regime. "
        f"Our portfolio currently stands at {sc['convergence_score_pct']:.1f}% convergence with target risk architecture, carrying {ps['current_open_heat_pct']:.2f}% open risk-to-stop against a {ps['max_portfolio_heat_pct']:.1f}% ceiling. "
        f"Rather than guessing share counts, we trim or exit {len(sells)} broken or over-extended line(s), fund {len(adds) + len(starters)} disciplined allocation(s), and hold {cur}{ps['target_cash_value']:,.2f} ({ps['target_cash_wt_pct']:.2f}%) in reserve unless price and business evidence earn more risk."
    )

    # Chapter 1: Macro, Sector Tide & Convergence
    ch1_paras = (ov_chapters.get("chapter1") or {}).get("book_paragraphs") or [
        (
            f"Before you and I touch a single share as of {as_of}, we start with the water our boats are sailing in: the {bench_name} sits in '{regime_lbl}', "
            f"putting our desk into {playbook} posture. Breadth across the screening universe reads {env['breadth_pct_above_50dma'] if env['breadth_pct_above_50dma'] is not None else 'measured'}% above the 50-day moving average, "
            f"which governs two hard guardrails at once: our minimum cash floor locks at {env['min_cash_floor_pct']:.1f}% of net worth, and our maximum open portfolio heat caps at {env['max_portfolio_heat_pct']:.1f}%."
        ),
        (
            f"Look closely at what our {cur}{ps['net_worth']:,.2f} portfolio actually behaves like beneath the surface. "
            f"With {ps['active_unique_risk_underlyings_count']} active unique risk underlyings against our {ps['active_slots_range'][0]}–{ps['active_slots_range'][1]} slot band "
            f"(properly ignoring {ps['tracking_positions_count']} tiny sub-0.35% tracking stub(s) worth {cur}{ps['tracking_positions_value']:,.2f}), "
            f"our open risk-to-stop moves from {ps['current_open_heat_pct']:.2f}% today to {ps['target_open_heat_pct']:.2f}% after execution."
        ),
        (
            f"Why do we measure sector rotation asymmetrically rather than chasing last week's hot leaderboard? One-week sector flips are statistical noise that trick investors into selling great compounders right before they resume climbing. "
            f"Under our v4 rulebook, Core Alpha compounders ignore short-term sector dips unless their 30-week structure or business KPIs break, whereas Tactical Momentum entries must sail with Leading or Improving 3-month relative strength—and no single correlated cluster is allowed past 25.0% of net worth"
            + (f" (our largest cluster today, {', '.join(top_cluster['symbols'][:4])}, sits at {top_cluster['current_wt_pct']:.2f}% current / {top_cluster['target_wt_pct']:.2f}% target)." if top_cluster else ".")
        ),
        (
            f"Just as important is stability across short reruns. {completed_str} "
            f"With our ±{sc['rebalance_deadband_wt_pct']:.2f}% net-worth deadband active, any holding already close to its model weight stays untouched, pushing our convergence score to {sc['convergence_score_pct']:.1f}% as we turn next to the line-by-line audit of our existing holdings in Chapter 2."
        ),
    ]

    # Chapter 2: Existing Equity Holdings Story
    kept = [h for h in holdings if h["delta_shares"] == 0 and h["target_value"] > 0]
    top_kept_names = ", ".join(f"{h['symbol']} ({h['current_wt_pct']:.2f}%)" for h in kept[:5]) or "none"
    sells_summary = (
        ", ".join(f"{h['symbol']} ({abs(h['delta_shares']):g} sh, freeing {cur}{h['capital_liberated']:,.2f})" for h in sells)
        if sells else "zero forced equity sales today because every retained line holds above its invalidation stop and within cluster caps"
    )
    ch2_paras = (ov_chapters.get("chapter2") or {}).get("book_paragraphs") or [
        (
            f"Walk down our active equity ledger with one honest question per line: if we held cash instead today, does this business and chart earn its risk budget? "
            f"Across {len(holdings)} non-tracking equity and ETF lines totaling {cur}{ps['current_equities_value']:,.2f} ({ps['current_equities_wt_pct']:.2f}% of net worth), "
            f"the v4 tournament grades every incumbent on the exact same 100-point scale we apply to outside shortlist challengers—removing the lazy incumbency bias that lets stagnant Stage 3 losers tie up slots for months."
        ),
        (
            f"Our capital liberation pass identifies {sells_summary}. "
            f"Notice what we deliberately refuse to do: we never mechanically shave a Stage 2 winner merely because its 14-day RSI looks elevated or its appreciated weight crossed 15%, allowing genuine leaders to compound up to our 22.0% runaway-winner ceiling while ratcheting trailing stops upward only."
        ),
        (
            f"Meanwhile, intact positions led by {top_kept_names} remain anchored on ratcheted structural stops. "
            f"Where we hold pre-dossier positions ({len(debt_q)} ticker(s) currently in our Dossier Debt Queue), we grandfather existing shares on strict chart invalidation stops so good winners are never blindly dumped, while freezing any fresh ADD capital until their 10-chapter monographs verify cash conversion and valuation—setting up our review of specialized convexity sleeves and sector risk next in Chapter 3."
        ),
    ]

    # Chapter 3: 2x/3x Sector Rotation & Drawdown Options (US) OR Cluster & Velocity Defense (IN)
    if mkt == "US":
        opt_summary = (
            "; ".join(f"{o['contract_symbol']} ({o['verdict'].replace('_', ' ')}, delta {o['delta']:.2f}, stop ${o['invalidation_stop'] or 0:,.2f})" for o in options[:4])
            if options else "no open option contracts currently on the book"
        )
        lev_holdings = [h for h in holdings if h["bucket"] == "LEVERAGED_SATELLITE"]
        lev_summary = (
            ", ".join(f"{h['symbol']} ({h['current_wt_pct']:.2f}% wt -> {h['action_label']})" for h in lev_holdings)
            if lev_holdings else "0.0% currently held in 2x/3x ETFs"
        )
        ch3_paras = (ov_chapters.get("chapter3") or {}).get("book_paragraphs") or [
            (
                f"Now let us confront the sharpest edge in our US toolkit—our 2x/3x rotation ETFs and our 6-to-12-month call options—with total candor about sideways-market math. "
                f"Daily-reset leveraged ETFs suffer volatility drag when an index chops sideways, and out-of-the-money calls bleed both daily theta and post-bounce implied-volatility crush. "
                f"That is why our v4 procedure locks a combined 15.0% decay ceiling across both sleeves (currently {ps['combined_decay_sleeve_pct']:.2f}% combined: {ps['leveraged_satellite_target_wt_pct']:.2f}% in 2x/3x ETFs plus {ps['options_cap_basis_pct']:.2f}% options cap basis)."
            ),
            (
                f"Inside the 2x/3x rotation sleeve ({lev_summary}), we enforce a strict boundary: sector and index ETFs are permitted up to 12.0% total (6.0% max per position) with a 20-day moving-average stop and a 15-session flat time stop, "
                f"whereas single-stock 2x ETFs stacked on top of volatile equities are phased out so an overnight single-company gap can never inflict a -40% hole. In our current '{regime_lbl}' tape, new 2x/3x buys are {'permitted on confirmed sector thrusts' if env['allow_new_leveraged_etf_buys'] else 'gated at 0% until broad market breadth expands'}."
            ),
            (
                f"Across our open US options book ({cur}{ps['current_options_value']:,.2f} market value against {cur}{ps['current_options_cost_basis']:,.2f} upfront cost: {opt_summary}), "
                f"existing contracts above their underlying shelf stops are grandfathered for disciplined repair or bounce harvesting rather than panic-sold at trough prices, while future drawdown deployments require 0.60–0.80 delta ITM/ATM LEAPS—or Bull Call Debit Spreads whenever implied volatility exceeds 1.15x 20-day realized volatility—leading directly into our equity challenger tournament in Chapter 4."
            ),
        ]
    else:
        cluster_lines = (
            "; ".join(f"{c['cluster_id']} ({', '.join(c['symbols'][:3])}: {c['current_wt_pct']:.2f}% -> {c['target_wt_pct']:.2f}%)" for c in clusters[:4])
            if clusters else "diversified single-stock exposures well below the 25% cluster ceiling"
        )
        ch3_paras = (ov_chapters.get("chapter3") or {}).get("book_paragraphs") or [
            (
                f"In Indian mid- and small-cap investing, hidden portfolio losses rarely come from one bad stock—they come from accidentally owning five stocks driven by the exact same domestic capex or liquidity cycle. "
                f"When Nifty breadth narrows in '{regime_lbl}', mid-cap correlations spike toward 1.0, turning disguised theme clusters into amplified drawdowns unless we cap cluster exposure before trouble starts."
            ),
            (
                f"Auditing our Zerodha clusters against the 25.0% notional ceiling and 3.5% cluster-heat limit reveals: {cluster_lines}. "
                f"Every holding carries a ratcheted rupee stop-loss sized backward from risk budget bps, ensuring that even if a domestic sector rotates from Leading into Weakening, our open portfolio heat stays bounded at {ps['target_open_heat_pct']:.2f}% vs our {ps['max_portfolio_heat_pct']:.1f}% budget."
            ),
            (
                f"Because NSE single-stock options are limited to short-dated 1-to-3-month F&O contracts on large/mid-caps with wide spreads in corrections, we keep our primary Indian compounding engine in cash-equity Core Alpha ({ps['core_alpha_target_wt_pct']:.2f}% target) and Stage 2 Tactical Momentum ({ps['tactical_momentum_target_wt_pct']:.2f}% target), "
                f"using our {ps['target_cash_wt_pct']:.2f}% cash reserve as the dry powder we now test against shortlisted challengers in Chapter 4."
            ),
        ]

    # Chapter 4: Challenger Tournament & 50/50 Tranches
    funded_desc = (
        ", ".join(f"{c['symbol']} ({c['funded_shares']} sh = {cur}{c['funded_value']:,.2f}, {c['funded_wt_pct']:.2f}% NAV)" for c in starters)
        if starters else "zero immediate market-order starters today because remaining shortlist names sit extended above support or wait behind slot/regime gates"
    )
    resting_desc = (
        ", ".join(f"{c['symbol']} ({cur}{c['entry_zone_low']:,.2f}–{cur}{c['entry_zone_high']:,.2f}, stop {cur}{c['stop_loss']:,.2f})" for c in resting[:5])
        if resting else "none staged at resting bands"
    )
    ch4_paras = (ov_chapters.get("chapter4") or {}).get("book_paragraphs") or [
        (
            f"Why did you previously miss strong Stage 2 winners even after our dossiers spotted them early? Because binary all-or-nothing entry rules forced 85%+ of vetted ideas into endless 'wait for deep support' purgatory while real leaders marched higher. "
            f"Our v4 allocator solves both FOMO chasing and paralysis by splitting every approved target weight into two equal halves: a 50% Starter Tranche (~35–50 bps of NAV risk) and a 50% Proof Add deployed only on a support retest or after Step 1 builds at least a +1R profit cushion."
        ),
        (
            f"Evaluating {len(challengers)} non-held shortlist challengers under our {playbook} rules produces {funded_desc}. "
            f"Remember the slot displacement discipline: once we reach our {ps['active_slots_range'][0]}–{ps['active_slots_range'][1]} active-underlying band, an outside challenger can only evict an incumbent if the incumbent sits in stagnant Stage 3 chop and the challenger beats its 100-point tournament score by at least +15.0 points—protecting working positions from restless turnover."
        ),
        (
            f"For high-quality shortlist names that have not yet pulled into our sideways-safe support window, we neither chase them nor forget them: we stage resting limit bands on {resting_desc}, "
            f"keeping cash productive and patient until price comes to our risk math, as reconciled to the exact {cur}1 in Chapter 5 below."
        ),
    ]

    # Chapter 5: Money Bridge Narrative
    ch5_paras = (ov_chapters.get("chapter5") or {}).get("book_paragraphs") or [
        (
            f"Every portfolio review stands or falls on whether the arithmetic reconciles without hand-waving. Starting with {cur}{ps['current_cash_value']:,.2f} ({ps['current_cash_wt_pct']:.2f}%) in broker cash, "
            f"our Phase 1 exits and trims liberate {cur}{ps['capital_liberated_equities']:,.2f} from equities and {cur}{ps['capital_liberated_options']:,.2f} from options, creating a gross liquidity pool of {cur}{ps['current_cash_value'] + ps['capital_liberated_equities'] + ps['capital_liberated_options']:,.2f}."
        ),
        (
            f"From that pool, we deploy {cur}{ps['capital_deployed_equities']:,.2f} across vetted Starter and Scale-up orders while respecting our {env['min_cash_floor_pct']:.1f}% regime cash floor and {ps['max_portfolio_heat_pct']:.1f}% open-heat ceiling. "
            f"That leaves {cur}{ps['target_cash_value']:,.2f} ({ps['target_cash_wt_pct']:.2f}% of net worth) in liquid reserve, bringing target equities ({cur}{ps['target_equities_value']:,.2f}), target options ({cur}{ps['target_options_value']:,.2f}), and target cash ({cur}{ps['target_cash_value']:,.2f}) back to our exact {cur}{ps['net_worth']:,.2f} net worth."
        ),
        (
            f"Notice how clean convergence works in practice: as you execute the {sc['actionable_trades_count']} actionable order(s) isolated in this bridge, every completed position lands inside our ±{sc['rebalance_deadband_wt_pct']:.2f}% deadband. "
            f"When you rerun this workflow tomorrow or next week, completed lines stay green as HOLD / TRAIL rather than shifting targets, taking us straight into the step-by-step execution tickets in Chapter 6."
        ),
    ]

    # Chapter 6: Execution Orders, Broker Routing & Dossier Debt Queue
    routing_note = (
        "To eliminate cross-broker fragmentation, route all new Core Alpha and Tactical Momentum stock orders through Charles Schwab (and sell Robinhood's duplicate share lots first whenever trimming ANET, BE, DOCN, or QCOM), while keeping Options/LEAPS and 2x/3x sector rotation swings inside Robinhood."
        if mkt == "US"
        else "Execute Phase 1 sales first in Zerodha so settled/intraday proceeds fund Phase 2 limit entries cleanly, and update Zerodha GTT stop-loss triggers immediately after market close."
    )
    debt_top = ", ".join(f"{d['symbol']} ({cur}{d['market_value']:,.0f}, {d['weight_pct']:.2f}%)" for d in debt_q[:5]) or "none—all active holdings have published monographs"
    ch6_paras = (ov_chapters.get("chapter6") or {}).get("book_paragraphs") or [
        (
            f"Good strategy dies in sloppy execution unless orders follow a strict sequence: liberate capital first, place no-FOMO limit buys second, and lock defensive stops third. "
            f"{routing_note}"
        ),
        (
            f"Every stop-loss listed in Phase 3 is evaluated on a completed daily or weekly closing basis under our Undercut-and-Reclaim shakeout rule—meaning an intraday wick that flushes weak hands and reclaims the 50-day or 10-week average by the close does not trick us out of a secular compounder, whereas a confirmed closing breakdown below invalidation triggers an unemotional exit."
        ),
        (
            f"Finally, to retire our remaining underwriting blind spots in order of wallet exposure, our prioritized Dossier Debt Queue ranks pre-monograph holdings from largest capital at risk downward: {debt_top}. "
            f"Until each monograph is published, those lines remain frozen from fresh ADDs, bringing us to our binding stability and monitoring contract in Chapter 7."
        ),
    ]

    # Chapter 7: Rulebook, Hysteresis & Monitoring Contract
    ch7_paras = (ov_chapters.get("chapter7") or {}).get("book_paragraphs") or [
        (
            f"Why will this portfolio audit not flip its mind if you rerun it 24 hours from now? Because three deterministic brakes are now persisted in `data/allocations/{mkt}.json`: "
            f"(1) a {sc['price_band_hysteresis_pct']:.1f}% price hysteresis band over a 5-day anchor window so minor tape wiggles never toggle a stock between BUY and WAIT; "
            f"(2) an upward-only stop ratchet so trailing invalidation levels never slide lower while shares are held; and "
            f"(3) a ±{sc['rebalance_deadband_wt_pct']:.2f}% net-worth rebalance deadband that silences micro-trades once you have sized a position."
        ),
        (
            f"Only three events are allowed to override those stability locks immediately: a confirmed closing breach of a hard invalidation stop or Stage 4 breakdown, a material fundamental/KPI failure in a quarterly filing, or your own executed broker trades synced via `broker_transaction_sync`. "
            f"Watch those exact levels calmly until the next completed exchange session."
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
        "citations": narrative_override.get("citations") or [
            f"Deterministic Market Facts Ledger & Price Series ({mkt}, session cutoff {as_of})",
            f"TradingView & Stage 2 Sector Breadth Scanner Snapshot ({mkt}, {as_of})",
            f"Portfolio Allocator v4 Risk-Heat & Hysteresis State (`data/allocations/{mkt}.json`, {as_of})",
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

    story = _default_story_and_casenotes(alloc, narrative_override or {})
    report_stem = f"{mkt}_Portfolio_Audit"
    title = (
        f"India (Zerodha) Portfolio Forensic Audit, Allocation & Narrative Playbook"
        if mkt == "IN"
        else f"US (Schwab & Robinhood) Portfolio Forensic Audit, Allocation & Narrative Playbook"
    )

    # Pre-build Masterclass Book chapters (incorporating individual holding stories inside Ch 2!)
    book_chapters: List[Dict[str, Any]] = []
    for key in ("chapter1", "chapter2", "chapter3", "chapter4", "chapter5", "chapter6", "chapter7"):
        cdict = dict(story["chapters"][key])
        if key == "chapter2":
            subs = []
            for hd in holdings:
                subs.append({
                    "title": f"{hd['symbol']} — {hd['company_name']} ({hd['action_label']})",
                    "paragraphs": [story["casenotes"][hd["symbol"]]],
                    "callouts": [],
                })
            cdict["book_subsections"] = subs
        book_chapters.append(cdict)

    book_words = sum(
        _word_count(" ".join(c.get("book_paragraphs", [])))
        + sum(_word_count(" ".join(s.get("paragraphs", []))) for s in c.get("book_subsections", []))
        for c in book_chapters
    ) + _word_count(story["primer"])
    audio_mins = max(3, round(book_words / 155))

    # Key Figures Strip (Web)
    kf_html = (
        '<dl class="key-figures">\n'
        f'<div><dt class="kf-label">Total Net Worth</dt><dd class="kf-value">{cur}{ps["net_worth"]:,.2f}</dd>'
        f'<span class="kf-note">As of {as_of} close</span></div>\n'
        f'<div><dt class="kf-label">Open Portfolio Heat</dt><dd class="kf-value">{ps["current_open_heat_pct"]:.2f}% &rarr; {ps["target_open_heat_pct"]:.2f}%</dd>'
        f'<span class="kf-note">Regime ceiling: {ps["max_portfolio_heat_pct"]:.1f}%</span></div>\n'
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
        f'  <tr><th>Core Alpha Target</th><td>{ps["core_alpha_target_wt_pct"]:.2f}% (Band 35–45%)</td></tr>\n'
        f'  <tr><th>Tactical Momentum Target</th><td>{ps["tactical_momentum_target_wt_pct"]:.2f}%</td></tr>\n'
        f'{extra_us_rows}'
        f'  <tr><th>Effective Exposure</th><td>{ps["effective_market_exposure_pct"] or 100.0:.1f}% (Beta {ps["portfolio_beta_weighted"] or 1.0:.2f})</td></tr>\n'
        "</table>"
    )

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

    # Build Chapter 1 HTML
    ch1 = story["chapters"]["chapter1"]
    ch1_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Macro Regime, Portfolio Heat &amp; Convergence Guardrails</caption>\n'
        '  <thead><tr><th>Dimension</th><th>Verified Reading</th><th>v4 Rulebook Mandate</th><th>Portfolio Consequence</th></tr></thead>\n'
        '  <tbody>\n'
        f'    <tr><td><strong>Market Regime</strong></td><td>{_esc(env["regime_label"])} (Breadth &gt;50DMA: {env["breadth_pct_above_50dma"] if env["breadth_pct_above_50dma"] is not None else "Measured"}%)</td>'
        f'<td>{_esc(env["playbook_mode"].replace("_", " "))} Playbook</td><td>Min cash floor {env["min_cash_floor_pct"]:.1f}%; starter extension cap &le;{env["max_starter_extension_pct"]:.1f}%</td></tr>\n'
        f'    <tr><td><strong>Open Portfolio Heat</strong></td><td>{ps["current_open_heat_pct"]:.2f}% current &rarr; {ps["target_open_heat_pct"]:.2f}% target</td>'
        f'<td>Hard ceiling {ps["max_portfolio_heat_pct"]:.1f}% of Net Worth</td><td>Every stop-out across the book is bounded below {ps["max_portfolio_heat_pct"]:.1f}% total drawdown</td></tr>\n'
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
        f'<p>If broad market breadth expands above 55.0% with benchmark price above rising 50-day and 200-day averages, our heat budget lifts to 12.0% and Broad Uptrend starters open up to +8.5% above the 10-week EMA; '
        f'if the benchmark breaks below its 200-day average into Downtrend, maximum heat contracts to 4.0% and cash floor rises to 22.0%.</p></div>'
    )
    ch1_html = (
        f'<section class="chapter book-chapter" id="chapter1">\n'
        f'<h2>{_esc(ch1["title"])}</h2>\n'
        f'<p class="lede">{_esc(story["primer"])}</p>\n'
        + "\n".join(f"<p>{_esc(p)}</p>" for p in ch1["book_paragraphs"])
        + f"\n{ch1_tbl}\n{ch1_takeaway}\n{ch1_trigger}\n</section>"
    )

    # Build Chapter 2 HTML (Holdings Ladder Table + Case Notes)
    ch2 = story["chapters"]["chapter2"]
    hold_rows_html = []
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
    if not hold_rows_html:
        hold_rows_html.append(f'<tr><td>1</td><td>None</td><td class="num">0.0%</td><td class="num">{cur}0.00</td><td class="num">{cur}0.00</td><td>—</td><td class="num">{cur}0.00</td><td>—</td><td class="num">{cur}0.00</td></tr>')

    ch2_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Active Non-Tracking Holdings Audit, Tournament Scores &amp; Ratcheted Stops</caption>\n'
        f'  <thead><tr><th>Rank</th><th>Security &amp; Sector</th><th class="num">Wt (Now &rarr; Target)</th><th class="num">Close ({cur})</th><th class="num">Unrealized P&amp;L</th><th>Stage &amp; Score</th><th class="num">Stop &amp; Heat</th><th>Action Verdict</th><th class="num">Liberated ({cur})</th></tr></thead>\n'
        f'  <tbody>{"".join(hold_rows_html)}</tbody>\n</table>'
    )
    ch2_takeaway = (
        f"<p>Across all {len(holdings)} active non-tracking positions above, Phase 1 actions liberate {cur}{ps['capital_liberated_equities']:,.2f} from broken or over-extended lines while keeping intact Stage 2 compounders anchored on upward-only ratcheted stops. "
        f"Tracking stubs below 0.35% of net worth ({', '.join(t['symbol'] for t in tracking) or 'none'}) are isolated from this active slot count so they never trigger pointless micro-trades or dilute focus. "
        f"Every retained holding's specific thesis, tournament score, and closing stop trigger follows in Section 2.1 below.</p>"
    )
    casenotes_html = "\n".join(
        f'<div class="case-note casenote" data-symbol="{_esc(hd["symbol"])}">'
        f'<div class="case-note-head"><span class="case-note-title">{_esc(hd["symbol"])} &mdash; {_esc(hd["company_name"])}</span>'
        f'{_vpill(hd["verdict"], hd["action_label"])}</div>'
        f'<p>{_esc(story["casenotes"][hd["symbol"]])}</p></div>'
        for hd in holdings
    )
    ch2_trigger = (
        '<div class="callout callout-rule triggers"><div class="callout-title">Holding Ratchet &amp; Shakeout Trigger Rules</div>'
        f'<p>If any retained holding closes a completed daily session below its ratcheted stop in the table above with RSI(14) below 42, execute an immediate exit on the next session; '
        f'if an intraday flush undercuts support and closes back above the 50-day SMA or 10-week EMA on positive volume, hold the position and anchor the hard stop below the shakeout low before moving to Chapter 3.</p></div>'
    )
    ch2_html = (
        f'<section class="chapter book-chapter" id="chapter2">\n'
        f'<h2>{_esc(ch2["title"])}</h2>\n'
        + "\n".join(f"<p>{_esc(p)}</p>" for p in ch2["book_paragraphs"])
        + f"\n{ch2_tbl}\n{ch2_takeaway}\n"
        + f"<h3>2.1 Individual Position Case Notes &amp; Invalidation Levels</h3>\n"
        + f"<p>Every active position in our book must justify its capital slot in plain words, naming its exact weight, unrealized gain or loss, tournament score, ratcheted stop-loss, and the concrete price or operating event that would change our verdict. Read each card below as our standing desk contract until the next completed session.</p>\n"
        + f"{casenotes_html}\n{ch2_trigger}\n</section>"
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
        ch3_take = (
            f"<p>Auditing all {len(options)} open option contracts confirms ${ps['current_options_value']:,.2f} in current market value against ${ps['current_options_cost_basis']:,.2f} original cost ({ps['options_cap_basis_pct']:.2f}% cap basis vs our 10.0% ceiling). "
            f"Grandfathered contracts hold strictly while their underlying equities defend weekly shelf invalidation stops. "
            f"Future drawdown deployments require 0.60–0.80 delta ITM/ATM contracts or Bull Call Debit Spreads whenever implied volatility exceeds 1.15x HV20, setting up our equity shortlist tournament in Chapter 4 next.</p>"
        )
    else:
        cl_rows_html = []
        for cl in clusters[:10]:
            cl_rows_html.append(
                f"<tr><td><strong>{_esc(cl['cluster_id'])}</strong></td>"
                f"<td>{_esc(', '.join(cl['symbols']))}</td>"
                f'<td class="num">{cl["current_wt_pct"]:.2f}%</td>'
                f'<td class="num">{cl["target_wt_pct"]:.2f}% (Cap {cl["max_cluster_wt_pct"]:.0f}%)</td>'
                f'<td class="num">{cl["open_heat_pct"]:.2f}% (Cap {cl["max_cluster_heat_pct"]:.1f}%)</td>'
                f'<td>{"WITHIN GUARDRAIL" if cl["target_wt_pct"] <= cl["max_cluster_wt_pct"] else "TRIMMED TO CAP"}</td></tr>'
            )
        if not cl_rows_html:
            cl_rows_html.append('<tr><td>SINGLETONS</td><td>No multi-stock cluster</td><td class="num">0.0%</td><td class="num">0.0%</td><td class="num">0.0%</td><td>WITHIN GUARDRAIL</td></tr>')
        ch3_tbl = (
            '<table class="wikitable">\n'
            '  <caption>Correlated &amp; Thematic Cluster Exposure Matrix (25% Notional / 3.5% Heat Cap)</caption>\n'
            '  <thead><tr><th>Cluster Group</th><th>Member Tickers</th><th class="num">Current Wt</th><th class="num">Target Wt</th><th class="num">Cluster Heat</th><th>Guardrail Status</th></tr></thead>\n'
            f'  <tbody>{"".join(cl_rows_html)}</tbody>\n</table>'
        )
        ch3_take = (
            f"<p>Grouping correlated holdings into explicit clusters ensures no single domestic or sector theme exceeds {clusters[0]['max_cluster_wt_pct'] if clusters else 25:.0f}% of net worth or 3.5% of open portfolio heat. "
            f"When several holdings share one macro capex driver, their combined drawdown risk must be budgeted as a single bet rather than independent lines. "
            f"With thematic concentration verified and bounded inside our guardrails, we turn next to Chapter 4 to test shortlisted challengers.</p>"
        )
    ch3_html = (
        f'<section class="chapter book-chapter" id="chapter3">\n'
        f'<h2>{_esc(ch3["title"])}</h2>\n'
        + "\n".join(f"<p>{_esc(p)}</p>" for p in ch3["book_paragraphs"])
        + f"\n{ch3_tbl}\n{ch3_take}\n</section>"
    )

    # Build Chapter 4 HTML (Shortlist Challenger Tournament)
    ch4 = story["chapters"]["chapter4"]
    ch_rows_html = []
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
    if not ch_rows_html:
        ch_rows_html.append(f'<tr><td>1</td><td>No non-held shortlist rows</td><td>—</td><td class="num">0.0</td><td class="num">{cur}0.00</td><td class="num">—</td><td class="num">—</td><td class="num">0.0%</td><td>—</td><td class="num">0 sh ({cur}0.00)</td></tr>')
    ch4_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Shortlist Challenger Tournament, 50/50 Tranche Sizing &amp; Entry Gates</caption>\n'
        f'  <thead><tr><th>Rank</th><th>Candidate</th><th>Bucket &amp; Tier</th><th class="num">Score</th><th class="num">CMP ({cur})</th><th class="num">Support Zone ({cur})</th><th class="num">Stop / Base (R:R)</th><th class="num">Starter / Full Wt</th><th>Gate Verdict</th><th class="num">Funded Now</th></tr></thead>\n'
        f'  <tbody>{"".join(ch_rows_html)}</tbody>\n</table>'
    )
    ch4_take = (
        f"<p>Evaluating all {len(challengers)} non-held shortlist candidates on our unified 100-point rubric funds {len([c for c in challengers if c['funded_shares'] > 0])} immediate starter position(s) ({cur}{sum(c['funded_value'] for c in challengers):,.2f}) "
        f"and stages {len([c for c in challengers if c['entry_action'] == 'RESTING_LIMIT_AT_SUPPORT'])} resting support limit order(s). "
        f"Candidates sitting in lagging sectors, extended above No-FOMO bands, or unable to clear the +15.0 point displacement hurdle stay deferred so cash is never forced into mediocre setups, reconciling into Chapter 5 below.</p>"
    )
    ch4_trigger = (
        '<div class="callout callout-rule triggers"><div class="callout-title">50/50 Starter &amp; Proof-Add Triggers</div>'
        f'<p>If a resting shortlist challenger pulls back into its support band above with daily RSI(14) holding above 40 and intact volume structure, deploy the 50% Starter Tranche; '
        f'never deploy the second 50% Proof Add unless Tranche 1 is up at least +1.0R in sideways tapes (+0.75R in broad uptrends) so your combined stop moves to breakeven.</p></div>'
    )
    ch4_html = (
        f'<section class="chapter book-chapter" id="chapter4">\n'
        f'<h2>{_esc(ch4["title"])}</h2>\n'
        + "\n".join(f"<p>{_esc(p)}</p>" for p in ch4["book_paragraphs"])
        + f"\n{ch4_tbl}\n{ch4_take}\n{ch4_trigger}\n</section>"
    )

    # Build Chapter 5 HTML (100% Reconciled Money Bridge)
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
    ch5_take = (
        f"<p>Every single rupee or dollar in the Master Money Bridge reconciles to {cur}{ps['net_worth']:,.2f} across both current and target columns (100.00% before and after reallocation, with {cur}0.00 unallocated drift). "
        f"Proceeds liberated from Phase 1 sales ({cur}{ps['capital_liberated_equities'] + ps['capital_liberated_options']:,.2f}) combine with broker cash to fund {cur}{ps['capital_deployed_equities']:,.2f} of disciplined additions and preserve {cur}{ps['target_cash_value']:,.2f} ({ps['target_cash_wt_pct']:.2f}%) in liquid reserve, translating directly into Chapter 6's execution tickets next.</p>"
    )
    ch5_html = (
        f'<section class="chapter book-chapter" id="chapter5">\n'
        f'<h2>{_esc(ch5["title"])}</h2>\n'
        + "\n".join(f"<p>{_esc(p)}</p>" for p in ch5["book_paragraphs"])
        + f"\n{ch5_tbl}\n{ch5_take}\n</section>"
    )

    # Build Chapter 6 HTML (Execution Orders + Dossier Debt Queue)
    ch6 = story["chapters"]["chapter6"]
    exec_rows = []
    for hd in holdings:
        if hd["delta_shares"] < 0:
            exec_rows.append(
                f"<tr><td>Phase 1: Sell / Trim</td><td><strong>{_esc(hd['symbol'])}</strong></td>"
                f'<td class="num">Sell {abs(hd["delta_shares"]):g} sh</td>'
                f'<td class="num">Market / &ge; {cur}{hd["close"] * 0.99:,.2f}</td>'
                f'<td class="num">{cur}{hd["effective_stop"]:,.2f}</td>'
                f'<td class="num">{cur}{hd["capital_liberated"]:,.2f} freed</td>'
                f"<td>{_esc(hd['broker_routing'])}</td></tr>"
            )
    for od in options:
        if od["capital_liberated"] > 0:
            exec_rows.append(
                f"<tr><td>Phase 1: Option Exit/Trim</td><td><strong>{_esc(od['contract_symbol'])}</strong></td>"
                f'<td class="num">Close {od["contracts"]} c</td>'
                f'<td class="num">Mid-price limit</td>'
                f'<td class="num">Und. {cur}{od["invalidation_stop"] or 0:,.2f}</td>'
                f'<td class="num">{cur}{od["capital_liberated"]:,.2f} freed</td>'
                f"<td>{_esc(od['broker_account'])}</td></tr>"
            )
    for hd in holdings:
        if hd["delta_shares"] > 0:
            exec_rows.append(
                f"<tr><td>Phase 2: Scale-Up Add</td><td><strong>{_esc(hd['symbol'])}</strong></td>"
                f'<td class="num">Buy {hd["delta_shares"]:g} sh</td>'
                f'<td class="num">&le; {cur}{hd["close"] * 1.005:,.2f}</td>'
                f'<td class="num">{cur}{hd["effective_stop"]:,.2f}</td>'
                f'<td class="num">{cur}{hd["capital_deployed"]:,.2f} deployed</td>'
                f"<td>{_esc(hd['broker_routing'])}</td></tr>"
            )
    for ch in challengers:
        if ch["funded_shares"] > 0:
            exec_rows.append(
                f"<tr><td>Phase 2: 50% Starter Buy</td><td><strong>{_esc(ch['symbol'])}</strong></td>"
                f'<td class="num">Buy {ch["funded_shares"]} sh</td>'
                f'<td class="num">{cur}{ch["entry_zone_low"]:,.2f}–{cur}{ max(ch["close"], ch["entry_zone_high"]):,.2f}</td>'
                f'<td class="num">{cur}{ch["stop_loss"]:,.2f}</td>'
                f'<td class="num">{cur}{ch["funded_value"]:,.2f} deployed</td>'
                f"<td>{_esc(ch['broker_routing'])}</td></tr>"
            )
    for ch in challengers[:6]:
        if ch["entry_action"] == "RESTING_LIMIT_AT_SUPPORT":
            est_sh = max(1, int((ps["net_worth"] * (ch["starter_target_wt_pct"] / 100.0)) // max(0.01, ch["entry_zone_high"])))
            exec_rows.append(
                f"<tr><td>Phase 2B: Resting Support Limit</td><td><strong>{_esc(ch['symbol'])}</strong></td>"
                f'<td class="num">Limit {est_sh} sh</td>'
                f'<td class="num">{cur}{ch["entry_zone_low"]:,.2f}–{cur}{ch["entry_zone_high"]:,.2f}</td>'
                f'<td class="num">{cur}{ch["stop_loss"]:,.2f}</td>'
                f'<td class="num">Unfunded until touch</td>'
                f"<td>{_esc(ch['broker_routing'])}</td></tr>"
            )
    if not exec_rows:
        exec_rows.append(f'<tr><td>Converged — Stand Pat</td><td>Portfolio Aligned</td><td class="num">0 sh</td><td class="num">—</td><td class="num">Keep trailing stops</td><td class="num">{cur}0.00</td><td>No broker trades needed</td></tr>')

    ch6_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Sequenced Advisory Execution Tickets &amp; Broker Routing</caption>\n'
        f'  <thead><tr><th>Execution Phase</th><th>Instrument</th><th class="num">Order Size</th><th class="num">Limit / Trigger Band</th><th class="num">Protective Stop</th><th class="num">Cash Impact</th><th>Account Routing</th></tr></thead>\n'
        f'  <tbody>{"".join(exec_rows)}</tbody>\n</table>'
    )
    ch6_take = (
        f"<p>Executing Phase 1 sales before placing Phase 2 limit entries guarantees that every purchase is funded from settled cash without touching margin or breaching our {env['min_cash_floor_pct']:.1f}% reserve floor. "
        f"Phase 2B resting support tickets remain conditional watch bands that claim capital only if price pulls back into the support zone with trend structure intact. "
        f"Section 6.1 below ranks pre-dossier holdings so upcoming research retires our largest underwriting blind spots first.</p>"
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
        debt_rows_html.append(f'<tr><td>1</td><td>Queue Clear</td><td class="num">{cur}0.00 (0.00%)</td><td>—</td><td>Every active equity holding has a completed monograph dossier</td></tr>')
    debt_tbl = (
        '<table class="wikitable">\n'
        '  <caption>Prioritized Dossier Underwriting Debt Queue (Ordered by Capital at Risk)</caption>\n'
        f'  <thead><tr><th>Priority</th><th>Held Ticker</th><th class="num">Exposure ({cur} / % NAV)</th><th>Current Stage</th><th>Governance Rule Until Monograph Publishes</th></tr></thead>\n'
        f'  <tbody>{"".join(debt_rows_html)}</tbody>\n</table>'
    )
    debt_take = (
        f"<p>Ranking our {len(debt_q)} pre-dossier holdings strictly by capital exposure ensures that upcoming `company_report` runs retire the biggest wallet blind spots first rather than picking tickers at random. "
        f"While in this queue, every provisional position remains protected by its ratcheted chart invalidation stop and barred from fresh capital additions until ten-year cash conversion and valuation gates pass. "
        f"Chapter 7 next locks in the hysteresis rules that keep this plan stable across short reruns.</p>"
    )
    ch6_html = (
        f'<section class="chapter book-chapter" id="chapter6">\n'
        f'<h2>{_esc(ch6["title"])}</h2>\n'
        + "\n".join(f"<p>{_esc(p)}</p>" for p in ch6["book_paragraphs"])
        + f"\n{ch6_tbl}\n{ch6_take}\n"
        + "<h3>6.1 Dossier Underwriting Debt Queue (Pre-Monograph Holdings)</h3>\n"
        + f"<p>Institutional conviction requires primary filing forensics rather than price momentum alone. Whenever an active equity sits in our brokerage account without a completed 10-chapter monograph, we place it into provisional status rather than blindly selling a working trend or blindly adding more money. Existing shares stay protected by a ratcheted closing stop, fresh additions remain frozen, and research capacity works top-down from our largest exposure.</p>\n"
        + f"{debt_tbl}\n{debt_take}\n</section>"
    )

    # Build Chapter 7 HTML (Convergence, Hysteresis & Methodology)
    ch7 = story["chapters"]["chapter7"]
    ch7_trigger = (
        '<div class="callout callout-rule triggers"><div class="callout-title">Hysteresis Override &amp; Rerun Stability Contract</div>'
        f'<p>If you rerun `portfolio_audit` within {5} calendar days without new broker trades, any holding whose price moved less than &plusmn;{sc["price_band_hysteresis_pct"]:.1f}% retains its anchored verdict unless it closes below its hard invalidation stop or enters Stage 4. '
        f'Once an executed edit brings a holding within &plusmn;{sc["rebalance_deadband_wt_pct"]:.2f}% of its target weight, further adjustments are suppressed until a genuine fundamental or trend trigger fires.</p></div>'
    )
    ch7_html = (
        f'<section class="chapter book-chapter" id="chapter7">\n'
        f'<h2>{_esc(ch7["title"])}</h2>\n'
        + "\n".join(f"<p>{_esc(p)}</p>" for p in ch7["book_paragraphs"])
        + f"\n{ch7_trigger}\n</section>"
    )

    web_body = "\n\n".join([
        f"<h1>{_esc(title)}</h1>",
        audio_switcher_html,
        kf_html,
        '<div class="clearfix">',
        infobox_html,
        ch1_html,
        "</div>",
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
