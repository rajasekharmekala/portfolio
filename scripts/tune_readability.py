#!/usr/bin/env python3
"""
Fix readability grade for primer, gate-exceptions, and ch04.
"""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from readability_check import fk_grade

SPINE_PATH = Path("work/BLISSGVS/spine.json")
CH04_PATH = Path("work/BLISSGVS/chapters/ch04.json")

# 1. Optimize Spine primer and gate_exceptions
spine = json.loads(SPINE_PATH.read_text(encoding="utf-8"))
spine["primer"] = (
    "Bliss GVS Pharma leads the global market in specialized suppository and pessary formulations. "
    "The company serves African pediatric malaria clinics and domestic contract partners like Sun Pharma and Mankind. "
    "On September 28, 2026, Anupam Rasayan acquired 50.07% controlling equity at ₹299 per share to expand Western contract exports. "
    "With Q2 FY27 sales reaching ₹313 crore on 26% EBITDA margins, we maintain a WAIT_FOR_SUPPORT verdict on our active 101 shares, "
    "holding with a stop at ₹490.65 while awaiting a low-volume support retest."
)
spine["gate_exceptions"] = [
    "PROMOTER SHARE PLEDGE DISCLOSURE: As of September 30, 2026, 95.77% of promoter equity is pledged to Catalyst Trusteeship Limited. This pledge covers 5,09,84,595 shares, or 47.95% of total company equity. It secures ₹300 crore of acquisition debentures issued by parent Anupam Rasayan. This debt reflects acquisition leverage rather than operating distress. However, it exceeds our 20% red-line rule and requires explicit disclosure.",
    "WORKING CAPITAL & RECEIVABLE DAYS DISCLOSURE: Consolidated debtor days stand at 204 days. Net trade receivables were ₹517.19 crore against FY26 revenue of ₹927.11 crore. Gross receivables reached ₹579.10 crore, with 62% past due. This reflects customary 180-to-240 day credit cycles in Sub-Saharan African pharmaceutical distribution.",
    "EXCHANGE SURVEILLANCE DISCLOSURE: Following a 325% price advance, the stock was placed under exchange surveillance. NSE and BSE applied Long Term ASM Stage IV and 100% trade-for-trade settlement effective July 2026."
]
SPINE_PATH.write_text(json.dumps(spine, indent=2, ensure_ascii=False), encoding="utf-8")
print("Updated spine.json primer and gate_exceptions")

# 2. Optimize ch04.json web_blocks
ch04 = json.loads(CH04_PATH.read_text(encoding="utf-8"))
for b in ch04["web_blocks"]:
    html_txt = b.get("html", "")
    if "competitive positioning is analyzed below" in html_txt:
        b["html"] = (
            "We analyze Bliss GVS Pharma's competitive position through Porter's Five Forces framework. "
            "The company holds an oligopolistic grip on suppository formulations across Sub-Saharan Africa. "
            "High manufacturing barriers and trusted brands protect its domestic and export contracts. "
            "However, Chinese exporters and local African import rules create fresh competitive pressure. "
            "We examine the durability of those competitive advantages."
        )
    elif "To ensure absolute analytical transparency" in html_txt:
        b["html"] = (
            "We provide primary links to verify every claim in this report. "
            "These sources include regulatory filings, credit ratings, and takeover documents. "
            "Readers can audit factory capacities, receivables, and takeover loan terms directly. "
            "The table below links to these primary public records."
        )
    elif "Achieving and maintaining European Union" in html_txt:
        b["html"] = (
            "Bliss GVS holds European Union EU-GMP certification for its Palghar plant. "
            "Under EU rules, non-sterile cleanrooms must maintain continuous Grade D air quality. "
            "Positive air pressure prevents dust from entering clean filling suites. "
            "Microbial testing must confirm fewer than 10 colony units per gram. "
            "This certification proves Palghar meets strict Western standards. "
            "It lowers the friction for European drug companies to outsource production."
        )
    elif "single greatest regulatory vulnerability" in html_txt:
        b["html"] = (
            "The primary regulatory risk facing Bliss GVS is African protectionist policy. "
            "In Nigeria, domestic pharmaceutical groups actively lobby for import bans. "
            "Local producers want tariffs on finished foreign medicines to boost domestic jobs. "
            "Because Bliss exports 92% of its goods from India, trade policy shifts are a key risk."
        )
    elif "In response to domestic lobbying" in html_txt:
        b["html"] = (
            "Nigeria has previously banned imports of simple oral tablets like paracetamol. "
            "However, local Nigerian plants cannot manufacture complex suppositories today. "
            "Even so, higher import tariffs remain a constant risk. "
            "Bliss manages this exposure by running local secondary packing lines in Lagos. "
            "Bulk goods are blistered and boxed locally, qualifying as regional products."
        )

CH04_PATH.write_text(json.dumps(ch04, indent=2, ensure_ascii=False), encoding="utf-8")
print("Updated ch04.json web_blocks")
