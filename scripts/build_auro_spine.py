#!/usr/bin/env python3
"""
Generator for Aurobindo Pharma Monograph spine.json.
Writes:
  work/AUROPHARMA/spine.json
"""
import json
from pathlib import Path

WORK_DIR = Path("work/AUROPHARMA")
WORK_DIR.mkdir(parents=True, exist_ok=True)

citations = [
    "InvestyWise / BSE Filing — Aurobindo Pharma Limited Q2 & H1 FY27 Financial Results & Press Release (4 Nov 2026): Consolidated revenue ₹10,263.29 Cr (+23.87% YoY), EBITDA ₹2,155.75 Cr (+28.46% YoY, 21.0% margin), PAT ₹1,123.84 Cr (+32.51% YoY) (<a href=\"https://www.investywise.com/aurobindo-pharma-reports-strong-q2-fy27-financial-results/\">investywise.com/aurobindo-pharma-reports-strong-q2-fy27-financial-results</a>).",
    "Univest / BSE Filing Summary — Aurobindo Pharma Q2 FY27 Consolidated Results Breakdown (4 Nov 2026): Revenue ₹10,263.29 Cr, PAT ₹1,123.84 Cr, Operating Profit ₹2,155.75 Cr (<a href=\"https://univest.in/blogs/aurobindo-pharma-q2-results-fy27-pat-1124-crore\">univest.in/blogs/aurobindo-pharma-q2-results-fy27-pat-1124-crore</a>).",
    "StockAnalysis — Aurobindo Pharma Limited (NSE: AUROPHARMA) Q1 FY27 Full Earnings Call Transcript (6 Aug 2026): Management Q&A with CFO S. Subramanian, USA CEO Swami Iyer, and Biologics CEO Dr. Satakarni Makkapati (<a href=\"https://stockanalysis.com/quote/nse/AUROPHARMA/transcripts/676648-q1-26-27/\">stockanalysis.com/quote/nse/AUROPHARMA/transcripts/676648-q1-26-27</a>).",
    "Aurobindo Pharma Official Corporate Portal — Q1 FY27 Earnings Conference Call Transcript PDF (6 Aug 2026) (<a href=\"https://www.aurobindo.com/api/uploads/conferencecalltranscripts/APL_ECT_Q1FY27_Final.pdf\">aurobindo.com/api/uploads/conferencecalltranscripts/APL_ECT_Q1FY27_Final.pdf</a>).",
    "Aurobindo Pharma Limited — Audited Consolidated Financial Results for Q4 FY26 and Full Year Ended 31 March 2026 (21 May 2026) (<a href=\"https://www.aurobindo.com/api/uploads/resultsannouncement/APL_PressRelease_Q4FY26.pdf\">aurobindo.com/api/uploads/resultsannouncement/APL_PressRelease_Q4FY26.pdf</a>).",
    "FinancialFilings — Aurobindo Pharma Limited Integrated Annual Report FY2025-26: Global Reach, Sustainable Health (<a href=\"https://financialfilings.com/filings/aurobindo-pharma-ltd/annual-report/2026/49887728/\">financialfilings.com/filings/aurobindo-pharma-ltd/annual-report/2026/49887728</a>).",
    "Aurobindo Pharma Official Corporate Portal — Results Announcements, Financial Statements & Investor Presentations Archive (<a href=\"https://www.aurobindo.com/investors/results-reports-presentations/results-announcements\">aurobindo.com/investors/results-reports-presentations/results-announcements</a>).",
    "Screener.in Consolidated 10-Year Financial Records, P&L, Balance Sheet, Cash Flow and Ratios for AUROPHARMA (7 Nov 2026) (<a href=\"https://www.screener.in/company/AUROPHARMA/consolidated/\">screener.in/company/AUROPHARMA/consolidated</a>).",
    "TradingView Verified Consumer-Tool Snapshot & Technical Indicators for NSE:AUROPHARMA as of 7 Nov 2026 (<a href=\"https://www.tradingview.com/chart/?symbol=NSE%3AAUROPHARMA\">tradingview.com/chart/?symbol=NSE%3AAUROPHARMA</a>).",
    "TradingView Technical Rating, Oscillators and Moving Averages for NSE:AUROPHARMA (<a href=\"https://www.tradingview.com/symbols/NSE-AUROPHARMA/technicals/\">tradingview.com/symbols/NSE-AUROPHARMA/technicals</a>).",
    "Dakshinam — Kakinada Becomes Entry Point to Penicillin-G: Lyfius Pharma PLI Commissioning (26 Oct 2026) (<a href=\"https://dakshinam.org/2026/10/26/kakinada-becomes-entry-point-to-penicillin-g/\">dakshinam.org/2026/10/26/kakinada-becomes-entry-point-to-penicillin-g</a>).",
    "Pharma Industry Report — Insight: Penicillin G - India's Return to Fermentation-Based Bulk Drugs and Import Substitution (13 Oct 2026) (<a href=\"https://pharma.industry-report.net/2026/10/13/insight-penicillin-g-kakinada-fermentation-bulk-drug-import-dependence/\">pharma.industry-report.net/2026/10/13/insight-penicillin-g-kakinada-fermentation-bulk-drug-import-dependence</a>).",
    "Aurobindo Pharma Corporate Announcement — Lyfius Pharma Kakinada SEZ PLI Commissioning Press Release (29 Oct 2024) (<a href=\"https://www.aurobindo.com/api/uploads/corporateannouncements/LtrToSEsLyfiusPressRelease29102024.pdf\">aurobindo.com/api/uploads/corporateannouncements/LtrToSEsLyfiusPressRelease29102024.pdf</a>).",
    "Multibagg AI — Aurobindo Pharma: USFDA OAI Classification for Eugia Pharma Specialities Unit-III (18 Feb 2026) (<a href=\"https://www.multibagg.ai/market-pulse/articles/aurobindo-usfda-oai-eugia-unitiii-cmqen7rhu1nbys60jojgfcsa3\">multibagg.ai/market-pulse/articles/aurobindo-usfda-oai-eugia-unitiii-cmqen7rhu1nbys60jojgfcsa3</a>).",
    "Medical Dialogues — Aurobindo Pharma Eugia Unit-III Receives OAI Status from USFDA: Inspection Details and Scope (<a href=\"https://medicaldialogues.in/news/industry/pharma/aurobindo-pharmas-eugia-unit-iii-receives-oai-status-from-usfda-172747\">medicaldialogues.in/news/industry/pharma/aurobindo-pharmas-eugia-unit-iii-receives-oai-status-from-usfda-172747</a>).",
    "CuraTeQ Biologics Corporate Portal — Expanding Access, Healing Lives: Pipeline Overview (<a href=\"https://www.curateqbio.com/\">curateqbio.com</a>).",
    "CuraTeQ Biologics Press Release — Aurobindo Pharma Targets 2029 as Turning Point for Its Biosimilars Business (<a href=\"https://www.curateqbio.com/press-release/aurobindo-pharma-targets-2029-as-turning-point-for-its-biosimilars-business\">curateqbio.com/press-release/aurobindo-pharma-targets-2029-as-turning-point-for-its-biosimilars-business</a>).",
    "InvestyWise — Aurobindo Pharma Subsidiary CuraTeQ Enters European Biosimilars Distribution Agreement with STADA Arzneimittel AG (25 Mar 2026) (<a href=\"https://www.investywise.com/aurobindo-pharma-enters-eu-biosimilars-distribution-deal/\">investywise.com/aurobindo-pharma-enters-eu-biosimilars-distribution-deal</a>).",
    "AlphaStreet — Aurobindo Pharma Limited (NSE: AUROPHARMA) Q1 2027 Earnings Call Management Commentary (<a href=\"https://alphastreet.com/india/aurobindo-pharma-limited-auropharma-q1-2027-earnings-call-transcript/\">alphastreet.com/india/aurobindo-pharma-limited-auropharma-q1-2027-earnings-call-transcript</a>).",
    "EarningsCalls.dev — Aurobindo Pharma Limited (AUROPHARMA) Management Q&A Transcript and Operational Breakdown (<a href=\"https://earningscalls.dev/transcripts/aurobindo-pharma-limited_auropharma_earnings_call_transcript_2025-08-05\">earningscalls.dev/transcripts/aurobindo-pharma-limited_auropharma_earnings_call_transcript_2025-08-05</a>).",
    "Aurobindo Pharma Corporate Portal — Annual Reports Archive and Financial Disclosures (<a href=\"https://www.aurobindo.com/investors/disclosures-under-regulation-46/financial-information/annual-reports\">aurobindo.com/investors/disclosures-under-regulation-46/financial-information/annual-reports</a>).",
    "Aurobindo Pharma Corporate Portal — Investor Meet Conference Call Transcripts Archive (<a href=\"https://www.aurobindo.com/investors/disclosures-under-regulation-46/investor-meet/conference-call-transcripts\">aurobindo.com/investors/disclosures-under-regulation-46/investor-meet/conference-call-transcripts</a>).",
    "StockAnalysis — Aurobindo Pharma Revenue Breakdown by Segment, Geography and Therapeutic Class (<a href=\"https://stockanalysis.com/quote/nse/AUROPHARMA/financials/metrics/\">stockanalysis.com/quote/nse/AUROPHARMA/financials/metrics</a>).",
    "ValueResearchOnline — Aurobindo Pharma Ltd Key Financial Ratios, Historical P/E Bands and Capital Efficiency (<a href=\"https://www.valueresearchonline.com/stocks/3034/aurobindo-pharma-ltd/\">valueresearchonline.com/stocks/3034/aurobindo-pharma-ltd</a>).",
    "Department of Pharmaceuticals, Ministry of Chemicals & Fertilizers, Government of India — Production Linked Incentive (PLI) Scheme for Bulk Drugs (<a href=\"https://pharmaceuticals.gov.in/schemes/production-linked-incentive-scheme-bulk-drugs\">pharmaceuticals.gov.in/schemes/production-linked-incentive-scheme-bulk-drugs</a>)."
]

spine = {
    "symbol": "AUROPHARMA",
    "market": "IN",
    "as_of": "2026-11-07",
    "title": "Aurobindo Pharma Ltd. (NSE: AUROPHARMA) — Deep Business Monograph & Stage 2 Dossier",
    "verdict": "IMMEDIATE_BUY",
    "archetype": "STAGE2_LEADER",
    "strategy_bucket": "TACTICAL_MOMENTUM",
    "conviction_tier": "TIER_1",
    "cmp": 1800.00,
    "entry_zone_low": 1675.00,
    "entry_zone_high": 1725.00,
    "stop_loss": 1655.00,
    "target_base": 2150.00,
    "target_bull": 2450.00,
    "target_bear": 1450.00,
    "asymmetry_ratio": 2.41,
    "weinstein_stage": "STAGE_2",
    "entry_posture": "BUY_BREAKOUT_AT_CMP_OR_SUPPORT",
    "report_status": "PUBLISHED — STAGE 2 MASTERCLASS MONOGRAPH",
    "book_masterclass_title": "The Fermentation Titan & The Specialty Pivot",
    "book_title": "The Fermentation Titan & The Specialty Pivot",
    "book_subtitle": "A step-by-step narrative walkthrough and audio companion to Aurobindo Pharma Limited: deconstructing the generic engine, global historical parallels, ten-year financial forensics, the Eugia specialty and CuraTeQ biosimilars ramp, both sides of the institutional debate, and the discipline of high-asymmetry execution.",
    "primer": "Aurobindo Pharma Limited manufactures oral generic formulations, sterile injectables, biosimilars, and active pharmaceutical ingredients across global markets [1][2][8]. Managing Director K. Nityananda Reddy and the leadership team have expanded consolidated trailing revenues past thirty-six thousand crore rupees with a net-cash balance sheet [1][2][8]. On 7 November 2026, the equity trades in a confirmed Stan Weinstein Stage 2 breakout at 1,800.00 rupees, within 0.28 percent of its 52-week high of 1,805.00 rupees [8][9]. Our house verdict is Immediate Buy at current market price or on pullbacks toward the 1,675.00 to 1,725.00 rupee support zone, backed by a structural stop at 1,555.00 rupees and a tactical stop at 1,655.00 rupees [8][9].",
    "citations": citations
}

(WORK_DIR / "spine.json").write_text(json.dumps(spine, indent=2), encoding="utf-8")
print("Successfully generated spine.json!")
