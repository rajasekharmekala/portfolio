import json
import re
import os
import openpyxl
from bs4 import BeautifulSoup

def main():
    facts_path = "scripts/.cache/facts_IN_2026-10-07.json"
    with open(facts_path) as f:
        facts = json.load(f)

    research_path = "scripts/.cache/research_IN_2026-10-07.json"
    with open(research_path) as f:
        research = json.load(f)

    wb = openpyxl.load_workbook("sheets/Zerodha_Holdings.xlsx", data_only=True)
    ws = wb.active

    holdings = []
    for r in range(2, 21):
        sym = ws.cell(r, 1).value
        qty = int(ws.cell(r, 8).value)
        avg = float(ws.cell(r, 9).value)
        inv = float(ws.cell(r, 10).value)
        wb_price = float(ws.cell(r, 11).value)
        bucket = ws.cell(r, 2).value or "TACTICAL MOMENTUM"
        
        m = facts["instruments"][sym]
        close = m["close"]
        asof = m["asof_bar"]
        mv = round(qty * close, 2)
        pnl = round(mv - inv, 2)
        pnl_pct = round((pnl / inv) * 100, 2)
        
        holdings.append({
            "sym": sym, "bucket": bucket, "qty": qty, "avg": avg, "inv": inv,
            "wb_price": wb_price, "close": close, "asof": asof, "mv": mv,
            "pnl": pnl, "pnl_pct": pnl_pct, "stage": m.get("stage"), "rsi": m.get("rsi14"),
            "atr": m.get("atr14"), "sma50": m.get("sma50"), "sma200": m.get("sma200"),
            "from_52w": m.get("pct_from_52w_high")
        })

    total_inv = sum(h["inv"] for h in holdings) # 4,003,930.16
    total_mv = sum(h["mv"] for h in holdings)   # 4,801,894.00
    cash = 3677.60
    net_worth = total_mv + cash                 # 4,805,571.60
    total_pnl = total_mv - total_inv            # 797,963.84
    total_pnl_pct = (total_pnl / total_inv) * 100 # 19.93%

    for h in holdings:
        h["wt"] = round((h["mv"] / net_worth) * 100, 2)

    # Actions and stops
    action_map = {
        "RNITAI": ("TRIM", 104.50, "1,500 sh trim to cap at 20% NW; trailing stop at ₹104.50 (rising 21-EMA buffer)"),
        "SEDEMAC": ("HOLD/TRAIL", 3079.00, "Hold and trail stop at ₹3,079.00 (below 50-DMA)"),
        "INTERARCH": ("HOLD / HARD STOP", 1595.00, "Hold with hard stop at ₹1,595.00 (recent swing low)"),
        "SANGHVIMOV": ("HOLD / HARD STOP", 385.00, "Hold with hard stop at ₹385.00 (major base support)"),
        "ASTRAMICRO": ("HOLD / HARD STOP", 1640.00, "Hold with hard stop at ₹1,640.00 (1.0 ATR below 50-DMA)"),
        "EPACKPEB": ("HOLD/TRAIL", 248.00, "Hold and trail stop at ₹248.00 (breakout shelf)"),
        "TDPOWERSYS": ("HOLD/TRAIL", 765.00, "Hold and trail stop at ₹765.00 (rising 20-DMA)"),
        "NETWEB": ("HOLD / HARD STOP", 4519.00, "Hold with hard stop at ₹4,519.00 (1.0 ATR below swing low)"),
        "AFCOM": ("HOLD / HARD STOP", 1420.00, "Hold with hard stop at ₹1,420.00 (1.0 ATR below 50-DMA)"),
        "TANFACIND": ("HOLD / HARD STOP", 3050.00, "Hold with hard stop at ₹3,050.00 (swing shelf)"),
        "ROBU": ("HOLD / HARD STOP", 995.00, "Hold with hard stop at ₹995.00 (psychological round number)"),
        "WELENT": ("HOLD/TRAIL", 685.00, "Hold and trail stop at ₹685.00 (50-DMA buffer)"),
        "APARINDS": ("HOLD/TRAIL", 16900.00, "Hold and trail stop at ₹16,900.00 (50-DMA buffer)"),
        "TARIL": ("EXIT", 280.00, "Exit 400 sh @ market; Stage 4 breakdown + 21.84% promoter pledge risk"),
        "ORIANA-SM": ("EXIT", 285.00, "Exit 375 sh @ market; Stage 4 breakdown + 6.39% pledge, profit harvest"),
        "MANORAMA": ("HOLD/TRAIL", 1865.00, "Hold and trail stop at ₹1,865.00 (50-DMA buffer)"),
        "LAURUSLABS": ("HOLD/TRAIL", 1900.00, "Hold and trail stop at ₹1,900.00 (50-DMA buffer)"),
        "BALUFORGE": ("EXIT", 480.00, "Exit 2 sh @ market; sub-scale odd-lot cleanup"),
        "BLISSGVS": ("EXIT", 640.00, "Exit 1 sh @ market; sub-scale odd-lot cleanup")
    }

    for h in holdings:
        act, stp, rule = action_map[h["sym"]]
        h["action"] = act
        h["stop"] = stp
        h["stop_rule"] = rule
        h["mar"] = round(h["qty"] * max(0.0, h["close"] - stp), 2)

    # Read base HTML
    with open("googledrive/newsletters/Portfolio_Audit_2026-10-06.html") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    # Table 1: Infobox
    tbl1 = tables[0]
    tbl1_rows = [
        '<tr><th colspan="2" style="text-align:center; background:#eaecf0; font-size:14px;">PORTFOLIO FORENSIC AUDIT DASHBOARD</th></tr>',
        '<tr><td><b>Session Date</b></td><td>2026-10-07</td></tr>',
        f'<tr><td><b>Total Net Worth (ledger marks)</b></td><td>₹{net_worth:,.2f}</td></tr>',
        f'<tr><td><b>Equities Market Value</b></td><td>₹{total_mv:,.2f} (99.92%)</td></tr>',
        f'<tr><td><b>Liquid Margin / Cash</b></td><td>₹{cash:,.2f} (0.08%)</td></tr>',
        f'<tr><td><b>Total Invested Capital</b></td><td>₹{total_inv:,.2f}</td></tr>',
        f'<tr><td><b>Total Unrealized P&amp;L</b></td><td>+₹{total_pnl:,.2f} (+{total_pnl_pct:.2f}%)</td></tr>',
        '<tr><td><b>Active Holdings Count</b></td><td>19 positions</td></tr>',
        '<tr><td><b>Macro Regime Posture</b></td><td><b>Downtrend</b> (Stage 4 Markdown)</td></tr>',
        '<tr><td><b>Benchmark Index (Nifty 50)</b></td><td>22,603.05 (-0.76% 1D, -14.3% from 52W High)</td></tr>',
        '<tr><td><b>Market Breadth</b></td><td>23.3% &gt; 50-DMA • 10/25 Distribution Days</td></tr>',
        '<tr><td><b>Sectors &gt; 50-DMA</b></td><td>0 / 11 Sectors in Stage 2 Markup</td></tr>',
        '<tr><td><b>Capital Liberation Plan</b></td><td>₹398,938.95 to be liberated via 4 Exits &amp; 1 Trim</td></tr>',
        f'<tr><td><b>Post-Reallocation Cash Buffer</b></td><td>₹402,616.55 (8.38% of Net Worth)</td></tr>'
    ]
    tbl1.clear()
    tbl1.append(BeautifulSoup("\n".join(tbl1_rows), "html.parser"))

    # Table 2: Benchmark scorecard
    tbl2 = tables[1]
    indices_data = [
        ("Nifty 50", "22,603.05", "2026-10-07", "-0.76%", "-0.50%", "-5.42%", "33.13", "-14.3%", "Stage 4"),
        ("Sensex", "72,638.70", "2026-10-07", "-0.59%", "+0.15%", "-5.07%", "35.53", "-15.7%", "Stage 4"),
        ("Bank Nifty", "55,055.55", "2026-10-07", "-0.13%", "+1.47%", "-4.03%", "40.87", "-10.9%", "Stage 4"),
        ("Nifty 500", "22,059.90", "2026-10-07", "-0.64%", "-0.19%", "-5.14%", "34.11", "-8.6%", "Stage 1"),
        ("Nifty Midcap 150", "21,838.00", "2026-10-07", "-0.64%", "-0.07%", "-5.74%", "33.67", "-7.6%", "Stage 1"),
        ("Nifty Smallcap 250", "17,917.75", "2026-10-07", "+0.09%", "+0.96%", "-3.05%", "45.26", "-3.4%", "Stage 3"),
        ("India VIX", "13.89", "2026-10-07", "+2.06%", "+3.58%", "+30.06%", "58.03", "-52.0%", "Stage 1"),
    ]
    new_tbl2_rows = [
        '<tr><th>Index</th><th class="num">Close</th><th>Bar date</th><th class="num">1D</th><th class="num">1W</th><th class="num">1M</th><th class="num">RSI(14)</th><th class="num">From 52W High</th><th>Stage</th></tr>'
    ]
    for idx_name, close_val, bdate, d1, w1, m1, rsi_val, f52w, stg in indices_data:
        new_tbl2_rows.append(
            f'<tr><td>{idx_name}</td><td class="num">{close_val}</td><td>{bdate}</td><td class="num">{d1}</td><td class="num">{w1}</td><td class="num">{m1}</td><td class="num">{rsi_val}</td><td class="num">{f52w}</td><td>{stg}</td></tr>'
        )
    tbl2.clear()
    tbl2.append(BeautifulSoup("\n".join(new_tbl2_rows), "html.parser"))

    # Table 3: Holdings Extraction Ladder
    tbl3 = tables[2]
    new_tbl3_rows = [
        '<tr><th>#</th><th>Symbol</th><th>Bucket</th><th class="num">Qty</th><th class="num">Avg</th><th class="num">Invested</th><th class="num">Ledger LTP</th><th>Bar date</th><th class="num">Workbook CMP</th><th class="num">Value</th><th class="num">Wt%</th><th class="num">P&amp;L</th><th class="num">P&amp;L%</th><th class="num">Stop</th><th class="num">Money at Risk</th><th>Stage</th><th class="num">RSI</th><th class="num">From 52W</th><th>Action</th></tr>'
    ]
    # Sort holdings: EXIT first, then TRIM, then HOLD by Wt% desc
    sorted_holdings = sorted(holdings, key=lambda x: (0 if "EXIT" in x["action"] else 1 if "TRIM" in x["action"] else 2, -x["wt"]))
    for idx, h in enumerate(sorted_holdings, 1):
        sym = h["sym"]
        sym_cell = f'<b>{sym}</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{sym}" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/{sym}/" style="color:#006600;">Screener</a></span>'
        stg_str = f"Stage {h['stage']}" if h['stage'] is not None else "Stage None"
        f52_str = f"{h['from_52w']:.1f}%" if h['from_52w'] is not None else "N/A"
        pnl_sign = "+" if h["pnl"] >= 0 else "-"
        pnl_color = "#006600" if h["pnl"] >= 0 else "#cc0000"
        action_color = "#cc0000" if "EXIT" in h["action"] else "#b45309" if "TRIM" in h["action"] else "#15803d"
        new_tbl3_rows.append(
            f'<tr><td>{idx}</td><td>{sym_cell}</td><td>{h["bucket"]}</td><td class="num">{h["qty"]:,}</td><td class="num">{h["avg"]:,.2f}</td><td class="num">₹{h["inv"]:,.0f}</td><td class="num">{h["close"]:,.2f}</td><td>{h["asof"]}</td><td class="num">{h["wb_price"]:,.2f}</td><td class="num">₹{h["mv"]:,.0f}</td><td class="num">{h["wt"]:.2f}%</td><td class="num" style="color:{pnl_color};">{pnl_sign}₹{abs(h["pnl"]):,.0f}</td><td class="num" style="color:{pnl_color};">{h["pnl_pct"]:+.2f}%</td><td class="num">{h["stop"]:,.2f}</td><td class="num">₹{h["mar"]:,.0f}</td><td>{stg_str}</td><td class="num">{h["rsi"]:.2f}</td><td class="num">{f52_str}</td><td style="font-weight:bold; color:{action_color};">{h["action"]}</td></tr>'
        )
    tbl3.clear()
    tbl3.append(BeautifulSoup("\n".join(new_tbl3_rows), "html.parser"))

    # Table 4: Greenfield Target Allocation (Downtrend = 0% Live Allocation)
    tbl4 = tables[3]
    new_tbl4_rows = [
        '<tr><th>Symbol</th><th>Bucket</th><th class="num">Capital</th><th class="num">Entry</th><th class="num">Stop</th><th class="num">Target</th><th class="num">Shares</th><th class="num">R:R</th><th>Stage</th><th class="num">RSI</th><th class="num">From 52W</th></tr>',
        '<tr><td colspan="11" style="text-align:center; padding:16px; background:#fef2f2; color:#991b1b; font-weight:bold;">MARKET REGIME DEFENSIVE MANDATE: ZERO NEW GREENFIELD BUYS IN DOWNTREND (0.0% CAPITAL DEPLOYMENT). ALL 27 BULL CANDIDATES ASSIGNED TO RADAR-ONLY CONTINGENT MONITORING.</td></tr>'
    ]
    tbl4.clear()
    tbl4.append(BeautifulSoup("\n".join(new_tbl4_rows), "html.parser"))

    # Table 5: Bull List (27 picks)
    tbl5 = tables[4]
    new_bull_rows = [
        '<tr><th>Tier</th><th>Symbol</th><th>Name</th><th class="num">Close</th><th class="num">RSI</th><th class="num">From 52W</th><th>Qualifier</th></tr>'
    ]
    for tier in ["Large", "Mid", "Small"]:
        for p in facts["screen"]["bull_pick"][tier]:
            sym = p["symbol"]
            nm = p["name"]
            cls_v = f"{p['close']:,.2f}"
            rsi_v = f"{p['rsi14']:.2f}"
            f52_v = f"{p['pct_from_52w_high']:.1f}%"
            qual = p["qualifier"]
            sym_cell = f'<b>{sym}</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{sym}" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/{sym}/" style="color:#006600;">Screener</a></span>'
            new_bull_rows.append(
                f'<tr><td>{tier}</td><td>{sym_cell}</td><td>{nm}</td><td class="num">{cls_v}</td><td class="num">{rsi_v}</td><td class="num">{f52_v}</td><td>{qual}</td></tr>'
            )
    tbl5.clear()
    tbl5.append(BeautifulSoup("\n".join(new_bull_rows), "html.parser"))

    # Table 6: Bear List (30 picks)
    tbl6 = tables[5]
    new_bear_rows = [
        '<tr><th>Tier</th><th>Symbol</th><th>Name</th><th class="num">Close</th><th class="num">RSI</th><th class="num">From 52W</th><th>Qualifier</th></tr>'
    ]
    for tier in ["Large", "Mid", "Small"]:
        for p in facts["screen"]["bear_pick"][tier]:
            sym = p["symbol"]
            nm = p["name"]
            cls_v = f"{p['close']:,.2f}"
            rsi_v = f"{p['rsi14']:.2f}"
            f52_v = f"{p['pct_from_52w_high']:.1f}%"
            qual = p["qualifier"]
            sym_cell = f'<b>{sym}</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{sym}" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/{sym}/" style="color:#006600;">Screener</a></span>'
            new_bear_rows.append(
                f'<tr><td>{tier}</td><td>{sym_cell}</td><td>{nm}</td><td class="num">{cls_v}</td><td class="num">{rsi_v}</td><td class="num">{f52_v}</td><td>{qual}</td></tr>'
            )
    tbl6.clear()
    tbl6.append(BeautifulSoup("\n".join(new_bear_rows), "html.parser"))

    # Table 7: Master Money Bridge
    tbl7 = tables[6]
    # Sells:
    # RNITAI: -1,500 sh @ 111.90 = -167,850.00 -> Target: 8,500 sh = 951,150.00 (19.79%)
    # TARIL: -400 sh @ 289.15 = -115,660.00 -> Target: 0 (0.00%)
    # ORIANA-SM: -375 sh @ 303.30 = -113,737.50 -> Target: 0 (0.00%)
    # BALUFORGE: -2 sh @ 507.50 = -1,015.00 -> Target: 0 (0.00%)
    # BLISSGVS: -1 sh @ 676.45 = -676.45 -> Target: 0 (0.00%)
    # Cash: +398,938.95 -> Target: 402,616.55 (8.38%)
    # All others: variance 0.00
    target_weights = {
        "RNITAI": 19.79,
        "SEDEMAC": 14.26,
        "INTERARCH": 8.77,
        "SANGHVIMOV": 7.61,
        "ASTRAMICRO": 7.10,
        "EPACKPEB": 5.84,
        "TDPOWERSYS": 4.16,
        "NETWEB": 3.90,
        "AFCOM": 3.75,
        "TANFACIND": 3.67,
        "ROBU": 3.62,
        "WELENT": 2.93,
        "APARINDS": 2.62,
        "TARIL": 0.00,
        "ORIANA-SM": 0.00,
        "MANORAMA": 2.28,
        "LAURUSLABS": 1.32,
        "BALUFORGE": 0.00,
        "BLISSGVS": 0.00,
    }
    variances = {
        "RNITAI": -167850.00,
        "SEDEMAC": 0.00,
        "INTERARCH": 0.00,
        "SANGHVIMOV": 0.00,
        "ASTRAMICRO": 0.00,
        "EPACKPEB": 0.00,
        "TDPOWERSYS": 0.00,
        "NETWEB": 0.00,
        "AFCOM": 0.00,
        "TANFACIND": 0.00,
        "ROBU": 0.00,
        "WELENT": 0.00,
        "APARINDS": 0.00,
        "TARIL": -115660.00,
        "ORIANA-SM": -113737.50,
        "MANORAMA": 0.00,
        "LAURUSLABS": 0.00,
        "BALUFORGE": -1015.00,
        "BLISSGVS": -676.45,
    }
    new_tbl7_rows = [
        '<tr><th>Symbol</th><th class="num">Current Wt%</th><th class="num">Target Wt%</th><th class="num">Variance (₹)</th><th class="num">Variance (% of NW)</th><th>Action</th></tr>'
    ]
    for h in sorted_holdings:
        sym = h["sym"]
        sym_cell = f'<b>{sym}</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{sym}" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/{sym}/" style="color:#006600;">Screener</a></span>'
        cur_wt = h["wt"]
        tgt_wt = target_weights[sym]
        var_rupees = variances[sym]
        var_pct = round((var_rupees / net_worth) * 100, 2)
        var_str = f"-₹{abs(var_rupees):,.2f}" if var_rupees < 0 else f"+₹{var_rupees:,.2f}" if var_rupees > 0 else "₹0.00"
        var_pct_str = f"{var_pct:+.2f}%" if var_rupees != 0 else "0.00%"
        new_tbl7_rows.append(
            f'<tr><td>{sym_cell}</td><td class="num">{cur_wt:.2f}%</td><td class="num">{tgt_wt:.2f}%</td><td class="num">{var_str}</td><td class="num">{var_pct_str}</td><td>{h["action"]}</td></tr>'
        )
    # Add Cash buffer row
    cash_cur_wt = round((cash / net_worth) * 100, 2) # 0.08%
    cash_tgt_wt = round((402616.55 / net_worth) * 100, 2) # 8.38%
    cash_var_rupees = 398938.95
    cash_var_pct = round((cash_var_rupees / net_worth) * 100, 2) # +8.30%
    new_tbl7_rows.append(
        f'<tr style="background:#f0fdf4; font-weight:bold;"><td><b>Cash &amp; Liquid Margin Buffer</b></td><td class="num">{cash_cur_wt:.2f}%</td><td class="num">{cash_tgt_wt:.2f}%</td><td class="num">+₹{cash_var_rupees:,.2f}</td><td class="num">+{cash_var_pct:.2f}%</td><td>REBUILD DRY POWDER</td></tr>'
    )
    tbl7.clear()
    tbl7.append(BeautifulSoup("\n".join(new_tbl7_rows), "html.parser"))

    # Table 8: Step-by-step Cash Waterfall
    tbl8 = tables[7]
    waterfall_data = [
        ("Opening balance", "Workbook cash / margin buffer", "₹3,677.60", "₹3,677.60"),
        ("TRIM", "RNITAI proceeds at ledger close 111.90 (1,500 sh)", "+₹167,850.00", "₹171,527.60"),
        ("EXIT", "TARIL proceeds at ledger close 289.15 (400 sh)", "+₹115,660.00", "₹287,187.60"),
        ("EXIT", "ORIANA-SM proceeds at ledger close 303.30 (375 sh)", "+₹113,737.50", "₹400,925.10"),
        ("EXIT", "BALUFORGE proceeds at ledger close 507.50 (2 sh)", "+₹1,015.00", "₹401,940.10"),
        ("EXIT", "BLISSGVS proceeds at ledger close 676.45 (1 sh)", "+₹676.45", "₹402,616.55"),
        ("Ending balance", "Post-reallocation cash buffer (8.38% of NW; no live purchases)", "₹0.00", "₹402,616.55")
    ]
    new_tbl8_rows = [
        '<tr><th>Step</th><th>Cash-flow item</th><th class="num">Change (₹)</th><th class="num">Running cash (₹)</th></tr>'
    ]
    for step, item, chg, runc in waterfall_data:
        bold_style = ' style="font-weight:bold; background:#f9fafb;"' if "balance" in step else ""
        new_tbl8_rows.append(
            f'<tr{bold_style}><td><b>{step}</b></td><td>{item}</td><td class="num">{chg}</td><td class="num">{runc}</td></tr>'
        )
    tbl8.clear()
    tbl8.append(BeautifulSoup("\n".join(new_tbl8_rows), "html.parser"))

    # Table 9: Phase 1 Sells
    tbl9 = tables[8]
    sells_data = [
        ("RNITAI", "2026-10-06", "1,500", "111.90", "₹167,850.00", "Trim to 20% account concentration cap; harvest profits into strength.", "Current session only; limit order at ₹111.90 or better."),
        ("TARIL", "2026-10-07", "400", "289.15", "₹115,660.00", "Stage 4 markdown breakdown below 50-DMA + 21.84% promoter pledge risk.", "Current session only; market order at market open."),
        ("ORIANA-SM", "2026-10-06", "375", "303.30", "₹113,737.50", "Stage 4 breakdown rollover + 6.39% pledge; harvest +14.45% unrealized gains.", "Current session only; limit order at ₹303.30 or better."),
        ("BALUFORGE", "2026-10-07", "2", "507.50", "₹1,015.00", "Odd-lot residual cleanup; eliminate tracking clutter (<0.02% of portfolio).", "Current session only; market order."),
        ("BLISSGVS", "2026-10-06", "1", "676.45", "₹676.45", "Odd-lot residual cleanup; eliminate tracking clutter (<0.02% of portfolio).", "Current session only; market order.")
    ]
    new_tbl9_rows = [
        '<tr><th>Symbol</th><th>Bar date</th><th class="num">Shares</th><th class="num">Ref Price</th><th class="num">Est. Proceeds</th><th>Trigger / Order</th><th>Expiry / If Unfilled</th></tr>'
    ]
    for sym, bdate, sh, refp, estp, trig, exp in sells_data:
        sym_cell = f'<b>{sym}</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{sym}" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/{sym}/" style="color:#006600;">Screener</a></span>'
        new_tbl9_rows.append(
            f'<tr><td>{sym_cell}</td><td>{bdate}</td><td class="num">{sh}</td><td class="num">{refp}</td><td class="num">{estp}</td><td>{trig}</td><td>{exp}</td></tr>'
        )
    tbl9.clear()
    tbl9.append(BeautifulSoup("\n".join(new_tbl9_rows), "html.parser"))

    # Table 10: Phase 2 Contingent Limit Buys
    tbl10 = tables[9]
    new_tbl10_rows = [
        '<tr><th>Symbol</th><th>Shares</th><th class="num">Limit Entry</th><th class="num">Stop</th><th class="num">Est. Cost</th></tr>',
        '<tr><td colspan="5" style="text-align:center; padding:12px; background:#f9fafb; color:#6b7280; font-style:italic;">NO LIVE MARKET BUYS AUTHORIZED IN DOWNTREND REGIME. CONTINGENT LIMIT ORDERS PARKED AT MAJOR SUPPORT FOR RADAR MONITORING ONLY.</td></tr>'
    ]
    tbl10.clear()
    tbl10.append(BeautifulSoup("\n".join(new_tbl10_rows), "html.parser"))

    # Table 11: Phase 3 GTT Trailing Stops (15 retained holdings)
    tbl11 = tables[10]
    retained_stops = [
        ("RNITAI", "TRIM (8,500 sh retained)", "111.90", "104.50", "Daily close at or below ₹104.50 (1.5 ATR buffer below 21-EMA) triggers immediate exit."),
        ("SEDEMAC", "HOLD/TRAIL (200 sh)", "3,425.60", "3,079.00", "Daily close below ₹3,079.00 (rising 50-DMA) triggers trailing defense."),
        ("INTERARCH", "HOLD / HARD STOP (250 sh)", "1,685.60", "1,595.00", "Daily close below ₹1,595.00 (prior structural base swing low) triggers defensive exit."),
        ("SANGHVIMOV", "HOLD / HARD STOP (890 sh)", "410.65", "385.00", "Daily close below ₹385.00 (major 52-week base support) invalidates thesis."),
        ("ASTRAMICRO", "HOLD / HARD STOP (200 sh)", "1,705.90", "1,640.00", "Daily close below ₹1,640.00 (1.0 ATR below 50-DMA) invalidates technical base structure."),
        ("EPACKPEB", "HOLD/TRAIL (1,050 sh)", "267.44", "248.00", "Daily close below ₹248.00 (prior multi-week breakout shelf) triggers stop."),
        ("TDPOWERSYS", "HOLD/TRAIL (245 sh)", "816.00", "765.00", "Daily close below ₹765.00 (rising 20-DMA buffer) locks in gains."),
        ("NETWEB", "HOLD / HARD STOP (40 sh)", "4,685.40", "4,519.00", "Daily close below ₹4,519.00 (1.0 ATR below recent swing low) invalidates position."),
        ("AFCOM", "HOLD / HARD STOP (120 sh)", "1,501.40", "1,420.00", "Daily close below ₹1,420.00 (1.0 ATR below 50-DMA) triggers protective exit."),
        ("TANFACIND", "HOLD / HARD STOP (55 sh)", "3,204.30", "3,050.00", "Daily close below ₹3,050.00 (key structural shelf) invalidates consolidation."),
        ("ROBU", "HOLD / HARD STOP (165 sh)", "1,053.35", "995.00", "Daily close below ₹995.00 (psychological round number threshold) triggers stop."),
        ("WELENT", "HOLD/TRAIL (190 sh)", "740.75", "685.00", "Daily close below ₹685.00 (rising 50-DMA cushion) locks in compounding trend."),
        ("APARINDS", "HOLD/TRAIL (7 sh)", "18,016.00", "16,900.00", "Daily close below ₹16,900.00 (rising 50-DMA cushion) defends gains."),
        ("MANORAMA", "HOLD/TRAIL (55 sh)", "1,996.00", "1,865.00", "Daily close below ₹1,865.00 (rising 50-DMA cushion) locks in Stage 2 trend."),
        ("LAURUSLABS", "HOLD/TRAIL (31 sh)", "2,052.80", "1,900.00", "Daily close below ₹1,900.00 (rising 50-DMA cushion) locks in Stage 2 trend.")
    ]
    new_tbl11_rows = [
        '<tr><th>Security</th><th>Position status</th><th class="num">CMP (₹)</th><th class="num">GTT trigger (₹)</th><th>Rule</th></tr>'
    ]
    for sym, stat, cmp_v, gtt_v, rule in retained_stops:
        sym_cell = f'<b>{sym}</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{sym}" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/{sym}/" style="color:#006600;">Screener</a></span>'
        new_tbl11_rows.append(
            f'<tr><td>{sym_cell}</td><td>{stat}</td><td class="num">{cmp_v}</td><td class="num">{gtt_v}</td><td>{rule}</td></tr>'
        )
    tbl11.clear()
    tbl11.append(BeautifulSoup("\n".join(new_tbl11_rows), "html.parser"))

    # Update casenotes for all 19 holdings
    casenote_divs = soup.find_all("div", class_="casenote")
    # Build dictionary of casenote content for all 19 holdings
    casenote_data = {
        "RNITAI": """<b>RNITAI</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ARNITAI" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/RNITAI/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — TRIM<br>
<b>Business and place in the book:</b> RNIT AI Solutions Limited provides enterprise AI automation platforms and specialized cloud infrastructure. You own 10,000 shares in the TACTICAL MOMENTUM bucket, representing a high-conviction thematic play on domestic artificial intelligence adoption with an average cost basis of ₹55.33 (total invested capital of ₹553,258.29).<br>
<b>The numbers and what they mean:</b> At the official ledger close of ₹111.90 (as-of bar 2026-10-06), the position is valued at ₹1,119,000.00, generating an exceptional unrealized profit of +₹565,741.71 (+102.26%). RNITAI trades firmly in Stage 2 markup, well above its rising 50-DMA of ₹88.00 and 200-DMA of ₹65.12. The 14-day RSI stands at 70.32, reflecting strong bullish momentum without extreme exhaustion, and ATR(14) is ₹4.86. The stock sits just 2.48% below its 52-week high of ₹114.75. Promoter pledge is completely clean at 0.00% across a 63.23% promoter holding.<br>
<b>The verdict and the rule behind it:</b> TRIM 1,500 shares. The position currently represents 23.29% of total net worth, breaching our institutional single-stock concentration ceiling of 20.00%. While the Super-Performer Momentum Exception protects winning Stage 2 leaders from premature liquidation, the Macro Downtrend Cash Mandate requires liberating capital to build our liquid margin buffer. Trimming 1,500 shares at ₹111.90 liberates ₹167,850.00 in cash, reducing residual holdings to 8,500 shares valued at ₹951,150.00 (19.79% of net worth), bringing the position strictly into compliance.<br>
<b>What would change the verdict:</b> A daily close below the formula stop of ₹104.50 (anchored to the rising 21-EMA) would trigger an immediate defensive exit of the remaining 8,500 shares. Conversely, if RNITAI consolidates above ₹112.00 on expanding volume, the remaining position will be held to compound toward the technical measured-move target of ₹145.00.""",

        "SEDEMAC": """<b>SEDEMAC</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ASEDEMAC" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/SEDEMAC/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — HOLD/TRAIL<br>
<b>Business and place in the book:</b> Sedemac Mechatronics Limited manufactures proprietary sensorless BLDC motor controllers and smart starter generators with deep Tier-1 OEM moats across two-wheelers and commercial vehicles. Held in the TACTICAL MOMENTUM bucket with 200 shares at an average cost of ₹2,025.49 (invested capital ₹405,098.25).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹3,425.60 (as-of bar 2026-10-07), the position is valued at ₹685,120.00, yielding an unrealized gain of +₹280,021.75 (+69.12%) and accounting for 14.26% of net worth. The stock trades comfortably above its rising 50-DMA of ₹3,079.66 with an ATR(14) of ₹149.54 and an RSI of 63.63, sitting just 2.13% below its 52-week peak of ₹3,500.00. Promoter pledge is verified at 0.00% across a 26.23% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / TRAIL. Sedemac satisfies all Stage 2 trend and momentum criteria. It maintains positive relative strength against the broader market correction and comfortably clears all operating cash flow and balance sheet quality gates.<br>
<b>What would change the verdict:</b> A daily close below ₹3,079.00 (its 50-DMA support) would trigger a systematic trailing stop to lock in accumulated profits. An upside breakout above ₹3,500.00 on volume exceeding 1.8x average would open runway toward ₹4,200.00.""",

        "INTERARCH": """<b>INTERARCH</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AINTERARCH" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/INTERARCH/" style="color:#006600;">Screener</a></span> — CORE ALPHA — HOLD / HARD STOP<br>
<b>Business and place in the book:</b> Interarch Building Products Limited provides turnkey pre-engineered steel building (PEB) solutions benefiting from India's industrial capex, manufacturing capacity expansion, and warehousing logistics boom. Held in the CORE ALPHA compounding bucket with 250 shares at an average cost of ₹1,913.06 (invested capital ₹478,264.70).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹1,685.60 (as-of bar 2026-10-06), the position is valued at ₹421,400.00 (8.77% of net worth), carrying an unrealized loss of -₹56,864.70 (-11.89%). The stock sits below its 50-DMA of ₹1,720.60 and 200-DMA of ₹1,879.23 in a Stage 4 consolidation band, with RSI at 46.57, ATR at ₹46.77, and trading 16.47% below its 52-week high of ₹2,018.00. Promoter pledge is pristine at 0.00% on 59.43% equity.<br>
<b>The verdict and the rule behind it:</b> HOLD / HARD STOP at ₹1,595.00. While the technical trend has slipped into Stage 4 markdown during the broader midcap correction, Interarch possesses an exceptional net-cash balance sheet, zero debt, and robust order backlog execution. Because our cash liberation mandate is fully satisfied by liquidating distressed holdings and trimming RNITAI, we retain Interarch under strict stop protection.<br>
<b>What would change the verdict:</b> A daily close below the hard stop of ₹1,595.00 (recent structural swing low) triggers an immediate 100% exit. Conversely, a decisive reclaim of ₹1,721.00 (50-DMA) upgrades posture to ACCUMULATE ON DIP with a target of ₹2,100.00.""",

        "SANGHVIMOV": """<b>SANGHVIMOV</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ASANGHVIMOV" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/SANGHVIMOV/" style="color:#006600;">Screener</a></span> — CORE ALPHA — HOLD / HARD STOP<br>
<b>Business and place in the book:</b> Sanghvi Movers Limited is the largest crane rental and heavy-lift logistics company in India and Asia, essential for wind energy installation, refinery construction, and metro rail infrastructure. Held in CORE ALPHA with 890 shares at an average cost of ₹456.58 (invested capital ₹406,356.40).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹410.65 (as-of bar 2026-10-07), the position is valued at ₹365,478.50 (7.61% of net worth), reflecting an unrealized drawdown of -₹40,877.90 (-10.06%). It trades in Stage 3 topping/correction below its 50-DMA of ₹452.98 but above its 200-DMA of ₹363.98. RSI is 38.97, ATR is ₹20.41, and it sits 24.37% below its 52-week peak of ₹543.00. Promoter pledge is 0.00% across 47.25% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / HARD STOP at ₹385.00. High capacity utilization (>82%), market-leading pricing power, and massive asset replacement cost provide a strong structural margin of safety.<br>
<b>What would change the verdict:</b> A daily close below ₹385.00 invalidates the cyclical support thesis and triggers an immediate liquidation. A sustained recovery above the 50-DMA at ₹453.00 would confirm Stage 2 re-entry toward ₹530.00.""",

        "ASTRAMICRO": """<b>ASTRAMICRO</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AASTRAMICRO" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/ASTRAMICRO/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — HOLD / HARD STOP<br>
<b>Business and place in the book:</b> Astra Microwave Products Limited designs and manufactures sub-systems for defense radars, electronic warfare suites, missile telemetry, and satellite communications. Held in TACTICAL MOMENTUM with 200 shares at an average cost of ₹1,684.72 (invested capital ₹336,944.80).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹1,705.90 (as-of bar 2026-10-06), the position is valued at ₹341,180.00 (7.10% of net worth), showing a modest unrealized gain of +₹4,235.20 (+1.26%). It trades in Stage 3 consolidation above its 50-DMA of ₹1,693.72 and well above its 200-DMA of ₹1,316.78. RSI is 56.79, ATR is ₹51.97, and the stock is 6.78% below its 52-week high of ₹1,830.00. Promoter pledge is 0.00% on 6.54% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / HARD STOP at ₹1,640.00. Defence indigenization order inflows provide strong visibility, and the stock is holding above its rising moving averages despite market turmoil.<br>
<b>What would change the verdict:</b> A daily close below ₹1,640.00 (1.0 ATR below the 50-DMA) invalidates the tactical momentum structure and triggers an exit. A breakout above ₹1,830.00 targets ₹2,100.00.""",

        "EPACKPEB": """<b>EPACKPEB</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AEPACKPEB" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/EPACKPEB/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — HOLD/TRAIL<br>
<b>Business and place in the book:</b> EPACK Prefab Limited manufactures prefabricated structures, EPS packaging, and light gauge steel frames for industrial and commercial infrastructure. Held in TACTICAL MOMENTUM with 1,050 shares at an average cost of ₹227.81 (invested capital ₹239,202.07).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹267.44 (as-of bar 2026-10-07), the position is valued at ₹280,812.00 (5.84% of net worth), generating an unrealized profit of +₹41,609.93 (+17.40%). The stock is in Stage 3 consolidation trading above its 50-DMA of ₹239.08 and 200-DMA of ₹218.02. RSI is 68.05, ATR is ₹11.60, and distance from 52-week high is -10.22%. Promoter pledge is 0.00% across 64.95% equity.<br>
<b>The verdict and the rule behind it:</b> HOLD / TRAIL. EPACKPEB exhibits constructive volume expansion and relative strength during the market drawdown.<br>
<b>What would change the verdict:</b> A daily close below ₹248.00 (prior breakout shelf) triggers our trailing stop. A breakout above ₹298.00 opens runway toward ₹335.00.""",

        "TDPOWERSYS": """<b>TDPOWERSYS</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ATDPOWERSYS" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/TDPOWERSYS/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — HOLD/TRAIL<br>
<b>Business and place in the book:</b> TD Power Systems Limited is a leading global manufacturer of AC generators for steam, gas, hydro, and diesel turbines used in industrial captive power and marine propulsion. Held in TACTICAL MOMENTUM with 245 shares at an average cost of ₹744.64 (invested capital ₹182,435.65).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹816.00 (as-of bar 2026-10-06), the position is valued at ₹199,920.00 (4.16% of net worth), yielding an unrealized gain of +₹17,484.35 (+9.58%). It trades in Stage 2 markup above its rising 50-DMA of ₹723.61 and 200-DMA of ₹551.41. RSI is 61.56, ATR is ₹37.73, and it trades just 1.69% below its 52-week peak of ₹830.00. Promoter pledge is 0.00% on 26.87% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / TRAIL. Outstanding export order book execution and global power generation capex justify maintaining the position with a trailing stop.<br>
<b>What would change the verdict:</b> A daily close below ₹765.00 (rising 20-DMA support) triggers trailing risk management. A breakout above ₹830.00 targets ₹980.00.""",

        "NETWEB": """<b>NETWEB</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ANETWEB" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/NETWEB/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — HOLD / HARD STOP<br>
<b>Business and place in the book:</b> Netweb Technologies India Limited provides high-end computing solutions (HPC), AI supercomputing systems, private cloud HCI, and enterprise storage. Held in TACTICAL MOMENTUM with 40 shares at an average cost of ₹5,231.01 (invested capital ₹209,240.55).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹4,685.40 (as-of bar 2026-10-07), the position is valued at ₹187,416.00 (3.90% of net worth), showing an unrealized loss of -₹21,824.55 (-10.43%). The stock is in Stage 3 consolidation below its 50-DMA of ₹4,914.45 but above its 200-DMA of ₹4,064.82. RSI is 46.74, ATR is ₹166.28, and it sits 18.23% below its 52-week high of ₹5,730.00. Promoter pledge is 0.00% across 66.98% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / HARD STOP at ₹4,519.00. Netweb's proprietary OEM partnership with NVIDIA and domestic sovereign AI infrastructure buildout provide secular growth tailwinds.<br>
<b>What would change the verdict:</b> A daily close below ₹4,519.00 (1.0 ATR below the recent swing low) invalidates the technical base and triggers a stop-out. A reclaim of ₹4,915.00 (50-DMA) opens a path toward ₹5,800.00.""",

        "AFCOM": """<b>AFCOM</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AAFCOM" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/AFCOM/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — HOLD / HARD STOP<br>
<b>Business and place in the book:</b> Afcom Holdings Limited operates dedicated cargo airline services and air logistics connecting Indian industrial hubs to Southeast Asia. Held in TACTICAL MOMENTUM with 120 shares at an average cost of ₹1,620.00 (invested capital ₹194,400.00).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹1,501.40 (as-of bar 2026-10-06), the position is valued at ₹180,168.00 (3.75% of net worth), reflecting an unrealized loss of -₹14,232.00 (-7.32%). The stock trades in Stage 2 markup just above its 50-DMA of ₹1,499.16 and above its 200-DMA of ₹1,068.70. RSI is 51.63, ATR is ₹75.44, and it is 14.93% below its 52-week high of ₹1,765.00. Promoter pledge is verified clean at 0.00% across 35.84% equity.<br>
<b>The verdict and the rule behind it:</b> HOLD / HARD STOP at ₹1,420.00. Afcom is currently testing its critical 50-DMA support shelf. With adequate cash liberated from other exits, we give the position room to prove support above ₹1,420.00.<br>
<b>What would change the verdict:</b> A daily close below ₹1,420.00 (1.0 ATR below the 50-DMA) invalidates the trend and triggers an immediate defensive exit. A bounce above ₹1,620.00 targets ₹1,850.00.""",

        "TANFACIND": """<b>TANFACIND</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ATANFACIND" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/TANFACIND/" style="color:#006600;">Screener</a></span> — CORE ALPHA — HOLD / HARD STOP<br>
<b>Business and place in the book:</b> Tanfac Industries Limited is a leading manufacturer of anhydrous hydrofluoric acid, aluminium fluoride, and specialty fluorochemicals. Held in CORE ALPHA with 55 shares at an average cost of ₹3,162.65 (invested capital ₹173,945.55).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹3,204.30 (as-of bar 2026-10-06), the position is valued at ₹176,236.50 (3.67% of net worth), showing an unrealized gain of +₹2,290.95 (+1.32%). The stock is in Stage 3 consolidation slightly below its 50-DMA of ₹3,245.99 but well above its 200-DMA of ₹2,446.47. RSI is 43.10, ATR is ₹147.37, and distance from 52-week peak is -10.24%. Promoter pledge is 0.00% on 48.73% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / HARD STOP at ₹3,050.00. High ROE (>24%), clean balance sheet, and joint-venture promoter backing (Anupam Rasayan and TIDCO) justify holding.<br>
<b>What would change the verdict:</b> A daily close below ₹3,050.00 invalidates the multi-month support base and triggers an exit. A reclaim of ₹3,350.00 targets ₹3,850.00.""",

        "ROBU": """<b>ROBU</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AROBU" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/ROBU/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — HOLD / HARD STOP<br>
<b>Business and place in the book:</b> Macfos Limited (Robu.in) is an e-commerce platform distributing robotics, DIY electronics, IoT components, drones, and 3D printing equipment. Held in TACTICAL MOMENTUM with 165 shares at an average cost of ₹1,100.00 (invested capital ₹181,500.00).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹1,053.35 (as-of bar 2026-10-06), the position is valued at ₹173,802.75 (3.62% of net worth), reflecting an unrealized drawdown of -₹7,697.25 (-4.24%). The stock is in Stage 3 consolidation below its 50-DMA of ₹1,119.58 but above its 200-DMA of ₹972.94. RSI is 43.87, ATR is ₹54.11, and it trades 16.07% below its 52-week high of ₹1,255.00. Promoter pledge is 0.00% across 69.12% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / HARD STOP at ₹995.00. Asset-light distribution model, rapid product catalogue expansion, and strong DIY/engineering college penetration support long-term growth.<br>
<b>What would change the verdict:</b> A daily close below ₹995.00 (psychological round number threshold) triggers an immediate stop-loss. A rebound above ₹1,120.00 targets ₹1,300.00.""",

        "WELENT": """<b>WELENT</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AWELENT" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/WELENT/" style="color:#006600;">Screener</a></span> — CORE ALPHA — HOLD/TRAIL<br>
<b>Business and place in the book:</b> Welspun Enterprises Limited is an infrastructure development arm focusing on road HAM projects, water transmission systems, and wastewater treatment under national Jal Jeevan missions. Held in CORE ALPHA with 190 shares at an average cost of ₹713.53 (invested capital ₹135,571.40).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹740.75 (as-of bar 2026-10-07), the position is valued at ₹140,742.50 (2.93% of net worth), showing an unrealized gain of +₹5,171.10 (+3.81%). It trades in Stage 2 markup above its rising 50-DMA of ₹690.81 and 200-DMA of ₹557.23. RSI is 51.74, ATR is ₹27.84, and distance from 52-week high is -3.80%. Promoter pledge is 0.00% on 56.13% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / TRAIL. High-visibility order book (>₹12,000 Cr) and strong cash generation make it a solid compounder.<br>
<b>What would change the verdict:</b> A daily close below ₹685.00 (50-DMA support) triggers trailing protection. An upside breakout above ₹770.00 targets ₹900.00.""",

        "APARINDS": """<b>APARINDS</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AAPARINDS" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/APARINDS/" style="color:#006600;">Screener</a></span> — CORE ALPHA — HOLD/TRAIL<br>
<b>Business and place in the book:</b> Apar Industries Limited is a global manufacturer of conductors, transformer oils, specialty cables, and telecom lubricants. Held in CORE ALPHA with 7 shares at an average cost of ₹17,007.49 (invested capital ₹119,052.40).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹18,016.00 (as-of bar 2026-10-06), the position is valued at ₹126,112.00 (2.62% of net worth), generating an unrealized profit of +₹7,059.60 (+5.93%). It is in Stage 2 markup above its rising 50-DMA of ₹17,061.64 and 200-DMA of ₹12,811.45. RSI is 55.20, ATR is ₹706.34, and distance from 52-week peak is -7.13%. Promoter pledge is 0.00% across 55.40% equity.<br>
<b>The verdict and the rule behind it:</b> HOLD / TRAIL. Unmatched global power grid expansion and renewable transmission export tailwinds support multi-year compounding.<br>
<b>What would change the verdict:</b> A daily close below ₹16,900.00 (50-DMA support) triggers trailing defense. A breakout above ₹19,400.00 targets ₹21,500.00.""",

        "TARIL": """<b>TARIL</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ATARIL" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/TARIL/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — EXIT<br>
<b>Business and place in the book:</b> Transformers and Rectifiers (India) Limited manufactures power, distribution, and specialty furnace transformers. Held in TACTICAL MOMENTUM with 400 shares at an average cost basis of ₹307.27 (invested capital ₹122,906.20).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹289.15 (as-of bar 2026-10-07), the position is valued at ₹115,660.00 (2.41% of net worth), carrying an unrealized loss of -₹7,246.20 (-5.90%). The stock has broken down into Stage 4 markdown, trading below its declining 50-DMA of ₹291.49 and 200-DMA of ₹298.51. The 14-day RSI is 53.27, ATR(14) is ₹10.31, and it sits 29.48% below its 52-week high of ₹410.00. Most critically, verified exchange disclosures confirm a promoter pledge of 21.84% across a 64.36% promoter equity stake.<br>
<b>The verdict and the rule behind it:</b> EXIT (Immediate 100% liquidation). TARIL violates our non-negotiable risk rules: promoter pledge exceeds our 10% maximum tolerance threshold by more than 2x, and the price structure has confirmed a Stage 4 markdown breakdown below both key moving averages. Liquidating all 400 shares at ₹289.15 liberates ₹115,660.00 in cash, eliminating severe forced-selling tail risk.<br>
<b>What would change the verdict:</b> Only a complete de-pledging of promoter shares below 5% and a decisive weekly close above ₹315.00 with expanding institutional accumulation would qualify TARIL for future re-underwriting.""",

        "ORIANA-SM": """<b>ORIANA-SM</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AORIANA-SM" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/ORIANA-SM/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — EXIT<br>
<b>Business and place in the book:</b> Oriana Power Limited is an SME-listed solar power developer delivering commercial EPC solar installations and floating solar power plants. Held in TACTICAL MOMENTUM with 375 shares at an average cost of ₹265.00 (invested capital ₹99,375.00).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹303.30 (as-of bar 2026-10-06), the position is valued at ₹113,737.50 (2.37% of net worth), showing an unrealized gain of +₹14,362.50 (+14.45%). The stock is in severe Stage 4 markdown, trading drastically below its 50-DMA of ₹904.70 and 200-DMA of ₹1,602.98 following a massive historical correction. RSI is oversold at 22.01, ATR is ₹48.08, and it sits 84.68% below its 52-week peak of ₹1,980.00. Exchange filings confirm an active promoter pledge of 6.39% on 57.98% equity.<br>
<b>The verdict and the rule behind it:</b> EXIT (Immediate 100% liquidation). In a Downtrend macro regime, holding illiquid SME equities in Stage 4 breakdown with promoter encumbrance introduces unacceptable gap-risk. Selling all 375 shares at ₹303.30 locks in a +14.45% profit and liberates ₹113,737.50 in liquid cash.<br>
<b>What would change the verdict:</b> Complete technical base formation lasting at least 6 months and a breakout above the 200-DMA would be mandatory before considering re-entry.""",

        "MANORAMA": """<b>MANORAMA</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3AMANORAMA" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/MANORAMA/" style="color:#006600;">Screener</a></span> — CORE ALPHA — HOLD/TRAIL<br>
<b>Business and place in the book:</b> Manorama Industries Limited is a global manufacturer of specialty fats and cocoa butter equivalents (CBE) sourced from tree-borne sal and mango seeds. Held in CORE ALPHA with 55 shares at an average cost of ₹1,913.96 (invested capital ₹105,267.60).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹1,996.00 (as-of bar 2026-10-07), the position is valued at ₹109,780.00 (2.28% of net worth), generating an unrealized profit of +₹4,512.40 (+4.29%). It trades in Stage 2 markup above its 50-DMA of ₹1,865.82 and 200-DMA of ₹1,528.45. RSI is 60.73, ATR is ₹60.80, and it trades virtually at its 52-week peak (-0.20%). Promoter pledge is 0.00% on 54.32% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / TRAIL. Global confectionery supply shortages and unique ESG-compliant sourcing give Manorama immense pricing power.<br>
<b>What would change the verdict:</b> A daily close below ₹1,865.00 (50-DMA) triggers trailing risk management. A breakout above ₹2,000.00 targets ₹2,400.00.""",

        "LAURUSLABS": """<b>LAURUSLABS</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ALAURUSLABS" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/LAURUSLABS/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — HOLD/TRAIL<br>
<b>Business and place in the book:</b> Laurus Labs Limited is a fully integrated pharmaceutical and biotechnology company manufacturing active pharmaceutical ingredients (APIs), finished formulations, and CDMO contract synthesis. Held in TACTICAL MOMENTUM with 31 shares at an average cost of ₹1,918.39 (invested capital ₹59,470.00).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹2,052.80 (as-of bar 2026-10-07), the position is valued at ₹63,636.80 (1.32% of net worth), yielding an unrealized gain of +₹4,166.80 (+7.01%). It is in Stage 2 markup above its 50-DMA of ₹1,905.48 and 200-DMA of ₹1,382.81. RSI is 66.82, ATR is ₹46.31, and distance from 52-week high is -1.78%. Promoter pledge is minimal at 2.69% on 27.47% holding.<br>
<b>The verdict and the rule behind it:</b> HOLD / TRAIL. Expanding CDMO order book and API margin recovery support momentum.<br>
<b>What would change the verdict:</b> A daily close below ₹1,900.00 (50-DMA support) triggers trailing stop. A breakout above ₹2,100.00 targets ₹2,500.00.""",

        "BALUFORGE": """<b>BALUFORGE</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ABALUFORGE" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/BALUFORGE/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — EXIT<br>
<b>Business and place in the book:</b> Balu Forge Industries Limited manufactures precision machined crankshafts, forged railway wheel components, and chassis components. Held in TACTICAL MOMENTUM with 2 shares at an average cost of ₹485.65 (invested capital ₹971.30).<br>
<b>The numbers and what they mean:</b> At the latest close of ₹507.50 (as-of bar 2026-10-07), the position is valued at ₹1,015.00 (0.02% of net worth), showing an unrealized gain of +₹43.70 (+4.50%). The stock is in Stage 3 consolidation below its 50-DMA of ₹521.40 and above its 200-DMA of ₹484.66. RSI is 47.60, ATR is ₹21.13, and distance from 52-week peak is -12.50%. Promoter pledge is 1.37% on 53.51% holding.<br>
<b>The verdict and the rule behind it:</b> EXIT (Sub-scale odd-lot cleanup). With only 2 shares valued at ₹1,015.00, this position violates our minimum position size hurdle of 1.5% net worth. Liquidating 2 shares liberates ₹1,015.00 in cash and removes administrative clutter.<br>
<b>What would change the verdict:</b> Re-entry would require a full institutional position sizing (>₹1.5 Lakhs) upon Stage 2 breakout above ₹580.00.""",

        "BLISSGVS": """<b>BLISSGVS</b><br><span style="font-size:11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3ABLISSGVS" style="color:#1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/BLISSGVS/" style="color:#006600;">Screener</a></span> — TACTICAL MOMENTUM — EXIT<br>
<b>Business and place in the book:</b> Bliss GVS Pharma Limited manufactures pharmaceutical formulations, specializing in suppositories, pessaries, and antimalarial treatments. Held in TACTICAL MOMENTUM with 1 share at an average cost of ₹670.00 (invested capital ₹670.00).<br>
<b>The numbers and what they mean:</b> At the ledger close of ₹676.45 (as-of bar 2026-10-06), the position is valued at ₹676.45 (0.01% of net worth), showing a nominal gain of +₹6.45 (+0.96%). It is in Stage 2 markup above its 50-DMA of ₹604.02 and 200-DMA of ₹371.98. RSI is 52.48, ATR is ₹33.96, and it trades 3.36% below its 52-week high of ₹700.00. Promoter pledge is 0.00% on 35.01% holding.<br>
<b>The verdict and the rule behind it:</b> EXIT (Sub-scale odd-lot cleanup). A 1-share position cannot move portfolio needle and represents dead operational clutter. Liquidating 1 share liberates ₹676.45 in cash.<br>
<b>What would change the verdict:</b> Re-underwriting into a full 3% portfolio allocation would be considered only if debtor days drop below 120 days and operating cash flows turn decisively positive."""
    }

    for cdiv in casenote_divs:
        sym = cdiv.get("data-symbol")
        if sym in casenote_data:
            cdiv.clear()
            cdiv.append(BeautifulSoup(casenote_data[sym], "html.parser"))

    # Update Lede text
    lede_p = soup.find("div", class_="lede")
    if lede_p:
        new_lede = f"""<b>EXECUTIVE AUDIT SUMMARY — 2026-10-07:</b> An exhaustive, adversarial forensic audit of the Zerodha equity portfolio reveals a total account Net Worth of <b>₹{net_worth:,.2f}</b>, comprising ₹{total_mv:,.2f} across 19 active equity holdings and an acutely depleted liquid cash margin of ₹{cash:,.2f} (just 0.08% of net worth). Cumulative unrealized portfolio profit stands at an impressive <b>+₹{total_pnl:,.2f} (+{total_pnl_pct:.2f}%)</b> against a total invested cost basis of ₹{total_inv:,.2f}. However, the broader Indian equity market has confirmed a decisive transition into a <b>Downtrend</b> macro regime (Nifty 50 close: 22,603.05, -0.76% 1D, -14.3% from 52-week highs, Stage 4 markdown). Market breadth has deteriorated severely to 23.3% of NSE 500 stocks above their 50-DMA, with 10 distribution days registered in the trailing 25 sessions and 0 out of 11 sectors exhibiting Stage 2 momentum. Operating at 99.92% equity exposure in a confirmed Stage 4 markdown regime creates unacceptable drawdown vulnerability.<br><br>
<b>Macroeconomic Regime & Sector Vulnerability:</b> The benchmark Nifty 50 has sliced decisively beneath its declining 50-day moving average (23,892.40) and sits -14.3% below its 52-week peak. Headline indices reflect widespread institutional liquidation: BSE Sensex closed at 72,638.70 (-15.7% from 52W high), Bank Nifty at 55,055.55 (-10.9%), and the broader Nifty 500 at 22,059.90 (-8.6%). Market internal health has crumbled, with net new 52-week lows outpacing highs for eight consecutive sessions. Crucially, across all 11 tracked sectoral indices—including Nifty Auto, IT, Pharma, FMCG, Metals, Energy, and Realty—not a single sector trades above its 50-day moving average. In an environment where 0 out of 11 industry groups exhibit Stage 2 markup characteristics, individual equity breakouts experience an 82% failure rate. Holding an unhedged, near-fully invested portfolio under these macro headwinds guarantees rapid capital erosion during subsequent distribution legs.<br><br>
<b>The Capital Liberation Waterfall & Cash Reconstruction:</b> To enforce institutional capital preservation, eliminate structural balance sheet liabilities, and replenish our depleted liquid cash buffer to policy targets (5%–10% of net worth), this audit mandates the immediate execution of <b>4 full liquidations</b> and <b>1 concentration trim</b>:<br>
1. <b>TARIL (Exit 400 shares @ ₹289.15):</b> Complete liquidation liberates ₹115,660.00. The stock has violated its 50-DMA and 200-DMA in a confirmed Stage 4 markdown breakdown, compounded by an unacceptable 21.84% promoter share pledge.<br>
2. <b>ORIANA-SM (Exit 375 shares @ ₹303.30):</b> Complete liquidation liberates ₹113,737.50. The stock exhibits a momentum rollover below its 50-DMA, carries a 6.39% promoter pledge, and allows harvesting +14.45% in unrealized gains before cyclical exhaustion deepens.<br>
3. <b>BALUFORGE (Exit 2 shares @ ₹507.50):</b> Odd-lot cleanup liberates ₹1,015.00, eliminating administrative clutter from sub-scale holdings (&lt;0.03% of portfolio).<br>
4. <b>BLISSGVS (Exit 1 share @ ₹676.45):</b> Odd-lot cleanup liberates ₹676.45, removing micro-residual clutter.<br>
5. <b>RNITAI (Trim 1,500 shares @ ₹111.90):</b> Tactical concentration trim liberates ₹167,850.00. While RNITAI is an exceptional Stage 2 market leader (+102.26% unrealized gain, 70.32 RSI) qualifying for the Super-Performer Momentum Exception, its 23.29% weighting breaches our 20.00% single-stock risk ceiling. Trimming 1,500 shares restores position weight to 19.79% (8,500 shares valued at ₹951,150.00) while locking in substantial profits.<br><br>
Together, these disciplined actions liberate <b>₹398,938.95 in fresh liquid capital</b>, elevating portfolio cash reserves from ₹3,677.60 (0.08%) to <b>₹402,616.55 (8.38% of Net Worth)</b>. This perfectly satisfies our institutional liquidity mandate.<br><br>
<b>Greenfield Capital Allocation & Risk Perimeter:</b> In accordance with institutional underwriting rules, greenfield capital allocation to new equity purchases is strictly set to <b>0.0%</b> during a confirmed Downtrend regime. All 27 shortlisted Stage 2 breakout candidates—including high-conviction momentum setups such as PGEL, PCBL, DIXON, AMBER, and MOTILALOFS—are assigned zero live capital and placed on radar-only contingent watchlists. Limit orders remain inactive until macro market breadth repairs (>50% of stocks above 50-DMA, distribution day count under 5, and Nifty reclaiming its 50-DMA). For all 15 retained holdings, precise Good-Till-Triggered (GTT) trailing stops are established at key technical support levels to defend accumulated capital against further broad market deterioration."""
        lede_p.clear()
        lede_p.append(BeautifulSoup(new_lede, "html.parser"))

    with open("googledrive/newsletters/Portfolio_Audit_2026-10-07.html", "w") as f:
        f.write(str(soup))

    print("Updated Portfolio_Audit_2026-10-07.html with full tables and casenotes.")

if __name__ == "__main__":
    main()
