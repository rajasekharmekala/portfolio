#!/usr/bin/env python3
"""
Stage 2 Sector & Stock Momentum Scanner (TheWrap via macOS Browser Automation)
Supports both Indian (NSE/BSE) and US (NYSE/NASDAQ) markets:
  - IN: https://thewrap.in/data-tools/stage2  (default min Market Cap >= ₹1,000 Cr)
  - US: https://thewrap.in/data-tools/ustocks (default min Market Cap >= $1.0B)

Usage:
  .venv/bin/python scripts/stage2_scanner.py --market IN --min-mcap 1000 --out data/views/stage2_IN_latest.json
  .venv/bin/python scripts/stage2_scanner.py --market US --min-mcap 1.0  --out data/views/stage2_US_latest.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from uuid import uuid4

import requests

# Lazy-load chrome_ctl only when --source powerbi is used so default TradingView mode is 100% headless.
SKILL_PATHS = [
    os.path.expanduser("~/.agents/skills/macos-browser-automation/scripts"),
    os.path.expanduser("~/.agents/skills-dangerously-allow/macos-browser-automation/scripts"),
]
chrome_ctl = None
for p in SKILL_PATHS:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)
try:
    import chrome_ctl as _chrome_ctl
    chrome_ctl = _chrome_ctl
except ImportError:
    chrome_ctl = None

POWERBI_URLS = {
    "IN": {
        "wrap_url": "https://thewrap.in/data-tools/stage2",
        "pbi_url": "https://app.powerbi.com/view?r=eyJrIjoiOTJhNWMwODgtZTk0OS00NDM0LTgwM2MtNjYzZTQ0ZjgzNGM1IiwidCI6ImE3ODlmNjk1LTUxZWYtNGExMy1hZTMyLTk3NDFiNGRmMDBiNyJ9",
        "pbi_match": "OTJhNWMwODgt",
        "default_min_mcap": 1000.0,
    },
    "US": {
        "wrap_url": "https://thewrap.in/data-tools/ustocks",
        "pbi_url": "https://app.powerbi.com/view?r=eyJrIjoiMTgxNzEzZWItNDliZS00OTZkLWE2NjMtNTdiMzU3ZjFlYTc4IiwidCI6ImE3ODlmNjk1LTUxZWYtNGExMy1hZTMyLTk3NDFiNGRmMDBiNyJ9",
        "pbi_match": "MTgxNzEzZWIt",
        "default_min_mcap": 1.0,
    },
}


def run_js(code: str, match: str) -> str:
    return chrome_ctl.execute_js(code, match=match)


def clean_cell(val: str) -> str:
    if not val:
        return ""
    return re.sub(r"\s*Additional Conditional Formatting\s*", "", val).strip()


def clean_duplicated_label(t: str) -> str:
    """Clean PowerBI doubled SVG text labels (including truncated '…' prefixes)."""
    t = t.strip()
    if "…" in t:
        parts = t.split("…", 1)
        if len(parts) == 2 and parts[1].strip():
            return parts[1].strip()
    half = len(t) // 2
    if half > 2 and t[:half] == t[half:]:
        return t[:half]
    return re.sub(r"Industry$", "", t).strip()


def ensure_powerbi_open(market: str) -> str:
    """Verify or open TheWrap PowerBI dashboard for the given market in Chrome."""
    cfg = POWERBI_URLS[market]
    if market == "IN":
        # Own a fresh tab: existing dashboard tabs can carry another user's filters.
        match_token = "portfolio-stage2-" + uuid4().hex
        chrome_ctl.navigate(cfg["pbi_url"] + "#" + match_token, new_tab=True)
        time.sleep(6.0)
        return match_token
    match_token = cfg["pbi_match"]
    tabs = chrome_ctl.list_tabs()
    if any(match_token in t.get("url", "") for t in tabs):
        return match_token

    # Try resolving dynamic embed URL from open thewrap.in tab if present
    wrap_sub = cfg["wrap_url"].split("thewrap.in")[-1]
    if any(wrap_sub in t.get("url", "") for t in tabs):
        try:
            inner = chrome_ctl.execute_js(
                """(() => {
                    const f = document.querySelector('iframe');
                    if (!f || !f.contentDocument) return '';
                    const innerF = f.contentDocument.querySelector('iframe');
                    return innerF ? innerF.src : '';
                })()""",
                match=wrap_sub,
            )
            if inner and "app.powerbi.com" in inner:
                chrome_ctl.navigate(inner, new_tab=True)
                time.sleep(5.0)
                return match_token
        except Exception:
            pass

    chrome_ctl.navigate(cfg["pbi_url"], new_tab=True)
    time.sleep(6.0)
    return match_token


def clear_india_slicers(match_token: str) -> dict:
    """Clear saved category and range selections before applying the cap filter."""
    js = """(() => {
        const labels = ['Industry', 'TradingView Code', 'SME Only Flag', 'ASM ESM GSM',
                        'Stage2 Status', 'Cheat Entry', 'Percentage Return Range:',
                        '# of Weeks in TheWrap List:', 'Market Cap Range (in cr.):',
                        'Relative Strength Range:', 'Avg Weekly Vol (in cr):'];
        const visuals = Array.from(document.querySelectorAll('visual-container'));
        return JSON.stringify(labels.map(label => {
            const v = visuals.find(x => x.innerText.trim().split('\\n')[0].trim() === label);
            const button = v && v.querySelector('[aria-label="Clear selections"]');
            if (button) button.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}));
            return {label, found: !!v, cleared: !!button};
        }));
    })()"""
    rows = json.loads(run_js(js, match=match_token) or "[]")
    time.sleep(2)
    core = {"Industry", "TradingView Code", "SME Only Flag", "ASM ESM GSM", "Stage2 Status", "Cheat Entry"}
    ranges = {"Percentage Return Range:", "# of Weeks in TheWrap List:", "Market Cap Range (in cr.):",
              "Relative Strength Range:", "Avg Weekly Vol (in cr):"}
    cleared = {r["label"] for r in rows if r.get("found") and r.get("cleared")}
    if not (core | ranges).issubset(cleared):
        raise RuntimeError("Could not clear all Stage 2 slicers: " + ", ".join(sorted((core | ranges) - cleared)))
    state_js = """(() => JSON.stringify(Array.from(document.querySelectorAll('visual-container'))
        .map(v => v.innerText.trim().split('\\n').map(x => x.trim()))
        .filter(x => ['Industry','TradingView Code','SME Only Flag','ASM ESM GSM','Stage2 Status','Cheat Entry'].includes(x[0]))))()"""
    states = json.loads(run_js(state_js, match=match_token) or "[]")
    state_map = {row[0]: row[1] if len(row) > 1 else "" for row in states}
    if any(state_map.get(label) != "All" for label in core):
        raise RuntimeError("Stage 2 category slicers did not reset to All: " + str(state_map))
    return {"category_slicers_cleared": sorted(cleared), "states": state_map, "results": rows}


def close_owned_tab(match_token: str):
    """Close only the scanner's uniquely tagged tab, even if tab indices change."""
    script = f'''tell application "Google Chrome"
        repeat with w in windows
            repeat with t in tabs of w
                if URL of t contains {json.dumps("#" + match_token)} then
                    close t
                    return "closed"
                end if
            end repeat
        end repeat
        return "not found"
    end tell'''
    chrome_ctl.run_applescript(script)


def apply_market_cap_filter(match_token: str, slicer_label: str, min_mcap: float):
    """Set the minimum market cap filter on the PowerBI slicer input."""
    js = f"""
    (() => {{
        const mcapVisual = Array.from(document.querySelectorAll("visual-container"))
            .find(v => v.innerText.includes({json.dumps(slicer_label)}));
        if (!mcapVisual) return JSON.stringify({{ ok: false, error: "Market cap slicer not found" }});

        const inputs = Array.from(mcapVisual.querySelectorAll("input"));
        if (!inputs || inputs.length === 0) return JSON.stringify({{ ok: false, error: "Inputs not found" }});

        const minInput = inputs[0];
        minInput.focus();
        minInput.value = "{min_mcap:g}";
        minInput.dispatchEvent(new Event("input", {{ bubbles: true }}));
        minInput.dispatchEvent(new Event("change", {{ bubbles: true }}));
        minInput.dispatchEvent(new KeyboardEvent("keydown", {{ key: "Enter", keyCode: 13, bubbles: true }}));
        minInput.blur();

        return JSON.stringify({{ ok: true, applied: "{min_mcap:g}" }});
    }})()
    """
    res = run_js(js, match=match_token)
    time.sleep(2.0)
    return json.loads(res) if res else {"ok": False}


def extract_bar_chart_sectors(match_token: str, title_snippet: str, value_key: str):
    """Extract ranked sectors/industries and percentages from a PowerBI bar chart visual."""
    js = f"""
    (() => {{
        const v = Array.from(document.querySelectorAll("visual-container"))
            .find(vc => vc.innerText.includes({json.dumps(title_snippet)}));
        if (!v) return JSON.stringify([]);
        const texts = Array.from(v.querySelectorAll("text")).map(t => t.textContent.trim()).filter(Boolean);
        return JSON.stringify(texts);
    }})()
    """
    raw_texts = json.loads(run_js(js, match=match_token) or "[]")
    numbers = []
    names = []
    for t in raw_texts:
        if re.match(r"^\d+(\.\d+)?%?$", t):
            numbers.append(float(t.rstrip("%")))
        elif t and not t.startswith("Industry") and not t.startswith("Sector"):
            names.append(clean_duplicated_label(t))
    out = []
    count = min(len(names), len(numbers))
    for i in range(count):
        val = int(numbers[i]) if numbers[i].is_integer() else numbers[i]
        out.append({"sector": names[i], value_key: val})
    return out


def extract_scrollable_sectors(match_token: str, title_snippet: str, value_key: str):
    """Read all visible chart pages, and report whether the bottom was reached."""
    js = f"""(() => {{
        const v = Array.from(document.querySelectorAll('visual-container'))
            .find(x => x.innerText.includes({json.dumps(title_snippet)}));
        const chart = v && v.querySelector('svg');
        if (!chart) return JSON.stringify({{found:false}});
        const brush = v.querySelector('g.brush');
        const overlay = brush && brush.querySelector('rect.overlay');
        const selection = brush && brush.querySelector('rect.selection');
        const top = !selection || +selection.getAttribute('y') <= 1;
        const bottom = !overlay || !selection ||
            (+selection.getAttribute('y') + +selection.getAttribute('height') >= +overlay.getAttribute('height') - 1);
        return JSON.stringify({{found:true, top, bottom}});
    }})()"""
    wheel = f"""(() => {{
        const v = Array.from(document.querySelectorAll('visual-container'))
            .find(x => x.innerText.includes({json.dumps(title_snippet)}));
        const chart = v && v.querySelector('svg');
        if (chart) chart.dispatchEvent(new WheelEvent('wheel', {{deltaY:300, bubbles:true, cancelable:true}}));
    }})()"""
    for _ in range(100):
        state = json.loads(run_js(js, match=match_token) or "{}")
        if not state.get("found"):
            return [], False
        if state.get("top"):
            break
        run_js(wheel.replace("deltaY:300", "deltaY:-300"), match=match_token)
        time.sleep(0.8)
    else:
        return [], False
    rows = {}
    no_growth = 0
    for _ in range(100):
        previous = len(rows)
        for row in extract_bar_chart_sectors(match_token, title_snippet, value_key):
            rows[row["sector"]] = row
        state = json.loads(run_js(js, match=match_token) or "{}")
        if not state.get("found"):
            return list(rows.values()), False
        if state.get("bottom"):
            return list(rows.values()), True
        no_growth = no_growth + 1 if len(rows) == previous else 0
        if no_growth >= 5:
            return list(rows.values()), False
        run_js(wheel, match=match_token)
        time.sleep(0.8)
    return list(rows.values()), False


def extract_table_by_title(match_token: str, title_snippet: str):
    """Extract visible rows from a titled PowerBI table/matrix visual."""
    js = f"""
    (() => {{
        const v = Array.from(document.querySelectorAll("visual-container"))
            .find(vc => vc.innerText.includes({json.dumps(title_snippet)}));
        if (!v) return JSON.stringify([]);

        const rows = Array.from(v.querySelectorAll("[role='row']")).map(r => {{
            return Array.from(r.querySelectorAll("[role='gridcell'], [role='columnheader'], [role='rowheader']")).map(c => c.innerText.trim());
        }});
        return JSON.stringify(rows);
    }})()
    """
    res = run_js(js, match=match_token)
    rows = json.loads(res) if res else []
    if not rows or len(rows) < 2:
        return []
    header = [clean_cell(h) for h in rows[0]]
    result = []
    for r in rows[1:]:
        if len(r) == len(header):
            cleaned_row = {header[i]: clean_cell(r[i]) for i in range(len(header)) if header[i] != "Row Selection"}
            result.append(cleaned_row)
    return result


def scroll_and_extract_table(
    match_token: str,
    title_snippet: str,
    key_col_index: int = 1,
    max_scrolls: int = 50,
    sort_by_col: str = "",
    stop_col_name: str = "",
    stop_values: tuple = (),
):
    """Scroll through a PowerBI table visual and capture deduplicated rows."""
    if sort_by_col:
        sort_state = run_js(
            f"""
            (() => {{
                const v = Array.from(document.querySelectorAll("visual-container"))
                    .find(vc => vc.innerText.includes({json.dumps(title_snippet)}));
                if (!v) return "";
                const hdr = Array.from(v.querySelectorAll("[role='columnheader']"))
                    .find(c => c.innerText.includes({json.dumps(sort_by_col)}));
                if (!hdr) return "";
                const ariaSort = hdr.getAttribute("aria-sort") || "";
                if (ariaSort !== "ascending") {{
                    hdr.click();
                    return "clicked_from_" + ariaSort;
                }}
                return "already_ascending";
            }})()
            """,
            match=match_token,
        )
        time.sleep(2.0)
        # Verify it didn't land on descending if aria-sort was empty/descending
        sort_check = run_js(
            f"""
            (() => {{
                const v = Array.from(document.querySelectorAll("visual-container"))
                    .find(vc => vc.innerText.includes({json.dumps(title_snippet)}));
                if (!v) return "";
                const hdr = Array.from(v.querySelectorAll("[role='columnheader']"))
                    .find(c => c.innerText.includes({json.dumps(sort_by_col)}));
                if (!hdr) return "";
                const ariaSort = hdr.getAttribute("aria-sort") || "";
                if (ariaSort === "descending") {{
                    hdr.click();
                    return "clicked_again_to_ascending";
                }}
                return ariaSort;
            }})()
            """,
            match=match_token,
        )
        if "clicked_again" in sort_check:
            time.sleep(2.0)

    # Reset scroll to top
    run_js(
        f"""
        (() => {{
            const v = Array.from(document.querySelectorAll("visual-container"))
                .find(vc => vc.innerText.includes({json.dumps(title_snippet)}));
            if (v) {{
                const vp = v.querySelector(".mid-viewport");
                if (vp) {{ vp.scrollTop = 0; vp.dispatchEvent(new Event("scroll", {{ bubbles: true }})); }}
            }}
        }})()
        """,
        match=match_token,
    )
    time.sleep(1.0)

    captured = {}
    headers = None
    stop_col_idx = None
    no_growth = 0

    for _ in range(max_scrolls):
        js = f"""
        (() => {{
            const v = Array.from(document.querySelectorAll("visual-container"))
                .find(vc => vc.innerText.includes({json.dumps(title_snippet)}));
            if (!v) return JSON.stringify({{ error: "visual not found" }});
            const vp = v.querySelector(".mid-viewport");
            const rows = Array.from(v.querySelectorAll("[role='row']")).map(r => {{
                return Array.from(r.querySelectorAll("[role='gridcell'], [role='columnheader'], [role='rowheader']")).map(c => c.innerText.trim());
            }});
            return JSON.stringify({{
                scrollTop: vp ? vp.scrollTop : 0,
                scrollHeight: vp ? vp.scrollHeight : 0,
                clientHeight: vp ? vp.clientHeight : 0,
                rows: rows
            }});
        }})()
        """
        data = json.loads(run_js(js, match=match_token) or "{}")
        rows = data.get("rows", [])
        if not headers and rows:
            headers = [clean_cell(h) for h in rows[0]]
            if stop_col_name and stop_col_name in headers:
                stop_col_idx = headers.index(stop_col_name)

        new_found = 0
        hit_stop_val = False
        for r in rows[1:]:
            if len(r) > key_col_index and r[key_col_index] and r[key_col_index] not in ("TradingView Code", "Symbol", "Industry"):
                if stop_col_idx is not None and stop_col_idx < len(r):
                    cell_val = clean_cell(r[stop_col_idx])
                    if cell_val in stop_values:
                        hit_stop_val = True
                        continue
                key = clean_cell(r[key_col_index])
                if key not in captured:
                    captured[key] = [clean_cell(c) for c in r]
                    new_found += 1

        if hit_stop_val or data.get("scrollTop", 0) + data.get("clientHeight", 0) >= data.get("scrollHeight", 0):
            break
        if new_found == 0:
            no_growth += 1
            if no_growth >= 3:
                break
            time.sleep(1.0)
            continue
        no_growth = 0

        step_px = max(200, data.get("clientHeight", 300) - 80)
        run_js(
            f"""
            (() => {{
                const v = Array.from(document.querySelectorAll("visual-container"))
                    .find(vc => vc.innerText.includes({json.dumps(title_snippet)}));
                const vp = v ? v.querySelector(".mid-viewport") : null;
                if (vp) {{
                    vp.scrollTop += {step_px};
                    vp.dispatchEvent(new Event("scroll", {{ bubbles: true }}));
                }}
            }})()
            """,
            match=match_token,
        )
        time.sleep(0.8)

    cleaned = []
    if not headers:
        return cleaned
    for key, r in captured.items():
        if len(r) == len(headers):
            cleaned.append({headers[i]: r[i] for i in range(len(headers)) if headers[i] != "Row Selection"})
        else:
            cleaned.append({"key": key, "raw": r})
    return cleaned


def split_stage2_rows(rows: list) -> tuple:
    """Separate dashboard exits from the active Stage 2 universe."""
    removed = [r for r in rows if r.get("Stage2 Status", "").strip().casefold() == "removed"]
    current = [r for r in rows if r.get("Stage2 Status", "").strip().casefold() != "removed"]
    return current, removed


def extract_in(match_token: str, min_mcap: float) -> dict:
    print(f"[*] [IN] Applying Market Cap filter >= ₹{min_mcap:g} Cr...")
    filter_result = apply_market_cap_filter(match_token, "Market Cap Range (in cr.)", min_mcap)
    if not filter_result.get("ok"):
        raise RuntimeError(f"Market cap filter failed: {filter_result}")
    verify_filter = """(() => {
        const v=Array.from(document.querySelectorAll('visual-container')).find(x=>x.innerText.includes('Market Cap Range (in cr.)'));
        const input=v && v.querySelector('input'); return input ? input.value : '';
    })()"""
    visible_min = run_js(verify_filter, match=match_token).replace(",", "").strip()
    try:
        cap_verified = float(visible_min) == min_mcap
    except ValueError:
        cap_verified = False
    if not cap_verified:
        raise RuntimeError(f"Market cap filter was not verified: {visible_min!r}")

    print("[*] [IN] Extracting summary cards...")
    summary_js = """
    (() => {
        const visuals = Array.from(document.querySelectorAll("visual-container"));
        const getCardVal = (label) => {
            const v = visuals.find(vc => vc.innerText.includes(label));
            if (!v) return null;
            const lines = v.innerText.split("\\n").map(s => s.trim()).filter(Boolean);
            const num = lines.find(s => /^\\d+$/.test(s));
            return num ? parseInt(num, 10) : null;
        };
        const updateDate = (() => {
            const v = visuals.find(vc => vc.innerText.includes("Last Updated On"));
            return v ? v.innerText.split("\\n")[0].trim() : "";
        })();
        return JSON.stringify({
            last_updated: updateDate,
            continuing_trend: getCardVal("Continuing Trend"),
            new_additions: getCardVal("New Additions"),
            re_entries: getCardVal("Re Entries"),
            removed: getCardVal("Removed")
        });
    })()
    """
    summary = json.loads(run_js(summary_js, match=match_token) or "{}")

    print("[*] [IN] Extracting sector breadth rankings...")
    sectors, sector_chart_complete = extract_scrollable_sectors(
        match_token,
        "Which sector is the strongest with maximum percentage",
        "pct_in_stage2",
    )

    print("[*] [IN] Extracting featured tables (New Additions, Top 25, RS Details, Momentum)...")
    new_stage2 = extract_table_by_title(match_token, "New Stage2 This Week:")
    top_25 = extract_table_by_title(match_token, "Top 25 in Stage2")
    rs_details = extract_table_by_title(match_token, "Relative Strength Details")
    vol_details = extract_table_by_title(match_token, "Avg Weekly Volume Details")
    momentum_details = extract_table_by_title(match_token, "Momentum Details")

    print("[*] [IN] Scrolling and extracting all Stage 2 stocks table...")
    all_stocks = scroll_and_extract_table(
        match_token,
        "All Stocks In Stage2 with All Details",
        key_col_index=1,
        max_scrolls=160,
    )
    # The dashboard's all-stocks table also includes this week's exits.
    current_stocks, removed_stocks = split_stage2_rows(all_stocks)
    active_counts = [summary.get(k) for k in ("continuing_trend", "new_additions", "re_entries")]
    expected_active = sum(active_counts) if all(isinstance(x, int) for x in active_counts) else None

    return {
        "market": "IN",
        "source_url": POWERBI_URLS["IN"]["wrap_url"],
        "as_of": summary.get("last_updated") or None,
        "extracted_at": datetime.now().isoformat(),
        "min_mcap_cr": min_mcap,
        "summary": summary,
        "strongest_sectors": sectors,
        "sector_chart_complete": sector_chart_complete,
        "new_additions_this_week": new_stage2,
        "top_25_stage2": top_25,
        "relative_strength_leaders": rs_details,
        "volume_trend_leaders": vol_details,
        "momentum_leaders": momentum_details,
        "stage2_universe_count": len(current_stocks),
        "expected_active_count": expected_active,
        "stage2_universe_complete": expected_active is not None and len(current_stocks) == expected_active,
        "stage2_universe": current_stocks,
        "removed_this_week": removed_stocks,
    }


def extract_us(match_token: str, min_mcap_b: float) -> dict:
    print(f"[*] [US] Applying Market Cap filter >= ${min_mcap_b:g}B...")
    apply_market_cap_filter(match_token, "Market Cap Range ($B)", min_mcap_b)

    print("[*] [US] Extracting summary cards...")
    summary_js = """
    (() => {
        const visuals = Array.from(document.querySelectorAll("visual-container"));
        const getLine0 = (label) => {
            const v = visuals.find(vc => vc.innerText.includes(label));
            return v ? v.innerText.split("\\n")[0].trim() : null;
        };
        return JSON.stringify({
            last_updated: getLine0("Last Updated On"),
            total_filtered_companies: getLine0("Total Listed Companies"),
            total_market_cap: getLine0("Total Market Cap ($)")
        });
    })()
    """
    summary = json.loads(run_js(summary_js, match=match_token) or "{}")

    print("[*] [US] Extracting strongest industries (% outperforming S&P 500)...")
    strongest_industries = extract_bar_chart_sectors(
        match_token,
        "What percentage of stocks in each industry are outperforming",
        "pct_outperforming_sp500",
    )

    print("[*] [US] Scrolling and extracting full Industry Breadth & Returns matrix...")
    industry_matrix = scroll_and_extract_table(
        match_token,
        "How are the returns in each industry?",
        key_col_index=1,
        max_scrolls=30,
    )

    print("[*] [US] Extracting Breakout Scanner setups (excluding 'No Breakout')...")
    breakout_stocks = scroll_and_extract_table(
        match_token,
        "Which stocks are being captured under Breakout Scanner?",
        key_col_index=1,
        max_scrolls=25,
        sort_by_col="Breakout Type",
        stop_col_name="Breakout Type",
        stop_values=("No Breakout",),
    )

    print("[*] [US] Extracting Volume Scanner leaders (Explosive / Accumulation / Spike)...")
    volume_leaders = scroll_and_extract_table(
        match_token,
        "Which stocks are being captured under Volume Scanner?",
        key_col_index=1,
        max_scrolls=15,
        sort_by_col="Volume Analysis",
        stop_col_name="Volume Analysis",
        stop_values=("Normal Volume",),
    )

    print("[*] [US] Extracting Momentum Scanner & Return Leaders...")
    top_1m = extract_table_by_title(match_token, "Return 1 Month")
    top_3m = extract_table_by_title(match_token, "Return 3 Months")
    top_6m = extract_table_by_title(match_token, "Return 6 Months")
    short_interest = extract_table_by_title(match_token, "Which stocks have the highest short interest?")

    return {
        "market": "US",
        "source_url": POWERBI_URLS["US"]["wrap_url"],
        "as_of": summary.get("last_updated") or datetime.now().strftime("%Y-%m-%d"),
        "extracted_at": datetime.now().isoformat(),
        "min_mcap_usd_b": min_mcap_b,
        "summary": summary,
        "strongest_sectors": strongest_industries,
        "industry_breadth_matrix": industry_matrix,
        "breakout_scanner_count": len(breakout_stocks),
        "breakout_scanner": breakout_stocks,
        "volume_scanner_leaders": volume_leaders,
        "return_leaders_1m": top_1m,
        "return_leaders_3m": top_3m,
        "return_leaders_6m": top_6m,
        "high_short_interest": short_interest,
    }


TV_SCAN_COLUMNS = [
    "name",
    "description",
    "exchange",
    "sector",
    "industry",
    "close",
    "change",
    "volume",
    "average_volume_10d_calc",
    "average_volume_30d_calc",
    "SMA50",
    "SMA200",
    "EMA50",
    "EMA200",
    "SMA30|1W",
    "EMA10|1W",
    "RSI",
    "price_52_week_high",
    "Perf.W",
    "Perf.1M",
    "Perf.3M",
    "Perf.6M",
    "Perf.Y",
    "market_cap_basic",
]

TV_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
}


def _safe_num(val):
    if val is None or isinstance(val, bool):
        return None
    try:
        f = float(val)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def fetch_tradingview_universe(market: str, min_mcap: float, limit: int = 3500) -> tuple[list[dict], float | None]:
    """Fetch full filtered stock universe from TradingView Scanner API (single batch POST, no browser)."""
    region = "india" if market == "IN" else "america"
    url = f"https://scanner.tradingview.com/{region}/scan"
    mcap_raw = float(min_mcap) * (1e7 if market == "IN" else 1e9)
    exchanges = ["NSE", "BSE"] if market == "IN" else ["NYSE", "NASDAQ", "AMEX"]

    payload = {
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "market_cap_basic", "operation": "egreater", "right": mcap_raw},
            {"left": "exchange", "operation": "in_range", "right": exchanges},
        ],
        "options": {"lang": "en"},
        "markets": [region],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": TV_SCAN_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, limit],
    }
    resp = requests.post(url, json=payload, headers=TV_HEADERS, timeout=30)
    resp.raise_for_status()
    raw_rows = resp.json().get("data", [])

    # Deduplicate symbols across exchanges (prefer NSE over BSE for IN)
    exchange_priority = {"NSE": 0, "BSE": 1, "NASDAQ": 0, "NYSE": 1, "AMEX": 2}
    by_sym: dict[str, dict] = {}
    for item in raw_rows:
        vals = item.get("d", [])
        if len(vals) != len(TV_SCAN_COLUMNS):
            continue
        row = dict(zip(TV_SCAN_COLUMNS, vals))
        sym = str(row.get("name") or "").strip().upper()
        if not sym:
            continue
        ex = str(row.get("exchange") or "").upper()
        prev = by_sym.get(sym)
        if prev is None or exchange_priority.get(ex, 9) < exchange_priority.get(str(prev.get("exchange") or "").upper(), 9):
            by_sym[sym] = row

    spy_3m = None
    if market == "US":
        try:
            b_resp = requests.post(
                url,
                json={"symbols": {"tickers": ["AMEX:SPY"]}, "columns": ["Perf.3M"]},
                headers=TV_HEADERS,
                timeout=15,
            )
            b_data = b_resp.json().get("data", [])
            if b_data and b_data[0].get("d"):
                spy_3m = _safe_num(b_data[0]["d"][0])
        except Exception:
            spy_3m = None

    return list(by_sym.values()), spy_3m


def _is_stage2(row: dict) -> bool:
    """Weinstein / Minervini Stage 2 trend template from TradingView weekly + daily moving averages."""
    close = _safe_num(row.get("close"))
    sma30w = _safe_num(row.get("SMA30|1W"))
    sma50 = _safe_num(row.get("SMA50"))
    sma200 = _safe_num(row.get("SMA200"))
    if close is None or close <= 0:
        return False
    above_30w = (sma30w is not None and close > sma30w)
    above_200 = (sma200 is not None and close > sma200)
    stack_ok = (sma50 is not None and sma200 is not None and sma50 > sma200)
    if sma30w is not None and sma200 is not None and sma50 is not None:
        return above_30w and above_200 and stack_ok
    if sma30w is not None:
        return above_30w
    return above_200


def _compute_rs_percentiles(rows: list[dict]) -> dict[str, float]:
    """Compute cross-sectional 0..100 Relative Strength percentile rank from weighted 3M/6M/1Y performance."""
    scored = []
    for r in rows:
        sym = str(r.get("name") or "").strip().upper()
        p3 = _safe_num(r.get("Perf.3M"))
        p6 = _safe_num(r.get("Perf.6M"))
        p1y = _safe_num(r.get("Perf.Y"))
        parts = [(0.4, p3), (0.35, p6), (0.25, p1y)]
        valid = [(w, v) for w, v in parts if v is not None]
        if valid:
            w_sum = sum(w for w, _ in valid)
            score = sum(w * v for w, v in valid) / w_sum
            scored.append((sym, score))
    scored.sort(key=lambda x: x[1])
    n = len(scored)
    if n <= 1:
        return {sym: 50.0 for sym, _ in scored}
    return {sym: round(100.0 * idx / (n - 1), 1) for idx, (sym, _) in enumerate(scored)}


def build_tradingview_stage2(market: str, min_mcap: float, rows: list[dict], spy_3m: float | None = None) -> dict:
    """Build drop-in compatible Stage 2 / Momentum snapshot dict from TradingView universe rows."""
    today = datetime.now().strftime("%Y-%m-%d")
    rs_map = _compute_rs_percentiles(rows)

    by_ind: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        ind = str(r.get("industry") or r.get("sector") or "Other").strip() or "Other"
        by_ind[ind].append(r)

    if market == "IN":
        stage2_rows = []
        new_additions = []
        for r in rows:
            if not _is_stage2(r):
                continue
            sym = str(r.get("name") or "").strip().upper()
            ind = str(r.get("industry") or r.get("sector") or "Other").strip()
            close = _safe_num(r.get("close")) or 0.0
            sma30w = _safe_num(r.get("SMA30|1W"))
            vol = _safe_num(r.get("volume")) or 0.0
            avg30 = _safe_num(r.get("average_volume_30d_calc")) or 0.0
            vol_ratio = round(vol / avg30, 2) if avg30 > 0 else None
            avg_weekly_vol_cr = round((avg30 * 5.0 * close) / 1e7, 2) if (avg30 > 0 and close > 0) else None
            mcap_cr = round((_safe_num(r.get("market_cap_basic")) or 0.0) / 1e7, 1)
            perf_w = _safe_num(r.get("Perf.W"))
            perf_3m = _safe_num(r.get("Perf.3M"))
            rs_pct = rs_map.get(sym)

            rec = {
                "TradingView Code": sym,
                "Company": str(r.get("description") or sym).strip(),
                "Exchange": str(r.get("exchange") or "NSE").strip(),
                "Sector": str(r.get("sector") or "").strip(),
                "Industry": ind,
                "Stage2 Status": "Continuing",
                "Relative Strength %": rs_pct,
                "% Return": round(perf_3m, 2) if perf_3m is not None else None,
                "Avg Weekly Vol (in cr.)": avg_weekly_vol_cr,
                "Close": round(close, 2),
                "Market Cap (Cr)": mcap_cr,
                "Volume Ratio": vol_ratio,
            }
            stage2_rows.append(rec)
            # Flag fresh Stage 2 breakouts (within 0-5% above 30W SMA with positive weekly gain)
            if sma30w and sma30w > 0 and 0.0 < ((close - sma30w) / sma30w) <= 0.05 and (perf_w or 0.0) > 0:
                rec_new = dict(rec, **{"Stage2 Status": "New Addition"})
                new_additions.append(rec_new)

        stage2_rows.sort(key=lambda x: (x.get("Relative Strength %") or -1.0), reverse=True)
        new_additions.sort(key=lambda x: (x.get("Relative Strength %") or -1.0), reverse=True)

        strongest_sectors = []
        for ind, ind_rows in by_ind.items():
            if len(ind_rows) < 3:
                continue
            s2_cnt = sum(1 for r in ind_rows if _is_stage2(r))
            strongest_sectors.append({
                "sector": ind,
                "pct_in_stage2": round(100.0 * s2_cnt / len(ind_rows), 1),
                "stage2_count": s2_cnt,
                "total_count": len(ind_rows),
            })
        strongest_sectors.sort(key=lambda x: (x["pct_in_stage2"], x["stage2_count"]), reverse=True)

        total_n = len(rows)
        s2_n = len(stage2_rows)
        return {
            "market": "IN",
            "source": "tradingview_scanner",
            "source_url": "https://scanner.tradingview.com/india/scan",
            "as_of": today,
            "extracted_at": datetime.now().isoformat(),
            "min_mcap_cr": min_mcap,
            "summary": {
                "last_updated": today,
                "total_filtered_companies": total_n,
                "continuing_trend": s2_n - len(new_additions),
                "new_additions": len(new_additions),
                "re_entries": 0,
                "removed": 0,
                "pct_universe_stage2": round(100.0 * s2_n / total_n, 1) if total_n else 0.0,
            },
            "strongest_sectors": strongest_sectors,
            "sector_chart_complete": True,
            "new_additions_this_week": new_additions[:50],
            "top_25_stage2": stage2_rows[:25],
            "relative_strength_leaders": stage2_rows[:25],
            "volume_trend_leaders": sorted(
                [r for r in stage2_rows if r.get("Volume Ratio") is not None],
                key=lambda x: x["Volume Ratio"],
                reverse=True,
            )[:25],
            "momentum_leaders": sorted(
                [r for r in stage2_rows if r.get("% Return") is not None],
                key=lambda x: x["% Return"],
                reverse=True,
            )[:25],
            "stage2_universe_count": s2_n,
            "expected_active_count": s2_n,
            "stage2_universe_complete": True,
            "stage2_universe": stage2_rows,
            "removed_this_week": [],
        }

    # US market
    bench_3m = spy_3m if spy_3m is not None else 0.0
    strongest_industries = []
    industry_matrix = []
    for ind, ind_rows in by_ind.items():
        n = len(ind_rows)
        above_200 = sum(1 for r in ind_rows if (_safe_num(r.get("close")) or 0) > (_safe_num(r.get("EMA200")) or 1e18))
        above_50 = sum(1 for r in ind_rows if (_safe_num(r.get("close")) or 0) > (_safe_num(r.get("EMA50")) or 1e18))
        outperf = sum(1 for r in ind_rows if (_safe_num(r.get("Perf.3M")) or -1e9) > bench_3m)
        p3_vals = [_safe_num(r.get("Perf.3M")) for r in ind_rows if _safe_num(r.get("Perf.3M")) is not None]
        pct_out = round(100.0 * outperf / n, 1) if n else 0.0
        pct_200 = round(100.0 * above_200 / n, 1) if n else 0.0
        pct_50 = round(100.0 * above_50 / n, 1) if n else 0.0
        industry_matrix.append({
            "Industry": ind,
            "Stock Count": n,
            "% Above 200D EMA": f"{pct_200:.1f}%",
            "% Above 50D EMA": f"{pct_50:.1f}%",
            "% Outperforming S&P 500": f"{pct_out:.1f}%",
            "Avg 3M Return %": round(sum(p3_vals) / len(p3_vals), 2) if p3_vals else None,
        })
        if n >= 3:
            strongest_industries.append({
                "sector": ind,
                "pct_outperforming_sp500": pct_out,
                "total_count": n,
            })
    strongest_industries.sort(key=lambda x: (x["pct_outperforming_sp500"], x["total_count"]), reverse=True)
    industry_matrix.sort(key=lambda x: float(x["% Outperforming S&P 500"].rstrip("%")), reverse=True)

    breakout_stocks = []
    volume_leaders = []
    for r in rows:
        sym = str(r.get("name") or "").strip().upper()
        ind = str(r.get("industry") or r.get("sector") or "Other").strip()
        close = _safe_num(r.get("close")) or 0.0
        h52 = _safe_num(r.get("price_52_week_high")) or 0.0
        vol = _safe_num(r.get("volume")) or 0.0
        avg30 = _safe_num(r.get("average_volume_30d_calc")) or 0.0
        vol_ratio = round(vol / avg30, 2) if avg30 > 0 else 0.0
        chg = _safe_num(r.get("change")) or 0.0
        if _is_stage2(r) and h52 > 0 and close >= 0.95 * h52 and (vol_ratio >= 0.8 or chg >= 1.5):
            b_type = "52W High Breakout" if close >= 0.99 * h52 else "Near-High Accumulation"
            breakout_stocks.append({
                "Symbol": sym,
                "Company": str(r.get("description") or sym).strip(),
                "Industry": ind,
                "Breakout Type": b_type,
                "Close": round(close, 2),
                "Change %": round(chg, 2),
                "Volume Ratio": vol_ratio,
                "RS %": rs_map.get(sym),
            })
        if vol_ratio >= 1.5 and chg > 0:
            v_label = "Explosive Volume" if vol_ratio >= 2.5 else ("Volume Spike" if vol_ratio >= 2.0 else "Accumulation")
            volume_leaders.append({
                "Symbol": sym,
                "Company": str(r.get("description") or sym).strip(),
                "Industry": ind,
                "Volume Analysis": v_label,
                "Close": round(close, 2),
                "Change %": round(chg, 2),
                "Volume Ratio": vol_ratio,
            })

    breakout_stocks.sort(key=lambda x: (x.get("RS %") or 0.0, x.get("Volume Ratio") or 0.0), reverse=True)
    volume_leaders.sort(key=lambda x: x.get("Volume Ratio") or 0.0, reverse=True)

    def _top_perf(col: str) -> list[dict]:
        valid = [r for r in rows if _safe_num(r.get(col)) is not None]
        valid.sort(key=lambda r: _safe_num(r.get(col)) or -1e9, reverse=True)
        return [
            {
                "Symbol": str(r.get("name") or "").strip().upper(),
                "Industry": str(r.get("industry") or r.get("sector") or "").strip(),
                "Return %": round(_safe_num(r.get(col)) or 0.0, 2),
                "Close": round(_safe_num(r.get("close")) or 0.0, 2),
            }
            for r in valid[:25]
        ]

    total_mcap_b = round(sum((_safe_num(r.get("market_cap_basic")) or 0.0) for r in rows) / 1e9, 1)
    return {
        "market": "US",
        "source": "tradingview_scanner",
        "source_url": "https://scanner.tradingview.com/america/scan",
        "as_of": today,
        "extracted_at": datetime.now().isoformat(),
        "min_mcap_usd_b": min_mcap,
        "spy_3m_return_pct": round(bench_3m, 2),
        "summary": {
            "last_updated": today,
            "total_filtered_companies": len(rows),
            "total_market_cap": f"${total_mcap_b:,.1f}B",
        },
        "strongest_sectors": strongest_industries,
        "industry_breadth_matrix": industry_matrix,
        "breakout_scanner_count": len(breakout_stocks),
        "breakout_scanner": breakout_stocks,
        "volume_scanner_leaders": volume_leaders[:100],
        "return_leaders_1m": _top_perf("Perf.1M"),
        "return_leaders_3m": _top_perf("Perf.3M"),
        "return_leaders_6m": _top_perf("Perf.6M"),
        "high_short_interest": [],
    }


def extract_tradingview(market: str, min_mcap: float) -> dict:
    print(f"[*] [{market}] Fetching filtered universe from TradingView Scanner API (min mcap={min_mcap:g})...")
    rows, spy_3m = fetch_tradingview_universe(market, min_mcap)
    print(f"[+] [{market}] Retrieved {len(rows)} unique stocks from TradingView.")
    return build_tradingview_stage2(market, min_mcap, rows, spy_3m=spy_3m)


def main():
    parser = argparse.ArgumentParser(description="Extract Stage 2 & Momentum breadth (TradingView default, PowerBI optional)")
    parser.add_argument("--market", choices=["IN", "US"], default="IN", help="Target market: IN or US")
    parser.add_argument("--min-mcap", type=float, default=None, help="Minimum market cap (₹ Cr for IN, $B for US)")
    parser.add_argument("--out", type=str, default=None, help="Output path for JSON data")
    parser.add_argument(
        "--source",
        choices=["tradingview", "powerbi"],
        default="tradingview",
        help="Data backend: tradingview (fast headless API, default) or powerbi (legacy Chrome scrape)",
    )
    args = parser.parse_args()

    market = args.market.upper()
    min_mcap = args.min_mcap if args.min_mcap is not None else POWERBI_URLS[market]["default_min_mcap"]
    out_path = args.out or f"data/views/stage2_{market}_latest.json"

    if args.source == "tradingview":
        payload = extract_tradingview(market, min_mcap)
    else:
        if chrome_ctl is None:
            print("Error: chrome_ctl (macos-browser-automation) is required for --source powerbi", file=sys.stderr)
            sys.exit(1)
        print(f"[*] Ensuring TheWrap {market} PowerBI dashboard is open in Chrome...")
        match_token = ensure_powerbi_open(market)

        if market == "IN":
            try:
                slicers = clear_india_slicers(match_token)
                payload = extract_in(match_token, min_mcap)
                payload["slicer_verification"] = slicers
            finally:
                close_owned_tab(match_token)
        else:
            payload = extract_us(match_token, min_mcap)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[+] Saved {market} Stage 2 / Momentum snapshot to: {out_path}")


if __name__ == "__main__":
    main()
