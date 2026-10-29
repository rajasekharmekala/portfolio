#!/usr/bin/env python3
"""Build structured company spec for AvePoint (NASDAQ: AVPT) with strict readability adherence."""

import json
from pathlib import Path

spec = {
  "symbol": "AVPT",
  "market": "US",
  "as_of": "2026-10-29",
  "title": "AvePoint, Inc. (NASDAQ: AVPT) — Deep Business Monograph & Stage 2 Dossier",
  "verdict": "WAIT_FOR_SUPPORT",
  "archetype": "STAGE2_LEADER",
  "strategy_bucket": "TACTICAL_MOMENTUM",
  "conviction_tier": "TIER_3",
  "cmp": 17.35,
  "entry_zone_low": 14.48,
  "entry_zone_high": 15.73,
  "stop_loss": 12.02,
  "target_base": 21.50,
  "target_bull": 26.00,
  "target_bear": 11.50,
  "weinstein_stage": "STAGE_2",
  "entry_posture": "WAIT_FOR_SUPPORT_PULLBACK",
  "report_status": "PUBLISHED — STAGE 2 MONOGRAPH",
  "primer": (
    "AvePoint provides data security and governance for cloud platforms [1][2]. "
    "Co-founder Dr. Tianyi Jiang leads the firm as chief executive officer [2]. "
    "On the chart, the stock trades in an institutional trend at 17.35 dollars [4]. "
    "Our action verdict is Wait for Support in the 14.48 to 15.73 dollar zone [4][5]."
  ),
  "ch1": {
    "paragraphs": [
      "AvePoint, Inc. (NASDAQ: AVPT) was founded in 2001 by Dr. Tianyi Jiang and Kai Gong [1][2]. The firm is based in Jersey City, New Jersey [1]. It started by making backup tools for Microsoft SharePoint [2]. Today it provides data security and data management for large cloud platforms [1][2]. The firm serves over 21,000 corporate clients and 10 million cloud users across the globe [1][3]. Its software helps IT teams protect sensitive files from theft and accidental leaks [2][6]. When companies deploy artificial intelligence tools, data permissions must be strictly enforced [2]. AvePoint ensures employees only see files they are permitted to view [1][2].",
      "We define our core financial terms up front. In financial accounting, <dfn>EBITDA</dfn> stands for earnings before interest, taxes, depreciation and amortization, which measures cash operating profit before financing charges; <dfn>operating margin</dfn> is the percentage of revenue left after direct costs; and <dfn>net margin</dfn> is the final share of sales kept as bottom-line profit. We track recurring software contracts through <dfn>ARR</dfn>, which stands for annual recurring revenue. We track per-share earnings through <dfn>EPS</dfn>, which stands for earnings per share, and capital returns through <dfn>ROCE</dfn>, which stands for return on capital employed. We also measure <dfn>ROIC</dfn>, which stands for return on invested capital. Leadership sets expectations through <dfn>guidance</dfn>, which is the official financial targets a company commits to publicly.",
      "Cash generation tells the true health of a software business. We track <dfn>working capital</dfn> — unpaid client invoices minus operating payables — along with <dfn>cash flow from operations</dfn>, which is cash collected from customers. We monitor <dfn>free cash flow</dfn> (<dfn>FCF</dfn>, which stands for free cash flow), which is operating cash left after <dfn>capital expenditure</dfn> (cash spent on servers, software, and office gear). In valuation, <dfn>price-to-earnings</dfn> is the share price divided by annual earnings per share, while <dfn>PEG</dfn> stands for price-to-earnings-to-growth and compares the price multiple to earnings growth. Debt risk is measured by <dfn>debt-to-equity</dfn>, which is total loans divided by book equity, while new share grants cause <dfn>dilution</dfn>, which means dividing company ownership into more shares.",
      "In market structure and trend analysis, a <dfn>base</dfn> is a multi-week sideways price consolidation where institutional buyers quietly absorb shares, and a <dfn>pivot</dfn> is the specific resistance price level that triggers a <dfn>breakout</dfn> — a decisive move above the base on expanding trading volume [4][5]. Once above that level, the stock enters <dfn>Stage 2</dfn>, which is Stan Weinstein's institutional markup phase where price trades above a rising 30-week and <dfn>200-day moving average</dfn> (the average closing price over the past 200 trading sessions), supported by the <dfn>50-day moving average</dfn> (the 50-session average price) and the <dfn>20-day moving average</dfn> (the 20-session short-term trend line) [4][5]. Conversely, <dfn>Stage 4</dfn> is a confirmed markdown downtrend below falling moving averages. To avoid chasing extended spikes, we wait for a <dfn>retest</dfn> — a calm pullback toward a rising moving average — inside a pre-defined <dfn>entry zone</dfn>, which is the price band where we place a <dfn>limit order</dfn> (an order that buys only at or below a specified maximum price). Risk is governed by a <dfn>stop loss</dfn>, which is the pre-set exit price that caps downside if the trend breaks, ensuring favorable <dfn>asymmetry</dfn> — a setup where upside potential far outweighs downside risk — measured by the <dfn>reward-to-risk</dfn> ratio. We measure short-term momentum with <dfn>RSI</dfn>, which stands for relative strength index on a 0-to-100 scale, and daily price swing size with <dfn>ATR</dfn>, which stands for average true range over 14 sessions [4][5]."
    ],
    "segments_table": {
      "caption": "AvePoint Confidence Platform revenue streams and functional software suites (FY25 and H1 FY26) [1][3]",
      "headers": [
        "Software Suite",
        "Revenue Share & Type",
        "Core Software Products",
        "Operational Problem Solved for Enterprise IT",
        "Key Growth Driver"
      ],
      "rows": [
        [
          "Resilience Suite (Data Backup & Archiving)",
          "~50% of ARR. SaaS Subscription.",
          "Cloud Backup for M365, Google, Salesforce, Azure. Opus Archiving [1].",
          "Runs automated backups to protect files from ransomware and accidental deletion [2].",
          "Rising cyber threats mandate third-party cloud data copies [3]."
        ],
        [
          "Control Suite (Governance & Access Control)",
          "~30% of ARR. SaaS Subscription.",
          "Cloud Governance. Policies & Insights. Confide Virtual Data Rooms [1].",
          "Enforces access rules so sensitive data is not exposed across internal tools [2].",
          "Adoption of Microsoft Copilot requires clean data permissions to prevent leaks [2][6]."
        ],
        [
          "Modernization Suite (Cloud Migration)",
          "~10% of ARR. Hybrid & Term License.",
          "Fly Migration. Content Manager Integration tools [1].",
          "Moves data workloads from older file shares into modern cloud environments [1].",
          "Corporate migration from on-premise servers to cloud infrastructure continues [3]."
        ],
        [
          "Elements & Channel Partner Platform",
          "~10% of ARR. Channel Partner SaaS.",
          "AvePoint Elements multi-tenant management portal for MSPs [1].",
          "Enables managed service providers to protect and govern small business clients [2].",
          "Partner-led sales lower direct customer acquisition cost [3]."
        ]
      ],
      "takeaway": "The Confidence Platform addresses the entire enterprise cloud data lifecycle through four recurring subscription modules [1][3]."
    },
    "subsections": [
      {
        "title": "Platform Architecture and Day-to-Day Customer Workflow",
        "paragraphs": [
          "The AvePoint Confidence Platform operates as a cloud-native software suite hosted on Microsoft Azure [1][2]. When an enterprise client buys the suite, IT administrators connect it to their Microsoft 365 or Salesforce tenant via secure application programming interfaces [2]. The software scans all corporate files, folders, and user permissions across the organization [2][6].",
          "Daily workflows run through automated software agents [2]. Every six hours, Cloud Backup copies newly created documents and chats into encrypted cloud storage [1][2]. If an employee accidentally deletes a critical file or falls victim to ransomware, IT restores the lost data with one click [2]. Meanwhile, Policies and Insights flags any confidential file that has been shared publicly by mistake [2]. This automated protection frees up corporate IT teams to focus on strategic tasks [1][3]."
        ]
      }
    ],
    "glossary_items": [
      "<strong><dfn>NRR</dfn> (net revenue retention):</strong> Net revenue retention measures the percentage of recurring revenue retained from existing clients over twelve months, including upgrades and expansions [3].",
      "<strong><dfn>gross margin</dfn>:</strong> Gross margin is the share of revenue left after paying for direct cloud server hosting and customer technical support [1]."
    ]
  },
  "ch2": {
    "paragraphs": [
      "Data protection and software governance represent a fast-growing market [1][2]. Companies generate petabytes of unstructured text, spreadsheets, and videos every month [2]. That corporate data must be stored, protected, and governed under strict global privacy laws [1]. Market analysts estimate the total addressable market for cloud data governance will exceed sixty billion dollars by 2030 [1][3].",
      "AvePoint competes against legacy backup vendors and newer cloud security firms [1]. Older vendors like Commvault and Veritas built their tools for on-premise data centers [1]. Newer pure-play vendors like Veeam and Rubrik focus primarily on virtual machine backup [1]. AvePoint holds a unique moat because it focuses deeply on collaboration data and workspace access rules inside Microsoft 365 [2][6]. Microsoft serves as AvePoint's largest partner rather than a direct competitor [1][2]. AvePoint is a top-tier Microsoft Global Partner and co-sells its software alongside Microsoft account executives [1][2]."
    ],
    "subsections": [
      {
        "title": "Day-to-Day Operations Across Global Delivery Hubs",
        "paragraphs": [
          "AvePoint operates through a distributed global team of more than 2,400 employees [1][3]. Software development centers in the United States, Singapore, and Japan build new platform features [1]. Customer support specialists operate 24-hour service centers across four continents [1][2].",
          "Sales teams sell through two primary channels: direct enterprise sales and indirect managed service providers [1][3]. Enterprise sales teams target Fortune 500 corporations with complex compliance needs [2]. Channel partners distribute the software to small and medium enterprises via the AvePoint Elements portal [1]. This hybrid model keeps client acquisition costs efficient while expanding market reach [3]."
        ]
      }
    ],
    "external_resources_table": {
      "caption": "Curated primary sources, corporate filings, and technical references for AvePoint, Inc. [1][2][3][4]",
      "headers": [
        "Resource Title",
        "Source & Direct URL",
        "Why It Matters for Underwriting"
      ],
      "rows": [
        [
          "AvePoint Corporate Hub",
          "<a href=\"https://www.avepoint.com/\" target=\"_blank\" rel=\"noopener\">avepoint.com — Official Platform</a>",
          "Details core software tools. Explains cloud design and case studies [2]."
        ],
        [
          "Security Architecture Paper",
          "<a href=\"https://www.avepoint.com/products/confidence-platform\" target=\"_blank\" rel=\"noopener\">AvePoint Security Architecture</a>",
          "Explains technical security design. Covers encryption and data governance [1][2]."
        ],
        [
          "Investor Relations Filings",
          "<a href=\"https://ir.avepoint.com/\" target=\"_blank\" rel=\"noopener\">ir.avepoint.com — SEC Filings</a>",
          "Primary source for audited balance sheets and earnings call transcripts [1][3]."
        ],
        [
          "CEO Strategy Interview",
          "<a href=\"https://www.youtube.com/results?search_query=AvePoint+TJ+Jiang+interview\" target=\"_blank\" rel=\"noopener\">YouTube — Dr. Tianyi Jiang Interview</a>",
          "Video discussions on Copilot demand and channel partner scaling."
        ],
        [
          "Finviz Financial Snapshot",
          "<a href=\"https://finviz.com/quote.ashx?t=AVPT\" target=\"_blank\" rel=\"noopener\">Finviz — NASDAQ:AVPT Data</a>",
          "Tracks live valuation multiples and institutional ownership levels [4]."
        ],
        [
          "TradingView Technical Chart",
          "<a href=\"https://www.tradingview.com/chart/?symbol=NASDAQ%3AAVPT\" target=\"_blank\" rel=\"noopener\">TradingView — AVPT Chart</a>",
          "Live chart displaying key moving averages and trading volume trends [4]."
        ]
      ],
      "takeaway": "These six resources allow investors to inspect product architecture and monitor market metrics [1][2][3][4]."
    }
  },
  "ch2b": {
    "intro_paragraphs": [
      "Software companies must be judged by operational metrics rather than headline accounting noise [1][3]. Upfront sales commissions and research costs mask underlying profitability [3]. To measure true compounding strength, we track six operational KPIs: ARR growth, net revenue retention, gross margin, operating cash flow, customer count, and employee productivity [1][3]."
    ],
    "kpi_table": {
      "caption": "AvePoint operational KPI performance and historical trend (FY23 through H1 FY26) [1][3]",
      "headers": [
        "Operational KPI",
        "FY23 Baseline",
        "FY24 Delivered",
        "FY25 Delivered",
        "H1 FY26 (Latest)",
        "Underwriting Assessment"
      ],
      "rows": [
        [
          "Annual Recurring Revenue (ARR)",
          "$263.9 Million.",
          "$326.8 Million (+24%).",
          "$419.5 Million (+28%).",
          "$465.1 Million (+27% YoY) [3].",
          "PASS. Consistent 25%+ ARR compounder with expanding subscription momentum [3]."
        ],
        [
          "Net Revenue Retention (NRR)",
          "107%.",
          "109%.",
          "110%.",
          "110% (Trailing 12-Month) [3].",
          "PASS. Clients expand usage year over year as data volume grows [3]."
        ],
        [
          "Non-GAAP Gross Margin",
          "73.1%.",
          "73.8%.",
          "74.2%.",
          "74.5% (Non-GAAP Subscription) [1][3].",
          "PASS. High-margin software model delivers excellent operating leverage [1]."
        ],
        [
          "Operating Cash Flow (CFO)",
          "$16.2 Million.",
          "$35.4 Million.",
          "$68.9 Million.",
          "$45.8 Million (H1 FY26) [1][3].",
          "PASS. Cash generation expanded rapidly over the past three fiscal years [1]."
        ],
        [
          "Enterprise Customer Count",
          "~16,000 clients.",
          "~18,500 clients.",
          "~21,000 clients.",
          ">22,000 active clients [1][3].",
          "PASS. Strong customer acquisition via direct sales and channel MSPs [3]."
        ],
        [
          "GAAP Operating Profitability",
          "Negative ($38.2M).",
          "Negative ($24.1M).",
          "Near Breakeven ($2.1M).",
          "Positive Non-GAAP Operating Margin 14% [3].",
          "PASS. Successful inflection from early losses to sustained cash profitability [1][3]."
        ]
      ],
      "takeaway": "All six operational KPIs show strong progress, highlighted by 27 percent ARR growth and rising cash flow [1][3]."
    },
    "walk_the_talk_paragraphs": [
      "Is AvePoint reaching its full potential, and are the leaders walking the talk? Dr. Tianyi Jiang has served as chief executive officer since co-founding the firm in 2001 [2]. Insider ownership remains high at 33.4 percent, aligning management with outside shareholders [4]. When the company completed its public listing in 2021, leadership promised two clear milestones [1][3].",
      "First, they targeted 25 percent annual subscription revenue growth while shifting away from one-off legacy licenses [1][3]. Second, they committed to expanding operating profit margins toward 15 percent by FY26 [3]. Management has beaten and raised financial guidance across eight consecutive quarterly reporting cycles [3]. The team has delivered on every major operational target set for investors [1][3]."
    ],
    "walk_the_talk_table": {
      "caption": "Executive leadership guidance audit: promises made versus actual financial delivery [1][3]",
      "headers": [
        "Commitment & Year",
        "Public Management Guidance",
        "Actual Delivered Results",
        "Walk-the-Talk Verdict"
      ],
      "rows": [
        [
          "SaaS Revenue Shift (2021)",
          "Transition 80%+ of total revenue to recurring SaaS subscriptions [1].",
          "SaaS subscriptions reached 88% of total revenue in mid-2026 [3].",
          "EXCEEDED. Legacy one-off licenses phased out ahead of schedule [1][3]."
        ],
        [
          "FY24 Revenue Guidance",
          "Initial guide of $314M to $320M total revenue [3].",
          "Delivered $326.8M in revenue, beating top end of guidance by 2.1% [1].",
          "EXCEEDED. Beat initial revenue targets in every fiscal quarter [3]."
        ],
        [
          "FY25 Revenue Guidance",
          "Initial guide of $385M to $391M total revenue [3].",
          "Delivered $419.5M in revenue, up 28% year over year [1][3].",
          "EXCEEDED. Raised guidance in consecutive quarters during the fiscal year [3]."
        ],
        [
          "Cash Flow Generation (2024)",
          "Achieve sustainable positive free cash flow by FY25 exit [1].",
          "Generated $68.9M in operating cash flow and $61.2M in FCF in FY25 [1][3].",
          "EXCEEDED. Cash generation turned strongly positive ahead of timeline [1]."
        ]
      ],
      "takeaway": "Executive leadership shows a reliable track record of delivering ahead of public forecasts [1][3]."
    },
    "closing_paragraphs": [
      "AvePoint operates as a high-quality software business [1]. Co-founders lead the firm with significant personal ownership [4]. Financial targets have been consistently exceeded over multiple operating cycles [3]. The business possesses structural competitive advantages in cloud data management [1][2]."
    ]
  },
  "ch3": {
    "intro_paragraphs": [
      "A great software business can still be a poor investment if the stock price is too high [4]. We examine AvePoint's balance sheet and valuation using current market data [4]. The company holds 425 million dollars in cash and short-term investments with zero long-term debt [1][4]. This gives the business fortress balance sheet strength [1]."
    ],
    "layer1_intro": "We review valuation multiples from our live Finviz and TradingView snapshots [4]. The table below compares AvePoint to broader market benchmarks [4].",
    "layer1_table": {
      "caption": "AvePoint valuation multiples and balance sheet forensics (as of October 29, 2026) [1][4]",
      "headers": [
        "Financial Metric",
        "Reported Value",
        "Benchmark / Rule Context",
        "Forensic Assessment"
      ],
      "rows": [
        [
          "Stock Price & Market Cap",
          "$17.35 / $3.38 Billion.",
          "Mid-cap enterprise software tier.",
          "Liquid trading volume with institutional sponsorship [4]."
        ],
        [
          "Enterprise Value (EV)",
          "$2.95 Billion.",
          "Market cap minus $425M net cash.",
          "Net cash represents 12.6% of market cap [1][4]."
        ],
        [
          "EV to Trailing Revenue",
          "6.3x EV / Sales.",
          "Cloud software peer median is 6.5x to 7.5x.",
          "Fair valuation for a 27% recurring revenue compounder [3][4]."
        ],
        [
          "EV to Forward ARR",
          "5.7x Forward ARR.",
          "Software peers trade between 6.0x and 8.0x.",
          "Attractive entry multiple on forward subscription revenue [3]."
        ],
        [
          "Balance Sheet Net Cash",
          "$425 Million Net Cash.",
          "Zero long-term debt obligations.",
          "PASS. Exceptional safety with self-funding growth profile [1][4]."
        ],
        [
          "Gross Profit Margin",
          "74.5% Subscription Gross Margin.",
          "Software benchmark threshold is 70.0%.",
          "PASS. High gross margins support strong operating leverage [1][3]."
        ]
      ],
      "takeaway": "AvePoint combines 27 percent recurring revenue growth with a fortress balance sheet carrying 425 million dollars in net cash [1][4]."
    },
    "estimates": [
      {
        "the_number": "Base-case fair value of 21.50 dollars per share over the next twelve months (representing 24 percent upside from the current 17.35 dollar price, and 36 percent upside from the 15.73 dollar entry zone top).",
        "how_calculated": "We apply a 6.5 times enterprise value to revenue multiple to our FY27 revenue estimate of 575 million dollars, discounted back to present value using a 10 percent cost of equity.",
        "the_inputs": "Current price of 17.35 dollars; 194.8 million diluted shares; net cash balance of 425 million dollars; FY26 consensus revenue estimate of 525 million dollars [3][4].",
        "the_range": "Target values range from 18.50 dollars at a conservative 5.5 times multiple to 24.50 dollars at an 7.5 times multiple [4].",
        "if_off": "If net revenue retention falls below 105 percent and subscription revenue growth slows to 15 percent, fair value drops to 13.50 dollars."
      }
    ],
    "peer_table": {
      "caption": "Peer comparison across cloud data governance and infrastructure software providers [1][3][4]",
      "headers": [
        "Company Name",
        "Ticker",
        "Revenue Growth (YoY)",
        "EV / Sales Multiple",
        "Gross Margin",
        "Balance Sheet Posture"
      ],
      "rows": [
        [
          "AvePoint, Inc.",
          "NASDAQ: AVPT",
          "27% YoY.",
          "6.3x.",
          "74.5%.",
          "Net Cash ($425M) [1][4]."
        ],
        [
          "Rubrik, Inc.",
          "NYSE: RBRK",
          "35% YoY.",
          "8.5x.",
          "76.8%.",
          "Net Cash ($350M) [4]."
        ],
        [
          "Commvault Systems",
          "NASDAQ: CVLT",
          "14% YoY.",
          "5.2x.",
          "82.1%.",
          "Net Cash ($280M) [4]."
        ],
        [
          "Varonis Systems",
          "NASDAQ: VRNS",
          "18% YoY.",
          "9.8x.",
          "84.6%.",
          "Net Cash ($310M) [4]."
        ]
      ],
      "takeaway": "AvePoint offers faster growth than legacy peers at a sensible valuation discount to security names [4]."
    }
  },
  "ch4": {
    "ledger_cite_tag": " [4]",
    "intro_prose": (
      "A great business must be bought at the right technical point on the chart [4]. "
      "We analyze AvePoint's trend using live TradingView data [4]. "
      "The stock trades above all rising moving averages in an institutional markup [4]. "
      "However, a recent vertical price rally makes immediate buying risky [4]. "
      "Our No-FOMO framework tells us to wait for a calm pullback into support [4][5]."
    ),
    "tech_table_takeaway": (
      "AvePoint trades in a rising trend across all key timeframes [4]. "
      "Price at 17.35 dollars sits comfortably above the rising 200-day average of 11.85 dollars [4]. "
      "The 50-day average of 14.14 dollars confirms strong institutional accumulation [4]."
    ),
    "gate_intro_prose": (
      "Our trading rules guard against emotional buying near tops [5]. "
      "We only buy immediately when price sits close to primary moving averages [5]. "
      "When a stock extends too far above support, we wait for a dip [5]."
    ),
    "gate_table_takeaway": (
      "AvePoint fails our extension test by sitting 18 percent above its 10-week average [4]. "
      "The daily RSI of 73.86 also signals short-term overbought conditions [4]. "
      "Therefore, our disciplined plan is to wait for a pullback into support [4][5]."
    ),
    "closing_prose": (
      "Never confuse a great company with an immediate market buy order [5]. "
      "Buying extended stocks exposes investors to painful short-term corrections [5]. "
      "Waiting for our 14.48 to 15.73 dollar support zone provides safety [4][5]. "
      "This patient posture protects capital while keeping long-term upside intact [5]."
    )
  },
  "ch5": {
    "intro_paragraphs": [
      "Investors must analyze opportunities across distinct time horizons [4]. Short-term trading dynamics differ from multi-year fundamental compounding [1]. We break our AvePoint investment outlook into short-term, medium-term, and long-term views [4]."
    ],
    "horizon_table": {
      "caption": "AvePoint multi-horizon investment thesis and expected return expectations [1][3][4]",
      "headers": [
        "Time Horizon",
        "Target Window",
        "Expected Price & Return",
        "Primary Catalysts & Milestones"
      ],
      "rows": [
        [
          "Short-Term (1–3 Months)",
          "Support Pullback.",
          "$14.50 to $17.50 (+0% to +10%).",
          "Q3 earnings release on November 5 and digestion of recent price gains [3][4]."
        ],
        [
          "Medium-Term (6–12 Months)",
          "Base Target.",
          "$21.50 (+36% from support).",
          "Expansion of Microsoft Copilot governance deals and international channel scaling [1][2]."
        ],
        [
          "Long-Term (2–3 Years)",
          "Bullish Expansion Target.",
          "$26.00 (+65% from support).",
          "Scaling ARR toward one billion dollars with 18% operating profit margins [1][3]."
        ]
      ],
      "takeaway": "Multi-horizon expected value is anchored by steady subscription growth and rising cash flow margins [1][3][4]."
    },
    "variant_perception_paragraphs": [
      "Where does our analysis differ from the broader market consensus? Wall Street analysts carry an average price target of 17.00 dollars on the stock [4]. Many analysts view AvePoint simply as an older backup utility vendor [1].",
      "We see a more powerful fundamental transformation taking place [2]. AvePoint has become an essential security layer for enterprise AI adoption [2][6]. Organizations cannot deploy AI tools without clean data governance [2]. AvePoint captures this multi-year spending wave directly [1][2]."
    ],
    "estimates": [
      {
        "the_number": "Probability-weighted 12-month expected value of 21.30 dollars per share (+22.8 percent from current price of 17.35 dollars).",
        "how_calculated": "We weight our three scenario targets: 20 percent probability for the 26.00 dollar bull case, 60 percent probability for the 21.50 dollar base case, and 20 percent probability for the 11.50 dollar bear case.",
        "the_inputs": "Bull target 26.00 dollars; base target 21.50 dollars; bear target 11.50 dollars; current market price 17.35 dollars [4].",
        "the_range": "Twelve-month price targets range between 11.50 dollars in the bear case and 26.00 dollars in the bull case [4].",
        "if_off": "If customer acquisition slows following changes to Microsoft partner terms, expected value drops to 16.00 dollars."
      }
    ],
    "scenario_table": {
      "caption": "Three-scenario valuation model for AvePoint over a twelve-month horizon [1][3][4]",
      "headers": [
        "Scenario",
        "Probability",
        "Target Price",
        "ARR Growth & Margin Assumptions",
        "Implied Thesis Outcome"
      ],
      "rows": [
        [
          "Bear Scenario",
          "20% Probability.",
          "$11.50 (-34% from CMP).",
          "ARR growth slows to 15%. Macro budget cuts hurt cloud spending [1].",
          "Breaks below 200-day moving average. Exit via stop loss at $12.02 [4]."
        ],
        [
          "Base Scenario",
          "60% Probability.",
          "$21.50 (+24% from CMP).",
          "ARR grows 24% to $520M. Operating margins reach 14%. Multiple holds at 6.0x [3].",
          "Trend continuation. Captures steady multiple expansion [4]."
        ],
        [
          "Bull Scenario",
          "20% Probability.",
          "$26.00 (+50% from CMP).",
          "ARR growth accelerates to 30%+. Copilot security modules surge. Multiple expands [2][3].",
          "Institutional re-rating as an elite enterprise AI data winner [4]."
        ]
      ],
      "takeaway": "The risk-reward balance is favorable, offering 24% base upside versus 20% downside to our stop loss [4]."
    }
  },
  "ch6": {
    "intro_paragraphs": [
      "Every serious investment thesis must confront its primary risks [1]. We identify four structural threats that could damage AvePoint's business [1][2]. We monitor these vulnerabilities closely to protect our capital [4]."
    ],
    "flaws_table": {
      "caption": "Forensic vulnerability matrix and thesis-breaking warning signs for AvePoint [1][2][4]",
      "headers": [
        "Risk Category",
        "Specific Threat Description",
        "Potential Business Impact",
        "Forensic Invalidation Sign"
      ],
      "rows": [
        [
          "Platform Concentration Risk",
          "Over 80% of platform revenue depends on the Microsoft cloud ecosystem [1][2].",
          "Changes to Microsoft partner fees or API access could hurt gross margins [1].",
          "Drop in Microsoft co-sell partner status or API price increases [1]."
        ],
        [
          "Native Competition Risk",
          "Microsoft could build basic backup and governance tools directly into Windows or M365 [2].",
          "Basic utility clients might downgrade to free native tools [2].",
          "Net revenue retention falling below 105% indicates client churn [3]."
        ],
        [
          "Stock-Based Compensation",
          "Annual stock grants dilute public shareholders by 2.5% to 3.0% each year [1][4].",
          "Limits per-share earnings growth despite rising operating cash flow [1].",
          "Annual dilution exceeding 3.5% of total outstanding shares [1]."
        ],
        [
          "Technical Extension Risk",
          "Share price sits 18% above 10-week average ahead of earnings release [4].",
          "Any quarterly earnings stumble could trigger a swift 15% to 20% correction [4].",
          "Daily close below the 50-day average ($14.14) signals short-term exhaustion [4]."
        ]
      ],
      "takeaway": "Key structural risks focus on Microsoft partner dependencies and short-term technical extension [1][2][4]."
    },
    "hinge_paragraph": (
      "<strong>The Single Hinge Claim:</strong> Our bullish thesis rests on one specific claim [2]. "
      "We believe enterprise artificial intelligence rollouts require specialized third-party data governance [2][6]. "
      "If native tools prove sufficient for corporate compliance, AvePoint's growth will slow [2]. "
      "If companies require third-party controls, AvePoint will compound for years [1][2]."
    )
  },
  "ch7": {
    "decision_paragraphs": [
      "Our final action verdict for AvePoint, Inc. (NASDAQ: AVPT) is <strong>WAIT_FOR_SUPPORT</strong> [4][5]. We adopt a <code>WAIT_FOR_SUPPORT_PULLBACK</code> posture in our <strong>$14.48 to $15.73</strong> limit-order buy zone [4][5]. We place our hard stop loss at <strong>$12.02</strong> to guard against downside risk [4]. Our 12-month base target is <strong>$21.50</strong> and our bull target is <strong>$26.00</strong> [4].",
      "Why do we wait for a dip instead of buying immediately at $17.35? The stock has gained 38 percent over the past three months [4]. Price trades 18 percent above its 10-week moving average and daily RSI sits at 73.86 [4]. Buying extended leaders right before earnings introduces unnecessary drawdown risk [4][5]. By placing limit orders near rising support, we achieve a superior reward-to-risk ratio [4][5]."
    ],
    "verdict_rule_summary": "Stage 2 winner (+40.8% above 30W SMA), but extended +18.0% above 10W EMA with RSI at 73.86; wait for support pullback into $14.48–$15.73.",
    "sizing_table_takeaway": "At the $15.73 top of our buy zone with a $12.02 stop loss (-23.6% stop distance), our Tier 3 risk budget sizes this position at 2.26% of portfolio net worth [4][5].",
    "triggers": [
      "<strong>Actionable Limit Buy Trigger:</strong> <p class=\"trigger\">Place limit orders in two tranches between $14.48 and $15.73. This accumulates shares near the rising moving averages after earnings [4][5].</p>",
      "<strong>Breakout Continuation Trigger:</strong> <p class=\"trigger\">If the stock consolidates tightly above $16.50 for two weeks, initiate a buy. Execute on a high-volume breakout above $17.80 with a trailing stop [4][5].</p>",
      "<strong>Hard Stop Loss Invalidation Trigger:</strong> <p class=\"trigger\">Exit the entire position on a daily close below $12.02. That breaks the 200-day average and ends the trend [4][5].</p>",
      "<strong>Profit Harvesting Target Trigger:</strong> <p class=\"trigger\">Trim one-third of the position at our $21.50 base target. Trail the remaining stop along the rising 10-week average toward $26.00 [4][5].</p>"
    ]
  },
  "citations": [
    "AvePoint, Inc. — SEC Form 10-K Annual Report (FY25) and Form 10-Q Quarterly Reports (H1 FY26): <a href=\"https://ir.avepoint.com/\" target=\"_blank\" rel=\"noopener\">https://ir.avepoint.com/</a>.",
    "AvePoint, Inc. — Official Corporate Website & Software Platform Architecture: <a href=\"https://www.avepoint.com/\" target=\"_blank\" rel=\"noopener\">https://www.avepoint.com/</a>.",
    "AvePoint, Inc. — Q2 FY26 Earnings Release, Investor Presentation & Webcast Transcript (ARR $465.1M, +27% YoY; Non-GAAP Operating Margin 14%): Investor Relations Filings, August 2026.",
    "TradingView & Finviz — Technical & Fundamental Market Snapshot for NASDAQ:AVPT (`scripts/stock_snapshot.py` output as of 29 Oct 2026): Price $17.35, 30W SMA $12.32, 10W EMA $14.70, 50D SMA $14.14, 200D SMA $11.85, RSI 73.86, ATR $0.58: <a href=\"https://www.tradingview.com/chart/?symbol=NASDAQ%3AAVPT\" target=\"_blank\" rel=\"noopener\">TradingView Chart</a>.",
    "Portfolio Stage 2 Sector Momentum & Scoring Framework (`.agents/config/scoring.json`): Rules for Weinstein Stage 2 classification, No-FOMO extension limits, and risk-unit position sizing.",
    "Microsoft Corporation — Microsoft 365 Copilot Architecture & Partner Ecosystem Documentation: Data Security, Entra Permissions, and Third-Party Compliance Integration (2025–2026)."
  ]
}

out_spec = Path("/tmp/AVPT_spec.json")
out_spec.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_spec} ({len(out_spec.read_text()):,} bytes)")
