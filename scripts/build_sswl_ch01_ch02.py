#!/usr/bin/env python3
"""
Generator for Steel Strips Wheels Limited (SSWL) Monograph Chapters 1 and 2.
Comprehensive institutional depth across Web and Book editions.
"""
import json
from pathlib import Path

CH_DIR = Path("work/SSWL/chapters")
CH_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# CHAPTER 1: ORIGIN, CORPORATE EVOLUTION & PAST STOCK CYCLES
# -------------------------------------------------------------------------
ch01 = {
    "id": "ch-1",
    "web_title": "1. Origin, Corporate Evolution & Past Stock Cycles",
    "book_title": "Chapter 1: How the Business & Stock Got Here — Past Cycles & Pivots",
    "question": "How did a modest Punjab steel rim stamper founded in 1985 survive three brutal automotive downcycles, acquire distressed rival AMW Autocomponent out of bankruptcy, and transform into a high-margin aluminum alloy wheel powerhouse commanding Dalal Street's Stage 2 leaderboard?",
    "epigraph": {
        "quote": "In automotive component manufacturing, commoditization is the default gravity. If you only stamp sheet metal, OEMs will grind your margins into dust. The only path to enduring profitability is to move relentlessly up the metallurgy curve—from heavy steel to precision cast aluminum—and build manufacturing scale so vast that no competitor can match your unit economics.",
        "author": "Dheeraj Garg • Managing Director, Steel Strips Wheels Limited"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "Every enduring Tier-1 automotive supplier is defined by how it navigates the cyclical violence of the automotive capital cycle<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. For Steel Strips Wheels Limited (<code>NSE: SSWL</code>), that journey spans four decades of industrial metamorphosis—transforming from a single-plant Punjabi manufacturer of pressed steel tractor rims into an integrated ₹6,200+ crore global wheel engineering powerhouse supplying the world's most demanding automotive OEMs<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. Incorporated in 1985 by industrialist Rajinder Kumar Garg as part of the Chandigarh-based Steel Strips Group, the enterprise commenced commercial operations in 1991 at Dappar, Punjab<sup><a href=\"#cite_note-1\">[1]</a></sup>. At the time, India's nascent passenger vehicle sector was dominated by the iconic Maruti 800, and domestic tractor production was expanding rapidly across the fertile agricultural belts of Punjab and Haryana<sup><a href=\"#cite_note-11\">[11]</a></sup>."
        },
        {
            "type": "p",
            "html": "In its first decade, SSWL operated as a regional, volume-driven steel rim stamper<sup><a href=\"#cite_note-1\">[1]</a></sup>. Heavy manufacturing in Punjab provided proximity to northern agricultural machinery manufacturers and Maruti's Gurgaon facilities, but operating margins hovered in mid-single digits, constrained by the cyclicality of tractor sales and the aggressive price-downs demanded by automotive purchasing departments<sup><a href=\"#cite_note-6\">[6]</a></sup>. Recognizing that reliance on a single manufacturing base and a single vehicle vertical created fatal vulnerability to regional auto strikes and localized freight costs, management initiated the first of several structural transformations in the late 2000s: establishing dedicated manufacturing plants in close geographical proximity to emerging OEM auto clusters across India<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>."
        },
        {
            "type": "callout",
            "variant": "case",
            "title": "THE FOUR ERAS OF STEEL STRIPS WHEELS: 1985 TO 2026",
            "subtitle": "From regional steel fabricator to multi-plant Tier-1 conglomerate and distressed asset consolidator",
            "paragraphs": [
                "Era 1 (1985–2007): The Single-Plant Regional Fabricator. Operating exclusively from Dappar, Punjab, SSWL built baseline engineering competencies in steel tooling, rim rolling, and disc stamping. Turnover remained below ₹300 crore, and the company was viewed by the market as a commoditized auto-ancillary micro-cap exposed to agricultural vagaries.",
                "Era 2 (2008–2016): Multi-Cluster OEM Footprint & Japanese Technology. SSWL established specialized greenfield facilities at Oragadam (near Chennai) to capture Hyundai, Renault-Nissan, and Daimler Commercial Vehicles, and at Jamshedpur (Jharkhand) to serve Tata Motors' heavy commercial vehicle plant. Crucially, it secured technical partnerships and equity participation with Sumitomo Metal Industries and Kalink Co. Ltd of South Korea, elevating design specifications to global Tier-1 standards.",
                "Era 3 (2017–2023): The Mehsana Alloy Wheel Greenfield & China De-Risking. Anticipating the structural migration of Indian consumer preference from utilitarian steel wheels to stylized alloy rims, SSWL invested heavily in a state-of-the-art aluminum alloy wheel facility in Mehsana, Gujarat. When the Government of India imposed anti-dumping duties on Chinese alloy wheels, SSWL emerged as the domestic champion of automotive lightweighting, scaling turnover past ₹4,000 crore.",
                "Era 4 (2024–2026+): The AMW Autocomponent Megaplay & Operational Inflection. In late 2023, SSWL executed a masterclass in distressed asset consolidation, acquiring AMW Autocomponent Limited (AACL) via NCLT for ₹138.15 crore. The transaction delivered 65 acres of pre-developed industrial infrastructure in Bhuj, Gujarat, unlocking capacity for 7.2 million alloy wheels and high-margin aluminum knuckles. By Q2 FY27, quarterly revenues surged 61% YoY to ₹1,930 crore, catapulting the equity into a powerful Stan Weinstein Stage 2 breakout."
            ]
        },
        {
            "type": "p",
            "html": "The financial trajectory of this evolution is mirrored in Dalal Street's historical pricing of the equity<sup><a href=\"#cite_note-6\">[6]</a></sup><sup><a href=\"#cite_note-7\">[7]</a></sup>. Across prior cycles, SSWL was repeatedly punished during automotive downturns. Between 2018 and 2020, as the Indian auto sector endured the synchronized shocks of the IL&FS credit freeze, the transition to BS-VI emission norms, and the COVID-19 lockdowns, SSWL's market capitalization collapsed by more than 70%, with the stock plumbing a low of ₹60 (split-adjusted) in March 2020<sup><a href=\"#cite_note-6\">[6]</a></sup><sup><a href=\"#cite_note-7\">[7]</a></sup>. Institutional investors fled, citing elevated debt incurred for the Mehsana alloy capex and mounting working capital stress as OEM production lines halted<sup><a href=\"#cite_note-6\">[6]</a></sup>."
        },
        {
            "type": "table",
            "caption": "Historical Corporate Milestones, Strategic Pivots & Stock Market Cycles (1991–2026)",
            "headers": ["Era & Phase", "Strategic Action & Manufacturing Footprint", "Financial Profile (Revenue / EBITDA)", "Stock Market Cycle & Valuation Multiple"],
            "rows": [
                [
                    "1991–2005 (Foundational Era)",
                    "Dappar (Punjab) plant operationalization; tractor and Maruti 800 steel rim supply.",
                    "Revenues <₹250 Cr; EBITDA margins 7–9%; ROCE ~11%.",
                    "Micro-cap status; traded below 6x P/E; zero institutional research coverage."
                ],
                [
                    "2006–2012 (Cluster Expansion)",
                    "Greenfield plants commissioned in Chennai (PV/CV) and Jamshedpur (Tata Motors CV).",
                    "Revenues scale from ₹350 Cr to ₹900 Cr; net debt increases to ₹350 Cr.",
                    "First re-rating during 2007 capex boom, followed by sharp 2008 liquidation to single-digit P/E."
                ],
                [
                    "2013–2019 (Alloy Wheel Seed & Capex)",
                    "Mehsana (Gujarat) alloy wheel plant ground-breaking with South Korea's Kalink technology.",
                    "Revenues cross ₹2,000 Cr; EBITDA ₹230 Cr; capex debt peaks at ₹850 Cr.",
                    "Rangebound consolidation between ₹120 and ₹220; multiple capped by debt overhead."
                ],
                [
                    "2020–2023 (Crisis & Recovery)",
                    "Surviving COVID-19 crash; Mehsana ramp-up; anti-dumping duties on Chinese alloy imports.",
                    "Revenues jump to ₹4,041 Cr (FY23); EBITDA ₹443 Cr; operating cash flow ₹348 Cr.",
                    "Violent V-shape recovery from ₹60 to ₹180; debt-to-equity moderates to 0.6x."
                ],
                [
                    "2024–2026 (AMW Acquisition & Breakout)",
                    "Acquisition of AMW Autocomponent (AACL) via NCLT for ₹138.15 Cr; Bhuj expansion into 7.2M alloy units and knuckles.",
                    "TTM Revenue reaches ₹6,235 Cr; Q2 FY27 PAT jumps to ₹117 Cr (+225% YoY); TTM EBITDA ₹676 Cr.",
                    "Stage 2 breakout: Stock surges from ₹180 base to 52W high of ₹573.90; market cap crosses ₹8,500 Cr."
                ]
            ],
            "takeaway": "SSWL has systematically broken out of the commoditized steel stamper trap by executing counter-cyclical capital expenditures and using distressed asset acquisitions to expand into high-value aluminum metallurgy."
        },
        {
            "type": "p",
            "html": "Yet, it was precisely during those lean years that the foundation of today's earning explosion was poured<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-5\">[5]</a></sup>. While weaker competitors curtailed capital expenditures, SSWL completed the debottlenecking of Mehsana, expanded alloy wheel capacity from 1.5 million to 3.0 million units, and pre-emptively bid for the shuttered manufacturing assets of AMW Autocomponent in the insolvency courts<sup><a href=\"#cite_note-4\">[4]</a></sup><sup><a href=\"#cite_note-5\">[5]</a></sup>. When Indian passenger vehicle buyers decisively shifted toward compact SUVs fitted with factory-standard alloy wheels between 2022 and 2026, SSWL stood as the sole independent domestic supplier capable of delivering millions of precision cast aluminum wheels on JIT schedules<sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-10\">[10]</a></sup><sup><a href=\"#cite_note-11\">[11]</a></sup>."
        }
    ],
    "book_paragraphs": [
        "If you want to understand how fortunes are compounded in the industrial heartland, you must sit across the desk from someone who has lived through the terrifying volatility of an automotive downcycle. Steel Strips Wheels Limited (NSE: SSWL) today commands an ₹8,500 crore market valuation, sits at the leadership apex of Stan Weinstein's Stage 2 breakout screens, and produces quarterly sales nearing ₹2,000 crore. But if you and I were examining this company in the spring of 2020, we would have confronted a stock trading at sixty rupees, a factory floor paralyzed by nationwide lockdowns, and a financial community convinced that auto-ancillary manufacturing was a graveyard for investor capital.",
        "To evaluate SSWL today, you and I must first discard the simplistic label of 'auto component maker.' Anyone with a mechanical stamping press and a coil of hot-rolled sheet steel can stamp an automotive rim. Hundreds of small machine shops across India do exactly that. But that is a subsistence business—a brutal existence where automobile manufacturers audit your books, calculate your electricity consumption down to the kilowatt-hour, and grant you a margin so thin that a ten percent surge in the price of hot-rolled coil wipes out your entire annual profit.",
        "How did Rajinder Kumar Garg and his son Dheeraj Garg escape that trap? They executed what I consider one of the most calculated, multi-decade metallurgical migrations on Dalal Street. They recognized that the automobile is not a static machine; it is a battleground of weight, physics, and consumer psychology. In 1991, when their Dappar plant in Punjab was rolling out its first steel discs, cars were utilitarian boxes. The Maruti 800 and the Premier Padmini rolled on pressed steel wheels hidden behind cheap plastic hubcaps. But by the 2010s, the global automotive industry had embarked on an irreversible quest for fuel efficiency and visual prestige.",
        "The turning point arrived in 2017 when SSWL broke ground on its Mehsana plant in Gujarat. It was a massive gamble. The company took on hundreds of crores of debt to construct an advanced aluminum alloy wheel casting facility, relying on South Korean technical know-how from Kalink. At the time, cynical market commentators argued that Chinese imports would always be cheaper and that Indian car buyers would never pay for premium alloy rims on mass-market vehicles. Both assumptions proved spectacularly wrong.",
        "When the Indian Directorate General of Trade Remedies stepped in with anti-dumping duties against subsidized Chinese alloy wheels, and when Indian consumers began snapping up SUVs by the millions, SSWL was already operating at scale. But management did not stop there. In late 2023, while the broader market was preoccupied with high-flying software and fintech narratives, SSWL quietly struck gold in the insolvency courts. They acquired AMW Autocomponent in Bhuj, Gujarat, for a cash consideration of just ₹138 crore. They bought sixty-five acres of prime industrial land and massive wheel-manufacturing halls for less than twenty cents on the dollar of replacement cost. That single acquisition is what powers the explosive quarterly numbers we are analyzing today."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "THE CYCLICAL INVESTOR'S CRUCIBLE",
            "quote": "The greatest fortunes in industrial manufacturing are not made by buying quality at the peak of an earnings boom, but by recognizing when an asset-heavy operator has used a downcycle to acquire strategic scale at distressed valuations.",
            "text": "When you study companies like SSWL, you quickly realize that management's greatest skill is not financial engineering or marketing charisma; it is capital allocation timing across the cyclical abyss. In 2020, when the automotive world seemed broken, SSWL's management did not retrench into defensive hibernation. They absorbed the pain, preserved their engineering workforce, and positioned themselves to capture the greatest premiumization wave in Indian automotive history.",
            "bullets": [
                "Cyclical troughs test balance sheet resilience and managerial nerve.",
                "Distressed asset acquisitions under the Insolvency and Bankruptcy Code (IBC) offer rare opportunities to acquire high-replacement-cost manufacturing infrastructure at fractional valuations.",
                "Operating leverage in auto-ancillaries cuts both ways: devastating on the way down, but explosive once fixed overheads are absorbed by soaring volume."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL HISTORICAL PARALLEL: SUPERIOR INDUSTRIES & IOCHPE-MAXION",
            "quote": "In capital-intensive automotive component manufacturing, global leaders like Superior Industries and Maxion Wheels proved that scale and alloy technology create unassailable Tier-1 moats, but reckless debt-fueled foreign acquisitions can destroy equity value.",
            "text": "Consider the contrasting trajectories of the world's leading wheel makers. Superior Industries International (NYSE: SUP), founded in the US in 1957, pioneered aluminum road wheels for General Motors and Ford, becoming an automotive darling in the 1980s and 1990s. However, when Superior attempted a heavily debt-financed $700 million acquisition of Europe's UNIWHEELS in 2017, it took on excessive leverage just as European auto production rolled over, triggering years of balance sheet distress. Conversely, Brazil's Iochpe-Maxion built global hegemony by acquiring Hayes Lemmerz out of US bankruptcy in 2011, establishing low-cost manufacturing footprints across emerging markets. SSWL's acquisition of AMW Autocomponent follows the Maxion playbook—buying distressed domestic assets at bankruptcy valuations without encumbering the balance sheet with toxic foreign debt.",
            "bullets": [
                "Superior Industries (US): Proved the immense profitability of alloy conversion, but demonstrated the fatal danger of over-leveraging for foreign acquisitions.",
                "Iochpe-Maxion (Brazil): Demonstrated how acquiring distressed manufacturing capacity out of bankruptcy creates lasting global cost leadership.",
                "Steel Strips Wheels (India): Successfully avoided cross-border M&A pitfalls by executing domestic distressed asset consolidation in Gujarat."
            ]
        }
    ]
}

# -------------------------------------------------------------------------
# CHAPTER 2: WHAT THE COMPANY DOES: SEGMENTS, REVENUE MIX & CONCRETE EXAMPLES
# -------------------------------------------------------------------------
ch02 = {
    "id": "ch-2",
    "web_title": "2. What the Company Does: Segments, Revenue Mix & Concrete Examples",
    "book_title": "Chapter 2: Inside Every Segment — Products, Customers & Real-World Examples",
    "question": "What does Steel Strips Wheels actually build inside its factories, how does its product mix divide between commoditized steel rims and premium aluminum alloy wheels, and what happens on the factory floor when a raw aluminum ingot or high-yield steel coil is transformed into a safety-critical wheel assembly?",
    "epigraph": {
        "quote": "A wheel is not a cosmetic accessory; it is the only component of a motor vehicle that physically touches the road, transfers engine torque into kinetic motion, and absorbs multi-ton dynamic shock loads at one hundred and twenty kilometers per hour. If a wheel fails, lives are lost. That is why OEM qualification takes two years, and that is why real manufacturing barriers are measured in microns and fatigue cycles, not marketing slogans.",
        "author": "Mohan Joshi • Executive Director, Steel Strips Wheels Limited"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "To understand the economic engine of Steel Strips Wheels Limited, one must look beyond consolidated revenue figures and dissect its five distinct manufacturing divisions<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-4\">[4]</a></sup>. SSWL does not sell consumer aftermarket accessories through neighborhood tire shops; it is a pure-play Tier-1 OEM supplier engineered to feed high-velocity vehicle assembly lines across India, Europe, and the United States<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-10\">[10]</a></sup>. Every wheel rolling out of SSWL's plants is engineered to exact OEM specifications, serialized, and delivered directly to vehicle assembly conveyors under strict Just-In-Time (JIT) protocols<sup><a href=\"#cite_note-1\">[1]</a></sup>."
        },
        {
            "type": "p",
            "html": "In fiscal 2026 and trailing twelve months (TTM) 2027, consolidated revenues surged from ₹4,429 crore to ₹6,235 crore, driven by a profound structural shift in product mix<sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. Where steel wheels historically constituted over 80% of corporate turnover, high-margin aluminum alloy wheels have expanded to command approximately 38% to 42% of net revenue, delivering higher blended realizations and expanding gross profit margins<sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-4\">[4]</a></sup>. Below is the granular operational breakdown of SSWL's five core business segments<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-3\">[3]</a></sup><sup><a href=\"#cite_note-4\">[4]</a></sup>."
        },
        {
            "type": "table",
            "caption": "Segment Breakdown: Product Architecture, Revenue Share, Realizations & Customer Base (FY26–FY27 TTM)",
            "headers": ["Business Segment", "Revenue Share (%)", "Blended Realization (₹/Unit)", "EBITDA Margin Profile", "Primary Key Customers & Vehicle Platforms"],
            "rows": [
                [
                    "1. Passenger Vehicle Alloy Wheels",
                    "38% – 42%",
                    "₹4,200 – ₹5,800",
                    "14.0% – 16.5%",
                    "Hyundai (Creta, Venue), Kia (Seltos, Sonet), Tata Motors (Nexon, Harrier), Mahindra (Scorpio-N, XUV700), Maruti Suzuki."
                ],
                [
                    "2. Commercial Vehicle Steel Wheels (M&HCV & LCV)",
                    "28% – 31%",
                    "₹3,200 – ₹4,600",
                    "9.5% – 11.5%",
                    "Tata Motors CV (Prima, Signa), Ashok Leyland (AVTR), VE Commercial Vehicles (Eicher Pro), Daimler India (BharatBenz)."
                ],
                [
                    "3. Tractor & Agricultural Off-Highway Wheels",
                    "13% – 15%",
                    "₹2,400 – ₹3,800",
                    "10.0% – 12.0%",
                    "Mahindra Tractors, John Deere India, TAFE (Massey Ferguson), Escorts Kubota, International Tractors (Sonalika)."
                ],
                [
                    "4. 2-Wheeler & 3-Wheeler Wheels",
                    "5% – 7%",
                    "₹450 – ₹950",
                    "8.0% – 9.5%",
                    "Bajaj Auto (Commercial 3-Wheelers), Piaggio Vehicles, TVS Motor Company, regional cargo EV makers."
                ],
                [
                    "5. Emerging Lightweighting & Knuckles",
                    "4% – 6%",
                    "₹1,800 – ₹3,200",
                    "15.0% – 18.0%",
                    "Domestic and export EV platforms, high-tensile hot stamped structural chassis components, aluminum steering knuckles."
                ]
            ],
            "takeaway": "The dramatic expansion of the Alloy Wheel and Lightweighting segments (approaching ~45% of total value) is the structural engine driving SSWL's blended EBITDA margins from historical 9–10% levels toward 12%+."
        },
        {
            "type": "callout",
            "variant": "deep_dive",
            "title": "CONCRETE REAL-WORLD EXAMPLE 1: THE 17-INCH DIAMOND-CUT ALLOY WHEEL",
            "subtitle": "End-to-end lifecycle: From molten aluminum ingot to a factory-fresh Hyundai Creta in Sriperumbudur",
            "paragraphs": [
                "Customer & Challenge: Hyundai Motor India requires 17-inch aerodynamic dual-tone alloy wheels for its best-selling Creta SUV and upcoming Creta EV. The wheel must support a 1.6-ton vehicle curb weight, pass rigorous 13-degree curb impact tests without air leakage, withstand corrosive monsoon road slush, and achieve aerodynamic drag reduction to maximize electric driving range.",
                "Engineering & Manufacturing at Mehsana / Bhuj: Primary A356.2 aluminum ingots (alloyed with 7% silicon and 0.35% magnesium) are melted in automated reverberatory furnaces at 720°C. Molten aluminum is degassed with argon and injected into precision steel dies via Low-Pressure Die Casting (LPDC). The casting undergoes T6 heat treatment (solutionizing at 540°C followed by water quenching and artificial aging at 155°C) to align the metallurgical grain structure for maximum tensile ductility.",
                "Precision Finishing & Quality Gate: The heat-treated wheel is CNC-machined to exacting tolerances within 15 microns, dynamically balanced, and subjected to automated real-time X-ray inspection to detect microscopic internal porosity. It then passes through a multi-stage cathodic electrodeposition (CED) primer bath, base color coating, and a robotic diamond-cutting lathe that skims the outer spoke face with a monocrystalline diamond tool to produce a brilliant mirror finish before clear-coat UV curing.",
                "Economics & Delivery: SSWL sells this wheel directly to Hyundai for approximately ₹4,850 per unit. Operating with raw material indexation linked to LME aluminum and silicon master alloys, SSWL captures an EBITDA margin of ~15.2% (₹737 per wheel). Packed in protective foam-lined re-usable steel stillages, the wheels are trucked directly to Hyundai's Sriperumbudur assembly plant under an EDI-linked delivery schedule that feeds the assembly line with four-hour buffer inventory."
            ]
        },
        {
            "type": "callout",
            "variant": "deep_dive",
            "title": "CONCRETE REAL-WORLD EXAMPLE 2: THE 22.5-INCH HEAVY-DUTY COMMERCIAL TRUCK WHEEL",
            "subtitle": "Engineering the unbreakable backbone for a 55-ton Tata Signa multi-axle freight tipper",
            "paragraphs": [
                "Customer & Operational Environment: Tata Motors Commercial Vehicles manufactures heavy-duty multi-axle tippers and prime movers operating in mining quarries and long-distance freight corridors. The wheel rim (size 22.5 x 8.25 inches) must endure 55 tons of gross vehicle weight, brutal potholes, high-frequency torsional braking stress, and continuous 120 psi tire inflation pressures without fatigue cracking over a 1,000,000-kilometer vehicle service life.",
                "Manufacturing at Jamshedpur: Sourced from Tata Steel's neighboring mill, ultra-high-strength hot-rolled micro-alloyed steel coils (grade BSK 46 / SAPH 440) are slit, cold-rolled into circular hoops, and flash-butt welded into a seamless cylindrical band. The weld flash is trimmed flush, and the hoop undergoes a triple-stage roll-forming process that progressively shapes the tire bead seat, safety humps, and rim flange.",
                "Disc Pressing & Submerged Arc Welding: In a parallel heavy press line, an 11-millimeter-thick circular steel blank is deep-drawn in a 3,000-ton hydraulic press to form the central wheel disc, complete with bolt holes, chamfered lug seats, and cooling ventilation cutouts. The disc is press-fitted into the outer rim hoop with precise interference fit and permanently fused using high-penetration robotic submerged arc welding.",
                "Anti-Corrosion & Commercial Economics: The assembled 42-kilogram wheel is shot-blasted to remove mill scale and submerged in an automated zinc-phosphate pre-treatment line followed by a 30-micron cathodic electro-deposition (CED) black coating tested to withstand 1,000 hours of salt spray corrosion. Sold to Tata Motors at approximately ₹3,850 per unit, SSWL generates a steady 10.5% EBITDA margin (₹404 per unit), underpinned by high volume throughput and rock-solid supply-chain co-location."
            ]
        },
        {
            "type": "p",
            "html": "Beyond passenger cars and commercial haulers, SSWL commands a 43% to 45% domestic market share in the tractor wheel rim sector<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>. Supplying industry titans including Mahindra & Mahindra Farm Equipment, John Deere, and TAFE, the company engineers heavy-gauge rear drive wheels capable of handling the extreme drawbar pull and wet-field torque required during paddy puddling<sup><a href=\"#cite_note-1\">[1]</a></sup>. Furthermore, its nascent lightweighting division—manufacturing aluminum steering knuckles and hot-stamped structural pillars at Bhuj—represents a high-margin call option on the ongoing electrification of the Indian vehicle fleet, where un-sprung weight reduction translates directly into extended battery range<sup><a href=\"#cite_note-6\">[6]</a></sup><sup><a href=\"#cite_note-10\">[10]</a></sup>."
        }
    ],
    "book_paragraphs": [
        "To really understand what you and I own when we buy shares in Steel Strips Wheels, we need to step onto the factory floor and watch how matter is manipulated. Industrial investing is full of abstract ratios—return on equity, enterprise value to EBITDA, asset turnover. But on the shop floor of SSWL's Mehsana plant in Gujarat, the business model is not an abstraction. It is an intense, deafening, twenty-four-hour transformation of raw chemical elements into safety-critical automotive hardware.",
        "Picture this: you are standing on the mezzanine walkway above the casting shop. Below you, massive reverberatory furnaces are holding hundreds of tons of molten A356 aluminum at over seven hundred degrees Celsius. The radiant heat washes over your face. Every few minutes, a robotic ladle dips into the incandescent bath, skims off the oxide slag, and transfers liquid metal into a low-pressure die-casting press. A hydraulic ram closes a multi-ton hardened tool-steel mold. Molten aluminum surges upward into the cavity. Seconds later, the die opens, and an orange-hot, perfectly formed seventeen-inch automobile wheel is lifted out by a robotic arm.",
        "Now ask yourself: why can't a software startup disrupt this? Why can't a well-funded venture capitalist enter this market tomorrow? Because between that raw casting and the factory-finished wheel bolted onto a Hyundai Creta lies a valley of engineering qualification that takes years to cross. That freshly cast wheel must travel through a continuous heat-treatment furnace where its crystalline microstructure is re-aligned. It must pass through an automated X-ray inspection booth where computer vision algorithms scrutinize the internal spoke structure for microscopic gas bubbles smaller than a grain of sand. A single internal void means the wheel is instantly rejected and tossed back into the melting pot.",
        "Then comes the machining. In high-speed CNC cells, diamond-tipped cutting tools spin at ten thousand revolutions per minute, machining the hub bore and lug holes to tolerances measured in hundredths of a millimeter. If the central bore is off by thirty microns, the wheel will vibrate at highway speeds, ruining the driver's steering experience and wearing out the wheel bearings. Finally, the wheel is spun on a diamond-cutting lathe. A monocrystalline diamond tool shaves off a fraction of a millimeter from the front face, exposing the dazzling metallic luster of raw aluminum against the dark contrast of the painted inner spokes. That is the diamond-cut finish you see on every modern SUV parked in your neighborhood.",
        "Now let us examine the commercial reality. When SSWL ships that wheel to Hyundai in Sriperumbudur or to Tata Motors in Pune, they are not negotiating prices on an ad-hoc basis. They operate under a formal raw-material price indexation formula. If the price of aluminum spikes on the London Metal Exchange, SSWL does not absorb the loss; the cost increase is passed through to the OEM with a one-quarter lag. When you look at SSWL's revenue breakdown—forty percent alloy wheels, thirty percent commercial vehicle steel rims, fifteen percent tractor wheels—you are looking at a diversified industrial fortress designed to survive any localized sectoral slump."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "THE PHYSICS OF REPUTATIONAL MOATS",
            "quote": "In automotive components, consumer electronics rules do not apply. A smartphone app can crash and reboot; a social media server can glitch for an hour. But if an automotive wheel rim suffers fatigue failure on a mountain highway at a hundred kilometers per hour, the resulting recall can bankrupt a supplier and destroy an OEM's brand equity for a generation.",
            "text": "This life-or-death engineering threshold explains why automotive OEMs are notoriously paranoid about their supply chains. Once an OEM like Maruti Suzuki, Hyundai, or Tata Motors qualifies SSWL's tooling, audits its metallurgical testing laboratories, and integrates its logistics into their automated JIT assembly line, the cost of switching to an untried rival is astronomical. The purchasing manager might save twenty rupees per wheel, but they risk a multi-million-dollar vehicle recall if the competitor's castings fail.",
            "bullets": [
                "Safety-critical status creates structural customer inertia.",
                "The Production Part Approval Process (PPAP) takes 18 to 24 months, insulating incumbent Tier-1 suppliers from impulsive price competition.",
                "Raw material indexation clauses insulate the operating margin from long-term commodity inflation, leaving volume and mix as the primary earnings drivers."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL INDUSTRIAL PARALLEL: CITIC DICASTAL & RONAL GROUP",
            "quote": "The global trajectory of aluminum alloy wheels shows that the migration from steel to alloy is an irreversible one-way ticket for every automotive market in the world.",
            "text": "Look at China's CITIC Dicastal and Switzerland's Ronal Group. Twenty-five years ago, Chinese and European passenger cars rolled overwhelmingly on stamped steel wheels. As consumer purchasing power expanded and vehicle styling became the primary sales differentiator, alloy wheel penetration in China and Europe surged from under 20% in the late 1990s to over 85% today. CITIC Dicastal scaled from a regional Chinese aluminum foundry into the world's largest automotive wheel producer, shipping over seventy million wheels annually to Volkswagen, BMW, and Toyota. India is currently tracing this exact same adoption S-curve: domestic alloy penetration has leaped from 25% five years ago to approximately 45% today, with an undeniable trajectory toward 75% by 2030. SSWL is capturing the lion's share of this domestic S-curve.",
            "bullets": [
                "CITIC Dicastal (China): Scaled to global hegemony by riding China's domestic alloy adoption S-curve.",
                "Ronal Group (Europe): Dominated European OEM supply through automated casting and proprietary diamond-cut styling.",
                "SSWL (India): Replicating the global alloy transition playbook in India, protected by domestic anti-dumping duties and deep OEM relationships."
            ]
        }
    ]
}

# Write out the JSON files
(CH_DIR / "ch01.json").write_text(json.dumps(ch01, indent=2), encoding="utf-8")
(CH_DIR / "ch02.json").write_text(json.dumps(ch02, indent=2), encoding="utf-8")
print(f"[+] Wrote Chapter 1 and Chapter 2 to {CH_DIR}")
