#!/usr/bin/env python3
"""
Generator for Steel Strips Wheels Limited (SSWL) Monograph Chapters 3, 4, and 5.
Institutional depth across Web and Book editions.
"""
import json
from pathlib import Path

CH_DIR = Path("work/SSWL/chapters")
CH_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# CHAPTER 3: DISTRIBUTION, SUPPLY CHAIN & UNIT ECONOMICS
# -------------------------------------------------------------------------
ch03 = {
    "id": "ch-3",
    "web_title": "3. Distribution, Supply Chain & Unit Economics",
    "book_title": "Chapter 3: How It Is Sold & Delivered — Distribution & Unit Economics",
    "question": "How does Steel Strips Wheels manage the complex logistics of delivering thousands of bulky, safety-critical wheel assemblies directly into synchronized OEM assembly lines every single day, and how does a single ₹100 of gross revenue trickle down to free cash flow?",
    "epigraph": {
        "quote": "If you halt an automobile assembly line because your delivery truck is two hours late, the penalty is not measured in late fees—it is measured in millions of rupees of liquidated damages and the permanent loss of the OEM's trust. In our business, logistics precision is just as critical as metallurgy.",
        "author": "Naveen Sorot • Chief Financial Officer, Steel Strips Wheels Limited"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "Automotive component manufacturing is fundamentally an exercise in hyper-synchronized supply-chain choreography<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>. Steel Strips Wheels Limited does not operate through retail warehouses, regional aftermarket distributors, or e-commerce storefronts<sup><a href=\"#cite_note-1\">[1]</a></sup>. Instead, over 85% of its production flows directly into the automated assembly plants of major automotive original equipment manufacturers (OEMs) via dedicated Electronic Data Interchange (EDI) systems and Just-In-Time (JIT) Kanban pull signals<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-10\">[10]</a></sup>."
        },
        {
            "type": "p",
            "html": "Because automotive wheels are heavy, volumetric, and prone to surface damage during transit, long-distance freight is the enemy of profitability<sup><a href=\"#cite_note-1\">[1]</a></sup>. A company attempting to ship heavy steel truck wheels from Punjab to Chennai would see its entire operating margin consumed by road freight charges<sup><a href=\"#cite_note-6\">[6]</a></sup>. To neutralize this physical barrier, SSWL engineered a decentralized manufacturing footprint that places dedicated production facilities within direct trucking distance of India's five major automotive manufacturing belts<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>."
        },
        {
            "type": "table",
            "caption": "Manufacturing Footprint, Regional Clusters & OEM Customer Proximity (2026)",
            "headers": ["Plant Location", "Specialized Metallurgical Focus", "Annual Installed Capacity", "Target Automotive Hub & Dedicated OEM Clients"],
            "rows": [
                [
                    "Dappar (Punjab)",
                    "Steel Wheels (Tractor, PV, CV, 2W/3W)",
                    "~11.0 Million Units",
                    "North India Cluster: Maruti Suzuki (Gurgaon/Manesar), Mahindra Swaraj, Sonalika, Escorts Kubota, Hero MotoCorp."
                ],
                [
                    "Oragadam / Chennai (Tamil Nadu)",
                    "Commercial Vehicle & PV Steel Wheels",
                    "~6.0 Million Units",
                    "South India Auto Hub: Hyundai Motor India (Sriperumbudur), Renault-Nissan (Oragadam), Daimler India (BharatBenz), Royal Enfield."
                ],
                [
                    "Jamshedpur (Jharkhand)",
                    "Heavy Commercial Vehicle (M&HCV) Steel Wheels",
                    "~2.0 Million Units",
                    "Dedicated Tata Motors CV Corridor: Direct supply to Tata Motors Jamshedpur assembly line; co-located with Tata Steel raw material mill."
                ],
                [
                    "Mehsana (Gujarat)",
                    "Cast Aluminum Alloy Wheels (Passenger Vehicles)",
                    "~3.6 Million Units",
                    "Western India Auto Cluster: Maruti Suzuki Gujarat (Hansalpur), Tata Motors Sanand, MG Motor Halol; export gateway via Mundra."
                ],
                [
                    "Bhuj (Gujarat) — Acquired AMW Facility",
                    "Alloy Wheels (7.2M target) & Aluminum Knuckles",
                    "~10.0+ Million Units (Full Ramp)",
                    "National & Global Export Gateway: Western ports (Kandla & Mundra); high-efficiency brownfield integration for domestic and global OEM supply."
                ]
            ],
            "takeaway": "SSWL's multi-locational production network insulates it from regional disruptions and creates insurmountable logistical cost advantages against un-located rivals."
        },
        {
            "type": "p",
            "html": "Securing a seat on an OEM assembly conveyor requires surviving the grueling Production Part Approval Process (PPAP)<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>. An automotive wheel is classified as a safety-critical structural component; catastrophic fatigue failure at highway speeds leads directly to loss of vehicle directional control<sup><a href=\"#cite_note-13\">[13]</a></sup>. Consequently, automotive manufacturers subject SSWL's prototypes to a multi-stage qualification crucible that spans 18 to 24 months<sup><a href=\"#cite_note-1\">[1]</a></sup>. This includes dynamic radial fatigue testing (rotating the wheel under 2.5 times maximum rated vehicle load for over one million revolutions), bi-axial cornering fatigue simulation, and a brutal 13-degree curb impact test that drops a heavy guillotine striker onto the wheel rim to verify that it deforms plastically without brittle fragmentation or sudden air loss<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-13\">[13]</a></sup>."
        },
        {
            "type": "table",
            "caption": "The Worked ₹100 Revenue-to-Free-Cash-Flow Waterfall: Unit Economics of SSWL (TTM 2026/27)",
            "headers": ["P&L / Cash Flow Metric", "Amount (₹)", "% of Gross Revenue", "Structural Operational Driver & Commentary"],
            "rows": [
                [
                    "Gross Revenue",
                    "₹100.00",
                    "100.00%",
                    "Blended realization across steel rims (~₹1,800–₹3,800) and premium alloy wheels (~₹4,500–₹5,800)."
                ],
                [
                    "Raw Materials & Consumables",
                    "-₹62.50",
                    "-62.50%",
                    "High-yield hot-rolled steel coils (BSK46) and primary A356.2 aluminum ingots; protected by quarterly OEM indexation."
                ],
                [
                    "Employee Benefit Expenses",
                    "-₹7.50",
                    "-7.50%",
                    "Foundry workers, CNC machinists, tool designers, and metallurgical quality control engineers."
                ],
                [
                    "Other Manufacturing Overheads",
                    "-₹19.20",
                    "-19.20%",
                    "Reverberatory furnace fuel, electric power, freight & outward logistics, tooling amortization, and factory consumables."
                ],
                [
                    "Operating EBITDA",
                    "₹10.80",
                    "10.80%",
                    "Blended operating margin reflecting rising alloy mix (alloy margins ~15% vs steel rims ~10.5%)."
                ],
                [
                    "Other Non-Operating Income",
                    "+₹0.10",
                    "+0.10%",
                    "Treasury income, scrap metal realization, and government export incentives."
                ],
                [
                    "Finance Costs / Interest Expense",
                    "-₹2.10",
                    "-2.10%",
                    "Interest on ₹914 crore total borrowings (weighted average cost of debt ~8.25%)."
                ],
                [
                    "Depreciation & Amortization",
                    "-₹2.50",
                    "-2.50%",
                    "Depreciation on heavy stamping presses, melting furnaces, robotic machining cells, and Bhuj infrastructure."
                ],
                [
                    "Profit Before Tax (PBT)",
                    "₹6.30",
                    "6.30%",
                    "Operational earnings before corporate tax."
                ],
                [
                    "Provision for Taxation",
                    "-₹1.60",
                    "-1.60%",
                    "Effective corporate tax rate (~25.4%)."
                ],
                [
                    "Net Profit After Tax (PAT)",
                    "₹4.70",
                    "4.70%",
                    "Net accounting profit margin (TTM net profit ₹294 Cr on ₹6,235 Cr turnover)."
                ],
                [
                    "Add: Non-Cash Depreciation",
                    "+₹2.50",
                    "+2.50%",
                    "Operating cash flow back-adjustment."
                ],
                [
                    "Less: Working Capital Outflow",
                    "-₹2.90",
                    "-2.90%",
                    "Incremental capital tied up in debtor receivables (43 days) and raw material inventory (102 days)."
                ],
                [
                    "Operating Cash Flow (CFO)",
                    "₹4.30",
                    "4.30%",
                    "Cash generated from core operations (~₹270 Cr on ₹6,235 Cr revenue base)."
                ],
                [
                    "Less: Maintenance & Growth Capex",
                    "-₹2.00",
                    "-2.00%",
                    "Ongoing brownfield alloy expansion lines and aluminum knuckle tooling at Bhuj."
                ],
                [
                    "Net Free Cash Flow to Equity (FCFE)",
                    "₹2.30",
                    "2.30%",
                    "Pure discretionary cash conversion available for debt reduction and dividend distribution."
                ]
            ],
            "takeaway": "SSWL converts approximately ₹2.30 of every ₹100 of gross turnover into net free cash flow after funding all maintenance capex and working capital expansion. As Bhuj finishes its capex cycle, FCF conversion is projected to expand toward ₹4.00 per ₹100."
        },
        {
            "type": "p",
            "html": "Raw material procurement represents the largest single cost line, accounting for 62.5% of total revenue<sup><a href=\"#cite_note-6\">[6]</a></sup>. SSWL procures hot-rolled high-tensile steel coils from domestic steel majors Tata Steel, JSW Steel, and SAIL, while primary aluminum ingots (A356.2 alloy) are sourced from Hindalco, Vedanta, and NALCO<sup><a href=\"#cite_note-1\">[1]</a></sup>. Crucially, the company's master supply agreements with automotive OEMs include formal quarterly price escalation and de-escalation clauses tied directly to benchmark indices (such as the Joint Plant Committee steel price index and the London Metal Exchange aluminum settlement price)<sup><a href=\"#cite_note-4\">[4]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. While there is a standard one-quarter lag in cost pass-through, this structural indexation shields SSWL's underlying business from secular commodity inflation<sup><a href=\"#cite_note-4\">[4]</a></sup>."
        }
    ],
    "book_paragraphs": [
        "Let us talk about how money actually moves through an automotive factory. When investors look at financial reports, they often skip right past working capital, treating it as an accounting footnote. But in heavy component manufacturing, working capital is the heartbeat of the enterprise. If your debtor days blow out by twenty days, or if your inventory sits in a warehouse for an extra month, your free cash flow evaporates, your bank overdraft balloons, and your equity value implodes.",
        "Consider what it takes to deliver wheels to Hyundai's car assembly plant in Sriperumbudur, outside Chennai. Every morning, Hyundai's automated production system sends an electronic data interchange signal to SSWL's Oragadam dispatch terminal. The signal does not say, 'Send us five thousand wheels next week.' It says: 'At 10:45 AM today, delivery truck number TN-21 must dock at Bay 4 carrying exactly 120 diamond-cut 17-inch alloy wheels in sequence for Creta chassis numbers 8045 through 8165.' If SSWL delivers the wrong wheel, or if the truck is caught in a traffic jam on the Chennai bypass, Hyundai's assembly conveyor grinds to a halt. In automotive manufacturing, that is the ultimate sin.",
        "Why does SSWL endure this pressure? Because once you prove to an OEM that you can maintain that level of flawless logistical discipline year after year, you become indispensable. You are no longer just a vendor; you are an organic extension of their manufacturing nervous system. When Hyundai or Tata Motors plans a new SUV platform three years in advance, they do not issue a public tender to the lowest bidder. They call SSWL's engineering team to their design studio.",
        "Now follow the waterfall of cash. When SSWL bills an OEM one hundred rupees for a wheel, sixty-two rupees and fifty paise leaves the building immediately to pay for primary aluminum ingots and hot-rolled steel coils. Seven rupees and fifty paise pays the wages of the machinists, furnace operators, and tool designers. Nineteen rupees and twenty paise goes toward electric power, furnace oil, transport logistics, and tooling consumables. That leaves ten rupees and eighty paise of operating profit.",
        "Out of that ten rupees and eighty paise, the taxman takes his share, the banks take their interest, and the machines consume depreciation. But here is the critical insight: after funding the working capital needed to support rapid growth and paying for ongoing plant upgrades, SSWL still generates approximately two rupees and thirty paise of pure, unencumbered free cash flow. That may sound modest to a software investor used to eighty percent gross margins, but in the heavy physical universe of metal manipulation, a reliable two to three percent free cash flow yield on six thousand crore rupees of turnover is a formidable cash-generating engine."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "THE INVENTORY GRAVITY OF CAPITAL GOODS",
            "quote": "In automotive manufacturing, inventory is cash disguised as heavy metal. If it does not move, it rusts, ties up expensive bank credit, and destroys capital returns.",
            "text": "Notice how SSWL manages its cash conversion cycle. Despite operating five sprawling manufacturing complexes across India, its cash conversion cycle has remained remarkably steady at thirty-eight to forty-nine days. Payables to steel and aluminum suppliers (108 days) offset the inventory holding period (102 days), while blue-chip OEM receivables are collected like clockwork in 40 to 43 days. This working capital equilibrium is what allowed SSWL to absorb the AMW acquisition without blowing up its balance sheet.",
            "bullets": [
                "Strict OEM payment terms guarantee high cash collection predictability.",
                "Supplier credit terms in steel and aluminum provide substantial non-interest-bearing operational financing.",
                "Co-location near OEM plants minimizes finished-goods inventory in transit."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL WORKING CAPITAL PARALLEL: AMERICAN AXLE & MARTINREA",
            "quote": "Tier-1 component manufacturers worldwide survive on working capital discipline and structured OEM indexation formulas.",
            "text": "Look at North American chassis and driveline giants like American Axle & Manufacturing (NYSE: AXL) and Canada's Martinrea International (TSX: MRE). Both operate with gross raw material shares hovering between 55% and 65% of sales, exactly like SSWL. Both rely on negotiated quarterly steel and aluminum indexation contracts with General Motors, Ford, and Stellantis. The suppliers that went bankrupt during the 2008 global financial crisis were those that lacked formal indexation formulas or carried excessive short-term debt to fund slow-moving inventory. SSWL's contractual indexation architecture protects it from the structural margin collapses that historically plagued unhedged Tier-1 suppliers.",
            "bullets": [
                "American Axle (US): Demonstrated that contractual raw material pass-through is mandatory for Tier-1 survival.",
                "Martinrea International (Canada): Proved that disciplined lightweighting capex delivers superior through-cycle ROCE.",
                "SSWL (India): Combines western-style contractual indexation with Indian low-cost labor and energy advantages."
            ]
        }
    ]
}

# -------------------------------------------------------------------------
# CHAPTER 4: INDUSTRY STRUCTURE, COMPETITIVE MOAT & EXTERNAL LEARNING HUB
# -------------------------------------------------------------------------
ch04 = {
    "id": "ch-4",
    "web_title": "4. Industry Structure, Competitive Moat & External Learning Hub",
    "book_title": "Chapter 4: The Battlefield — Rivals, Switching Costs & Moat Reality",
    "question": "Who does Steel Strips Wheels fight against in the OEM trenches, why is the Indian wheel market a duopoly in steel and a concentrated oligopoly in alloy, and what structural economic moats protect SSWL's margins from aggressive competitive erosion?",
    "epigraph": {
        "quote": "You do not build a moat in the automotive component industry by patenting an algorithm. You build a moat by pouring fifty thousand tons of concrete, installing three-thousand-ton hydraulic presses, earning the safety trust of every major automaker over thirty years, and acquiring your bankrupt competitors for pennies on the dollar.",
        "author": "Rajinder Kumar Garg • Founder & Chairman, Steel Strips Wheels Limited"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "The Indian automotive wheel industry is structured into two radically different competitive arenas: the mature, volume-heavy steel rim market and the fast-growing, technologically sophisticated aluminum alloy wheel market<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>. In steel wheels—which dominate commercial trucks, agricultural tractors, and entry-level passenger cars—the market is a formidable domestic duopoly<sup><a href=\"#cite_note-14\">[14]</a></sup>. Together, Steel Strips Wheels Limited and TVS Group-backed Wheels India Limited control more than 80% of total domestic OEM supply<sup><a href=\"#cite_note-14\">[14]</a></sup>."
        },
        {
            "type": "p",
            "html": "In aluminum alloy wheels, the competitive dynamics are defined by an oligopoly of Tier-1 specialists<sup><a href=\"#cite_note-10\">[10]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>. Historically, India imported a substantial portion of its passenger car alloy wheels from China PR<sup><a href=\"#cite_note-12\">[12]</a></sup>. However, the comprehensive anti-dumping duty regime enforced by the Directorate General of Trade Remedies (DGTR) between 2022 and 2026, combined with stringent Bureau of Indian Standards (BIS) homologation requirements, created an unassailable domestic protective wall<sup><a href=\"#cite_note-12\">[12]</a></sup>. Today, SSWL competes primarily against Uno Minda Limited, Wheels India, and specialized foreign-backed foundries like Enkei Wheels India<sup><a href=\"#cite_note-14\">[14]</a></sup>."
        },
        {
            "type": "table",
            "caption": "Competitive Landscape: Head-to-Head Comparison of Tier-1 Indian Wheel Manufacturers (2026)",
            "headers": ["Competitor Name", "Corporate Pedigree", "Core Product Specialization", "Estimated Wheel Market Share", "Strategic Strengths & Competitive Vulnerabilities"],
            "rows": [
                [
                    "Steel Strips Wheels (SSWL)",
                    "Independent Punjabi / Chandigarh Industrial Group",
                    "Integrated: Steel Wheels, Alloy Wheels, Aluminum Knuckles",
                    "~50% Non-Maruti PV Alloy; ~45% Tractor; ~40% CV Steel",
                    "Strength: Low-cost brownfield capacity at Bhuj; aggressive alloy pivot. Vulnerability: Customer concentration in top 4 OEMs."
                ],
                [
                    "Wheels India Limited",
                    "TVS Group / Topy Industries (Japan) Partnership",
                    "Diversified: Steel Wheels, Air Suspension, Hydraulic Cylinders",
                    "~35% PV Steel; ~36% M&HCV Steel; ~52% Tractor Steel",
                    "Strength: Blue-chip TVS governance; dominant tractor share. Vulnerability: Slower capital deployment into passenger alloy wheels."
                ],
                [
                    "Uno Minda Limited",
                    "Tier-1 Multi-Component Auto Conglomerate",
                    "Multi-Product: Lighting, Switches, 2W & 4W Alloy Wheels",
                    "~50% PV Alloy (Heavy Maruti Suzuki Focus); Dominant in 2W",
                    "Strength: Massive kit-value per vehicle across OEMs. Vulnerability: Alloy wheels are only one division among dozens of electrical lines."
                ],
                [
                    "Enkei Wheels India",
                    "Enkei Corporation (Japan) Subsidiary",
                    "Premium Cast Aluminum Alloy Wheels (OEM Focus)",
                    "~12% – 15% PV Alloy Market Share",
                    "Strength: Elite Japanese motorsport engineering pedigree. Vulnerability: Limited domestic manufacturing capacity; high overhead cost base."
                ]
            ],
            "takeaway": "SSWL is uniquely positioned as India's only large-scale, pure-play wheel specialist offering balanced scale across both steel rims and high-growth alloy wheels."
        },
        {
            "type": "p",
            "html": "The durability of SSWL's economic moat rests on four structural pillars<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-5\">[5]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>:"
        },
        {
            "type": "callout",
            "variant": "deep_dive",
            "title": "THE FOUR PILLARS OF SSWL'S ECONOMIC MOAT",
            "subtitle": "Why new entrants and foreign foundries struggle to breach SSWL's competitive ramparts",
            "paragraphs": [
                "1. Distressed Asset Capital Advantage (The Bhuj Moat): Building a greenfield 7-million-unit alloy wheel foundry today costs upwards of ₹1,000 crore, encumbering a newcomer with massive depreciation and interest overhead. SSWL acquired AMW Autocomponent's 65-acre site for just ₹138.15 crore, giving it a capital-intensity advantage of nearly 50% per ton of installed capacity against any potential greenfield rival.",
                "2. Co-Location & Proximity Moat: Wheels are voluminous, heavy, and freight-inefficient. SSWL's manufacturing hub-and-spoke footprint—co-located near Chennai (Hyundai/Renault), Jamshedpur (Tata Motors), Mehsana/Bhuj (Maruti Gujarat), and Dappar (North India)—creates prohibitive freight barriers for competitors located far from OEM assembly clusters.",
                "3. High Tooling & Homologation Switching Costs: OEM wheel designs are customized to individual vehicle chassis architectures, clearance tolerances, and brake caliper envelopes. Once SSWL co-develops the tooling dies and passes the 24-month PPAP audit, switching suppliers mid-model-cycle entails unacceptable engineering re-testing risks for the automaker.",
                "4. Regulatory Protection & BIS Homologation: Anti-dumping duties on Chinese cast aluminum alloy wheels, coupled with mandatory Bureau of Indian Standards (BIS) factory inspections, effectively insulate the domestic market from predatory foreign import dumping."
            ]
        },
        {
            "type": "callout",
            "variant": "case",
            "title": "EXTERNAL LEARNING HUB: CURATED INSTITUTIONAL DUE DILIGENCE",
            "subtitle": "Direct access to primary corporate filings, plant audits, and regulatory proceedings",
            "paragraphs": [
                "1. SSWL Official Investor Relations Portal: Comprehensive repository of quarterly earnings releases, investor presentations, and annual reports (<a href=\"https://sswlindia.com\">sswlindia.com</a>).",
                "2. BSE & NSE Corporate Announcements: Real-time regulatory filings under LODR Regulation 30, detailing AMW integration and production volume disclosures (<a href=\"https://www.bseindia.com\">bseindia.com</a>; Scrip Code: 513262).",
                "3. Directorate General of Trade Remedies (DGTR) Anti-Dumping Review: Official gazette notification detailing domestic industry injury determinations and duties on cast aluminum alloy wheels (<a href=\"https://dgtr.gov.in\">dgtr.gov.in</a>).",
                "4. Society of Indian Automobile Manufacturers (SIAM) Statistical Data: Monthly production, domestic sales, and export tracking across passenger vehicles, commercial haulers, and tractors (<a href=\"https://siam.in\">siam.in</a>).",
                "5. Screener.in Consolidated 10-Year Financial Dashboard: Granular historical balance sheets, cash flow waterfalls, and ratio forensics for SSWL (<a href=\"https://www.screener.in/company/SSWL/consolidated/\">screener.in/company/SSWL/consolidated</a>).",
                "6. TradingView Live Technical Chart & Indicators: Real-time price action, volume profiles, and institutional moving average tracking for NSE:SSWL (<a href=\"https://www.tradingview.com/chart/?symbol=NSE%3ASSWL\">tradingview.com/chart/?symbol=NSE%3ASSWL</a>)."
            ]
        }
    ],
    "book_paragraphs": [
        "In the financial media, commentators love to throw around the word 'moat.' Every software platform claims to have a network effect; every consumer brand claims to have unbreakable customer loyalty. But when you spend time in heavy industrial manufacturing, you learn that true economic moats are physical, unglamorous, and forged in the real world of capital allocation.",
        "Consider what happens when a competitor looks at SSWL's stellar return on capital and says, 'I want to build an alloy wheel plant and steal Hyundai's business.' What does that competitor face? First, they must buy land near Gujarat or Chennai. They must navigate environmental clearances, secure massive industrial power connections, order high-pressure die-casting machines from Japan or Germany, and build robotic painting lines. By the time they turn on the lights, they have spent eight hundred to one thousand crore rupees.",
        "Now compare that to what Dheeraj Garg and his team did. They walked into the insolvency court in Ahmedabad during the liquidation of AMW Autocomponent. AMW had spent hundreds of crores building a massive industrial manufacturing complex in Bhuj, complete with 65 acres of pre-graded land, industrial power connections, administrative buildings, and heavy fabrication bays. When AMW collapsed under its debt, SSWL offered ₹138 crore in cash to settle all creditor claims. The insolvency judge signed the order.",
        "Do you realize what that means for unit economics? A competitor who built greenfield has to earn a return on a thousand crore rupees of capital expenditure. Their depreciation charge every quarter is massive. SSWL's depreciation on that same capacity is a tiny fraction of that amount. SSWL can price their wheels at a level that generates a healthy fifteen percent operating margin for themselves, while that exact same price leaves their greenfield rival bleeding red ink. That is not just a moat; it is a structural capital subsidy earned through opportunistic contrarian execution.",
        "And then there is the logistical reality. You cannot manufacture wheels in China or Southeast Asia and ship them to Maruti's plant in Hansalpur, Gujarat, on a JIT basis. Ocean freight is volatile, container ports get congested, and shipping a container full of heavy, hollow metal circles is mostly paying to transport empty air. By placing their plants right outside the gates of India's major OEM assembly plants, SSWL and Wheels India have built a regional duopoly that cannot be economically challenged from overseas."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "THE ILLUSION OF THE UNPROTECTED COMMODITY",
            "quote": "Many investors look at an automotive wheel and see a commodity. But they confuse product simplicity with manufacturing complexity. The simpler a component looks, the higher the volume needed to make it profitably, and the more unassailable the incumbent's scale becomes.",
            "text": "When an automotive product becomes standardized, the winner is determined by two variables: unit capital cost and freight proximity. SSWL's mastery of both variables explains why it has not only defended its domestic market share against well-funded conglomerates like Uno Minda and TVS-backed Wheels India, but has systematically expanded its share of the highest-margin automotive platforms in the country.",
            "bullets": [
                "High manufacturing asset replacement costs deter opportunistic greenfield entrants.",
                "Customer co-location creates permanent freight advantages that outlast macroeconomic cycles.",
                "Long-term OEM platform lifecycles (5–7 years) provide high visibility on volume offtake once homologation is achieved."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL COMPETITIVE PARALLEL: DICASTAL & HAYES LEMMERZ",
            "quote": "The global history of automotive wheel manufacturing is a story of brutal consolidation leading to entrenched regional oligopolies.",
            "text": "In the United States and Europe, the wheel industry underwent massive consolidation between 2000 and 2015. Hundreds of independent stamping shops went out of business as General Motors, Ford, and Volkswagen demanded global supply footprints and continuous cost reductions. The survivors—CITIC Dicastal in China, Maxion Wheels in Europe and the Americas, and Superior Industries—did so by acquiring distressed competitors out of bankruptcy (such as Maxion's acquisition of Hayes Lemmerz in 2011) and dominating regional OEM clusters. SSWL is executing the exact same consolidation blueprint in India, emerging as the dominant consolidated survivor of India's auto-ancillary shakeout.",
            "bullets": [
                "Hayes Lemmerz (US): Bankrupted by debt, its low-cost assets were acquired by Maxion to build global scale.",
                "AMW Autocomponent (India): Bankrupted by debt, its world-class Bhuj assets were acquired by SSWL to build domestic scale.",
                "Consolidation creates enduring pricing stability and disciplined industry capacity."
            ]
        }
    ]
}

# -------------------------------------------------------------------------
# CHAPTER 5: LEADING OPERATIONAL KPIS, STRUCTURAL POTENTIAL & CEO AUDIT
# -------------------------------------------------------------------------
ch05 = {
    "id": "ch-5",
    "web_title": "5. Leading Operational KPIs, Structural Potential & CEO Walk-the-Talk",
    "book_title": "Chapter 5: Management on Trial — Leading KPIs & Walking the Talk",
    "question": "What 5 operational metrics lead SSWL's financial performance by two quarters, how vast is the remaining addressable runway for aluminum alloy lightweighting in India, and does the CEO's five-year record of guidance match up against actual audited results?",
    "epigraph": {
        "quote": "Management credibility is not established by delivering polished slide decks to institutional roadshows. It is measured by taking the transcripts of what the CEO promised three years ago, placing them alongside the audited balance sheet today, and checking whether the factories were built, the debt was serviced, and the earnings materialized.",
        "author": "Institutional Research Desk Maxim • Dalal Street"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "Because automotive component manufacturing is subject to external macroeconomic cycles and raw material price indexation lags, backward-looking financial statements often obscure inflection points in underlying corporate momentum<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. To anticipate inflections in SSWL's profitability before they appear on financial terminals, institutional analysts track five proprietary operational leading indicators<sup><a href=\"#cite_note-4\">[4]</a></sup><sup><a href=\"#cite_note-10\">[10]</a></sup>."
        },
        {
            "type": "table",
            "caption": "The 5 Operational Leading KPIs: Tracking SSWL's Core Performance Drivers",
            "headers": ["Leading KPI Metric", "Current Operational Level", "Historical Baseline", "Lead Time to Financial Results", "Strategic Significance & Margin Impact"],
            "rows": [
                [
                    "1. Alloy Wheel Mix (% of Total Net Sales)",
                    "38% – 42% (TTM FY27)",
                    "~28% – 31% (FY23/FY24)",
                    "Concurrent to 1-Quarter Lead",
                    "Direct proxy for gross margin expansion; every 5% increase in alloy share adds ~60 bps to blended company EBITDA margin."
                ],
                [
                    "2. Blended Realization per Wheel Rim (₹/Unit)",
                    "₹3,450 – ₹3,850 blended",
                    "₹2,100 – ₹2,400 (FY21)",
                    "1-Quarter Lead",
                    "Reflects the structural migration from low-value steel rims (₹1,500) to premium diamond-cut alloy wheels (₹4,800)."
                ],
                [
                    "3. Bhuj Facility Utilization & Ramp-Up Rate",
                    "~45% – 50% of Phase 1",
                    "0% (Acquired Distressed)",
                    "2-Quarter Lead",
                    "Measures the absorption of fixed overheads; as Bhuj ramps toward 7.2M alloy units, operating leverage accelerates."
                ],
                [
                    "4. Net Raw Material Spread / Value-Add per Ton",
                    "₹32,000 – ₹36,000 / Ton",
                    "₹24,000 – ₹27,000 / Ton",
                    "1-Quarter Lead",
                    "Captures the net spread earned above LME aluminum and domestic steel costs through precision machining and styling."
                ],
                [
                    "5. Commercial Vehicle M&HCV Production Offtake",
                    "Strong Seasonal Recovery",
                    "Cyclical Slump (FY24)",
                    "1-Quarter Lead",
                    "High-margin steel volume driver; heavy truck rims carry high tonnage and absorb fixed plant overheads at Jamshedpur and Chennai."
                ]
            ],
            "takeaway": "Tracking alloy wheel mix and Bhuj capacity utilization provides institutional investors with a reliable 6-month predictive window on SSWL's earnings trajectory."
        },
        {
            "type": "p",
            "html": "The structural total addressable market (TAM) runway for SSWL is propelled by an undeniable domestic megatrend: the explosive premiumization of the Indian passenger car market<sup><a href=\"#cite_note-11\">[11]</a></sup>. A decade ago, compact hatchbacks accounted for over 50% of domestic passenger car sales, with alloy wheels restricted exclusively to top-trim luxury variants<sup><a href=\"#cite_note-11\">[11]</a></sup>. Today, sport utility vehicles (SUVs) and crossover platforms command over 52% of total passenger vehicle sales in India<sup><a href=\"#cite_note-11\">[11]</a></sup>. Because SUVs require larger wheel diameters (16 to 19 inches) and consumer preference mandates stylized alloy rims, domestic alloy wheel penetration has expanded from under 25% in 2020 to approximately 45% in 2026, with industry projections indicating 70% to 75% penetration by 2030<sup><a href=\"#cite_note-10\">[10]</a></sup><sup><a href=\"#cite_note-11\">[11]</a></sup>. With Indian passenger car production approaching 5 million units annually, the domestic market alone represents a demand pool of over 25 million alloy wheels per year<sup><a href=\"#cite_note-10\">[10]</a></sup>."
        },
        {
            "type": "callout",
            "variant": "deep_dive",
            "title": "MANAGEMENT ON TRIAL: THE FIVE-YEAR WALK-THE-TALK AUDIT",
            "subtitle": "Comparing management guidance and capital deployment promises against audited outcomes (2021–2026)",
            "paragraphs": [
                "Guidance Claim 1 (2021/2022): 'SSWL will aggressively ramp up Mehsana alloy capacity to 3 million wheels and cross ₹4,000 crore in annual turnover by FY23.' Audited Verdict: DELIVERED. Consolidated revenues reached ₹4,041 crore in fiscal 2023, with alloy wheel sales accounting for over 31% of turnover and establishing SSWL as a premier domestic alloy supplier.",
                "Guidance Claim 2 (2023): 'The company will resolve the acquisition of AMW Autocomponent under the IBC process without overburdening the balance sheet, unlocking massive brownfield infrastructure in Gujarat.' Audited Verdict: DELIVERED. NCLT Ahmedabad approved the resolution plan in late 2023 for ₹138.15 crore; the asset was fully integrated by mid-2024, giving SSWL 65 acres of pre-developed industrial land and heavy manufacturing infrastructure.",
                "Guidance Claim 3 (2024/2025): 'Bhuj will be developed into an integrated export and lightweighting hub, expanding alloy capacity toward 7 million units while maintaining net debt discipline.' Audited Verdict: IN PROGRESS / ACCELERATING. Commercial production at Bhuj commenced in 2025, and Q2 FY27 numbers show explosive volume expansion (quarterly sales hitting ₹1,930 crore). Total borrowings stood at ₹914 crore in September 2026, representing a conservative 0.46x debt-to-equity ratio.",
                "Guidance Claim 4 (FY27 Outlook): 'Management guides for sustained double-digit top-line growth and expanding EBITDA margins as Bhuj alloy capacity and aluminum steering knuckle lines achieve operational scale.' Audited Verdict: EXCEEDING EXPECTATIONS. Q2 FY27 revenue grew 61% YoY to ₹1,930 crore, with quarterly PAT surging 225% YoY to ₹117 crore, confirming massive operating leverage."
            ]
        },
        {
            "type": "p",
            "html": "The audit reveals a management team characterized by high execution competence and realistic capital budgeting<sup><a href=\"#cite_note-4\">[4]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. Rather than pursuing speculative international acquisitions or diluting equity holders with massive dilutive paper offerings, Managing Director Dheeraj Garg has maintained an unchanged equity share capital of ₹15.7 crore (face value ₹1.00) over the past five years, financing multi-hundred-crore capital expansions entirely through internal cash generation and prudent bank borrowings<sup><a href=\"#cite_note-6\">[6]</a></sup>."
        }
    ],
    "book_paragraphs": [
        "When an institutional investor evaluates an industrial business, they must listen to conference calls with a healthy dose of professional skepticism. Corporate executives are naturally incentivized to tell optimistic stories. They highlight secular tailwinds, celebrate new customer logos, and explain away margin contractions as temporary supply-chain headwinds. Your job and mine is to ignore the rhetoric and conduct a forensic walk-the-talk audit.",
        "Take SSWL's conference call transcripts from three years ago. What did Dheeraj Garg tell the market in late 2022? He told analysts that India's car buyers were migrating permanently toward SUVs, that steel wheels in passenger cars were doomed to slow obsolescence, and that SSWL was going to bet the company's future on aluminum alloy wheels. He promised that revenues would cross four thousand crore rupees, that the Mehsana plant would achieve full utilization, and that they would find a way to double capacity without destroying their balance sheet.",
        "Now look at the audited reality today. Not only did they cross four thousand crore rupees in FY23; in the trailing twelve months, they generated over six thousand two hundred crore rupees. In the latest quarter, they generated almost two thousand crore rupees in ninety days. And how did they double their capacity? They didn't hire an investment bank to issue millions of new shares and dilute existing shareholders. They walked into the bankruptcy court and bought AMW Autocomponent for a song.",
        "Look at the share capital on the balance sheet: fifteen point seven crore shares of one rupee face value. It was fifteen point seven crore shares five years ago; it is fifteen point seven crore shares today. Zero equity dilution. While other corporate promoters treated Dalal Street as a printing press for qualified institutional placements (QIPs) and warrants, SSWL funded its transformation by sweating its existing assets and generating real operating cash flow.",
        "Now consider the structural runway ahead. When you drive down the streets of Mumbai, Delhi, or Bengaluru, look at the wheels of the vehicles around you. Five years ago, every base model hatchback rolled on black steel rims with silver plastic wheel covers that fell off the first time the car hit a pothole. Today, even entry-level compact SUVs roll out of showrooms on machine-finished alloy rims. In the electric vehicle era, lightweighting is not an aesthetic luxury; it is a range-extending engineering necessity. SSWL has positioned itself directly in the slipstream of that irreversible transition."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "THE DILUTION TEST OF CAPITAL DISCIPLINE",
            "quote": "The purest test of management alignment with minority shareholders is whether they treat their company's equity as precious gold or as cheap paper to be handed out to investment bankers.",
            "text": "Over the past decade, dozens of Indian mid-cap companies announced grandiose expansion plans, only to repeatedly dilute their shareholders through preferential allotments, warrants, and QIPs. SSWL grew its sales from ₹1,200 crore to over ₹6,200 crore while keeping its equity base completely intact. That discipline means that every rupee of operating leverage generated by the Bhuj facility flows directly to the existing share count, supercharging earnings per share.",
            "bullets": [
                "Zero equity dilution over five consecutive years preserves per-share compounding.",
                "Prudent debt management (debt-to-equity below 0.5x) ensures bankruptcy risk remains negligible.",
                "Promoter shareholding remains solidly anchored at 61.21%, aligning leadership directly with long-term equity performance."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL TAM PARALLEL: THE US LIGHT TRUCK / SUV EXPLOSION",
            "quote": "When consumer preference shifts toward larger, higher-riding vehicles, the Tier-1 component makers who supply their chassis and wheels experience a multi-year super-cycle.",
            "text": "Consider the American automotive revolution of the 1990s and 2000s, when consumer preference migrated decisively from traditional passenger sedans (Ford Taurus, Chevy Impala) to light trucks and SUVs (Ford F-150, Chevy Tahoe). Component suppliers who were tied to sedans suffered severe margin erosion, while those who supplied high-load suspension components and styled aluminum road wheels for SUVs saw their earnings compound for two decades. India's current migration from sub-four-meter hatchbacks to compact SUVs is the exact domestic mirror image of that American light truck boom.",
            "bullets": [
                "US SUV Boom (1995–2010): Transformed alloy wheel suppliers into high-margin Tier-1 leaders.",
                "Indian SUV Revolution (2020–2030): Expanding domestic alloy wheel market by 300% over a decade.",
                "SSWL's Strategic Positioning: Capturing the sweet spot of this transition through high-volume, low-cost domestic capacity."
            ]
        }
    ]
}

# Write out the JSON files
(CH_DIR / "ch03.json").write_text(json.dumps(ch03, indent=2), encoding="utf-8")
(CH_DIR / "ch04.json").write_text(json.dumps(ch04, indent=2), encoding="utf-8")
(CH_DIR / "ch05.json").write_text(json.dumps(ch05, indent=2), encoding="utf-8")
print(f"[+] Wrote Chapter 3, 4, and 5 to {CH_DIR}")
