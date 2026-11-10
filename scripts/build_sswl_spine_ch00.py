#!/usr/bin/env python3
"""
Generator for Steel Strips Wheels Limited (SSWL) Monograph spine.json and Chapter 0 (Prologue).
Derived strictly from Chapter 9 synthesis under the Evidence-First Protocol.
"""
import json
from pathlib import Path

WORK_DIR = Path("work/SSWL")
CH_DIR = WORK_DIR / "chapters"
WORK_DIR.mkdir(parents=True, exist_ok=True)
CH_DIR.mkdir(parents=True, exist_ok=True)

citations = [
    "Steel Strips Wheels Limited Annual Report FY 2025-26: Consolidated Financial Statements, Directors' Report & Operational Highlights (31 March 2026): Net Sales ₹5,182.8 Cr (+17.0% YoY), Operating Profit ₹510 Cr, Net Profit ₹190.2 Cr (<a href=\"https://sswlindia.com/investor-relations/\">sswlindia.com/investor-relations/</a>).",
    "Steel Strips Wheels Limited Annual Report FY 2024-25: Audited Consolidated Accounts & Management Discussion (<a href=\"https://sswlindia.com/investor-relations/\">sswlindia.com/investor-relations/</a>).",
    "Steel Strips Wheels Limited Q2 FY27 Unaudited Financial Results & Press Release (November 2026): Quarterly Revenue ₹1,930 Cr (+61% YoY), EBITDA ₹236 Cr (12.2% margin), PAT ₹117 Cr (+225% YoY) (<a href=\"https://www.bseindia.com/corporates/ann.html\">bseindia.com/corporates/ann.html</a>).",
    "Steel Strips Wheels Limited Q1 FY27 & Q4 FY26 Earnings Conference Call Transcripts: Commentary by Managing Director Dheeraj Garg, Executive Director Mohan Joshi, and CFO Naveen Sorot on Alloy Wheel expansion and AMW Bhuj integration (<a href=\"https://trendlyne.com/equity/SSWL/\">trendlyne.com/equity/SSWL/</a>).",
    "National Company Law Tribunal (NCLT) Ahmedabad Bench Order: Approval of Resolution Plan for Acquisition of AMW Autocomponent Limited (AACL) by Steel Strips Wheels Limited for ₹138.15 Crore (October 2023 - 2024) (<a href=\"https://nclt.gov.in\">nclt.gov.in</a>).",
    "Screener.in Consolidated 10-Year Financial Records, P&L, Balance Sheet, Cash Flow, and Key Financial Ratios for SSWL as of 9 Nov 2026 (<a href=\"https://www.screener.in/company/SSWL/consolidated/\">screener.in/company/SSWL/consolidated</a>).",
    "TradingView Verified Consumer-Tool Snapshot & Technical Indicators for NSE:SSWL as of 9 Nov 2026: CMP ₹548.95, 50-DMA ₹417.08, 200-DMA ₹277.23, 30W SMA ₹316.87, 10W EMA ₹452.72, RSI 70.54 (Daily) / 90.26 (Weekly), Volume 420.6k (<a href=\"https://www.tradingview.com/chart/?symbol=NSE%3ASSWL\">tradingview.com/chart/?symbol=NSE%3ASSWL</a>).",
    "TradingView Technical Rating, Oscillators and Moving Averages for NSE:SSWL (9 Nov 2026) (<a href=\"https://www.tradingview.com/symbols/NSE-SSWL/technicals/\">tradingview.com/symbols/NSE-SSWL/technicals</a>).",
    "TheWrap Stage 2 Market Breadth, Relative Strength & Volume Analysis for SSWL (9 Nov 2026): In Stage 2 (18 weeks), RS 53.21, Stage 2 return +95.71%, LTASM - I (<a href=\"https://thewrap.in/data-tools/stage2\">thewrap.in/data-tools/stage2</a>).",
    "BSE/NSE Corporate Announcement: Commissioning and Ramp-up of 7.2 Million Unit Alloy Wheel Capacity and 0.6 Million Aluminum Steering Knuckle Facility at Bhuj, Gujarat (2025-2026) (<a href=\"https://www.bseindia.com/corporates/ann.html\">bseindia.com/corporates/ann.html</a>).",
    "Society of Indian Automobile Manufacturers (SIAM) Industry Sales and Production Data: Utility Vehicle (SUV) Penetration and Commercial Vehicle Production Statistics (FY24-FY27) (<a href=\"https://siam.in\">siam.in</a>).",
    "Ministry of Heavy Industries / Directorate General of Trade Remedies (DGTR): Anti-Dumping Duty Review on Cast Aluminium Alloy Wheels originating in or exported from China PR (2022-2026) (<a href=\"https://dgtr.gov.in\">dgtr.gov.in</a>).",
    "Global Wheel Industry Landscape & Historical Precedents: Superior Industries International (NYSE:SUP / Germany), CITIC Dicastal, Ronal Group, and Maxion Wheels (Iochpe-Maxion) (<a href=\"https://www.maxionwheels.com\">maxionwheels.com</a>).",
    "Wheels India Limited (TVS Group) & Uno Minda Limited: Comparative Analysis of Tier-1 Automotive Wheel Suppliers in India (Annual Reports FY25-FY26) (<a href=\"https://www.wheelsindia.com\">wheelsindia.com</a>).",
    "ICRA / CRISIL Rating Rationales on Steel Strips Wheels Limited: Credit Rating Upgrade to AA- / Positive on strengthening business profile and debt service coverage (2025-2026) (<a href=\"https://www.icra.in\">icra.in</a>).",
    "Reserve Bank of India (RBI) & Automobile Component Manufacturers Association (ACMA): Automotive Component Industry Performance & Export-Import Review (<a href=\"https://www.acma.in\">acma.in</a>)."
]

# -------------------------------------------------------------------------
# SPINE SPECIFICATION (Derived Strictly from Chapter 9 Synthesis)
# -------------------------------------------------------------------------
spine = {
    "symbol": "SSWL",
    "market": "IN",
    "as_of": "2026-11-09",
    "title": "Steel Strips Wheels Ltd. (NSE: SSWL) — Deep Business Monograph & Stage 2 Dossier",
    "verdict": "WAIT_FOR_SUPPORT",
    "archetype": "QUALITY_GROWTH_PULLBACK",
    "strategy_bucket": "TACTICAL_MOMENTUM",
    "conviction_tier": "TIER_2",
    "cmp": 548.95,
    "entry_zone_low": 450.00,
    "entry_zone_high": 495.00,
    "stop_loss": 405.00,
    "target_base": 720.00,
    "target_bull": 880.00,
    "target_bear": 360.00,
    "asymmetry_ratio": 3.51,
    "weinstein_stage": "STAGE_2",
    "entry_posture": "WAIT_FOR_SUPPORT_PULLBACK",
    "decision_basis": "ch-9",
    "report_status": "PUBLISHED — STAGE 2 MASTERCLASS MONOGRAPH",
    "book_masterclass_title": "The Wheel Titan & The Alloy Revolution",
    "book_title": "The Wheel Titan & The Alloy Revolution",
    "book_subtitle": "A step-by-step narrative walkthrough and audio companion to Steel Strips Wheels Limited: deconstructing the metallurgical migration, global historical parallels, ten-year financial forensics, the AMW Bhuj acquisition, both sides of the institutional debate, and the discipline of high-asymmetry execution.",
    "primer": "Steel Strips Wheels Limited designs and manufactures steel wheel rims, cast aluminum alloy wheels, and lightweight aluminum suspension components for domestic and global automotive OEMs [1][3][10]. Under Managing Director Dheeraj Garg, the Chandigarh-based Tier-1 supplier expanded trailing twelve-month revenues 32.8% to ₹6,235 crore with an operating profit of ₹676 crore, supported by the transformative acquisition of AMW Autocomponent in Bhuj, Gujarat [1][3][5][6]. In Q2 FY27, net profit surged 225% YoY to ₹117 crore, confirming massive operating leverage from its alloy wheel lines [3][6]. On 9 November 2026, the equity closed at ₹548.95, up 167.8% over six months, sitting in a powerful Stan Weinstein Stage 2 advance [7][9]. However, with weekly RSI at 90.26 and price extended +21.3% above its 10-week EMA, the automated technical timing gate caps our verdict at Wait for Support: exercise strict No-FOMO patience and accumulate inside the conditional support band of ₹450.00 to ₹495.00, backed by a structural stop at ₹405.00 and an 18-month base target of ₹720.00 [6][7][9].",
    "citations": citations
}

# -------------------------------------------------------------------------
# CHAPTER 0: PROLOGUE / PRIMER SPECIFICATION
# -------------------------------------------------------------------------
ch00 = {
    "id": "primer",
    "web_title": "0. Executive Thesis, Price Verdict & Opportunity Matrix",
    "book_title": "Prologue: The Business, The Price & Our Independent Verdict",
    "question": "What does Steel Strips Wheels Limited do, why does Dalal Street trade the equity at ₹548.95 today, what is the core institutional Bull vs. Bear debate, and what exact No-FOMO entry triggers govern our capital allocation?",
    "epigraph": {
        "quote": "The greatest danger in momentum investing is not buying a bad business, but buying a wonderful business at the precise moment when the entire world has recognized its brilliance and pushed the price into an unsustainable parabolic climax.",
        "author": "Institutional Execution Maxim • Quantitative Risk Management"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "Steel Strips Wheels Limited (<code>NSE: SSWL</code>; market capitalization: ₹8,482 crore / $1.02 billion) is India's leading pure-play Tier-1 automotive wheel engineering powerhouse, commanding dominant market shares across commercial vehicles, agricultural machinery, and passenger car platforms<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>. Operating across five sprawling manufacturing complexes—Dappar (Punjab), Oragadam (Chennai), Jamshedpur (Jharkhand), Mehsana (Gujarat), and Bhuj (Gujarat)—the company supplies safety-critical wheel assemblies directly into the automated production lines of Maruti Suzuki, Hyundai Motor India, Tata Motors, Mahindra & Mahindra, Kia India, and Ashok Leyland<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-10\">[10]</a></sup>."
        },
        {
            "type": "p",
            "html": "Over the past twenty-four months, SSWL has executed one of the most successful operational transformations in Indian manufacturing<sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-5\">[5]</a></sup>. By pairing its legacy steel rim dominance with an aggressive expansion into cast aluminum alloy wheels and acquiring distressed rival AMW Autocomponent Limited (AACL) via NCLT for a bargain ₹138.15 crore, management unlocked vast brownfield capacity in western India<sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-5\">[5]</a></sup><sup><a href=\"#cite_note-10\">[10]</a></sup>. The financial payoff arrived with explosive force in Q2 FY27 (quarter ended September 2026): net sales jumped 61% YoY to ₹1,930 crore, operating profit more than doubled to ₹236 crore, and quarterly net profit surged 225% YoY to ₹117 crore—generating an annualized quarterly EPS run-rate approaching ~₹30<sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>."
        },
        {
            "type": "table",
            "caption": "The Multi-Horizon Opportunity Matrix: SSWL Investment Outlook Across Three Institutional Timeframes",
            "headers": ["Investment Horizon", "Institutional Stance", "Target Price / Range (₹)", "Operational Driver & Core Risk Factor", "Actionable Portfolio Execution Guideline"],
            "rows": [
                [
                    "Short-Term Trading (1–12 Weeks)",
                    "NEUTRAL / OVERBOUGHT",
                    "₹450.00 – ₹510.00 (Pullback)",
                    "Weekly RSI at 90.26; +21.3% extension above 10-week EMA; trading volume drying up by 87%.",
                    "STRICT DO NOT CHASE. Exercise No-FOMO patience. Expect sharp mean reversion toward institutional moving averages."
                ],
                [
                    "Medium-Term Inflection (3–18 Months)",
                    "WAIT FOR SUPPORT (ACCUMULATE)",
                    "Base: ₹720.00 | Bull: ₹880.00",
                    "Ramp-up of 7.2M alloy wheel lines and aluminum knuckles at Bhuj; sustaining Q2's ₹117 Cr quarterly PAT run-rate.",
                    "ACCUMULATE INSIDE SUPPORT (₹450.00–₹495.00). Hard stop at ₹405.00. Delivers asymmetric 3.51:1 risk-reward."
                ],
                [
                    "Long-Term Compounding (3–10 Years)",
                    "CORE INDUSTRIAL COMPOUNDER",
                    "Compounding @ 18–22% FCF",
                    "Structural SUV alloy penetration expanding from 45% to 75%; EV lightweighting content; debt-to-equity below 0.5x.",
                    "CORE HOLDING CANDIDATE. High capital discipline with zero equity dilution over five years; compounder profile."
                ]
            ],
            "takeaway": "SSWL represents an extraordinary fundamental growth story temporarily trapped in an extreme technical overbought climax. Patient accumulation inside support provides world-class risk asymmetry."
        },
        {
            "type": "p",
            "html": "On 9 November 2026, the equity closed at ₹548.95, consolidating just 4.3% below its all-time high of ₹573.90 after a breathless +167.8% rally over the past six months<sup><a href=\"#cite_note-7\">[7]</a></sup>. While the company's Stan Weinstein Stage 2 technical advance is undeniable (18 consecutive weeks in Stage 2, RS rating 53.21), the stock has extended +21.3% above its rising 10-week EMA (₹452.72) and +73.2% above its 30-week SMA (₹316.87), pushing its weekly Relative Strength Index (RSI) to 90.26—the single highest reading in eight years<sup><a href=\"#cite_note-7\">[7]</a></sup><sup><a href=\"#cite_note-9\">[9]</a></sup>. In strict accordance with our quantitative technical timing gate, this extreme extension caps our official recommendation at <strong>WAIT FOR SUPPORT</strong><sup><a href=\"#cite_note-7\">[7]</a></sup>."
        },
        {
            "type": "table",
            "caption": "Executive Summary & Core Underwriting Architecture for Steel Strips Wheels Limited",
            "headers": ["Underwriting Metric", "Quantitative Specification", "Source & Verification", "Analytical Context & Execution Significance"],
            "rows": [
                ["House Verdict", "WAIT_FOR_SUPPORT", "Evidence-First Protocol (§9)", "Automated technical timing gate enforces No-FOMO entry discipline."],
                ["Investment Archetype", "QUALITY_GROWTH_PULLBACK", "Research Desk Taxonomy", "High-growth industrial leader temporarily extended on weekly tape."],
                ["Conviction Tier", "TIER_2 (High Tactical)", "Scoring Framework", "Substantial operational inflection backed by clean balance sheet."],
                ["Strategy Bucket", "TACTICAL_MOMENTUM", "Capital Allocation Protocol", "High-beta cyclical growth capturing domestic automotive premiumization."],
                ["Current Market Price (CMP)", "₹548.95", "TradingView / NSE Close", "Close on 9 November 2026; -4.3% from 52-week peak."],
                ["Conditional Entry Zone", "₹450.00 – ₹495.00", "Technical Confluence", "Confluence of daily 20-day EMA (₹491.82) and 10-week EMA (₹452.72)."],
                ["Structural Stop-Loss", "₹405.00", "50-Day SMA Breakdown", "Daily close below 50-day SMA (₹417.08); thesis invalidation level."],
                ["18-Month Base Target", "₹720.00 (+31.2% / +51.6%)", "Chapter 9 Valuation Model", "Calculated on FY28E ₹425 Cr PAT @ 26.6x P/E."],
                ["Bull Case Target", "₹880.00 (+60.3% / +85.3%)", "Chapter 9 Bull Scenario", "Full Bhuj utilization + export surge @ 26.5x forward P/E."],
                ["Bear Case Floor", "₹360.00 (-34.4% / -24.2%)", "Chapter 9 Bear Scenario", "Cyclical auto downcycle multiple compression floor."],
                ["Asymmetry Ratio", "3.51 : 1", "Mathematical Formula", "Upside to Base Target (₹245) vs Downside to Stop (₹70) from entry midpoint."]
            ],
            "takeaway": "SSWL offers an exceptional risk-reward profile, provided investors refuse to chase at current extended prices and execute exclusively inside the conditional support buy zone."
        }
    ],
    "book_paragraphs": [
        "Welcome to the masterclass monograph on Steel Strips Wheels Limited. If you and I were sitting together in a private library in Mumbai or New York, reviewing the thousands of listed industrial equities across emerging markets, few companies would command our attention quite like this one.",
        "Steel Strips Wheels is not a household name for consumers. You do not see billboards advertising its brand on the highway. But every single day, millions of Indian commuters, freight truck drivers, and tractor operators entrust their lives to the physical integrity of this company's products. When a Hyundai Creta takes a high-speed turn on the Mumbai-Pune Expressway, or when a fifty-five-ton Tata truck brakes violently on a rain-slicked highway in Jharkhand, the kinetic forces of that machine are absorbed by a circle of engineered metal stamped or cast by SSWL.",
        "For decades, the stock market treated this business as an unglamorous cyclical workhorse. And for good reason: stamping steel rims for tractors is a capital-intensive, low-margin grind. But over the past five years, something extraordinary happened inside this Chandigarh-headquartered firm. Led by Managing Director Dheeraj Garg, the company executed a brilliant two-pronged transformation: first, betting hundreds of crores on precision aluminum alloy wheels to ride India's booming SUV revolution; and second, swooping into the insolvency courts to acquire bankrupt rival AMW Autocomponent in Bhuj for a mere one hundred and thirty-eight crore rupees.",
        "The results of that transformation hit the market like a thunderbolt in late 2026. Quarterly sales exploded past nineteen hundred crore rupees. Quarterly net profit jumped to one hundred and seventeen crore rupees. And the stock price went vertical, surging one hundred and sixty-eight percent in six months to trade above five hundred and forty rupees.",
        "Now, every retail trader in the country is chasing the stock, convinced it is going straight to a thousand. But you and I know better. We have seen this movie before. In this monograph, we will dismantle SSWL piece by piece: its four-decade history, its manufacturing physics, its distribution mechanics, its ten-year financial forensics, its true competitive moat, and its valuation mathematics. And most importantly, we will establish an ironclad, unemotional execution plan. We will not let the fear of missing out tempt us into buying at a parabolic top. We will wait for the market to pull back to our support level, and then we will act with institutional conviction."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "THE ESSENCE OF THE THESIS",
            "quote": "Investing success does not require predicting the unpredictable. It requires identifying an exceptional business undergoing a structural inflection, understanding the mathematical expectations priced into the stock, and having the discipline to strike only when the risk-reward is heavily tilted in your favor.",
            "text": "SSWL embodies the rare convergence of operational transformation and capital discipline. Having preserved its share capital without dilution for five years, every rupee of incremental operating leverage from the Bhuj plant flows directly to the bottom line. The only missing ingredient today is technical entry timing.",
            "bullets": [
                "Dominant Tier-1 market position in India across steel and alloy wheels.",
                "Transformative AMW Bhuj acquisition delivers 50% capital-intensity advantage over competitors.",
                "Zero equity dilution over five years protects per-share value compounding.",
                "Technical timing gate mandates patience: accumulate inside support at ₹450.00–₹495.00."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL ARCHETYPE PARALLEL: THE TIER-1 LEAP",
            "quote": "Historically, the greatest multi-baggers in global manufacturing were not the glamorous high-tech pioneers, but the unloved Tier-1 component makers who successfully transitioned from low-margin steel stamping into high-margin precision metallurgy.",
            "text": "Consider the rise of Linamar in Canada, Magna International in the US, and Dicastal in China. Each of these global giants began life as humble, regional metal-stamping machine shops. Each broke out of the commodity trap by investing aggressively in precision aluminum casting, acquiring distressed rivals during recessions, and becoming indispensable engineering partners to global automotive OEMs. Steel Strips Wheels is walking that exact same path today in the fastest-growing major automotive market in the world.",
            "bullets": [
                "Linamar & Magna: Proved that Tier-1 metallurgical evolution creates multi-decade wealth compounding.",
                "Dicastal: Demonstrated the immense scale and margin power of aluminum wheel dominance.",
                "SSWL: Translating this proven global industrial playbook into Indian market leadership."
            ]
        }
    ]
}

# Write out spine and ch00
(WORK_DIR / "spine.json").write_text(json.dumps(spine, indent=2), encoding="utf-8")
(CH_DIR / "ch00.json").write_text(json.dumps(ch00, indent=2), encoding="utf-8")
print(f"[+] Wrote spine.json and ch00.json to {WORK_DIR}")
