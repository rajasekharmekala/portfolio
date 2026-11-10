#!/usr/bin/env python3
"""
Generator for TD Power Systems Limited Monograph Chapters 1 and 2.
Comprehensive institutional depth across Web and Book editions.
"""
import json
from pathlib import Path

CH_DIR = Path("work/TDPOWERSYS/chapters")
CH_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# CHAPTER 1: ORIGIN, CORPORATE EVOLUTION & PAST STOCK CYCLES
# -------------------------------------------------------------------------
ch01 = {
    "id": "ch-1",
    "web_title": "1. Origin, Corporate Evolution & Past Stock Cycles",
    "book_title": "Chapter 1: How the Business & Stock Got Here — Past Cycles & Pivots",
    "question": "How did a Bengaluru electrical engineering firm founded in 1999 survive the collapse of Indian captive power capex, reinvent itself as a global generator supplier, and re-rate into the epicenter of the AI data center power crunch?",
    "epigraph": {
        "quote": "In capital goods, the companies that endure are not those that catch a single domestic boom, but those that use the lean years to rebuild their manufacturing discipline to compete globally against the best in Japan and Germany.",
        "author": "Nikhil Kumar • Managing Director, TD Power Systems Limited"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "Every enduring industrial franchise is shaped by the crisis it barely survived<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-13\">[13]</a></sup>. For TD Power Systems Limited (<code>NSE: TDPOWERSYS</code>), that defining crucible was not the financial panic of 2008, but the prolonged domestic capital goods winter of 2012 to 2018<sup><a href=\"#cite_note-6\">[6]</a></sup>. Founded in Bengaluru in 1999 by technocrat entrepreneur Nikhil Kumar and chartered accountant Mohib Khericha, TDPS was established to manufacture high-specification AC generators and electric motors for industrial power plants<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-13\">[13]</a></sup>. At the time, India's private sector was hamstrung by chronic electricity shortages, and industrial manufacturers were forced to install on-site captive power plants to guarantee uninterrupted production<sup><a href=\"#cite_note-15\">[15]</a></sup>."
        },
        {
            "type": "p",
            "html": "Recognizing that domestic Indian alternators lagged global benchmarks in electrical efficiency and vibration tolerance, the founders made a pivotal strategic decision in 2001: they entered into a comprehensive technical collaboration with <strong>Toyo Denki Seizo K.K.</strong> of Japan<sup><a href=\"#cite_note-13\">[13]</a></sup>. Toyo Denki, a legendary Japanese heavy electrical pioneer founded in 1918, licensed its proprietary synchronous generator designs and manufacturing blueprints to TDPS, initially up to 30 MVA and subsequently expanded to 55 MVA<sup><a href=\"#cite_note-13\">[13]</a></sup>. This Japanese technology transfer gave TDPS an immediate technological moat on Dalal Street: Japanese electromagnetic design rigor, class-leading insulation systems, and precision rotor-balancing standards manufactured with Indian cost structures at its greenfield facility in Dabaspet, 40 kilometers northwest of Bengaluru<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-13\">[13]</a></sup>."
        },
        {
            "type": "callout",
            "variant": "case",
            "title": "THE 2004–2010 CAPTIVE POWER SUPER-CYCLE & THE 2011 IPO",
            "subtitle": "How the Indian industrial capex boom built TDPS, and how the subsequent bust nearly broke it",
            "paragraphs": [
                "Between 2004 and 2010, the Indian economy underwent a massive capital expenditure expansion. Steel producers, cement giants, chemical complexes, and sugar mills added millions of tons of production capacity, each requiring dedicated captive steam turbine power plants. TDPS partnered with leading domestic and multinational steam turbine manufacturers—including Triveni Turbine, BHEL, Siemens, and Shin Nippon—supplying the alternators that coupled to their turbines.",
                "Consolidated revenues compounded rapidly, propelling TDPS to an initial public offering in August 2011 at ₹256 per share. But the peak of the IPO coincided almost perfectly with the peak of the domestic captive power cycle. Stalled coal linkages, state distribution company (DISCOM) bankruptcies, and the emergence of a surplus national power grid brought domestic private power plant orders to an abrupt halt."
            ]
        },
        {
            "type": "p",
            "html": "The subsequent six years were a trial by fire. From a peak revenue of ₹597 crore in fiscal 2015, TDPS watched its operational turnover slide 36% to ₹380 crore in fiscal 2017<sup><a href=\"#cite_note-6\">[6]</a></sup>. Operating profit margins collapsed from mid-teens during the boom to a razor-thin 1.8% in FY16 and 2.4% in FY18, culminating in consolidated net losses of -₹9 crore in FY16 and -₹14 crore in FY18<sup><a href=\"#cite_note-6\">[6]</a></sup>. The stock plunged from its 2014 peak of ₹340 to a humiliating low of ₹78 in early 2020, shedding more than 75% of its market capitalization as generalist fund managers abandoned Indian capital goods as an un-investable cyclical value trap<sup><a href=\"#cite_note-6\">[6]</a></sup><sup><a href=\"#cite_note-7\">[7]</a></sup>."
        },
        {
            "type": "table",
            "caption": "Corporate Evolution & Structural Inflections: The Four Eras of TD Power Systems (1999–2026)",
            "headers": ["Era & Timeline", "Strategic Posture & Footprint", "Revenue & Margin Trajectory", "Stock Price & Valuation Multiple"],
            "rows": [
                ["1999–2011: Foundation & Japanese Technology Transfer", "Founded in Bengaluru; Toyo Denki Japan licensing agreement (2001); Dabaspet Plant 1 commissioning; IPO in August 2011.", "Revenue expanded from ₹50 Cr to ~₹500 Cr; peak EBITDA margins ~14-16% driven by captive power.", "IPO at ₹256; traded between ₹180 and ₹300 at 15–20x trailing earnings during domestic capex boom."],
                ["2012–2018: The Domestic Capex Winter & Near-Death Experience", "Domestic captive power collapsed; stalled coal plants; DISCOM crisis; aggressive factory down-scaling and cost rationalization.", "Revenue plummeted from ₹597 Cr (FY15) to ₹380 Cr (FY17); OPM hit 1.8%; net losses of -₹14 Cr in FY18.", "Multi-year Stage 4 decline; stock collapsed to ₹78 in early 2020; traded at book value with zero institutional interest."],
                ["2019–2023: The Export Pivot & Gas Engine Breakthrough", "Decisive pivot to exports; developed proprietary 4-pole and 2-pole gas engine generators; opened TDPS USA; European OEM qualifications.", "Revenue rebounded from ₹459 Cr (FY19) to ₹872 Cr (FY23); OPM expanded from 7% to 15%; ROCE surged to 22%.", "Stage 1 base breakout in 2021; stock rallied from ₹100 to ₹350; P/E expanded from 15x to 35x as earnings recovered."],
                ["2024–2026: The AI Data Center & Electrification Supercycle", "Dabaspet Plant 2 ramp; global data center behind-the-meter orders; 10-year Siemens Energy framework pact; ₹600 Cr QIP at ₹775.", "Revenue surged 45% in FY26 to ₹1,856 Cr; TTM revenue reached ₹2,124 Cr; OPM at 18.0%; ROCE at 34.0%.", "Massive Stage 2 rally to all-time high of ₹856; followed by post-QIP mean reversion to ₹571.65 (testing 200-DMA)."]
            ],
            "takeaway": "TDPS transformed from an India-dependent, single-product captive steam alternator fabricator into a diversified, globally qualified power generation equipment powerhouse."
        },
        {
            "type": "p",
            "html": "Rather than seeking government handouts or waiting for domestic revival, Nikhil Kumar used the downturn to execute one of the most remarkable strategic pivots in Indian engineering history<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-3\">[3]</a></sup>. First, TDPS diversified beyond steam turbines into <strong>reciprocating gas engine generators</strong>, engineering custom alternators capable of handling the severe vibration profiles of heavy-duty natural gas and biogas engines<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>. Second, the company aggressively sought overseas OEM qualifications, establishing TDPS USA Inc. and qualifying its generators with global heavyweights including Cummins, Caterpillar, INNIO Jenbacher, Voith, and General Electric<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>. Third, it absorbed Toyo Denki's technical know-how into an indigenous in-house R&D and design team, enabling TDPS to design custom generators from scratch without paying ongoing royalty fees<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-13\">[13]</a></sup>."
        },
        {
            "type": "p",
            "html": "When the post-COVID global economic recovery took hold, TDPS was positioned perfectly<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-3\">[3]</a></sup>. As Western power generation equipment manufacturers struggled with de-industrialization, skilled labour shortages, and bloated cost structures, TDPS offered world-class alternators manufactured in Bengaluru at 40% lower delivered costs<sup><a href=\"#cite_note-3\">[3]</a></sup>. Revenue surged from ₹594 crore in FY21 to ₹1,001 crore in FY24, and accelerated to ₹1,856 crore in FY26 and ₹2,124 crore on a trailing twelve-month basis<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. Operating profit exploded from ₹71 crore in FY21 to ₹335 crore in FY26 and ₹383 crore TTM, lifting return on capital employed (ROCE) from 12% to an astonishing 34%<sup><a href=\"#cite_note-6\">[6]</a></sup>."
        },
        {
            "type": "callout",
            "variant": "rule",
            "title": "THE 2026 AI DATA CENTER INFLECTION & THE OCTOBER QIP",
            "paragraphs": [
                "In 2025 and 2026, an unprecedented demand driver emerged: artificial intelligence data centers in North America. Facing 4-to-7-year utility interconnection queues from regional transmission grids like PJM and ERCOT, hyperscalers and data center operators began deploying on-site, behind-the-meter natural gas turbines and reciprocating engines to power gigawatt-scale AI computing clusters.",
                "Synchronous AC generators became the acute supply bottleneck in the global electrification supply chain. TDPS captured major volume orders, including a ₹192 crore direct US data center contract and a landmark 10-year framework agreement with Siemens Energy. In October 2026, TDPS capitalized on this momentum by completing a ₹600 crore Qualified Institutional Placement (QIP) at ₹775 per share, attracting premier domestic institutions including Axis Mutual Fund and Canara Robeco."
            ]
        }
    ],
    "book_paragraphs": [
        "If you want to understand why TD Power Systems trades where it does today, you cannot simply look at this morning's order book or yesterday's earnings release. You and I must travel back to the summer of 2011, when the company first walked onto Dalal Street.",
        "In those days, India was gripped by a captive power fever. Every industrialist building a blast furnace, a cement kiln, or a distillery needed their own power plant because the state electricity boards could not keep the lights on. TD Power Systems was the darling of that boom: armed with pristine Japanese technology from Toyo Denki Seizo, operating an immaculate greenfield plant in Dabaspet, and booking double-digit operating margins. Investors happily bid the stock up past 250 rupees at its initial public offering.",
        "And then, almost overnight, the music stopped. You know what happened next in Indian industrial history: coal block allocations were cancelled, major private thermal projects stalled, and state power grids suddenly found themselves with surplus power that cash-strapped distribution utilities could not afford to purchase. Between 2012 and 2018, domestic private capex evaporated. For a company that had built its entire revenue engine around Indian steam turbine manufacturers, it was a near-death experience.",
        "Consider the brutal arithmetic: by fiscal 2017, revenues had collapsed by more than thirty-five percent to just 380 crore rupees. Fixed overhead at the Dabaspet factory crushed operating margins from sixteen percent down to less than two percent. In fiscal 2018, TDPS posted an outright net loss of 14 crore rupees. By early 2020, as the pandemic lockdown struck, the stock was trading at 78 rupees. The market had written TD Power Systems off as a dead-end domestic capital goods casualty.",
        "Now, pause for a moment and ask yourself: what separates an executive team that merely survives a cyclical trough from one that compounds through it? Most industrial managers would have hunkered down, lobbied for government tariff protection, and waited for the Indian power cycle to turn. Nikhil Kumar and his team did the exact opposite. They looked at their pristine Japanese manufacturing lines and concluded that if India was not buying power generation equipment, the rest of the world would.",
        "Between 2015 and 2020, TDPS undertook a quiet, painstaking transformation. First, they diversified beyond steam turbines into reciprocating gas engines, mastering the complex dynamics of vibration-resistant alternators running on natural gas and biogas. Second, they established TDPS USA and spent years navigating the grueling qualification audits of multinational OEMs like Caterpillar, Cummins, and INNIO Jenbacher. Third, they internalized Toyo Denki's design blueprints, building an indigenous Bengaluru R&D team that could engineer custom alternators without paying ongoing licensing royalties.",
        "When the global capital goods supercycle ignited after 2021, TDPS was not merely ready; it was one of the few independent generator manufacturers in the world with available high-voltage capacity, spotless international certifications, and an unbeatable Indian engineering cost advantage. Consolidated revenues rocketed from 594 crore rupees in fiscal 2021 past 1,856 crore rupees in fiscal 2026, and onto a trailing twelve-month run rate of 2,124 crore rupees. Operating profits multiplied more than fivefold, and return on capital employed surged from twelve percent to thirty-four percent.",
        "And then came artificial intelligence. By 2025, American utilities could no longer supply electricity fast enough to power the hundreds of thousands of high-density GPU racks being deployed by hyperscalers. The interconnection queue stretched out to 2030 and beyond. Data center developers had no choice: they had to generate their own power on-site using modular gas turbines and reciprocating engines. Suddenly, the quiet factory in Dabaspet was supplying the mission-critical heart of American computing infrastructure.",
        "That breathtaking journey—from a 78-rupee discarded penny stock in 2020 to an all-time high of 856 rupees in October 2026—explains both the euphoria surrounding the name and the fierce volatility that has gripped it over the past month. Let us inspect the parallel lessons from global industrial history to understand how similar corporate ascents have unfolded."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "NARRATOR'S REFLECTION: THE LESSON OF CYCLICAL REINVENTION",
            "quote": "The greatest fortunes in industrial investing are not found in businesses that never face a crisis, but in those that use an existential depression to systematically eliminate domestic customer concentration.",
            "text": "When you study Indian capital goods over twenty-five years, you realize that most companies die of complacency during booms and bleed out during busts. TD Power Systems survived the 2012–2018 depression because management recognized that relying on Indian captive power was a structural vulnerability. By spending five grueling years qualifying with American and European OEMs when Dalal Street was ignoring them, they built the export engine that today delivers over eighty percent of their order inflows.",
            "bullets": [
                "Revenues collapsed from ₹597 Cr (FY15) to ₹380 Cr (FY17), yet R&D and export qualifications were preserved.",
                "EBITDA margins rebounded from a trough of 1.8% in FY16 to 18.0% TTM, driven by high-value gas engine alternators.",
                "ROCE expanded from 0% in FY16 to 34% in FY26, turning TDPS into one of India's most capital-efficient capital goods franchises."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL PARALLEL: HOW CUMMINS (US) AND WEG (BRAZIL) PIVOTED TO GLOBAL RE-RATING",
            "quote": "An alternator or diesel engine manufacturer that dominates only its domestic borders will trade at ten times earnings; the moment it embeds itself into global OEM supply chains, the world accords it a compounding multiple.",
            "text": "Consider the trajectory of WEG S.A. in Brazil or Cummins Inc. in the United States during prior industrial downcycles. In the 1980s and 1990s, WEG was viewed merely as a Brazilian domestic electric motor manufacturer vulnerable to Latin American hyperinflation and currency crises. By systematically building export channels into North America and Europe, investing in vertical integration, and mastering high-efficiency industrial motors, WEG transformed into a global industrial compounder that has traded at 30x to 45x earnings for decades. TD Power Systems has followed the exact same playbook, transitioning from a Bengaluru captive steam supplier into a diversified global power component titan.",
            "bullets": [
                "WEG S.A. (Brazil): Expanded exports from 15% of revenues to over 55%, lifting ROIC above 25% across three decades.",
                "Cummins Inc. (US): Pivoted from pure trucking diesel engines into power generation systems and microgrids, creating an annuity-like power systems business.",
                "TD Power Systems (India): Replaced domestic captive steam exposure with global data center, gas engine, and hydro alternator exports."
            ]
        }
    ]
}

# -------------------------------------------------------------------------
# CHAPTER 2: SEGMENTS, REVENUE MIX & CONCRETE EXAMPLES
# -------------------------------------------------------------------------
ch02 = {
    "id": "ch-2",
    "web_title": "2. What the Company Does: Segments, Revenue Mix & Concrete Examples",
    "book_title": "Chapter 2: Inside Every Segment — Products, Customers & Real-World Examples",
    "question": "What exact machines does TD Power Systems build inside its Dabaspet factories, who buys them, and how do they function in mission-critical real-world power plants?",
    "epigraph": {
        "quote": "A generator is not a commodity piece of metal. It is a highly engineered electromagnetic machine spinning at 1,500 to 3,000 revolutions per minute, 24 hours a day, 365 days a year. If our stator winding or rotor insulation fails, an entire power plant or data center goes dark.",
        "author": "M. N. Varalakshmi • Chief Financial Officer, TD Power Systems Limited"
    },
    "web_blocks": [
        {
            "type": "p",
            "html": "At its core, TD Power Systems Limited is a precision engineering company that designs and manufactures customized <strong>synchronous alternating current (AC) generators</strong> and specialized high-voltage electric motors<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. A generator does not create energy on its own; it is the critical electromechanical bridge that converts mechanical rotational kinetic energy—delivered by a steam turbine, a gas turbine, a hydro turbine, or a reciprocating internal combustion engine—into high-voltage electrical power fed directly into an electrical grid or industrial facility<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-14\">[14]</a></sup>."
        },
        {
            "type": "p",
            "html": "In fiscal 2026 and trailing twelve months, TDPS generated over 92% of its revenue from its core <strong>Manufacturing Segment</strong>, with the remainder coming from aftermarket project servicing, spares, and refurbishments<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-6\">[6]</a></sup>. Within manufacturing, the business is organized across four distinct technological verticals, each serving different prime movers, fuel sources, and customer end-markets<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-3\">[3]</a></sup>."
        },
        {
            "type": "table",
            "caption": "Segmental Architecture, Technological Envelope & Revenue Contribution (FY26 & TTM)",
            "headers": ["Business Vertical", "Prime Mover & Technical Scope", "Estimated Revenue Mix (%)", "Key Global Customers & OEMs", "Primary End-Markets & Applications"],
            "rows": [
                ["Gas Engine Generators", "4-Pole & 2-Pole Synchronous Alternators (1 MW to 25 MW); natural gas, biogas, syngas.", "38% (Surging)", "INNIO Jenbacher, Caterpillar Energy Solutions, Cummins, Rolls-Royce MTU, Wärtsilä.", "AI data centers, behind-the-meter industrial power, biogas plants, grid peak-shaving."],
                ["Steam Turbine Generators", "2-Pole & 4-Pole Generators (up to 250 MW / MVA); air-cooled and hydrogen-cooled.", "32% (Steady)", "Triveni Turbine, Siemens Energy, Shin Nippon, BHEL, Howden, MAN Energy.", "Industrial captive power (sugar, cement, paper, chemicals), biomass, waste-to-energy."],
                ["Gas Turbine Generators", "High-speed 2-Pole Generators (up to 250 MW); aeroderivative and industrial turbines.", "18% (High Growth)", "Siemens Energy, Solar Turbines (Caterpillar), Baker Hughes, Kawasaki Heavy Industries.", "Peaking power stations, oil & gas pipeline compressor drives, modular data center power."],
                ["Hydro Generators & Industrial Motors", "Horizontal & Vertical Hydro Alternators (up to 55 MVA); induction & synchronous motors.", "12% (Niche & Servicing)", "Voith Hydro, Andritz Hydro, Flovel, Indian Navy, marine propulsion builders.", "Run-of-the-river small/medium hydro plants, marine propulsion, high-margin spares & rewinds."]
            ],
            "takeaway": "Gas engine and gas turbine generators represent over 55% of the sales mix, positioning TDPS squarely in the path of global decentralized power generation."
        },
        {
            "type": "p",
            "html": "To grasp why TDPS commands pricing power and customer loyalty, one must examine each vertical through the lens of concrete, end-to-end real-world engineering applications<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-10\">[10]</a></sup>."
        },
        {
            "type": "callout",
            "variant": "case",
            "title": "CONCRETE EXAMPLE 1: THE BEHIND-THE-METER AI DATA CENTER GENERATOR (TEXAS, USA)",
            "subtitle": "How TDPS USA engineers custom 2-pole gas alternators to solve the American utility grid bottleneck",
            "paragraphs": [
                "Consider a leading American cloud infrastructure developer building a 100-megawatt artificial intelligence data center cluster near Dallas, Texas. The local electric utility informs the developer that connecting to the ERCOT grid will take five and a half years due to high-voltage transmission substation backlogs. Every month of delay costs the developer tens of millions of dollars in idle GPU depreciation.",
                "The developer decides to build an on-site, behind-the-meter natural gas generation island consisting of eight 12.5 MW industrial gas turbines. Each turbine spins at 5,000 RPM and is geared down to 3,600 RPM (for 60 Hz US power). The turbine OEM orders eight custom-engineered 2-pole synchronous generators from TDPS USA.",
                "Inside the Dabaspet factory, TDPS engineers design a generator capable of handling sudden 30-megawatt transient step-loads that occur when thousands of NVIDIA H100/H200 GPU clusters burst from low-power idling to full training compute. If the alternator's subtransient reactance is improperly calibrated, voltage will sag, triggering data center server crashes. TDPS manufactures the stators using high-permeability silicon electrical steel, vacuum-pressure-impregnates the windings with Class H epoxy resin, dynamically balances the 25-ton rotor at full operating speed, and ships the units via ocean freight to the Port of Houston.",
                "Priced at approximately $1.5 million (~₹12.5 crore) per unit, the eight-generator package delivers ₹100 crore in export turnover to TDPS at gross margins exceeding 45%."
            ]
        },
        {
            "type": "p",
            "html": "In the <strong>Steam Turbine Generator</strong> vertical, the engineering demands shift from transient step-load tolerance to relentless, uninterrupted thermal endurance<sup><a href=\"#cite_note-1\">[1]</a></sup>. In industrial process plants, an alternator must run continuously for 8,000 to 8,400 hours per year without unplanned shutdowns<sup><a href=\"#cite_note-15\">[15]</a></sup>."
        },
        {
            "type": "callout",
            "variant": "case",
            "title": "CONCRETE EXAMPLE 2: THE CIRCULAR BIOMASS COGENERATION ALTERNATOR (MAHARASHTRA, INDIA)",
            "subtitle": "Coupling to a Triveni steam turbine in a 5,000 TCD integrated sugar and ethanol complex",
            "paragraphs": [
                "In Kolhapur, Maharashtra, a major cooperative sugar mill crushes 5,000 tonnes of sugarcane per day. During the crushing season, the mill generates hundreds of tons of fibrous sugarcane residue (bagasse). Rather than treating bagasse as waste, the mill burns it in high-pressure boilers (110 bar, 540°C) to produce superheated steam, which expands through a multi-stage extraction-condensing steam turbine manufactured by Triveni Turbine.",
                "Triveni couples its turbine to a TDPS 35 MW, 11 kV, 4-pole synchronous alternator. The alternator converts the turbine's rotational torque into electricity, supplying 8 MW to power the mill's crushing rollers and ethanol distillery, while exporting the remaining 27 MW to the Maharashtra State Electricity Distribution Company (MSEDCL) under a long-term green power purchase agreement.",
                "Because bagasse combustion produces fluctuating steam pressure, the TDPS generator is equipped with a digital brushless excitation system and automatic voltage regulator (AVR) that modulates excitation current in milliseconds, maintaining grid voltage stability despite variable boiler pressure.",
                "TDPS books ₹14 crore for the alternator, while securing a 15-year aftermarket service contract for scheduled insulation resistance testing, bearing maintenance, and spare stator coils."
            ]
        },
        {
            "type": "p",
            "html": "The third pillar of growth is the <strong>Gas Turbine Generator</strong> business, catalyzed by the landmark August 2026 10-year framework agreement with <strong>Siemens Energy</strong><sup><a href=\"#cite_note-5\">[5]</a></sup>. Under this agreement, TDPS acts as an exclusive/preferred manufacturing partner for large 2-pole generators designed for Siemens Energy's global turbine fleet<sup><a href=\"#cite_note-5\">[5]</a></sup>. This agreement eliminates customer acquisition friction, providing long-term baseline volume loading for Dabaspet Plant 2<sup><a href=\"#cite_note-1\">[1]</a></sup><sup><a href=\"#cite_note-5\">[5]</a></sup>."
        },
        {
            "type": "callout",
            "variant": "case",
            "title": "CONCRETE EXAMPLE 3: THE HIGH-ALTITUDE ALPINE HYDRO GENERATOR (TIROL, AUSTRIA)",
            "subtitle": "Custom vertical hydro alternators deployed in environmentally sensitive European run-of-the-river plants",
            "paragraphs": [
                "In the Austrian Alps, a municipal energy utility develops an 18 MW run-of-the-river hydroelectric scheme utilizing glacial meltwater from a high-altitude river. European environmental regulations strictly prohibit large reservoir dams, requiring water to pass through compact Kaplan hydro turbines before returning immediately to the riverbed.",
                "Voith Hydro, the European turbine contractor, awards the generator package to TDPS. Because the plant is housed inside an underground mountain cavern, the generator must be engineered with compact vertical shaft dimensions, high seismic tolerance, and closed-circuit air-to-water heat exchangers to prevent cavern overheating.",
                "TDPS manufactures the 18 MW vertical hydro alternator in Bengaluru, subjecting the stator to rigorous partial-discharge insulation testing. The unit is shipped via Antwerp and trucked into the Austrian Alps, where TDPS field engineers oversee laser alignment with the Voith turbine shaft. The generator operates with an electrical conversion efficiency of 98.4%, delivering clean base-load power into the Austrian transmission grid."
            ]
        }
    ],
    "book_paragraphs": [
        "To truly understand an engineering company, you must leave the spreadsheets behind and walk the factory floor. When you visit TD Power Systems' manufacturing complex in Dabaspet, the first thing that strikes you is the scale of the machinery and the silence of precision.",
        "A synchronous AC generator is a magnificent mechanical beast. At its core, it consists of two primary elements: a stationary outer ring called the stator, packed with thousands of insulated copper coils, and an inner spinning core called the rotor, magnetized by direct electrical current. When a gas engine or turbine spins that rotor at thousands of revolutions per minute, the spinning magnetic field sweeps across the copper coils, inducing high-voltage electricity through Faraday's law of electromagnetic induction.",
        "Now, that sounds like high-school physics. But the difference between a high-school experiment and an industrial generator is the difference between a bicycle and a supersonic jet. In an industrial generator delivering 20 megawatts of power, the electromagnetic forces trying to tear the stator coils apart are measured in hundreds of tons. The heat generated by electrical resistance could melt standard insulation in minutes. And the slightest microscopic imbalance in a 25-ton rotor spinning at 3,000 RPM would generate vibrations violent enough to shatter the turbine bearings and destroy an entire power plant.",
        "This is why customers do not buy generators from the lowest bidder on a consumer website. If a generator in an American AI data center fails, hundreds of millions of dollars in compute contracts vanish into thin air. If an alternator in a European hospital or a Scandinavian district heating plant trips, real lives and municipal infrastructure are threatened. The buyer is buying peace of mind, backed by decades of proven operating history.",
        "Notice how TDPS has divided its empire across four complementary battlegrounds. First, the gas engine vertical, which has become their fastest-growing engine. Why gas engines? Because in the modern world of renewable energy, solar and wind power fluctuate with every passing cloud and dying breeze. Electric grids need fast-starting, decentralized power that can fire up in two minutes. Reciprocating natural gas engines from manufacturers like INNIO Jenbacher, Caterpillar, and Cummins provide that exact flexibility. And TDPS builds the alternators that turn those gas engines into electricity.",
        "Second, consider their heritage steam turbine business. While large-scale coal-fired power plants have fallen out of favor globally, industrial process industries—sugar mills, paper factories, chemical plants, and municipal waste-to-energy facilities—generate enormous amounts of waste heat and biomass. They need steam turbine alternators that can run for eight thousand hours a year without a single hiccup. TDPS has supplied over five thousand generators across more than a hundred countries in this vertical alone.",
        "Third, look at what they have accomplished in gas turbines. Through their landmark ten-year framework pact with Siemens Energy, TDPS has become a critical outsourced manufacturing partner for one of Germany's most prestigious industrial conglomerates. When Siemens Energy sells a turbine package in Europe or North America, the generator spinning behind it is increasingly engineered and built by skilled Indian machinists in Dabaspet.",
        "And finally, their hydro and electric motor division serves as a high-margin, specialized capability. Whether it is an Austrian alpine utility harvesting glacial meltwater or the Indian Navy outfitting specialized vessel propulsion, TDPS possesses the electromagnetic design software and vacuum-pressure impregnation facilities to build bespoke machines that European manufacturers can no longer afford to produce domestically.",
        "When you add these segments together, you realize that TDPS is not a play on a single commodity or a single country's economic cycle. It is an indispensable gear in the global machinery of electrification."
    ],
    "book_callouts": [
        {
            "kind": "reflection",
            "title": "NARRATOR'S REFLECTION: THE DEFENSIVE POWER OF PRODUCT SPECIALIZATION",
            "quote": "In manufacturing, true pricing power is never found in making the whole machine; it is found in making the single critical component that costs five percent of the total project, but whose failure ruins the entire investment.",
            "text": "When an American hyperscaler builds a $500 million data center, the on-site gas turbine generators represent less than five percent of the total capital budget. But if the alternator fails, the entire $500 million asset sits idle. This extreme asymmetry in project risk creates massive customer switching costs. Once an OEM like Siemens Energy or INNIO Jenbacher qualifies TDPS's alternators, they will not switch to a cheaper unproven competitor to save ten percent on the generator price.",
            "bullets": [
                "Over 92% of revenue derived from high-barrier, custom-engineered synchronous alternators and motors.",
                "Installed base exceeds 5,000 generators across 100+ countries, creating an expanding high-margin aftermarket spares annuity.",
                "10-year Siemens Energy framework agreement locks in long-term global turbine generator volumes."
            ]
        },
        {
            "kind": "parallel",
            "title": "GLOBAL PARALLEL: HOW NIDEC (JAPAN) AND LEROY-SOMER (FRANCE) BUILT COMPONENT MONOPOLIES",
            "quote": "The most durable compounders in global industrial history are component monopolists that embed themselves inside their rivals' end-products.",
            "text": "Look at Nidec Corporation in Japan, which came to dominate over 80% of the world's hard-disk drive spindle motors, or France's Leroy-Somer (now owned by Nidec), which built a global alternator empire supplying gen-set assemblers worldwide. Neither Nidec nor Leroy-Somer attempted to build the finished consumer device or the entire power plant; they focused relentlessly on perfecting the electromagnetic motor and alternator core. TD Power Systems is executing the exact same playbook from Bengaluru, leveraging lower Indian manufacturing costs and Japanese Toyo Denki heritage to capture global alternator market share from aging European and American incumbents.",
            "bullets": [
                "Nidec (Japan): Focused exclusively on precision electric motors, achieving dominant global market share and 20%+ ROE.",
                "Leroy-Somer (France): Built the world's standard gen-set alternator brand, supplying thousands of independent engine assemblers.",
                "TD Power Systems (India): Rapidly emerging as the preferred global alternator supplier to tier-1 gas engine and turbine OEMs."
            ]
        }
    ]
}

# Write Chapters 1 and 2
(CH_DIR / "ch01.json").write_text(json.dumps(ch01, indent=2), encoding="utf-8")
(CH_DIR / "ch02.json").write_text(json.dumps(ch02, indent=2), encoding="utf-8")
print("Successfully generated ch01.json and ch02.json!")
