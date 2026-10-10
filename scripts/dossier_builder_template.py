"""
Autonomous Dossier Generator for Underwriting Batch:
1. OPTIEMUS (Optiemus Infracom Limited)
2. CARBORUNIV (Carborundum Universal Limited)
3. WENDT (Wendt (India) Limited)
4. KRBL (KRBL Limited)
"""

import os
import sys
from assemble_report import build

def build_dossier_html(
    symbol, company_name, bse_code, isin, macro_sector, fine_subsector, founded, hq,
    executives, business_overview, ttm_sales, opm, ttm_pat, roce, roe, de, cfo_pat,
    sales_3y_cagr, pat_3y_cagr, strategy_bucket, action_verdict, verdict_color,
    cmp, low_52w, high_52w, entry_low, entry_high, stop_loss, target_base, target_bull,
    asymmetry, weinstein_stage, rsi_14, rs_rating, entry_posture, atr_14, dist_support_atr,
    summary_lead, history_narrative, operations_narrative, sector_dynamics_narrative,
    financial_audit_narrative, pl_table_rows, bs_table_rows, cf_table_rows,
    layer1_rows, layer2_rows, layer3_narrative, peer_table_rows, peer_analysis_narrative,
    technical_narrative, fatal_flaws_rows, fatal_flaws_narrative, capital_allocation_narrative,
    monitoring_rows, citations
):
    # CSS template matching Wikipedia Institutional Design
    css = """
:root {
  --text-primary: #1f2937;
  --text-secondary: #4b5563;
  --text-muted: #6b7280;
  --bg-main: #ffffff;
  --bg-surface: #f9fafb;
  --bg-highlight: #f3f4f6;
  --border-color: #d1d5db;
  --border-subtle: #e5e7eb;
  --brand-blue: #1d4ed8;
  --brand-blue-light: #eff6ff;
  --brand-green: #15803d;
  --brand-green-light: #f0fdf4;
  --brand-amber: #b45309;
  --brand-amber-light: #fffbeb;
  --brand-red: #b91c1c;
  --brand-red-light: #fef2f2;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-serif: 'Newsreader', Georgia, 'Times New Roman', serif;
  --font-mono: 'JetBrains Mono', monospace;
}

body {
  font-family: var(--font-sans);
  color: var(--text-primary);
  background-color: var(--bg-main);
  line-height: 1.72;
  font-size: 15px;
  letter-spacing: -0.011em;
  margin: 0;
  padding: 32px 40px;
  max-width: 1240px;
  margin-left: auto;
  margin-right: auto;
}

.dossier-nav-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: var(--bg-main);
  border-bottom: 1px solid var(--border-color);
  padding: 10px 0;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.88em;
}

.dossier-nav-header a {
  color: var(--brand-blue);
  text-decoration: none;
}

.dossier-nav-header a:hover {
  text-decoration: underline;
}

.nav-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

h1.firstHeading {
  font-family: var(--font-serif);
  font-size: 2.35em;
  font-weight: 600;
  line-height: 1.2;
  margin-top: 0;
  margin-bottom: 0.2em;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
  color: #111827;
}

.siteSub {
  font-size: 0.88em;
  color: var(--text-muted);
  margin-bottom: 18px;
  font-style: italic;
}

.decision-banner {
  margin: 18px 0 24px 0;
  padding: 16px 20px;
  border-radius: 6px;
  border-left: 6px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--bg-surface);
}

.decision-banner.verdict-green {
  border-color: var(--brand-green);
  background-color: var(--brand-green-light);
}

.decision-banner.verdict-blue {
  border-color: var(--brand-blue);
  background-color: var(--brand-blue-light);
}

.decision-banner.verdict-amber {
  border-color: var(--brand-amber);
  background-color: var(--brand-amber-light);
}

.decision-banner.verdict-red {
  border-color: var(--brand-red);
  background-color: var(--brand-red-light);
}

.decision-banner h3 {
  margin: 0 0 4px 0;
  font-size: 1.15em;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.decision-banner p {
  margin: 0;
  font-size: 0.92em;
  color: var(--text-secondary);
}

.decision-stats {
  text-align: right;
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.clearfix::after {
  content: "";
  clear: both;
  display: table;
}

table.infobox {
  float: right;
  clear: right;
  margin: 0 0 1.2em 1.5em;
  width: 320px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-spacing: 0;
  font-size: 0.88em;
  line-height: 1.5;
  border-radius: 4px;
}

table.infobox caption {
  font-family: var(--font-serif);
  font-size: 1.35em;
  font-weight: 600;
  padding: 8px 12px;
  background-color: #f3f4f6;
  border-bottom: 2px solid #0b3d68;
  color: #111827;
}

table.infobox th.infobox-header {
  background-color: #eaecf0;
  text-align: left;
  padding: 6px 10px;
  font-weight: 700;
  font-size: 0.95em;
  color: #1f2937;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

table.infobox th {
  padding: 5px 8px;
  vertical-align: top;
  text-align: left;
  width: 42%;
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-subtle);
}

table.infobox td {
  padding: 5px 8px;
  vertical-align: top;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}

.toc {
  background-color: #f8f9fa;
  border: 1px solid var(--border-color);
  padding: 14px 18px;
  display: inline-block;
  min-width: 260px;
  margin: 16px 0 24px 0;
  border-radius: 4px;
}

.toc h2 {
  font-family: var(--font-sans);
  font-size: 1.05em;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 10px;
  text-align: center;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 6px;
}

.toc ul {
  list-style: none;
  padding-left: 0;
  margin: 0;
  font-size: 0.9em;
  line-height: 1.6;
}

.toc ul li {
  margin-bottom: 3px;
}

.toc a {
  color: var(--brand-blue);
  text-decoration: none;
}

.toc a:hover {
  text-decoration: underline;
}

.tocnumber {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.88em;
  margin-right: 6px;
}

h2 {
  font-family: var(--font-serif);
  font-size: 1.65em;
  font-weight: 600;
  margin-top: 1.8em;
  margin-bottom: 0.5em;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-color);
  color: #111827;
}

h3 {
  font-family: var(--font-sans);
  font-size: 1.25em;
  font-weight: 600;
  margin-top: 1.3em;
  margin-bottom: 0.4em;
  color: #1f2937;
}

h4 {
  font-family: var(--font-sans);
  font-size: 1.05em;
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0.3em;
  color: #374151;
}

p {
  margin-top: 0.5em;
  margin-bottom: 1em;
  text-align: justify;
}

table.wikitable {
  width: 100%;
  border-collapse: collapse;
  margin: 1.2em 0;
  font-size: 0.9em;
  background-color: var(--bg-main);
  border: 1px solid var(--border-color);
}

table.wikitable th {
  background-color: #eaecf0;
  color: #111827;
  font-weight: 600;
  text-align: left;
  padding: 7px 10px;
  border: 1px solid var(--border-color);
}

table.wikitable td {
  padding: 6px 10px;
  border: 1px solid var(--border-subtle);
  vertical-align: middle;
}

table.wikitable tr:nth-child(even) {
  background-color: #f9fafb;
}

table.wikitable tr:hover {
  background-color: #f3f4f6;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 0.82em;
  font-weight: 600;
  border-radius: 4px;
  font-family: var(--font-mono);
}

.badge-green { background-color: var(--brand-green-light); color: var(--brand-green); border: 1px solid var(--brand-green); }
.badge-blue { background-color: var(--brand-blue-light); color: var(--brand-blue); border: 1px solid var(--brand-blue); }
.badge-amber { background-color: var(--brand-amber-light); color: var(--brand-amber); border: 1px solid var(--brand-amber); }
.badge-red { background-color: var(--brand-red-light); color: var(--brand-red); border: 1px solid var(--brand-red); }

ol.reflist {
  font-size: 0.84em;
  line-height: 1.6;
  column-count: 2;
  column-gap: 28px;
  margin-top: 16px;
  padding-left: 24px;
}

ol.reflist li {
  margin-bottom: 8px;
  word-break: break-word;
}

ol.reflist a {
  color: var(--brand-blue);
  text-decoration: none;
}

ol.reflist a:hover {
  text-decoration: underline;
}

sup.reference {
  font-family: var(--font-mono);
  font-size: 0.75em;
  font-weight: 500;
  padding: 0 2px;
}

sup.reference a {
  color: var(--brand-blue);
  text-decoration: none;
}

sup.reference a:hover {
  text-decoration: underline;
}

.formula-box {
  background-color: #f8fafc;
  border: 1px solid #cbd5e1;
  border-left: 4px solid var(--brand-blue);
  padding: 12px 16px;
  margin: 14px 0;
  font-family: var(--font-mono);
  font-size: 0.88em;
  border-radius: 4px;
  line-height: 1.5;
}
"""

    # Banner color mapping
    banner_cls = f"verdict-{verdict_color}"

    # Calculate stop distance & upside percentages
    try:
        stop_pct = round(((cmp - stop_loss) / cmp) * 100, 1) if cmp > 0 else 0
        base_upside = round(((target_base - cmp) / cmp) * 100, 1) if cmp > 0 else 0
        bull_upside = round(((target_bull - cmp) / cmp) * 100, 1) if cmp > 0 else 0
    except Exception:
        stop_pct = 0
        base_upside = 0
        bull_upside = 0

    citations_html = "".join([
        f'<li id="cite_note-{idx+1}"><b>^{idx+1}</b> {c}</li>\n'
        for idx, c in enumerate(citations)
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name} ({symbol}) — Institutional Equity Research Dossier &amp; Underwriting Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>

<div class="dossier-nav-header">
  <div>
    <a href="../blogs/index.html">&larr; Return to Institutional Research Blog Index</a>
  </div>
  <div class="nav-controls">
    <span style="color: var(--text-muted); font-size: 0.9em;">Underwriting Cycle: <strong>Cycle 1</strong></span>
    <span class="badge badge-{'green' if 'PASS' in layer1_rows[0] else 'red'}">{strategy_bucket}</span>
  </div>
</div>

<h1 class="firstHeading">{company_name} (NSE: {symbol})</h1>
<div class="siteSub">From Wikipedia, the institutional equity encyclopedia &bull; Equity Underwriting Dossier &bull; {strategy_bucket} Mandate</div>

<div class="decision-banner {banner_cls}">
  <div>
    <h3 style="color: {'#15803d' if verdict_color=='green' else ('#1d4ed8' if verdict_color=='blue' else ('#b45309' if verdict_color=='amber' else '#b91c1c'))};">
      EXECUTIVE ACTION VERDICT: {action_verdict}
    </h3>
    <p>3-Layer Status: Layer 1 Hard Gate: <strong>{'PASS' if verdict_color in ['green', 'blue'] else 'FAIL'}</strong> | Layer 2 KPIs: <strong>{layer2_rows}</strong> | Layer 3 Posture: <strong>{entry_posture}</strong></p>
  </div>
  <div class="decision-stats">
    <div><strong>CMP:</strong> ₹{cmp:,.2f}</div>
    <div><strong>Asymmetry:</strong> {asymmetry}:1</div>
    <div><strong>Target:</strong> ₹{target_base:,.2f} (+{base_upside}%)</div>
  </div>
</div>

<div class="clearfix">

<!-- WIKIPEDIA FLOATED INFOBOX -->
<table class="infobox" role="presentation">
  <caption>{company_name}</caption>
  <tr>
    <td colspan="2" style="text-align: center; padding: 10px; background-color: #ffffff;">
      <div style="font-size: 1.4em; font-weight: 700; color: #0b3d68; font-family: var(--font-sans);">{symbol}</div>
      <div style="font-size: 0.85em; color: var(--text-muted); font-family: var(--font-mono);">{macro_sector} &bull; {fine_subsector}</div>
    </td>
  </tr>
  <tr><th colspan="2" class="infobox-header">Corporate Overview</th></tr>
  <tr><th>Company type</th><td>Public listed (NSE / BSE)</td></tr>
  <tr><th>Traded as</th><td>NSE: {symbol} &bull; BSE: {bse_code}<br>ISIN: {isin}</td></tr>
  <tr><th>Industry</th><td>{macro_sector}</td></tr>
  <tr><th>Sub-sector</th><td>{fine_subsector}</td></tr>
  <tr><th>Founded</th><td>{founded}</td></tr>
  <tr><th>Headquarters</th><td>{hq}</td></tr>
  <tr><th>Key leadership</th><td>{executives}</td></tr>
  <tr><th>Core products</th><td>{business_overview}</td></tr>

  <tr><th colspan="2" class="infobox-header">Latest Audited Financials (TTM / FY26)</th></tr>
  <tr><th>Revenue (TTM)</th><td>₹{ttm_sales:,.1f} Cr</td></tr>
  <tr><th>Operating Margin</th><td>{opm:.1f}%</td></tr>
  <tr><th>Net Profit (PAT)</th><td>₹{ttm_pat:,.1f} Cr</td></tr>
  <tr><th>ROCE / ROE</th><td><strong>{roce:.1f}%</strong> / {roe:.1f}%</td></tr>
  <tr><th>Debt-to-Equity</th><td>{de:.2f}x</td></tr>
  <tr><th>3Y CFO / PAT</th><td><strong>{cfo_pat:.2f}x</strong></td></tr>
  <tr><th>3Y Sales CAGR</th><td>{sales_3y_cagr:.1f}%</td></tr>
  <tr><th>3Y PAT CAGR</th><td>{pat_3y_cagr:.1f}%</td></tr>

  <tr><th colspan="2" class="infobox-header">Underwriting &amp; Valuation Snapshot</th></tr>
  <tr><th>Strategy Bucket</th><td>{strategy_bucket}</td></tr>
  <tr><th>Action Verdict</th><td><span class="badge badge-{verdict_color}">{action_verdict}</span></td></tr>
  <tr><th>Current Market Price</th><td>₹{cmp:,.2f}</td></tr>
  <tr><th>52-Week Range</th><td>₹{low_52w:,.2f} – ₹{high_52w:,.2f}</td></tr>
  <tr><th>Recommended Entry</th><td>₹{entry_low:,.2f} – ₹{entry_high:,.2f}</td></tr>
  <tr><th>Invalidation Stop</th><td>₹{stop_loss:,.2f} (-{stop_pct}%)</td></tr>
  <tr><th>Base Target (12–18M)</th><td>₹{target_base:,.2f} (+{base_upside}%)</td></tr>
  <tr><th>Bull Target (Blue-Sky)</th><td>₹{target_bull:,.2f} (+{bull_upside}%)</td></tr>
  <tr><th>Reward/Risk Asymmetry</th><td><strong>{asymmetry}:1</strong></td></tr>
  <tr><th>Weinstein Stage</th><td>Stage {weinstein_stage}</td></tr>
  <tr><th>RSI (14) / RS Rating</th><td>RSI: {rsi_14:.1f} &bull; RS: {rs_rating}/100</td></tr>
  <tr><th>Support Distance (ATR)</th><td>{dist_support_atr:.2f}x ATR (ATR: ₹{atr_14:.2f})</td></tr>
  <tr><th>Entry Posture</th><td><strong>{entry_posture}</strong></td></tr>
</table>

<!-- TABLE OF CONTENTS -->
<div class="toc">
  <h2>Contents</h2>
  <ul>
    <li><a href="#lead"><span class="tocnumber">0</span> Executive Summary &amp; Investment Pitch</a></li>
    <li><a href="#history"><span class="tocnumber">1</span> History &amp; Corporate Milestones</a></li>
    <li><a href="#operations"><span class="tocnumber">2</span> Operations, Business Segments &amp; Revenue Model</a></li>
    <li><a href="#sector-dynamics"><span class="tocnumber">3</span> Sector-Specific Operating Dynamics &amp; Competitive Moats</a></li>
    <li><a href="#financial-audit"><span class="tocnumber">4</span> Financial Performance &amp; Forensic Accounting Audit</a></li>
    <li><a href="#underwriting-framework"><span class="tocnumber">5</span> The 3-Layer Underwriting Framework &amp; Scorecard</a></li>
    <li><a href="#peer-matrix"><span class="tocnumber">6</span> Industry Landscape &amp; Peer Benchmarking Matrix</a></li>
    <li><a href="#technical-trade"><span class="tocnumber">7</span> Technical Posture, Moving Averages &amp; Execution Architecture</a></li>
    <li><a href="#fatal-flaws"><span class="tocnumber">8</span> Adversarial Red-Team: Fatal Flaws &amp; Invalidation Triggers</a></li>
    <li><a href="#capital-allocation"><span class="tocnumber">9</span> Portfolio Allocation &amp; Displacement Guidance</a></li>
    <li><a href="#thesis-trackers"><span class="tocnumber">10</span> Key Quarterly Monitoring Indicators</a></li>
    <li><a href="#references"><span class="tocnumber">11</span> References &amp; Regulatory Filings</a></li>
  </ul>
</div>

<!-- SECTION 0: EXECUTIVE SUMMARY -->
<h2 id="lead">Executive Summary &amp; Investment Pitch</h2>
{summary_lead}

<!-- SECTION 1: HISTORY -->
<h2 id="history">1. History &amp; Corporate Milestones</h2>
{history_narrative}

<!-- SECTION 2: OPERATIONS -->
<h2 id="operations">2. Operations, Business Segments &amp; Revenue Model</h2>
{operations_narrative}

<!-- SECTION 3: SECTOR DYNAMICS -->
<h2 id="sector-dynamics">3. Sector-Specific Operating Dynamics &amp; Competitive Moats</h2>
{sector_dynamics_narrative}

<!-- SECTION 4: FINANCIAL AUDIT -->
<h2 id="financial-audit">4. Financial Performance &amp; Forensic Accounting Audit</h2>
{financial_audit_narrative}

<h3>10-Year Consolidated Financial Trend</h3>
<table class="wikitable">
  <thead>
    <tr>
      <th>Metric (₹ Cr)</th>
      <th>FY17</th>
      <th>FY18</th>
      <th>FY19</th>
      <th>FY20</th>
      <th>FY21</th>
      <th>FY22</th>
      <th>FY23</th>
      <th>FY24</th>
      <th>FY25</th>
      <th>FY26</th>
      <th>TTM</th>
    </tr>
  </thead>
  <tbody>
    {pl_table_rows}
  </tbody>
</table>

<h3>Balance Sheet &amp; Capital Structure Forensics</h3>
<table class="wikitable">
  <thead>
    <tr>
      <th>Balance Sheet Item (₹ Cr)</th>
      <th>FY20</th>
      <th>FY21</th>
      <th>FY22</th>
      <th>FY23</th>
      <th>FY24</th>
      <th>FY25</th>
      <th>FY26</th>
    </tr>
  </thead>
  <tbody>
    {bs_table_rows}
  </tbody>
</table>

<h3>Cash Flow Quality &amp; Capital Conversion (CFO vs PAT)</h3>
<table class="wikitable">
  <thead>
    <tr>
      <th>Cash Flow Metric (₹ Cr)</th>
      <th>FY20</th>
      <th>FY21</th>
      <th>FY22</th>
      <th>FY23</th>
      <th>FY24</th>
      <th>FY25</th>
      <th>FY26</th>
      <th>3Y Cumul.</th>
    </tr>
  </thead>
  <tbody>
    {cf_table_rows}
  </tbody>
</table>

<!-- SECTION 5: 3-LAYER UNDERWRITING FRAMEWORK -->
<h2 id="underwriting-framework">5. The 3-Layer Underwriting Framework &amp; Scorecard</h2>
<p>
  All institutional portfolio entries must pass through the deterministic 3-layer underwriting framework. A failure at Layer 1 immediately halts progression and routes the security to rejection.
</p>

<h3>Layer 1: Binary Hard Gating Floors (Mandatory Pass Hurdle)</h3>
<table class="wikitable">
  <thead>
    <tr>
      <th>Gate Metric</th>
      <th>Institutional Floor</th>
      <th>Company Actual Value</th>
      <th>Gate Outcome</th>
      <th>Forensic Evaluation &amp; Primary Evidence</th>
    </tr>
  </thead>
  <tbody>
    {layer1_rows}
  </tbody>
</table>

<h3>Layer 2: Company &amp; Sector-Specific KPIs (Operational Scorecard)</h3>
<p>
  Layer 2 evaluates 3 to 5 operational drivers that directly determine unit economics, cash generation, and competitive moats in this industry.
</p>
<table class="wikitable">
  <thead>
    <tr>
      <th>KPI Metric</th>
      <th>Target Hurdle</th>
      <th>Actual Performance</th>
      <th>Status</th>
      <th>Operational Verification &amp; Transcript Source</th>
    </tr>
  </thead>
  <tbody>
    {layer2_rows}
  </tbody>
</table>

<h3>Layer 3: Support-Aware Entry Posture &amp; Timing Gate</h3>
{layer3_narrative}

<!-- SECTION 6: PEER BENCHMARKING -->
<h2 id="peer-matrix">6. Industry Landscape &amp; Peer Benchmarking Matrix</h2>
{peer_analysis_narrative}

<table class="wikitable">
  <thead>
    <tr>
      <th>Company Name</th>
      <th>Symbol</th>
      <th>Market Cap (₹ Cr)</th>
      <th>CMP (₹)</th>
      <th>P/E (TTM)</th>
      <th>ROCE %</th>
      <th>OPM %</th>
      <th>D/E (x)</th>
      <th>3Y Sales CAGR</th>
      <th>Stage &amp; Posture</th>
      <th>Relative Underwriting Verdict</th>
    </tr>
  </thead>
  <tbody>
    {peer_table_rows}
  </tbody>
</table>

<!-- SECTION 7: TECHNICAL POSTURE -->
<h2 id="technical-trade">7. Technical Posture, Moving Averages &amp; Execution Architecture</h2>
{technical_narrative}

<div class="formula-box">
  <strong>MATHEMATICAL ASYMMETRY RATIO DERIVATION:</strong><br>
  • Execution Entry Price: ₹{cmp:,.2f} (Recommended Zone: ₹{entry_low:,.2f} – ₹{entry_high:,.2f})<br>
  • Structural Invalidation Stop Loss: ₹{stop_loss:,.2f} (Downside Risk: ₹{cmp - stop_loss:,.2f} or -{stop_pct}%)<br>
  • 12–18 Month Fundamental Base Target: ₹{target_base:,.2f} (Upside Reward: ₹{target_base - cmp:,.2f} or +{base_upside}%)<br>
  • Asymmetry Ratio Formula: (Target Base - CMP) / (CMP - Stop Loss) = (₹{target_base - cmp:,.2f}) / (₹{cmp - stop_loss:,.2f}) = <strong>{asymmetry}:1</strong>
</div>

<!-- SECTION 8: FATAL FLAWS & RED-TEAM -->
<h2 id="fatal-flaws">8. Adversarial Red-Team: Fatal Flaws &amp; Invalidation Triggers</h2>
{fatal_flaws_narrative}

<table class="wikitable">
  <thead>
    <tr>
      <th>Risk Category</th>
      <th>Fatal Flaw Scenario</th>
      <th>Probability / Impact</th>
      <th>Monitoring Detection Trigger</th>
      <th>Structural Invalidation Action</th>
    </tr>
  </thead>
  <tbody>
    {fatal_flaws_rows}
  </tbody>
</table>

<!-- SECTION 9: CAPITAL ALLOCATION -->
<h2 id="capital-allocation">9. Portfolio Allocation &amp; Displacement Guidance</h2>
{capital_allocation_narrative}

<!-- SECTION 10: MONITORING INDICATORS -->
<h2 id="thesis-trackers">10. Key Quarterly Monitoring Indicators</h2>
<p>
  The following quarterly operational checkpoints will be audited during subsequent earnings releases to confirm thesis progression:
</p>
<table class="wikitable">
  <thead>
    <tr>
      <th>Quarterly Metric</th>
      <th>Baseline (Current)</th>
      <th>Target / Bull Threshold</th>
      <th>Bearish Invalidation Level</th>
      <th>Reporting Source &amp; Frequency</th>
    </tr>
  </thead>
  <tbody>
    {monitoring_rows}
  </tbody>
</table>

<!-- SECTION 11: REFERENCES -->
<h2 id="references">11. References &amp; Regulatory Filings</h2>
<ol class="reflist">
  {citations_html}
</ol>

</div>

<footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border-color); font-size: 0.82em; color: var(--text-muted); text-align: center;">
  Institutional Equity Underwriting Dossier &bull; Generated strictly for Autonomous Portfolio Management &bull; Data verified against Screener.in, NSE/BSE filings &amp; Company Disclosures &bull; Zero Hallucination Standard Enforced
</footer>

</body>
</html>
"""
    return build(html, market="IN", kind="dossier", workflow="Company research")
