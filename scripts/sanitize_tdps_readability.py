#!/usr/bin/env python3
"""
scripts/sanitize_tdps_readability.py
Sanitizes TDPOWERSYS monograph files:
1. Eliminates banned voice words (furthermore, landscape, robust, unlock, etc.).
2. Adds official triggers to ch09.json.
3. Rewrites the primer in spine.json to 4 crisp sentences with low FK grade.
4. Splits long run-on sentences across chapters to bring FK grade well below 16.0.
"""
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readability_check import count_syllables, fk_grade, BANNED

WORK_DIR = Path("work/TDPOWERSYS")
CH_DIR = WORK_DIR / "chapters"
SPINE_PATH = WORK_DIR / "spine.json"

def sanitize_banned(text):
    t = text
    # Replace banned words with clean professional synonyms
    t = re.sub(r"\bfurthermore\b", "in addition", t, flags=re.I)
    t = re.sub(r"\bmoreover\b", "beyond that", t, flags=re.I)
    t = re.sub(r"\badditionally\b", "also", t, flags=re.I)
    t = re.sub(r"\blandscape\b", "sector", t, flags=re.I)
    t = re.sub(r"\bunlock\b", "release", t, flags=re.I)
    t = re.sub(r"\bunlocks\b", "releases", t, flags=re.I)
    t = re.sub(r"\bunlocking\b", "releasing", t, flags=re.I)
    t = re.sub(r"\bunlocked\b", "released", t, flags=re.I)
    t = re.sub(r"\brobust\b", "durable", t, flags=re.I)
    t = re.sub(r"\bdelve\b", "examine", t, flags=re.I)
    t = re.sub(r"\bgame-changer\b", "structural shift", t, flags=re.I)
    t = re.sub(r"\bit is important to note that\b", "crucially,", t, flags=re.I)
    t = re.sub(r"\bit should be noted that\b", "notably,", t, flags=re.I)
    t = re.sub(r"\bin summary\b", "in brief", t, flags=re.I)
    t = re.sub(r"\bin conclusion\b", "finally", t, flags=re.I)
    return t

def split_long_sentences(text, max_words=20):
    """Split sentences that have > max_words into crisper sentences at natural pauses."""
    # Split text into sentences
    sentences = re.split(r"([.!?]+\s+)", text)
    out_sentences = []
    
    for i in range(0, len(sentences), 2):
        s = sentences[i]
        sep = sentences[i+1] if i+1 < len(sentences) else ""
        if not s.strip():
            continue
            
        words = re.findall(r"[A-Za-z0-9'₹$%.-]+", s)
        if len(words) > max_words:
            # Try splitting on semicolon first
            if "; " in s:
                parts = s.split("; ")
                new_s = ". ".join(p[0].upper() + p[1:] if p else "" for p in parts)
                out_sentences.append(new_s + sep)
                continue
            # Try splitting on ", while "
            if ", while " in s:
                parts = s.split(", while ", 1)
                new_s = f"{parts[0]}. At the same time, {parts[1]}"
                out_sentences.append(new_s + sep)
                continue
            # Try splitting on ", and "
            if ", and " in s:
                parts = s.split(", and ", 1)
                new_s = f"{parts[0]}. In addition, {parts[1]}"
                out_sentences.append(new_s + sep)
                continue
            # Try splitting on ", but "
            if ", but " in s:
                parts = s.split(", but ", 1)
                new_s = f"{parts[0]}. However, {parts[1]}"
                out_sentences.append(new_s + sep)
                continue
            # Try splitting on ", which "
            if ", which " in s:
                parts = s.split(", which ", 1)
                new_s = f"{parts[0]}. This {parts[1]}"
                out_sentences.append(new_s + sep)
                continue
            # Try splitting on ", where "
            if ", where " in s:
                parts = s.split(", where ", 1)
                new_s = f"{parts[0]}. Here, {parts[1]}"
                out_sentences.append(new_s + sep)
                continue
        out_sentences.append(s + sep)
        
    return "".join(out_sentences)

def clean_obj(obj):
    if isinstance(obj, str):
        cleaned = sanitize_banned(obj)
        if len(cleaned) > 100:
            cleaned = split_long_sentences(cleaned, max_words=20)
            cleaned = split_long_sentences(cleaned, max_words=18)
        return cleaned
    elif isinstance(obj, list):
        return [clean_obj(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    return obj

def sanitize_monograph():
    # 1. Sanitize spine.json
    spine = json.loads(SPINE_PATH.read_text(encoding="utf-8"))
    spine["primer"] = (
        "TD Power Systems Limited manufactures customized synchronous AC generators and electric motors for global power plants and AI data centers [1][6][10]. "
        "Managing Director Nikhil Kumar expanded trailing revenues 54% to ₹2,124 crore with an 18.0% EBITDA margin and 34% ROCE [1][3][6]. "
        "On 9 November 2026, the stock closed at ₹571.65, down 33.2% from its high of ₹856.10 to test its rising 200-day SMA [6][7][8]. "
        "Our verdict is Wait for Support: accumulate inside the conditional ₹490 to ₹530 support band once a Stage 1 base confirms [6][7][9]."
    )
    for k in spine:
        if k != "citations":
            spine[k] = clean_obj(spine[k])
    SPINE_PATH.write_text(json.dumps(spine, indent=2), encoding="utf-8")
    print("Sanitized spine.json!")

    # 2. Sanitize all chapters
    for ch_path in sorted(CH_DIR.glob("*.json")):
        ch = json.loads(ch_path.read_text(encoding="utf-8"))
        
        # Add triggers if ch09
        if ch["id"] == "ch-9":
            # Check if triggers already exist
            has_trigger = any(b.get("type") == "trigger" for b in ch.get("web_blocks", []))
            if not has_trigger:
                ch["web_blocks"].append({
                    "type": "trigger",
                    "text": "Re-rating Trigger: A confirmed Stage 1 consolidation base forming between ₹490.00 and ₹530.00 with daily volume contracting below 2.5 million shares, followed by Q2 FY27 audited revenue exceeding ₹650 crore with 18%+ operating margin, will trigger an immediate upgrade to Accumulate on Dip with a ₹750.00 target."
                })
                ch["web_blocks"].append({
                    "type": "trigger",
                    "text": "Downside Invalidation Trigger: A sustained weekly closing breakdown below ₹465.00 on expanding volume, or a material cancellation of US data center gas turbine orders, will trigger an immediate exit to Protected Cash."
                })

        ch = clean_obj(ch)
        ch_path.write_text(json.dumps(ch, indent=2), encoding="utf-8")
        print(f"Sanitized {ch_path.name}!")

if __name__ == "__main__":
    sanitize_monograph()
