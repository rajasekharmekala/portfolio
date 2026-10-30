#!/usr/bin/env python3
"""Build and assemble Watchlist to Shortlist summary reports for IN and US."""

import os
import subprocess
from pathlib import Path

# ==========================================
# IN Watchlist to Shortlist Body
# ==========================================
in_body = """
<h1>India Watchlist to Shortlist &amp; Stage 2 Rationalization (29 Oct 2026)</h1>
<div class="exec-theme-box">
  <div class="exec-theme-title">Executive Summary — Stage 2 Momentum & Watchlist Rationalization</div>
  <p class="exec-theme-p">
    Under our re-architected portfolio philosophy, we eliminate rigid numerical formula assertions in favor of Stan Weinstein Stage 2 trend confirmation, TheWrap relative strength momentum, and No-FOMO pullback entry timing. During the October 29 session, we completed a rigorous pruning pass across <code>data/watchlist/IN.json</code>, removing 35 names trapped in confirmed Stage 4 markdowns or structural deterioration to restore a focused, high-conviction watchlist of 110 active names.
  </p>
  <p class="exec-theme-p">
    Our primary breakout candidate is <strong>Firstsource Solutions Limited (NSE: FSL)</strong>, an RP-Sanjiv Goenka Group BPM and AI-enabled operations leader entering Week 1 of TheWrap's Stage 2 trend scanner at ₹306.45. Rather than chasing a vertical rally (+19.71% in one month, extended +10.56% above its 10-week average), we assign an <strong>ACCUMULATE_ON_DIP</strong> posture with staged limit orders inside the ₹273.03 to ₹288.73 support band.
  </p>
</div>

<section class="chapter" id="ch-1">
  <h2>1. Watchlist Pruning Audit — Pruning Stage 4 Traps</h2>
  <p>
    A bloated watchlist dilutes attention and tempts capital into falling knives. In Stan Weinstein's market structure framework, Stage 4 represents the markdown phase where institutions distribute shares and price trades beneath falling 30-week and 200-day moving averages.
  </p>
  <div class="table-wrap" tabindex="0">
    <table class="wikitable">
      <caption>Summary of Watchlist Rationalization & Pruning Pass for India (NSE/BSE)</caption>
      <thead>
        <tr>
          <th>Category / Metric</th>
          <th>Count / Value</th>
          <th>Strategic Rationale & Institutional Rule</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Starting Watchlist Universe</td>
          <td>145 symbols</td>
          <td>Historical watchlist containing accumulated Stage 4 drift and low-momentum candidates.</td>
        </tr>
        <tr>
          <td>Pruned Broken / Stage 4 Names</td>
          <td>35 symbols</td>
          <td>Pruned names exhibiting declining relative strength, broken moving averages, or governance red flags.</td>
        </tr>
        <tr>
          <td>Active Focused Watchlist</td>
          <td>110 symbols</td>
          <td>Curated universe of Stage 1 consolidations, Stage 2 breakouts, and quality compounders.</td>
        </tr>
        <tr>
          <td>Primary Stage 2 Focus Seed</td>
          <td>FSL (Firstsource Solutions)</td>
          <td>Confirmed Week 1 Stage 2 breakout on TheWrap India scanner (+17.48% relative strength).</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

<section class="chapter" id="ch-2">
  <h2>2. Candidate Evaluation & Deep Monograph Underwriting</h2>
  <p>
    We underwrite Firstsource Solutions Limited (NSE: FSL) through our deep business monograph framework. We analyze day-to-day operations across its four core verticals (Banking & Financial Services, Healthcare Provider/Payer RCM, Communications/Media/Tech, and Ascensos Retail CX), audit CEO Ritesh Idnani's guidance delivery, and verify technical support zones on TradingView.
  </p>
  <div class="table-wrap" tabindex="0">
    <table class="wikitable">
      <caption>Stage 2 Candidate Evaluation & No-FOMO Action Matrix for India</caption>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Company Name</th>
          <th>Weinstein Stage</th>
          <th>CMP (₹)</th>
          <th>Entry Zone (₹)</th>
          <th>Stop Loss (₹)</th>
          <th>Action Verdict</th>
          <th>Deep Research Monograph</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>FSL</strong></td>
          <td>Firstsource Solutions Limited</td>
          <td>Stage 2 (Week 1)</td>
          <td>₹306.45</td>
          <td>₹273.03 – ₹288.73</td>
          <td>₹253.79</td>
          <td><span class="badge badge-accent">ACCUMULATE_ON_DIP</span></td>
          <td><a href="../blogs/IN/FSL_dossier.html">Read 8-Chapter Book Monograph (114 KB)</a></td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

<section class="chapter" id="ch-3">
  <h2>3. No-FOMO Execution & Staged Limit Order Plan</h2>
  <p>
    FSL closed at ₹306.45, sitting +10.56% above its 10-week EMA (₹277.19) and +12.93% above its 50-day SMA (₹271.36). Our No-FOMO rule in <code>.agents/config/scoring.json</code> caps immediate market orders at +10.0% extension. 
  </p>
  <p>
    Therefore, we execute via two limit tranches:
  </p>
  <ul>
    <li><strong>Tranche 1 (50% size, ~3.1% net worth):</strong> Resting limit order at ₹284.50 to ₹288.73, targeting the 20-day EMA (₹284.46) and Classic R1 pivot (₹282.98).</li>
    <li><strong>Tranche 2 (50% size, ~3.1% net worth):</strong> Resting limit order at ₹273.03 to ₹278.00, accumulating shares near the rising 10-week EMA (₹277.19) and 50-day SMA (₹271.36).</li>
    <li><strong>Structural Invalidation Stop:</strong> Hard stop on a daily close below ₹253.79, anchored beneath the rising 30-week SMA (₹259.54) and 200-day SMA (₹260.19) minus 0.5x ATR.</li>
  </ul>
</section>
"""

# ==========================================
# US Watchlist to Shortlist Body
# ==========================================
us_body = """
<h1>US Watchlist to Shortlist &amp; Stage 2 Rationalization (29 Oct 2026)</h1>
<div class="exec-theme-box">
  <div class="exec-theme-title">Executive Summary — Stage 2 Momentum & Watchlist Rationalization</div>
  <p class="exec-theme-p">
    Our redesigned US research workflow prioritizes Stan Weinstein Stage 2 momentum, TheWrap industry relative strength, and strict No-FOMO entry execution. During the October 29 session, we completed a forensic rationalization of <code>data/watchlist/US.json</code>, removing 9 names that broke down into Stage 4 markdown to leave a streamlined universe of 43 high-momentum candidates.
  </p>
  <p class="exec-theme-p">
    Our primary Stage 2 focus candidate is <strong>AvePoint, Inc. (NASDAQ: AVPT)</strong>, a cloud data security and governance leader for Microsoft 365 and enterprise SaaS environments. While AvePoint is a fundamental category winner growing annual recurring revenue at 27% YoY, the stock has surged to $17.35, extending +18.03% above its 10-week moving average ahead of its November 5 earnings report. We assign a <strong>WAIT_FOR_SUPPORT</strong> posture, targeting a limit accumulation zone of $14.48 to $15.73.
  </p>
</div>

<section class="chapter" id="ch-1">
  <h2>1. Watchlist Rationalization — Eliminating Stage 4 Breakdowns</h2>
  <p>
    Protecting capital begins with eliminating deteriorating charts. When a stock breaks below its 30-week and 200-day moving averages, institutional distribution overwhelms buying power. We pruned 9 broken names from our US tracking list to focus research bandwidth on leaders.
  </p>
  <div class="table-wrap" tabindex="0">
    <table class="wikitable">
      <caption>Summary of Watchlist Rationalization & Pruning Pass for United States (NYSE/NASDAQ)</caption>
      <thead>
        <tr>
          <th>Category / Metric</th>
          <th>Count / Value</th>
          <th>Strategic Rationale & Institutional Rule</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Starting Watchlist Universe</td>
          <td>52 symbols</td>
          <td>Legacy tracking universe including names in Stage 3 distribution and Stage 4 markdown.</td>
        </tr>
        <tr>
          <td>Pruned Broken / Stage 4 Names</td>
          <td>9 symbols</td>
          <td>Pruned names failing long-term moving average tests or experiencing negative earnings revisions.</td>
        </tr>
        <tr>
          <td>Active Focused Watchlist</td>
          <td>43 symbols</td>
          <td>Curated list of high-growth cloud, semiconductor, and industrial leaders in Stage 1 bases and Stage 2 markups.</td>
        </tr>
        <tr>
          <td>Primary Stage 2 Focus Seed</td>
          <td>AVPT (AvePoint, Inc.)</td>
          <td>TheWrap US Software leader trading above all rising weekly and daily moving averages.</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

<section class="chapter" id="ch-2">
  <h2>2. Candidate Evaluation & Deep Monograph Underwriting</h2>
  <p>
    We underwrite AvePoint, Inc. (NASDAQ: AVPT) through our comprehensive 8-chapter monograph format. We examine its Confidence Platform architecture, SaaS subscription unit economics, enterprise customer adoption driven by Microsoft Copilot data governance, and CEO Dr. Tianyi Jiang's flawless guidance delivery.
  </p>
  <div class="table-wrap" tabindex="0">
    <table class="wikitable">
      <caption>Stage 2 Candidate Evaluation & No-FOMO Action Matrix for United States</caption>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Company Name</th>
          <th>Weinstein Stage</th>
          <th>CMP ($)</th>
          <th>Entry Zone ($)</th>
          <th>Stop Loss ($)</th>
          <th>Action Verdict</th>
          <th>Deep Research Monograph</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>AVPT</strong></td>
          <td>AvePoint, Inc.</td>
          <td>Stage 2 Markup</td>
          <td>$17.35</td>
          <td>$14.48 – $15.73</td>
          <td>$12.02</td>
          <td><span class="badge badge-accent">WAIT_FOR_SUPPORT</span></td>
          <td><a href="../blogs/US/AVPT_dossier.html">Read 8-Chapter Book Monograph (63 KB)</a></td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

<section class="chapter" id="ch-3">
  <h2>3. No-FOMO Execution & Post-Earnings Accumulation Plan</h2>
  <p>
    At $17.35, AvePoint sits +18.03% above its 10-week EMA ($14.70) and +22.70% above its 50-day SMA ($14.14), with daily RSI at 73.86. Buying extended software stocks five trading days before quarterly earnings carries high drawdown risk.
  </p>
  <p>
    Our execution plan enforces patient discipline:
  </p>
  <ul>
    <li><strong>Support Accumulation Zone:</strong> Staged limit buy orders in the $14.48 to $15.73 band, anchored between the rising 20-day EMA ($15.25) and 50-day SMA ($14.14).</li>
    <li><strong>Post-Earnings Timing Trigger:</strong> Allow the November 5, 2026 Q3 earnings release to digest short-term speculative positioning before executing limit fills.</li>
    <li><strong>Structural Invalidation Stop:</strong> Hard stop on a daily close below $12.02, anchored beneath the rising 200-day SMA ($11.85) and 30-week SMA ($12.32).</li>
    <li><strong>12-Month Targets:</strong> Base target of $21.50 (+36% from support zone top) and bull target of $26.00 (+65%).</li>
  </ul>
</section>
"""

Path("/tmp/in_w2s_body.html").write_text(in_body, encoding="utf-8")
Path("/tmp/us_w2s_body.html").write_text(us_body, encoding="utf-8")

# Assemble IN Watchlist to Shortlist Report
cmd_in = [
    ".venv/bin/python", "scripts/assemble_report.py",
    "--body", "/tmp/in_w2s_body.html",
    "--out", "docs/reports/IN_Watchlist_to_Shortlist.html",
    "--market", "IN",
    "--kind", "report",
    "--workflow", "Watchlist to Shortlist",
    "--as-of", "2026-10-29",
]
print("Running:", " ".join(cmd_in))
subprocess.check_call(cmd_in)

# Assemble US Watchlist to Shortlist Report
cmd_us = [
    ".venv/bin/python", "scripts/assemble_report.py",
    "--body", "/tmp/us_w2s_body.html",
    "--out", "docs/reports/US_Watchlist_to_Shortlist.html",
    "--market", "US",
    "--kind", "report",
    "--workflow", "Watchlist to Shortlist",
    "--as-of", "2026-10-29",
]
print("Running:", " ".join(cmd_us))
subprocess.check_call(cmd_us)

print("Successfully assembled both IN and US Watchlist to Shortlist reports!")

