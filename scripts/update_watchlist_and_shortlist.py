#!/usr/bin/env python3
"""
scripts/update_watchlist_and_shortlist.py
Synchronizes data/watchlist/IN.json and data/shortlist/IN.json with SSWL underwriting.
"""
import json
from pathlib import Path

WL_PATH = Path("data/watchlist/IN.json")
SL_PATH = Path("data/shortlist/IN.json")

def sync():
    # 1. Update Watchlist
    wl = json.loads(WL_PATH.read_text(encoding="utf-8"))
    sswl_entry = None
    
    # Remove from archive
    new_archive = []
    for item in wl.get("archive", []):
        if item.get("symbol") == "SSWL":
            sswl_entry = item
        else:
            new_archive.append(item)
    wl["archive"] = new_archive
    
    if not sswl_entry:
        for item in wl.get("active", []):
            if item.get("symbol") == "SSWL":
                sswl_entry = item
                break
                
    if not sswl_entry:
        sswl_entry = {"symbol": "SSWL", "company_name": "Steel Strips Wheels Limited"}

    sswl_entry.update({
        "symbol": "SSWL",
        "company_name": "Steel Strips Wheels Limited",
        "source_type": "TRANSCRIPT_WEEKLY_MEET",
        "status": "COMPLETED",
        "action_verdict": "WAIT_FOR_SUPPORT",
        "action_verdict_detail": "WAIT_FOR_SUPPORT: CMP ₹548.95 (+167.8% 6M rally, weekly RSI 90.26) extended +21.3% above 10w EMA; accumulate inside conditional support band ₹450.00–₹495.00.",
        "deep_research_status": "COMPLETED",
        "research_cycle": 1,
        "gate_status": "PASSED_CONDITIONAL",
        "gate_status_detail": "Business quality and balance sheet are elite (17.5% sales CAGR, zero dilution, 0.46x D/E), but technical timing gate caps at CAP_WAIT_FOR_SUPPORT due to extreme parabolic extension.",
        "kpi_health": "PASS",
        "kpi_score": "4/5",
        "entry_posture": "WAIT_FOR_SUPPORT_PULLBACK",
        "strategy_fit": "TACTICAL_MOMENTUM",
        "shortlist_action": "ADDED_TO_SHORTLIST_WAIT_FOR_SUPPORT",
        "last_researched_date": "2026-11-09",
        "strategy_bucket": "TACTICAL_MOMENTUM",
        "account_scope": "Zerodha (India)",
        "as_of_date": "2026-11-09",
        "stale_as_of": False,
        "theme_tags": "Auto Ancillaries, Alloy Wheels, Passenger Vehicle Lightweighting, Distressed Asset Consolidation, Export Expansion",
        "catalyst_timeline": "Ramp-up of 7.2M alloy wheel and aluminum knuckle capacity at Bhuj; sustained Q2 FY27 ₹117 Cr quarterly PAT run-rate; export market expansion.",
        "investment_thesis": "Leading Tier-1 wheel engineering player transitioning from commodity steel rims to high-margin cast alloy wheels; transformative acquisition of AMW Autocomponent in Bhuj provides 50% capital-intensity advantage with zero equity dilution.",
        "summary_rationale": "WAIT_FOR_SUPPORT; no new allocation at CMP ₹548.95. Extended +21.3% above 10-week EMA with weekly RSI at 90.26. Accumulate inside conditional support zone ₹450.00–₹495.00; structural stop ₹405.00; base target ₹720.00.",
        "notes": "Underwritten 2026-11-09 under updated 10-chapter monograph company_report workflow. Monograph: docs/blogs/IN/SSWL_dossier.html and SSWL_book.pdf.",
        "research_dossier_path": "docs/blogs/IN/SSWL_dossier.html",
        "dossier_path": "docs/blogs/IN/SSWL_dossier.html",
        "entry_zone": [450.0, 495.0],
        "stop_loss": 405.0,
        "target_base": 720.0,
        "target_bull": 880.0,
        "target_bear": 360.0,
        "primary_catalyst": "Bhuj Phase 1 & 2 operational ramp-up and margin expansion from alloy wheel mix shift.",
        "primary_kpi_summary": "TTM Sales ₹6,235 Cr (+32.8% YoY); Q2 FY27 PAT ₹117 Cr (+225% YoY); Net Debt-to-Equity 0.46x; 5-year CFO ₹1,796 Cr.",
        "moat_description": "Multi-locational OEM co-location duopoly in steel, low-cost brownfield capacity at Bhuj, 24-month PPAP homologation switching costs, and DGTR anti-dumping tariff protection.",
        "invalidation_condition": "Daily close below ₹405.00 (below 50-day SMA), or a structural breakdown in domestic passenger vehicle or commercial vehicle volumes."
    })
    
    # Put into active (or update existing)
    active_symbols = [x.get("symbol") for x in wl.get("active", [])]
    if "SSWL" in active_symbols:
        wl["active"] = [sswl_entry if x.get("symbol") == "SSWL" else x for x in wl["active"]]
    else:
        wl["active"].append(sswl_entry)
        
    WL_PATH.write_text(json.dumps(wl, indent=2), encoding="utf-8")
    print(f"[+] Updated data/watchlist/IN.json (active count: {len(wl['active'])})")

    # 2. Update Shortlist
    sl = json.loads(SL_PATH.read_text(encoding="utf-8"))
    sl_candidates = sl.get("active", [])
    sl_symbols = [x.get("symbol") for x in sl_candidates]
    
    sswl_sl_entry = {
        "symbol": "SSWL",
        "company_name": "Steel Strips Wheels Limited",
        "source_type": "TRANSCRIPT_WEEKLY_MEET",
        "strategy_bucket": "TACTICAL_MOMENTUM",
        "macro_sector": "Automotive",
        "fine_subsector": "Auto Parts: OEM / Wheels",
        "cap_tier": "Mid-Cap",
        "cmp": 548.95,
        "entry_zone_low": 450.0,
        "entry_zone_high": 495.0,
        "stop_loss": 405.0,
        "target_base": 720.0,
        "target_bull": 880.0,
        "target_bear": 360.0,
        "asymmetry_ratio": 3.51,
        "distance_from_support_atr": 1.93,
        "dist_from_20dma_pct": 11.61,
        "rsi_14": 70.54,
        "rs_rating": 53.21,
        "1d_return_pct": -0.72,
        "1w_return_pct": 11.13,
        "2w_return_pct": 22.45,
        "p_e": 29.43,
        "market_cap": 8482.09,
        "roe_pct": 15.9,
        "roic_pct": 16.5,
        "roce_pct": 14.8,
        "debt_to_equity": 0.46,
        "debt_to_ebitda": 1.35,
        "gross_margin_pct": 37.5,
        "fcf_margin_pct": 2.3,
        "opm_pct": 10.8,
        "cfo_to_pat": 1.13,
        "3y_revenue_cagr_pct": 17.5,
        "3y_sales_cagr_pct": 17.5,
        "3y_pat_cagr_pct": 20.8,
        "action_verdict": "WAIT_FOR_SUPPORT",
        "action_verdict_detail": "TACTICAL_MOMENTUM; wait for support; no new allocation at CMP ₹548.95.",
        "weinstein_stage": "STAGE_2",
        "weinstein_stage_detail": "TheWrap Stage 2; 18 weeks tagged; positive trend but extended +21.3% above 10w EMA.",
        "kpi_health": "PASS",
        "gate_status": "PASSED_CONDITIONAL",
        "gate_status_detail": "Business quality and balance sheet are elite, but technical timing gate caps at CAP_WAIT_FOR_SUPPORT.",
        "entry_posture": "WAIT_FOR_SUPPORT_PULLBACK; accumulate inside conditional ₹450–₹495 support band.",
        "momentum_state": "STAGE_2; price +21.3% above 10-week EMA; weekly RSI at 90.26.",
        "as_of_date": "2026-11-09",
        "stale_as_of": False,
        "last_researched_date": "2026-11-09",
        "research_dossier_path": "docs/blogs/IN/SSWL_dossier.html",
        "moat_description": "Multi-locational OEM co-location duopoly in steel, low-cost brownfield capacity at Bhuj, 24-month PPAP homologation switching costs, and DGTR anti-dumping tariff protection.",
        "primary_catalyst": "Bhuj Phase 1 & 2 operational ramp-up and margin expansion from alloy wheel mix shift.",
        "primary_kpi_summary": "TTM Sales ₹6,235 Cr (+32.8% YoY); Q2 FY27 PAT ₹117 Cr (+225% YoY); Net Debt-to-Equity 0.46x; 5-year CFO ₹1,796 Cr.",
        "invalidation_condition": "Daily close below ₹405.00 (below 50-day SMA), or a structural breakdown in domestic passenger vehicle or commercial vehicle volumes.",
        "notes": "Underwritten 2026-11-09 under updated 10-chapter monograph company_report workflow. Monograph: docs/blogs/IN/SSWL_dossier.html and SSWL_book.pdf."
    }
    
    if "SSWL" in sl_symbols:
        sl["active"] = [sswl_sl_entry if x.get("symbol") == "SSWL" else x for x in sl_candidates]
    else:
        sl["active"].append(sswl_sl_entry)
        
    SL_PATH.write_text(json.dumps(sl, indent=2), encoding="utf-8")
    print(f"[+] Updated data/shortlist/IN.json (active count: {len(sl['active'])})")

if __name__ == "__main__":
    sync()
