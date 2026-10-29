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

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

# Import chrome_ctl from macos-browser-automation skill
SKILL_PATH = os.path.expanduser("~/.agents/skills-dangerously-allow/macos-browser-automation/scripts")
if SKILL_PATH not in sys.path:
    sys.path.insert(0, SKILL_PATH)

try:
    import chrome_ctl
except ImportError:
    print(f"Error: Could not import chrome_ctl from {SKILL_PATH}", file=sys.stderr)
    sys.exit(1)

POWERBI_URLS = {
    "IN": {
        "wrap_url": "https://thewrap.in/data-tools/stage2",
        "pbi_url": "https://app.powerbi.com/view?r=eyJrIjoiMDlmNzhkZWItNDA5ZS00NjhmLTlkOTItOTM2MjkzYzYxMWZkIiwidCI6ImE3ODlmNjk1LTUxZWYtNGExMy1hZTMyLTk3NDFiNGRmMDBiNyJ9",
        "pbi_match": "MDlmNzhkZWIt",
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

        if hit_stop_val or data.get("scrollTop", 0) + data.get("clientHeight", 0) >= data.get("scrollHeight", 0) or new_found == 0:
            break

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
        time.sleep(0.5)

    cleaned = []
    if not headers:
        return cleaned
    for key, r in captured.items():
        if len(r) == len(headers):
            cleaned.append({headers[i]: r[i] for i in range(len(headers)) if headers[i] != "Row Selection"})
        else:
            cleaned.append({"key": key, "raw": r})
    return cleaned


def extract_in(match_token: str, min_mcap: float) -> dict:
    print(f"[*] [IN] Applying Market Cap filter >= ₹{min_mcap:g} Cr...")
    apply_market_cap_filter(match_token, "Market Cap Range (in cr.)", min_mcap)

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
    sectors = extract_bar_chart_sectors(
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
        max_scrolls=55,
    )

    return {
        "market": "IN",
        "source_url": POWERBI_URLS["IN"]["wrap_url"],
        "as_of": summary.get("last_updated") or datetime.now().strftime("%Y-%m-%d"),
        "extracted_at": datetime.now().isoformat(),
        "min_mcap_cr": min_mcap,
        "summary": summary,
        "strongest_sectors": sectors,
        "new_additions_this_week": new_stage2,
        "top_25_stage2": top_25,
        "relative_strength_leaders": rs_details,
        "volume_trend_leaders": vol_details,
        "momentum_leaders": momentum_details,
        "stage2_universe_count": len(all_stocks),
        "stage2_universe": all_stocks,
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


def main():
    parser = argparse.ArgumentParser(description="Extract Stage 2 & Momentum data from TheWrap via Chrome")
    parser.add_argument("--market", choices=["IN", "US"], default="IN", help="Target market: IN or US")
    parser.add_argument("--min-mcap", type=float, default=None, help="Minimum market cap (₹ Cr for IN, $B for US)")
    parser.add_argument("--out", type=str, default=None, help="Output path for JSON data")
    args = parser.parse_args()

    market = args.market.upper()
    min_mcap = args.min_mcap if args.min_mcap is not None else POWERBI_URLS[market]["default_min_mcap"]
    out_path = args.out or f"data/views/stage2_{market}_latest.json"

    print(f"[*] Ensuring TheWrap {market} PowerBI dashboard is open in Chrome...")
    match_token = ensure_powerbi_open(market)

    if market == "IN":
        payload = extract_in(match_token, min_mcap)
    else:
        payload = extract_us(match_token, min_mcap)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[+] Saved {market} Stage 2 / Momentum snapshot to: {out_path}")


if __name__ == "__main__":
    main()
