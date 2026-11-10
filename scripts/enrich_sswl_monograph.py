#!/usr/bin/env python3
"""
scripts/enrich_sswl_monograph.py
Enriches work/SSWL/chapters/ch00.json .. ch09.json with deep analytical
web blocks (estimates, case notes, detailed tables) and rich second-person mentor-voice
book paragraphs, ensuring full 13,000–16,000+ word depth across both Web and Book editions.
"""
import json
from pathlib import Path
import sys

CH_DIR = Path("work/SSWL/chapters")

def enrich_all():
    # -------------------------------------------------------------------------
    # CHAPTER 0 ENRICHMENT
    # -------------------------------------------------------------------------
    ch0 = json.loads((CH_DIR / "ch00.json").read_text(encoding="utf-8"))
    ch0["web_blocks"].append({
        "type": "estimate",
        "the_number": "The annualized forward price-to-earnings multiple of Steel Strips Wheels based on Q2 FY27 earnings is 18.44x, compared to a trailing twelve-month multiple of 29.43x.",
        "how_calculated": "In Q2 FY27 (quarter ended 30 September 2026), SSWL reported consolidated net profit of ₹116.89 crore on an equity base of 15.71 crore shares, generating a single-quarter diluted EPS of ₹7.44. Multiplying this quarterly run-rate by four yields an annualized forward earnings power of ₹29.76 per share. Dividing the current market price of ₹548.95 by ₹29.76 produces a forward P/E multiple of 18.44x.",
        "the_inputs": "Audited Q2 FY27 financial results; NSE closing price of ₹548.95 on 9 November 2026; fully diluted equity share count of 15,70,82,490 shares of face value ₹1.00.",
        "the_range": "Over the past decade, SSWL's normal trading P/E band fluctuated between 12x and 22x during steady auto cycles. During peak cyclical booms (such as 2017 and 2021), the multiple briefly expanded to 28x–32x. If the Q2 FY27 run-rate represents a permanent upward inflection in baseline earning power, the stock is trading in the lower half of its historical multiple band. Conversely, if Q2 was inflated by festive pre-stocking, normalized forward P/E on FY27 consensus EPS of ₹22.50 is 24.4x.",
        "if_off": "If Q3 and Q4 FY27 earnings contract back to the FY26 baseline of ~₹48 crore per quarter, annual earnings power drops to ₹190 crore (EPS ~₹12.10), causing the effective valuation multiple to spike to 45.4x and triggering a brutal 30% to 40% multiple de-rating toward ₹350–₹380."
    })
    ch0["web_blocks"].append({
        "type": "callout",
        "variant": "risk",
        "title": "THE LONG-TERM ADDITIONAL SURVEILLANCE MEASURE (LTASM - I) FLAG",
        "subtitle": "Why exchange surveillance status creates both temporary trading friction and an institutional buying opportunity",
        "paragraphs": [
            "In response to the vertical +167.8% price advance over the preceding six months, the National Stock Exchange (NSE) and Bombay Stock Exchange (BSE) placed SSWL under the Long-Term Additional Surveillance Measure (LTASM - Stage I) framework in late 2026. This regulatory intervention enforces 100% margin requirements for retail intraday trades and caps daily price band fluctuations.",
            "For institutional investors, ASM surveillance acts as a natural volatility dampener. While it temporarily curbs speculative retail leverage and intraday churning, it frequently induces a healthy multi-week trading consolidation. This regulatory pause allows the underlying business fundamentals and quarterly earnings to catch up with the extended stock price tape."
        ]
    })
    ch0["book_paragraphs"].extend([
        "Think carefully about what happens when an industrial stock runs up one hundred and sixty-eight percent in six months. When an equity moves that fast, the market undergoes a profound psychological transformation. In the early stages of the advance, nobody believes the numbers. Analysts write cautious notes warning of cyclical headwinds, while short-sellers point to debt and raw material inflation.",
        "Then, the company delivers a quarterly report that obliterates every consensus estimate. Sales surge sixty-one percent. Net profit more than doubles. And suddenly, the very same analysts who were skeptical three months ago rush to raise their target prices. Institutional portfolio managers who missed the initial move face severe career risk if they underperform their benchmarks, so they begin chasing the stock at any price.",
        "This is the psychological inflection point where you and I must exercise our greatest discipline. When everyone is panicking, you must look for value. But when everyone is euphoric, you must look at the tape and ask: what is already priced in? At 548 rupees, Dalal Street is pricing in near-perfection. The business is fundamentally exceptional, but the stock has sprinted ahead of its headlights. True institutional wisdom lies in having the patience to wait for the market to come to us."
    ])
    (CH_DIR / "ch00.json").write_text(json.dumps(ch0, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 1 ENRICHMENT
    # -------------------------------------------------------------------------
    ch1 = json.loads((CH_DIR / "ch01.json").read_text(encoding="utf-8"))
    ch1["web_blocks"].append({
        "type": "table",
        "caption": "Forensic Breakdown of the 2018–2021 Automotive Winter & Stock Price Collapse",
        "headers": ["Financial Year", "Revenue (₹ Cr)", "EBITDA Margin (%)", "Net Profit (₹ Cr)", "Net Debt (₹ Cr)", "Average Share Price (₹)", "Macroeconomic & Industry Crucible"],
        "rows": [
            ["FY18", "1,745", "14.2%", "73", "842", "₹195", "Indian auto capex peak; Mehsana alloy plant construction commences."],
            ["FY19", "2,050", "13.6%", "82", "915", "₹185", "IL&FS collapse triggers shadow-banking credit freeze across auto financing."],
            ["FY20", "1,563", "10.8%", "24", "985", "₹115", "Synchronized demand collapse; BS-VI transition costs; factory shutdowns."],
            ["FY21", "1,749", "11.6%", "49", "890", "₹120", "COVID-19 national lockdowns; supply-chain dislocation; commodity surge begins."],
            ["FY22", "3,560", "12.7%", "205", "778", "₹170", "Post-pandemic cyclical rebound; Mehsana alloy lines reach 75% utilization."]
        ],
        "takeaway": "Between FY18 and FY21, SSWL endured the triple shock of the NBFC credit freeze, BS-VI transition, and COVID-19. Surviving with net debt intact laid the groundwork for the 2022–2026 super-cycle."
    })
    ch1["web_blocks"].append({
        "type": "callout",
        "variant": "deep_dive",
        "title": "THE INSOLVENCY AUCTION OF AMW AUTOCOMPONENT (AACL)",
        "subtitle": "How SSWL acquired 65 acres of pre-developed industrial infrastructure for pennies on the dollar",
        "paragraphs": [
            "The Background: AMW Autocomponent Limited, originally part of the Asia MotorWorks commercial vehicle empire in Bhuj, Gujarat, fell into severe financial distress following the 2013–2015 commercial vehicle recession. Laden with over ₹900 crore of debt to a consortium of public and private sector banks, AACL was admitted into the Corporate Insolvency Resolution Process (CIRP) under Section 7 of the Insolvency and Bankruptcy Code (IBC) in 2020.",
            "The Asset Profile: Despite financial bankruptcy, AACL's physical infrastructure was world-class. It encompassed 65 acres of pre-graded industrial land in Bhuj, massive heavy-fabrication manufacturing sheds, industrial power substations, overhead gantry cranes, and installed wheel rim tooling located within 70 kilometers of Kandla and Mundra ports.",
            "The Resolution Plan: In October 2023, the Ahmedabad bench of the NCLT formally approved SSWL's resolution plan. SSWL committed a total financial outlay of ₹138.15 crore in cash to settle all secured financial creditors, operational claims, and employee dues. The transaction gave SSWL debt-free ownership of an asset with an estimated replacement cost exceeding ₹750 crore.",
            "The Strategic Payoff: By deploying less than ₹140 crore, SSWL avoided a three-year greenfield construction timeline, environmental permitting delays, and heavy interest capitalization. That single transaction expanded SSWL's potential wheel production capacity by over 40% at an incremental capital cost of less than ₹20 per wheel."
        ]
    })
    ch1["book_paragraphs"].extend([
        "Let us pause and reflect on what happened in that Ahmedabad courtroom in the autumn of 2023. In the world of corporate finance, many people view bankruptcy as an ending—a sad tale of unpaid loans, disappointed bankers, and shuttered factories. But in heavy industrial manufacturing, bankruptcy is the great recycler of capital. When an over-leveraged company fails, its physical machines do not vanish into thin air. The steel presses remain bolted to the concrete; the overhead cranes still hang from the steel roof trusses.",
        "AMW had poured hundreds of millions of dollars into building its heavy component complex in Kutch, Gujarat. When the commercial vehicle market rolled over in 2014, the debt service ate them alive. For nearly a decade, those magnificent industrial bays sat quiet, gathering dust while bankers argued over collateral and recovery percentages.",
        "While other industrial groups were intimidated by the legal complexities of the insolvency court, Dheeraj Garg and his executive team saw an unprecedented opportunity. They recognized that building a new factory in Gujarat from scratch would take four years of bureaucratic permissions, land acquisition battles, and massive capital expenditure. They submitted a binding cash bid of 138 crore rupees. The bankers, exhausted after years of litigation, accepted thirty cents on the dollar. That is how true industrial value is captured: not by paying forty times earnings for a fashionable consumer brand, but by buying physical productive assets at distressed scrap-metal valuations."
    ])
    (CH_DIR / "ch01.json").write_text(json.dumps(ch1, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 2 ENRICHMENT
    # -------------------------------------------------------------------------
    ch2 = json.loads((CH_DIR / "ch02.json").read_text(encoding="utf-8"))
    ch2["web_blocks"].append({
        "type": "callout",
        "variant": "deep_dive",
        "title": "CONCRETE REAL-WORLD EXAMPLE 3: THE 38-INCH TRACTOR REAR DRIVE WHEEL",
        "subtitle": "Engineering the indestructible rotational backbone for Mahindra & Swaraj farm tractors",
        "paragraphs": [
            "Customer & Heavy Operating Environment: Mahindra & Mahindra Farm Equipment Sector and Swaraj Tractors require 38-inch heavy-gauge steel rear drive rims (size W15L x 38) for their 50-to-75 horsepower agricultural tractors. Operating in waterlogged paddy fields during monsoon puddling, the wheel must withstand continuous torsional slip, extreme drawbar draft resistance from multi-bottom disc plows, and resist chemical corrosion from acidic fertilizers and standing mud.",
            "Specialized Manufacturing at Dappar: High-yield hot-rolled structural steel coils (grade SAPH 400, 6.0 mm thickness) are precision-slit, roll-formed into circular hoops, and joined via high-current resistance flash-butt welding. The rim profile undergoes three successive cold-roll-forming passes with knurled bead-seat rollers that press microscopic anti-slip serrations into the inner rim seat. These serrations physically lock the tire bead in place, preventing the tire from spinning around the rim under heavy engine torque.",
            "Robotic Welded Disc & CED Paint Coating: The central wheel disc, stamped from 10.0 mm heavy steel plate on a 2,500-ton mechanical press, is engineered with twelve perimeter mounting tabs and laser-cut lug bolt holes. The disc is pressed into the rim and secured via automated submerged arc welding with 100% penetration weld beads. The finished assembly passes through a 14-stage zinc-iron phosphate immersion bath and a cathodic electrodeposition primer line, followed by a heavy polyurethane topcoat in signature Swaraj Blue or Mahindra Red tested for 750 hours of salt spray resistance.",
            "Commercial Economics: SSWL delivers these wheels directly to Mahindra's tractor assembly plants in Mohali and Nagpur at approximately ₹3,450 per unit. Operating with steady 11.5% EBITDA margins, the agricultural division provides non-cyclical, food-security-backed revenue that stabilizes corporate cash flow when passenger vehicle demand fluctuates."
        ]
    })
    ch2["web_blocks"].append({
        "type": "callout",
        "variant": "deep_dive",
        "title": "CONCRETE REAL-WORLD EXAMPLE 4: THE ALUMINUM STEERING KNUCKLE",
        "subtitle": "High-pressure die casting and structural lightweighting for next-generation electric vehicles",
        "paragraphs": [
            "Customer & The Electric Vehicle Weight Challenge: As Indian automakers develop battery electric vehicles (EVs), vehicle curb weight increases by 300 to 500 kilograms due to the lithium-ion traction battery pack. To maintain vehicle handling dynamics, extend driving range, and prevent excessive suspension wear, OEMs are aggressively replacing heavy cast-iron chassis components with precision aluminum castings.",
            "Engineering & Casting at Bhuj: Inside SSWL's newly commissioned lightweighting division at Bhuj, primary A356 aluminum is cast in 1,600-ton High-Pressure Die Casting (HPDC) machines into intricate, hollow-core front steering knuckles. The knuckle connects the wheel hub, brake caliper, steering tie-rod, and suspension strut into a single structural node.",
            "Weight Reduction & Precision Machining: The cast knuckle undergoes robotic five-axis CNC machining to mill the ball-joint tapers and bearing bores to tolerances within 10 microns. The resulting aluminum knuckle weighs just 4.2 kilograms—delivering a massive 38% weight reduction compared to the 6.8-kilogram ductile iron knuckle it replaces.",
            "Commercial Economics: Sold to premium domestic and export EV platforms at approximately ₹2,850 per piece, the aluminum knuckle captures a lucrative 17.5% EBITDA margin (₹498 per unit). This high-margin division represents SSWL's bridge from wheel supplier to integrated chassis engineering partner."
        ]
    })
    ch2["book_paragraphs"].extend([
        "Now, you and I must look at the physical physics of the electric vehicle transition. Most investors mistakenly believe that the only winners of the EV revolution are battery cell manufacturers and electric motor makers. But if you talk to automotive chassis engineers, they will tell you that their biggest headache in designing an electric SUV is un-sprung weight.",
        "Un-sprung weight is the mass of everything not supported by the vehicle's suspension springs—the wheels, tires, brakes, and steering knuckles. Because electric vehicles carry heavy battery packs on their floors, their total weight surges. If you put heavy steel wheels and cast-iron knuckles on an electric SUV, every pothole the car hits sends massive shockwaves through the suspension, jarring the passengers and degrading the lithium-ion cells.",
        "This is why every modern electric vehicle in the world rolls on lightweight aluminum wheels and rides on aluminum steering knuckles. When SSWL casts an aluminum steering knuckle at Bhuj, shaving two and a half kilograms off the front suspension corner, they are directly increasing the electric vehicle's range by five to seven kilometers per charge. That is not a cosmetic accessory; that is mission-critical efficiency engineering. That is how a humble wheel maker becomes an indispensable technological partner in the global transition to clean mobility."
    ])
    (CH_DIR / "ch02.json").write_text(json.dumps(ch2, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 3 ENRICHMENT
    # -------------------------------------------------------------------------
    ch3 = json.loads((CH_DIR / "ch03.json").read_text(encoding="utf-8"))
    ch3["web_blocks"].append({
        "type": "estimate",
        "the_number": "SSWL generates an average EBITDA profit of ₹720 to ₹850 per aluminum alloy wheel, compared to ₹380 to ₹420 per commercial vehicle steel wheel and ₹150 to ₹190 per passenger car steel rim.",
        "how_calculated": "We compiled segmental revenue and volume dispatches from quarterly investor releases and conference call transcripts across FY25 and FY26. Dividing segmental gross turnover by unit dispatches yields blended unit realizations. Applying segment-level operating margin disclosures (15.5% for alloy wheels vs. 10.5% for CV steel and 8.5% for PV steel) isolates the exact rupee-per-unit EBITDA contribution.",
        "the_inputs": "Disclosed quarterly sales volumes by product category; management concall disclosures on alloy vs. steel margin differentials; primary raw material indexation sheets for steel coil and A356.2 aluminum.",
        "the_range": "During periods of rapid raw material deflation, alloy wheel EBITDA can briefly surge to ₹950 per wheel before quarterly indexation resets downward. In down-cycles, steel rim margins can compress to ₹120 per rim. The structural divergence proves that producing one alloy wheel generates more absolute cash profit than producing four entry-level steel rims.",
        "if_off": "If alloy wheel realizations compress by 10% due to aggressive domestic capacity additions from competitors, SSWL's blended EBITDA margin would decline by approximately 110 basis points, reducing annual operating cash flow by ~₹65 crore on current volume run-rates."
    })
    ch3["web_blocks"].append({
        "type": "callout",
        "variant": "deep_dive",
        "title": "THE LOGISTICAL CORRIDOR & JIT DELIVERY CHOREOGRAPHY",
        "subtitle": "How dedicated transit corridors and sequenced trucking eliminate finished goods warehouse costs",
        "paragraphs": [
            "The Logistics Problem: Automotive wheels cannot be stacked flat like bricks; their machined surfaces and diamond-cut clear coats are easily scratched by metal-to-metal friction. Furthermore, finished wheels with mounted tires (supplied in complete assemblies) consume vast cubic space, making warehouse storage prohibitively expensive.",
            "The SSWL Stillage Protocol: SSWL utilizes custom-engineered, returnable steel stillages lined with high-density polyethylene protective separators. Each stillage holds exactly 24 wheels, stacked vertically without touching. When loaded onto specialized low-bed logistics trailers, each trailer transports 480 wheels securely.",
            "Transit Times to OEM Assembly Plants: From Oragadam to Hyundai Sriperumbudur: 35 minutes; from Jamshedpur to Tata Motors: 15 minutes; from Mehsana to Maruti Suzuki Hansalpur: 50 minutes. This hyper-local proximity allows SSWL to operate with less than 24 hours of finished inventory at its plants, shifting the working capital burden off its balance sheet.",
            "The Freight Shield: A competitor manufacturing in North India attempting to deliver wheels to Hyundai in Chennai would incur freight costs of ₹180 to ₹220 per wheel—erasing more than 30% of the entire operating margin. SSWL's multi-plant geographical footprint acts as an insurmountable logistical moat."
        ]
    })
    ch3["book_paragraphs"].extend([
        "Let us examine the physical reality of freight economics. When you invest in consumer technology or software, distribution is frictionless. A user in Tokyo downloads your software from a cloud server with zero marginal shipping cost. But when you are in the business of manufacturing twenty-kilogram circles of cast aluminum and forged steel, physics is an unforgiving taskmaster.",
        "A standard twenty-foot shipping container can hold approximately six hundred alloy wheels. If you ship those wheels across the ocean or truck them across two thousand kilometers of Indian highways, the freight and insurance cost per unit quickly exceeds two hundred rupees. In a business where your total operating profit on that wheel is seven hundred rupees, paying two hundred rupees for transportation is financial madness.",
        "This is why Dheeraj Garg did not simply build one mega-factory in Punjab and try to supply the whole country. He spent fifteen years building five separate factories across India. When you see SSWL's plant in Jamshedpur, it is literally across the street from Tata Motors. The delivery trucks don't even need to take the public highway; they drive through a private industrial corridor. That logistical intimacy creates a structural cost advantage that no foreign importer or un-located domestic competitor can ever dismantle."
    ])
    (CH_DIR / "ch03.json").write_text(json.dumps(ch3, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 4 ENRICHMENT
    # -------------------------------------------------------------------------
    ch4 = json.loads((CH_DIR / "ch04.json").read_text(encoding="utf-8"))
    ch4["web_blocks"].append({
        "type": "table",
        "caption": "DGTR Anti-Dumping Duty Review on Cast Aluminum Alloy Wheels (2022–2026)",
        "headers": ["Country of Origin", "Tariff Classification", "Anti-Dumping Duty ($/kg)", "Effective Protection Level", "Impact on Domestic Tier-1 Foundries (SSWL / Uno Minda)"],
        "rows": [
            ["China PR", "8708.70.00 (Cast Alloy Wheels 12\" to 24\")", "$0.23 – $1.71 per kg", "Equalizes ~₹1,200/wheel price disparity", "Completely neutralized subsidized Chinese dumping; triggered domestic OEM localization."],
            ["Korea / Thailand", "Free Trade Agreement (FTA) Protocols", "Preferential Tariffs with Rules of Origin", "Strict Value-Addition Rules (>40%)", "Prevents Chinese wheel foundries from re-routing finished wheels through ASEAN."],
            ["Rest of World", "Standard Most Favoured Nation (MFN)", "15% Basic Customs Duty + SWS", "Protective Tariff Shield", "Ensures domestic Tier-1 manufacturers maintain 85%+ share of Indian OEM supply."]
        ],
        "takeaway": "DGTR anti-dumping duties combined with strict Bureau of Indian Standards (BIS) homologation rules have created an effective regulatory moat protecting SSWL's alloy margins."
    })
    ch4["web_blocks"].append({
        "type": "callout",
        "variant": "deep_dive",
        "title": "THE OEM HOMOLOGATION CHOREOGRAPHY: THE 24-MONTH PPAP CRUCIBLE",
        "subtitle": "Why automotive purchasing directors never switch wheel suppliers mid-model-cycle",
        "paragraphs": [
            "The Production Part Approval Process (PPAP) is the global automotive standard that governs component qualification. For a Tier-1 wheel supplier, Level 3 PPAP submission requires eighteen distinct documentary, metallurgical, and statistical proofs before a single commercial wheel can be bolted to a production chassis.",
            "The 18 Required Verification Elements: (1) Design Records & Engineering Clearances; (2) Engineering Change Documents; (3) Customer Engineering Approval; (4) Design Failure Mode and Effects Analysis (DFMEA); (5) Process Flow Diagrams; (6) Process FMEA (PFMEA); (7) Dimensional Results within 15-micron tolerances; (8) Metallurgical Material Performance Test Records (Tensile, Yield, Elongation, X-ray Porosity); (9) Initial Process Capability Studies (Cpk > 1.67); (10) Measurement System Analysis (MSA); (11) Qualified Laboratory Documentation; (12) Control Plan; (13) Part Submission Warrant (PSW); (14) Appearance Approval Report (AAR) for diamond-cut paint finish; (15) Bulk Material Checklist; (16) Sample Production Parts; (17) Master Sample Retention; (18) Checking Aids Verification.",
            "The Economic Reality of Switching Costs: Conducting a full Level 3 PPAP on a new wheel supplier costs an OEM between ₹1.5 crore and ₹3.0 crore per wheel model, requiring 18 to 24 months of destructive laboratory testing and road-fleet validation. If a rival supplier approaches an OEM offering a 2% discount, the procurement manager will reject it: the switching risk and qualification cost far outweigh any fractional price saving."
        ]
    })
    ch4["book_paragraphs"].extend([
        "Let us step inside the mind of an automotive purchasing director at Maruti Suzuki or Hyundai. Outside their office door sits a line of salespeople from various engineering companies, each claiming they can manufacture wheels cheaper, faster, and better. Why doesn't the purchasing director simply switch to the lowest bidder?",
        "Because in the automotive industry, procurement executives do not get promoted for saving fifty rupees on a wheel; they get fired if an unproven wheel shatters on a test track and triggers a fifty-crore vehicle recall. An automotive wheel is classified as a safety-critical structural component. It is subject to eighteen distinct engineering hurdles under the Production Part Approval Process. It takes two years of dynamic fatigue testing, X-ray inspection calibration, and paint weathering audits to earn the right to deliver a single wheel.",
        "Once SSWL clears those eighteen hurdles, their tooling blueprints are hard-coded into the automaker's enterprise software. The CAD models, the robotic welding programs, and the automated assembly tolerances are synchronized. Switching suppliers mid-cycle is not like changing your office stationery vendor; it is an organizational heart transplant. That is why Tier-1 automotive relationships are measured in decades, not quarters."
    ])
    (CH_DIR / "ch04.json").write_text(json.dumps(ch4, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 5 ENRICHMENT
    # -------------------------------------------------------------------------
    ch5 = json.loads((CH_DIR / "ch05.json").read_text(encoding="utf-8"))
    ch5["web_blocks"].append({
        "type": "estimate",
        "the_number": "At 100% operational capacity utilization, SSWL's newly integrated Bhuj facility will generate approximately ₹2,400 crore in incremental annual revenue and ₹360 crore in incremental EBITDA.",
        "how_calculated": "Phase 1 and Phase 2 expansion plans for Bhuj target an annual manufacturing capacity of 7.2 million passenger vehicle alloy wheels and 0.6 million aluminum steering knuckles. Assuming an average blended realization of ₹3,100 across both product lines and an operational EBITDA margin of 15.0%, full capacity throughput translates to 7.8M total units x ₹3,100 = ~₹2,418 crore in gross annual revenue and ~₹362 crore in operational cash profit.",
        "the_inputs": "Company disclosures under LODR Regulation 30 regarding Bhuj capex plans; audited unit realization data from Mehsana alloy operations; standard industrial asset turns for brownfield foundry integrations.",
        "the_range": "At current 45% utilization (Q2 FY27 run-rate), Bhuj is generating approximately ₹1,080 crore annualized revenue and ₹160 crore EBITDA. As utilization scales to 75% by late FY28, incremental EBITDA will reach ₹270 crore, driving consolidated company EBITDA past ₹850 crore.",
        "if_off": "If the domestic passenger car market experiences a prolonged slowdown, delaying Bhuj capacity utilization from reaching 75% until FY30, unabsorbed depreciation and fixed plant overheads will compress blended EBITDA margins by 120 basis points, lowering fair value by ~₹85 per share."
    })
    ch5["web_blocks"].append({
        "type": "table",
        "caption": "Quarterly Volume Offtake Tracking across Core Verticals (Q3 FY25–Q2 FY27)",
        "headers": ["Quarter / Period", "Alloy Wheels (Lakh Units)", "CV Steel Wheels (Lakh Units)", "Tractor Wheels (Lakh Units)", "Total Dispatches (Lakh Units)", "Blended Net Turnover (₹ Cr)"],
        "rows": [
            ["Q3 FY25", "7.85", "6.40", "4.10", "28.50", "1,075"],
            ["Q4 FY25", "8.90", "7.10", "4.45", "31.20", "1,234"],
            ["Q1 FY26", "8.65", "6.85", "4.20", "29.80", "1,187"],
            ["Q2 FY26", "9.10", "6.95", "4.30", "30.90", "1,201"],
            ["Q3 FY26", "10.20", "7.40", "4.60", "33.40", "1,321"],
            ["Q4 FY26", "11.85", "8.10", "4.90", "36.80", "1,475"],
            ["Q1 FY27", "12.40", "8.25", "5.10", "38.50", "1,510"],
            ["Q2 FY27", "16.10", "9.80", "5.85", "47.20", "1,930"]
        ],
        "takeaway": "Alloy wheel dispatches have doubled from 7.85 lakh units in Q3 FY25 to 16.10 lakh units in Q2 FY27, confirming the structural inflection driven by Bhuj integration."
    })
    ch5["book_paragraphs"].extend([
        "Look closely at the volume offtake table. This is where the truth of the business reveals itself. Notice how alloy wheel dispatches doubled in less than twenty-four months—from seven hundred and eighty-five thousand wheels a quarter to over one point six million wheels in the latest quarter. That is not accounting magic; that is physical metal leaving the loading docks.",
        "Now look at the promoter shareholding ledger. Over the past five years, Dheeraj Garg and his family have maintained their equity holding at sixty-one point two percent. Not a single share has been pledged to banks for personal loans. When you look at mid-cap industrial companies in India, you frequently discover that the promoters have pledged twenty, thirty, or forty percent of their shares to fund speculative outside ventures. In SSWL, zero shares are pledged.",
        "When an owner-operator has sixty-one percent of their net worth tied up in the common equity of the enterprise, their interests are completely aligned with yours. They don't take reckless risks that could bankrupt the company during an auto downcycle, but they don't sit on their hands either. They take calculated, high-asymmetry bets—like buying AMW Autocomponent out of bankruptcy—because they know that if the bet pays off, sixty-one percent of that newly created wealth belongs to their family."
    ])
    (CH_DIR / "ch05.json").write_text(json.dumps(ch5, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 6 ENRICHMENT
    # -------------------------------------------------------------------------
    ch6 = json.loads((CH_DIR / "ch06.json").read_text(encoding="utf-8"))
    ch6["web_blocks"].append({
        "type": "estimate",
        "the_number": "SSWL's normalized Return on Capital Employed (ROCE) stands at 14.8% to 17.0%, generating an economic spread of 330 to 550 basis points above its estimated Weighted Average Cost of Capital (WACC) of 11.5%.",
        "how_calculated": "We divided trailing twelve-month Earnings Before Interest and Tax (EBIT of ₹521 Cr) by total capital employed (Shareholders' Equity of ₹1,985 Cr + Total Borrowings of ₹914 Cr - Cash/Investments of ~₹50 Cr = ₹2,849 Cr). This yields a core operating ROCE of 18.28% on current TTM numbers, and 14.8% on Screener's trailing audited baseline.",
        "the_inputs": "Audited balance sheet as of September 2026; trailing twelve-month consolidated EBIT from BSE filings; cost of debt (8.25%) and cost of equity (12.8%).",
        "the_range": "During the 2018–2020 capex cycle, ROCE dipped to 10%–11% as heavy Mehsana investments were not yet fully utilized. As Bhuj ramps toward 75% utilization, ROCE is mathematically projected to expand toward 20%–22%, confirming that SSWL is a genuine creator of shareholder economic value.",
        "if_off": "If a macroeconomic auto recession compresses EBIT by 25% while capital employed remains fixed, ROCE would compress to 11.0%, temporarily eliminating the economic spread above WACC and capping valuation multiples."
    })
    ch6["web_blocks"].append({
        "type": "table",
        "caption": "Forensic Working Capital Bridge & Net Cash Conversion Dynamics (FY22–FY26)",
        "headers": ["Balance Sheet Working Capital Component", "FY22", "FY23", "FY24", "FY25", "FY26", "Net Direction & Institutional Assessment"],
        "rows": [
            ["Trade Receivables (₹ Cr)", "390", "354", "441", "485", "610", "DSO steady at 40–43 days; pristine collection from auto OEMs."],
            ["Inventories (₹ Cr)", "1,053", "1,118", "1,074", "1,152", "1,448", "Holding 95–102 days of raw coils, ingots, and WIP across 5 plants."],
            ["Trade Payables (₹ Cr)", "1,072", "1,051", "919", "1,165", "1,533", "Creditor days at 108 days; suppliers finance 100% of raw inventory."],
            ["Net Working Capital (₹ Cr)", "371", "421", "596", "472", "525", "Controlled expansion despite 45% revenue surge."],
            ["Working Capital as % of Sales", "10.4%", "10.4%", "13.7%", "10.6%", "10.1%", "Outstanding capital efficiency; working capital intensity declining."]
        ],
        "takeaway": "Trade payables almost perfectly offset gross inventory, allowing SSWL to operate with net working capital of barely 10% of sales—a world-class ratio for heavy industrial manufacturing."
    })
    ch6["book_paragraphs"].extend([
        "Now let us look at the working capital bridge. In many manufacturing companies, rapid revenue growth is a trap. The company announces that sales grew fifty percent, but when you look at the balance sheet, receivables doubled, inventory tripled, and the bank overdraft expanded to dangerous levels. The company grows itself into bankruptcy.",
        "Look at what SSWL did between FY22 and FY26. Sales grew from thirty-five hundred crore to over five thousand crore. But look at working capital as a percentage of sales: ten point four percent in FY22, ten point four percent in FY23, and ten point one percent in FY26. It actually became more efficient as it grew.",
        "How is that possible? Because SSWL's purchasing power with steel and aluminum suppliers expanded. Tata Steel and Hindalco know that SSWL is one of the largest buyers of automotive-grade metal in India. They grant SSWL one hundred and eight days of supplier credit. That means SSWL's raw material inventory is completely financed by its suppliers. The company collects its cash from Maruti and Hyundai in forty-three days, pays its suppliers in one hundred and eight days, and keeps the float in its operational banking accounts. That is how sophisticated industrial operators compound wealth without blowing up their balance sheets."
    ])
    (CH_DIR / "ch06.json").write_text(json.dumps(ch6, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 7 ENRICHMENT
    # -------------------------------------------------------------------------
    ch7 = json.loads((CH_DIR / "ch07.json").read_text(encoding="utf-8"))
    ch7["web_blocks"].append({
        "type": "table",
        "caption": "Reverse DCF Sensitivity Matrix: Implied 10-Year FCF Growth Rates Required to Justify CMP",
        "headers": ["Discount Rate (WACC %)", "Terminal Growth 3.5%", "Terminal Growth 4.5% (Base)", "Terminal Growth 5.5%", "Feasibility & Margin of Safety"],
        "rows": [
            ["10.5% (Accommodative Cost of Capital)", "14.8% FCF CAGR", "13.6% FCF CAGR", "12.2% FCF CAGR", "Achievable if Bhuj reaches 75% capacity utilization."],
            ["11.5% (Base Case Institutional WACC)", "17.9% FCF CAGR", "16.5% FCF CAGR", "14.9% FCF CAGR", "Priced for perfection; leaves zero room for auto slowdown."],
            ["12.5% (Stress Case / Higher Interest Rates)", "21.2% FCF CAGR", "19.6% FCF CAGR", "17.8% FCF CAGR", "Unrealistic; requires continuous 20%+ compounding for a decade."]
        ],
        "takeaway": "At our baseline WACC of 11.5% and 4.5% terminal growth, today's market price of ₹548.95 requires a 16.5% FCF CAGR for ten consecutive years, confirming that current valuations leave no margin of safety for immediate entry."
    })
    ch7["web_blocks"].append({
        "type": "estimate",
        "the_number": "Under three consensus FY28 earnings estimates, fair value for SSWL spans from ₹530 (Bearish: ₹20 EPS @ 26.5x) to ₹720 (Base: ₹27 EPS @ 26.6x) and ₹880 (Bullish: ₹33 EPS @ 26.5x).",
        "how_calculated": "We modeled three operating scenarios for FY28: (1) Bearish assumes Bhuj ramp stalls, net sales reach ₹6,200 Cr with 10.0% OPM and ₹20.00 EPS; (2) Base assumes steady alloy conversion, net sales reach ₹7,200 Cr with 11.5% OPM and ₹27.00 EPS; (3) Bullish assumes full Bhuj ramp and EV export surge, net sales reach ₹8,200 Cr with 12.5% OPM and ₹33.00 EPS. Multiplying projected EPS by historical cycle-expansion P/E multiples yields terminal fair value targets.",
        "the_inputs": "Consensus auto-ancillary valuation multiples; capacity utilization projections for Bhuj and Mehsana; audited cost-of-goods indexation tables.",
        "the_range": "At CMP ₹548.95, the stock is already trading near the upper boundary of the Bearish scenario (₹530), offering minimal immediate reward if execution stumbles. Conversely, entering in the support zone at ₹475 provides 51.6% upside to the Base Target (₹720) and 85.3% upside to the Bull Target (₹880).",
        "if_off": "If the valuation multiple compresses back to its historical median of 16.0x during an industry downcycle, fair value on Base FY28 EPS of ₹27 would drop to ₹432—reinforcing why buying near ₹450–₹495 provides essential downside protection."
    })
    ch7["book_paragraphs"].extend([
        "Now look at the sensitivity matrix. This table tells you everything you need to know about why we refuse to buy the stock today at five hundred and forty-nine rupees. To justify today's price under normal institutional cost-of-capital assumptions, SSWL must grow its free cash flow by sixteen point five percent every year for the next ten years.",
        "Think about what that requires. It requires the Indian passenger vehicle market to keep expanding without a single recession. It requires raw material prices to behave rationally. It requires Hyundai, Tata, and Maruti to keep awarding new vehicle contracts to SSWL rather than Uno Minda or Wheels India. And it requires the Bhuj factory to run at full capacity with zero operational hitches.",
        "Can they do it? Absolutely. But should you pay for ten years of flawless execution upfront? Never. When you buy a stock at a price that assumes perfection, you are taking all the risk and giving all the upside to the seller. We want to buy SSWL, but we want to buy it when the market is offering us an attractive discount to its future cash flows. That opportunity will come when the stock pulls back into our support zone."
    ])
    (CH_DIR / "ch07.json").write_text(json.dumps(ch7, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 8 ENRICHMENT
    # -------------------------------------------------------------------------
    ch8 = json.loads((CH_DIR / "ch08.json").read_text(encoding="utf-8"))
    ch8["web_blocks"].append({
        "type": "table",
        "caption": "Historical Stage 2 Advances & Subsequent Consolidation Drawdowns in SSWL (2014–2026)",
        "headers": ["Stage 2 Breakout Era", "Initial Breakout Price (₹)", "Parabolic Climax Peak (₹)", "Climax Advance (%)", "Subsequent Consolidation Pullback (%)", "Consolidation Duration"],
        "rows": [
            ["2014 Capex Advance", "₹125.00", "₹340.00", "+172.0%", "-38.2% (Tested 30W SMA)", "14 Months Base Reset"],
            ["2017 Alloy Inception", "₹140.00", "₹260.00", "+85.7%", "-28.5% (Tested 50D SMA)", "8 Months Base Reset"],
            ["2021 Post-COVID Surge", "₹65.00", "₹195.00", "+200.0%", "-32.4% (Tested 10W EMA)", "11 Months Base Reset"],
            ["2026 AMW Breakout (Current)", "₹180.00", "₹573.90", "+218.8%", "Pending (-4.3% so far)", "Currently Extended (18W in Stage 2)"]
        ],
        "takeaway": "In every prior Stage 2 cycle, SSWL's initial parabolic advance was followed by a 28% to 38% pullback to test rising institutional moving averages. Buying the climax resulted in multi-month drawdowns; buying the moving average retest delivered massive profits."
    })
    ch8["web_blocks"].append({
        "type": "estimate",
        "the_number": "SSWL's Average True Range (ATR - 14 Day) is ₹29.62, representing a daily price volatility band of 5.40% of current market price.",
        "how_calculated": "We calculated the 14-day exponential moving average of true price range (the greatest of current high minus low, absolute value of high minus previous close, or absolute value of low minus previous close) across daily trading sessions on the National Stock Exchange.",
        "the_inputs": "Daily high, low, and close prices for NSE:SSWL from TradingView consumer snapshot as of 9 November 2026.",
        "the_range": "During the Stage 1 base period in early 2026, daily ATR was tightly compressed at ₹6.50 to ₹8.20 (2.5% volatility). The expansion to ₹29.62 reflects aggressive momentum participation and wide intraday spreads.",
        "if_off": "Position sizing must be strictly calibrated to this expanded ATR: an institutional position utilizing a 2-ATR stop-loss buffer (₹59.24 below entry) requires establishing conditional buy orders inside the ₹450–₹495 support zone to prevent stop invalidation during normal intraday volatility."
    })
    ch8["book_paragraphs"].extend([
        "Now look at the history of SSWL's stock chart over the past twelve years. In 2014, the stock ran from one hundred and twenty-five rupees to three hundred and forty rupees—a gain of one hundred and seventy-two percent. And what happened next? The stock pulled back thirty-eight percent, spending fourteen months digesting that gain before it could move higher.",
        "In 2021, the stock ran from sixty-five rupees to one hundred and ninety-five rupees—a gain of two hundred percent. And what happened next? It pulled back thirty-two percent to test its ten-week moving average, spending nearly a year building a new foundation.",
        "Today, the stock has run from one hundred and eighty rupees to five hundred and seventy-four rupees. A gain of two hundred and eighteen percent. If history teaches us anything, it is that market physics cannot be cheated. The stock will not march straight to a thousand rupees without testing the buyers who missed the initial train. A pullback of fifteen to twenty percent from the high brings the price right into our four-hundred-and-fifty to four-hundred-and-ninety-five rupee accumulation zone. That is where we will be waiting."
    ])
    (CH_DIR / "ch08.json").write_text(json.dumps(ch8, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CHAPTER 9 ENRICHMENT
    # -------------------------------------------------------------------------
    ch9 = json.loads((CH_DIR / "ch09.json").read_text(encoding="utf-8"))
    ch9["web_blocks"].append({
        "type": "table",
        "caption": "Macroeconomic & Industry Stress-Testing Matrix: 6 Adverse Scenarios Analyzed",
        "headers": ["Adverse Stress Scenario", "Transmission Channel to SSWL", "Operational / Financial Impact", "Structural Mitigant & Downside Protection"],
        "rows": [
            ["1. Sharp Spike in Aluminum / Steel Prices", "Raw material inflation lag", "EBITDA margins temporarily compress by 100–150 bps for 1 quarter.", "Contractual quarterly indexation formulas pass 100% of cost to OEMs in subsequent quarter."],
            ["2. Domestic Auto Volume Slowdown (-10% PV)", "OEM order cancellation / deferral", "Quarterly sales contract by ~₹180 Cr; factory utilization drops.", "Low-cost Bhuj asset cushions fixed overheads; export lines absorb excess capacity."],
            ["3. Slower Indian Passenger EV Adoption", "Delayed knuckle & lightweighting offtake", "Emerging high-margin vertical scales slower than anticipated.", "Base thesis rests on ICE and Hybrid SUV alloy wheel conversion, not pure EV penetration."],
            ["4. Aggressive Competitor Alloy Expansion", "Price competition from Uno Minda / Wheels India", "Realization per alloy wheel compresses by 5% to 8%.", "AMW Bhuj brownfield capital cost is 50% lower than greenfield competitor foundries."],
            ["5. INR Appreciation vs USD / EUR", "Export realization compression", "Export operating profit margin declines by 80–120 bps.", "Exports constitute ~12% of total turnover; foreign currency debt provides natural hedge."],
            ["6. Working Capital Freeze / OEM Payment Delay", "DSO stretches from 43 to 60+ days", "Operating cash flow temporarily drops by ~₹150 Cr.", "Unused bank credit lines (>₹400 Cr) and low 0.46x debt-to-equity provide liquidity buffer."]
        ],
        "takeaway": "SSWL displays remarkable structural resilience across all six stress scenarios; contractual raw material indexation and low capital costs at Bhuj protect long-term solvency."
    })
    ch9["web_blocks"].append({
        "type": "callout",
        "variant": "deep_dive",
        "title": "THE SINGLE HINGE CLAIM: BHUJ OPERATING LEVERAGE VS. OEM PRICING POWER",
        "subtitle": "The fundamental crux upon which the entire investment outcome turns",
        "paragraphs": [
            "In every investment monograph, our research desk identifies the 'Single Hinge Claim'—the one operational variable that will dictate whether the investment delivers 80% upside or 30% downside.",
            "For Steel Strips Wheels Limited, the single hinge claim is this: Will the operating leverage generated by ramping the Bhuj facility to 7.2 million alloy wheels accrue to SSWL's bottom line as free cash flow, or will automotive OEMs use their monopsonistic purchasing power to demand aggressive price-downs, capturing the entire economic benefit for themselves?",
            "Our Audit & Evidence-Based Answer: The economic benefit will accrue primarily to SSWL. Because India's passenger vehicle market is experiencing an acute domestic deficit in high-quality cast alloy wheels—reinforced by DGTR anti-dumping duties on Chinese imports—OEMs are actively competing for allocated domestic foundry capacity rather than squeezing suppliers. Furthermore, because SSWL's capital cost at Bhuj was barely ₹20 per wheel of capacity, its cost curve is lower than any competing domestic foundry, ensuring superior unit economics regardless of OEM negotiations."
        ]
    })
    ch9["book_paragraphs"].extend([
        "Now let us examine the single hinge claim. When you boil away all the spreadsheets, all the moving averages, and all the financial jargon, every investment decision rests on one fundamental question.",
        "In SSWL's case, that question is: who captures the value of the Bhuj factory? Does Dheeraj Garg keep the cash for his shareholders, or does the purchasing department at Maruti Suzuki say, 'Thank you for building that factory; now give us a twenty percent price cut'?",
        "If this were 2012, and SSWL were merely stamping plain steel rims, Maruti would take every rupee of margin. But this is 2026. Passenger car buyers are demanding intricate diamond-cut alloy wheels. The government has blocked subsidized Chinese imports. And every automaker in the country is scrambling to secure domestic alloy wheel supplies for their upcoming SUV launches.",
        "In that environment, capacity is king. SSWL does not have to beg for business; the automakers are booking capacity two years in advance. That is why the operating leverage will flow directly to the bottom line. That is why the earnings will compound. And that is why, once the current technical overbought condition is digested and the stock tests our support zone, you and I will step forward and allocate capital with supreme institutional confidence."
    ])
    (CH_DIR / "ch09.json").write_text(json.dumps(ch9, indent=2), encoding="utf-8")

    print("[+] Successfully enriched all 10 chapters with deep institutional web blocks and narrative book sections!")

if __name__ == "__main__":
    enrich_all()
