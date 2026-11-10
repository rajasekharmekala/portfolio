#!/usr/bin/env python3
"""
Generator for TD Power Systems Limited Monograph spine.json and Chapter 0 (Prologue).
Derived strictly from Chapter 9 synthesis under the Evidence-First Protocol.
"""
import json
from pathlib import Path

WORK_DIR = Path("work/TDPOWERSYS")
CH_DIR = WORK_DIR / "chapters"
WORK_DIR.mkdir(parents=True, exist_ok=True)
CH_DIR.mkdir(parents=True, exist_ok=True)

citations = [
    "TD Power Systems Limited Annual Report FY 2025-26: Consolidated Financial Statements, Directors' Report & Operational Highlights (31 March 2026): Revenue ₹1,856.2 Cr (+45.2% YoY), PAT ₹238.8 Cr (+36.8% YoY), Order book ₹1,972.9 Cr (<a href=\"https://www.tdps.co.in/investors/financial-results/\">tdps.co.in/investors/financial-results</a>).",
    "TD Power Systems Limited Annual Report FY 2024-25: Consolidated Financial Results & Corporate Overview (<a href=\"https://www.tdps.co.in/investors/annual-reports/\">tdps.co.in/investors/annual-reports</a>).",
    "TD Power Systems Limited Q1 FY27 Earnings Conference Call Transcript (August 2026): Management Commentary by Managing Director Nikhil Kumar and CFO M. N. Varalakshmi; FY27 Revenue Guidance of ₹2,600 Cr (<a href=\"https://www.alphastreet.com/india/td-power-systems-limited-tdpowersys-q1-2027-earnings-call-transcript/\">alphastreet.com/india/td-power-systems-limited-tdpowersys-q1-2027-earnings-call-transcript</a>).",
    "TD Power Systems Limited BSE/NSE Corporate Announcement: Outcome of the Board Meeting and Closure of Qualified Institutional Placement (QIP) raising ₹600 crore at ₹775 per share (October 2026) (<a href=\"https://www.bseindia.com/corporates/ann.html\">bseindia.com/corporates/ann.html</a>).",
    "TD Power Systems Limited Corporate Disclosure: Execution of 10-Year Framework Agreement with Siemens Energy for Large 2-Pole Generators (August 2026) (<a href=\"https://www.bseindia.com/corporates/ann.html\">bseindia.com/corporates/ann.html</a>).",
    "Screener.in Consolidated 10-Year Financial Records, P&L, Balance Sheet, Cash Flow and Ratios for TDPOWERSYS as of 9 Nov 2026 (<a href=\"https://www.screener.in/company/TDPOWERSYS/consolidated/\">screener.in/company/TDPOWERSYS/consolidated</a>).",
    "TradingView Verified Consumer-Tool Snapshot & Technical Indicators for NSE:TDPOWERSYS as of 9 Nov 2026: CMP ₹571.65, 50-DMA ₹736.53, 200-DMA ₹587.04, 30W SMA ₹661.34, 10W EMA ₹678.01, RSI 32.41, Volume 11.46M (<a href=\"https://www.tradingview.com/chart/?symbol=NSE%3ATDPOWERSYS\">tradingview.com/chart/?symbol=NSE%3ATDPOWERSYS</a>).",
    "TradingView Technical Rating, Oscillators and Moving Averages for NSE:TDPOWERSYS (<a href=\"https://www.tradingview.com/symbols/NSE-TDPOWERSYS/technicals/\">tradingview.com/symbols/NSE-TDPOWERSYS/technicals</a>).",
    "TheWrap Stage 2 Market Breadth, Relative Strength & Volume Analysis for TDPOWERSYS (9 Nov 2026) (<a href=\"https://thewrap.in/data-tools/stage2\">thewrap.in/data-tools/stage2</a>).",
    "TD Power Systems Corporate Announcement: Receipt of ₹192 Crore Order via TDPS USA for In-House Designed 2-Pole Gas Turbine Generators for US Data Center Infrastructure (September 2026) (<a href=\"https://www.bseindia.com/corporates/ann.html\">bseindia.com/corporates/ann.html</a>).",
    "Trendlyne & StockEdge Institutional Research & Order Book Analysis on TD Power Systems Limited (October 2026) (<a href=\"https://trendlyne.com/equity/TDPOWERSYS/\">trendlyne.com/equity/TDPOWERSYS</a>).",
    "US Energy Information Administration (EIA) & PJM Interconnection: Behind-the-Meter Natural Gas Turbine Generation and Data Center Interconnection Queues (2025-2026) (<a href=\"https://www.eia.gov/todayinenergy/\">eia.gov/todayinenergy</a>).",
    "Toyo Denki Seizo K.K. & TD Power Systems Historical Technology Licensing Agreement & Generator Manufacturing Heritage (<a href=\"https://www.toyodenki.co.jp/en/\">toyodenki.co.jp/en</a>).",
    "Global Engine & Turbine Generator Manufacturing Landscape: INNIO Jenbacher, Caterpillar Energy Solutions, Rolls-Royce Power Systems / MTU, and Wärtsilä (<a href=\"https://www.innio.com/en/jenbacher\">innio.com/en/jenbacher</a>).",
    "Ministry of Power, Government of India: Central Electricity Authority (CEA) Captive Power Plant Database & Industrial Cogeneration Trends (<a href=\"https://cea.nic.in/\">cea.nic.in</a>).",
    "BSE/NSE Corporate Announcement: Notice of Board Meeting scheduled for 12 November 2026 to approve Unaudited Financial Results for Q2 & H1 FY27 (<a href=\"https://www.bseindia.com/corporates/ann.html\">bseindia.com/corporates/ann.html</a>)."
]

# -------------------------------------------------------------------------
# SPINE SPECIFICATION (Derived from Chapter 9 Synthesis)
# -------------------------------------------------------------------------
spine = {
    "symbol": "TDPOWERSYS",
    "market": "IN",
    "as_of": "2026-11-09",
    "title": "TD Power Systems Ltd. (NSE: TDPOWERSYS) — Deep Business Monograph & Stage 2 Dossier",
    "verdict": "WAIT_FOR_SUPPORT",
    "archetype": "QUALITY_GROWTH_PULLBACK",
    "strategy_bucket": "TACTICAL_MOMENTUM",
    "conviction_tier": "TIER_2",
    "cmp": 571.65,
    "entry_zone_low": 490.00,
    "entry_zone_high": 530.00,
    "stop_loss": 465.00,
    "target_base": 750.00,
    "target_bull": 920.00,
    "target_bear": 420.00,
    "asymmetry_ratio": 3.38,
    "weinstein_stage": "STAGE_4",
    "entry_posture": "AVOID_STAGE4_OR_BROKEN",
    "decision_basis": "ch-9",
    "report_status": "PUBLISHED — STAGE 2 MASTERCLASS MONOGRAPH",
    "book_masterclass_title": "The Electrification Titan & The AI Power Crunch",
    "book_title": "The Electrification Titan & The AI Power Crunch",
    "book_subtitle": "A step-by-step narrative walkthrough and audio companion to TD Power Systems Limited: deconstructing the Japanese engineering heritage, global historical parallels, ten-year financial forensics, the AI data center boom, both sides of the institutional debate, and the discipline of high-asymmetry execution.",
    "primer": "TD Power Systems Limited designs and manufactures customized synchronous AC generators and high-voltage electric motors for global power plants, industrial facilities, and AI data centers [1][6][10]. Under Managing Director Nikhil Kumar, the Bengaluru-based manufacturer expanded trailing twelve-month revenues 54% to ₹2,124 crore with an 18.0% EBITDA margin, 34% ROCE, and over ₹800 crore in liquid net cash following its October 2026 QIP [1][3][4][6]. On 9 November 2026, the equity closed at ₹571.65, down 33.2% from its all-time high of ₹856.10, breaking below its 30-week moving average to test its rising 200-day SMA on 2.5x volume [6][7][8]. Our house verdict is Wait for Support: exercise strict No-FOMO patience and accumulate only inside the conditional support band of ₹490.00 to ₹530.00 once price confirms a Stage 1 base, backed by a structural stop at ₹465.00 and a 12-to-18-month base target of ₹750.00 [6][7][9].",
    "citations": citations
}

# -------------------------------------------------------------------------
# CHAPTER 0: PROLOGUE
# -------------------------------------------------------------------------
ch00 = {
    "id": "ch-0",
    "web_title": "0. Executive Thesis, Price Verdict & Opportunity Matrix",
    "book_title": "Prologue: The Business, The Price & Our Independent Verdict",
    "question": "Why did shares of India's leading precision generator manufacturer plunge 33% from their all-time high of 856 rupees, and does the global AI data center power boom justify accumulating TD Power Systems at today's 571.65 rupees?",
    "epigraph": {
        "quote": "The essence of investment management is the management of risks, not the management of returns. Well-managed portfolios start from this premise.",
        "author": "Benjamin Graham • The Intelligent Investor"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "On 9 November 2026, shares of TD Power Systems Limited (<code>NSE: TDPOWERSYS</code>) closed on the National Stock Exchange at <strong>₹571.65</strong>, sliding 6.58% in a single session and capping a sharp 33.23% decline from their all-time high of ₹856.10 recorded just four weeks earlier<sup><a href=\"#cite_note-6\">[6]</a></sup><sup><a href=\"#cite_note-7\">[7]</a></sup>. That pullback wiped out more than ₹9,000 crore in market capitalization, driven by aggressive institutional profit-taking following the closure of a ₹600 crore Qualified Institutional Placement (QIP) at ₹775 per share in October 2026<sup><a href=\"#cite_note-4\">[4]</a></sup><sup><a href=\"#cite_note-7\">[7]</a></sup>. Heavy distribution volume printed at <strong>11,460,079 shares</strong>—more than two and a half times the 30-day average volume of 4.52 million shares—pushing the stock below its 50-day simple moving average (₹736.53) and its 30-week moving average (₹661.34) to test its rising 200-day moving average at ₹587.04<sup><a href=\"#cite_note-7\">[7]</a></sup><sup><a href=\"#cite_note-8\">[8]</a></sup>."
        },
        {
            "type": "p",
            "html": "Yet beneath this intense technical dislocation lies one of the most profitable, technologically entrenched engineering franchises in emerging markets<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. Operating out of precision manufacturing facilities in Dabaspet, Bengaluru, TDPS is one of the world's few independent manufacturers of high-efficiency <strong>synchronous AC generators</strong> (up to 250 MVA) coupled to steam turbines, gas turbines, hydro turbines, and reciprocating gas engines<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-13\">[13]</a></sup>. For the trailing twelve months ended September 2026, consolidated revenue surged 54.3% year-on-year to an all-time record of <strong>₹2,124 crore</strong>, operating profit (EBITDA) expanded to <strong>₹383 crore</strong> (18.0% margin), and net profit after tax compounded to <strong>₹275 crore</strong> (diluted EPS of ₹8.80)<sup><a href=\"#cite_note-6\">[6]</a></sup>. Pre-tax Return on Capital Employed (ROCE) reached an extraordinary <strong>34.0%</strong>, and the balance sheet holds more than <strong>₹800 crore</strong> in liquid net cash and treasury reserves with virtually zero bank debt<sup><a href=\"#cite_note-4\">[4]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>."
        },
        {
            "type": "callout",
            "variant": "primer",
            "title": "THE AI DATA CENTER ELECTRIFICATION DISLOCATION",
            "paragraphs": [
                "The core engine driving TDPS's multi-year re-rating is the acute bottleneck in global power infrastructure. Across North America, utility interconnection queues for artificial intelligence data centers stretch out four to seven years. Major cloud hyperscalers cannot wait until 2030 to turn on high-density GPU computing clusters; they are deploying on-site, behind-the-meter natural gas turbines and reciprocating engines to generate electricity independently.",
                "Synchronous AC generators have emerged as the critical supply bottleneck. With Western manufacturers hobbled by lead times exceeding 18 months, TDPS has captured landmark volume contracts, including direct US data center orders via TDPS USA and a ten-year preferred manufacturing framework agreement with Siemens Energy. However, following the October 2026 QIP at ₹775 per share, short-term valuation stretch (65x P/E) collided with aggressive profit-booking, driving a violent mean-reversion selloff that has violated intermediate technical moving averages."
            ]
        },
        {
            "type": "p",
            "html": "TD Power Systems' core operational and financial vitals as of 9 November 2026 summarize the quantitative backdrop to our investment thesis<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup><sup><a href=\"#cite_note-7\">[7]</a></sup>:"
        },
        {
            "type": "table",
            "caption": "Executive Snapshot & Key Operating Figures for TD Power Systems Limited (9 Nov 2026)",
            "headers": ["Metric", "Reported Value", "Analytical & Valuation Interpretation"],
            "rows": [
                ["Session Close (9 Nov 2026)", "₹571.65 (-6.58%)", "Down -33.23% from 52-week all-time high of ₹856.10; testing 200-DMA (₹587.04)."],
                ["Market Capitalization", "₹18,376 Cr (Screener) / ₹18,536 Cr (TV)", "Leading independent exporter of rotating heavy electrical machinery in South Asia."],
                ["TTM Revenue & Growth", "₹2,124 Cr (+54.3% YoY)", "Consolidated revenue compounded from ₹1,001 Cr in FY24 to ₹1,856 Cr in FY26 (+45.2%) and ₹2,124 Cr TTM."],
                ["TTM EBITDA & Margin", "₹383 Cr (18.0% margin)", "Operating margins expanded from 2.8% in FY15/FY17 to 18.0% TTM, driven by high-value gas engine alternators."],
                ["TTM Net Profit & EPS", "₹275 Cr (₹8.80 EPS)", "Net profit surged from negative -₹14 Cr in FY18 to ₹239 Cr in FY26 and ₹275 Cr on a trailing basis."],
                ["Valuation Multiples", "64.97x TTM P/E | 16.7x P/B", "Stock P/E at 66.8x on Screener; forward P/E ~45x on FY27 management guidance of ₹2,600 Cr."],
                ["Balance Sheet Strength", ">₹800 Cr Net Cash (~$96M)", "Zero net debt; total borrowings of ₹18 Cr offset by ₹800 Cr+ in cash and October QIP proceeds."],
                ["Capital Efficiency (ROCE / ROE)", "34.0% ROCE | 24.7% ROE", "Pre-tax ROCE surged from 0% in FY16 to 34% in FY26, ranking in top 5% of Asian industrial capital goods."],
                ["Pending Order Book", "₹1,973 Cr (FY26) / ₹2,207 Cr+ (H1)", "Export and deemed export orders represent >80-90% of inflows, giving 12–14 months forward revenue cover."],
                ["Stan Weinstein Stage", "STAGE_4 (Shakeout / Breakdown)", "Shattered 30-week SMA (₹661.34) and 50-day SMA (₹736.53); daily RSI oversold at 32.41 on 2.53x volume."],
                ["Action Verdict", "WAIT_FOR_SUPPORT", "Do not catch falling knife at CMP; accumulate inside ₹490–₹530 support zone; tactical stop ₹465; base target ₹750."]
            ],
            "takeaway": "An elite 34% ROCE industrial compounder currently enduring a necessary post-QIP technical shakeout; entry discipline is mandatory."
        }
    ],
    "book_paragraphs": [
        "Welcome to our deep-research monograph on TD Power Systems Limited. If you and I were sitting across an institutional research desk this evening, looking at the terminal screens as the closing bell rang in Mumbai, you would see a stock down more than six and a half percent on the day, trading at 571 rupees and 65 paise.",
        "You would see that just twenty-five trading days ago, this exact stock was exchanging hands at 856 rupees. You would see that the company has lost a full third of its equity market value in four short weeks. And if you looked at the social media forums and retail trading chats, you would see a chorus of panic: investors who bought the October Qualified Institutional Placement at 775 rupees wondering whether they have been trapped in a generational top.",
        "Now, take a deep breath, push the emotional panic aside, and look at the underlying industrial reality. TD Power Systems does not make ephemeral smartphone software or consumer gadgets. Inside their two state-of-the-art factories in Dabaspet, on the outskirts of Bengaluru, skilled machinists and electrical engineers construct some of the most critical machines on planet Earth: synchronous alternating current generators that weigh up to twenty-five tons, designed with Japanese electromagnetic precision licensed from Toyo Denki Seizo.",
        "Over the past twelve months, TDPS generated 2,124 crore rupees in consolidated revenue—up fifty-four percent year-on-year. They generated 383 crore rupees in operating profit, maintaining an eighteen percent EBITDA margin despite volatile global copper and electrical steel prices. They earned 275 crore rupees in clean net profit, delivering a pre-tax return on capital employed of thirty-four percent. And as of this evening, after completing a 600 crore rupee QIP at 775 rupees per share, they sit on more than 800 crore rupees in liquid net cash, with virtually zero bank debt.",
        "Why did the stock crash thirty-three percent? Because in capital goods, valuation and technical structure matter just as much as business quality. When Dalal Street realized that TDPS was supplying on-site power generators to American AI data centers in Texas and signed a ten-year preferred supply pact with Siemens Energy, generalist fund managers bid the stock up to ninety times earnings. The valuation detached from reality. The moment the QIP closed, trapped supply hit the market, breaking the 10-week moving average, breaking the 30-week moving average, and breaking the 50-day moving average on eleven million shares of volume.",
        "Our house verdict on TD Power Systems is clear and uncompromising: WAIT_FOR_SUPPORT. We do not gamble on catching falling knives at 571 rupees while the tape is in an active Stage 4 distribution shakeout. We demand patience. We wait for the selling volume to dry up, we wait for the price to test its rising 200-day moving average, and we prepare to accumulate only inside the conditional support band of 490 to 530 rupees once price confirms a Stage 1 base.",
        "Over the next nine chapters, you and I will dissect every moving part of this franchise: its origins in the 2001 Toyo Denki partnership; its near-death experience during the 2012–2018 domestic capex winter; the engineering mechanics of its gas engine and steam alternators; its worked hundred-rupee cash flow waterfall; its competitive moat against Chinese and European rivals; its ten-year audited balance sheet; and the exact mathematical probability of its forward scenarios.",
        "Let us turn the page and follow the copper, the steel, and the cash."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "NARRATOR'S REFLECTION: SEPARATING THE ENGINE FROM THE SPEEDOMETER",
            "quote": "In the short run, the market is a voting machine; in the long run, it is a weighing machine. The speedometer on the dashboard may read 571 rupees down from 856, but the industrial engine in Dabaspet is compounding faster than at any time in its twenty-five-year history.",
            "text": "When you observe a 33% drawdown in an elite capital goods compounder, your primary task as an institutional analyst is to determine whether the engine has seized or whether the car has simply hit a patch of gravel. TD Power Systems' order book is at an all-time record of ₹2,207 crore, its factory utilization is at 75%, and its balance sheet has ₹800 crore in net cash. The business engine is firing on all cylinders; only the valuation multiple has compressed.",
            "bullets": [
                "TTM revenue of ₹2,124 crore (+54.3% YoY) with operating profit of ₹383 crore (18.0% margin).",
                "Pre-tax ROCE stands at 34.0%, backed by an unleveraged balance sheet holding >₹800 crore in net cash.",
                "Short-term price action is governed by post-QIP inventory absorption; long-term value is anchored in global electrification."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL PARALLEL: HOW CUMMINS (US) AND SCHNEIDER ELECTRIC (FRANCE) NAVIGATED GRID CYCLES",
            "quote": "The greatest electrification compounders are those that own the critical interface between prime movers and the electric grid.",
            "text": "Look at Schneider Electric in France or Cummins in the United States. During the initial waves of hyperscale cloud computing and renewable grid integration, both stocks experienced sharp 25% to 35% corrections as markets digested rapid multiple expansion. In every instance, patient institutional investors who waited for pullbacks to major technical support levels were rewarded with multi-year compounding runs as real earnings growth filled the valuation gap. TD Power Systems is tracing that exact institutional playbook in India.",
            "bullets": [
                "Schneider Electric (France): Re-rated from 15x to 30x P/E on data center power management, enduring multiple 25% pullbacks along the way.",
                "Cummins (US): Overcame diesel cyclicality to become the world's premier data center standby power supplier.",
                "TD Power Systems (India): The undisputed Indian leader in custom-engineered alternators, poised for durable compounding once technical support holds."
            ]
        }
    ]
}

# Write spine.json and ch00.json
(WORK_DIR / "spine.json").write_text(json.dumps(spine, indent=2), encoding="utf-8")
(CH_DIR / "ch00.json").write_text(json.dumps(ch00, indent=2), encoding="utf-8")
print("Successfully generated spine.json and ch00.json!")
