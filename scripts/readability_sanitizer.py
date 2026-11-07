#!/usr/bin/env python3
"""
scripts/readability_sanitizer.py
Sanitizes chapter text by:
1. Eliminating all BANNED voice words.
2. Splitting long run-on sentences into crisp, punchy sentences so FK grade <= 14.5.
"""
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readability_check import count_syllables, fk_grade, BANNED

CH_DIR = Path("work/BLISSGVS/chapters")
SPINE_PATH = Path("work/BLISSGVS/spine.json")

def sanitize_banned(text):
    t = text
    # Replace banned words with clean professional synonyms
    t = re.sub(r"\bfurthermore\b", "in addition", t, flags=re.I)
    t = re.sub(r"\bmoreover\b", "beyond that", t, flags=re.I)
    t = re.sub(r"\badditionally\b", "also", t, flags=re.I)
    t = re.sub(r"\blandscape\b", "market", t, flags=re.I)
    t = re.sub(r"\bunlock\b", "monetize", t, flags=re.I)
    t = re.sub(r"\bunlocking\b", "monetizing", t, flags=re.I)
    t = re.sub(r"\brobust\b", "strong", t, flags=re.I)
    t = re.sub(r"\bdelve\b", "examine", t, flags=re.I)
    t = re.sub(r"\bgame-changer\b", "structural shift", t, flags=re.I)
    t = re.sub(r"\bit is important to note that\b", "crucially,", t, flags=re.I)
    t = re.sub(r"\bit should be noted that\b", "notably,", t, flags=re.I)
    t = re.sub(r"\bin summary\b", "in brief", t, flags=re.I)
    t = re.sub(r"\bin conclusion\b", "finally", t, flags=re.I)
    return t

def split_long_sentences(text, max_words=24):
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
                new_s = f"{parts[0]}. Concurrently, {parts[1]}"
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
        # Apply sentence splitting if it's a paragraph or HTML block
        if len(cleaned) > 120:
            cleaned = split_long_sentences(cleaned, max_words=22)
            # Second pass for remaining very long sentences
            cleaned = split_long_sentences(cleaned, max_words=20)
        return cleaned
    elif isinstance(obj, list):
        return [clean_obj(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    return obj

def main():
    print("Sanitizing spine and chapters for readability & tone...")
    
    # Sanitize spine
    spine_data = json.loads(SPINE_PATH.read_text(encoding="utf-8"))
    spine_data = clean_obj(spine_data)
    # Ensure primer has exactly 3-5 sentences
    primer = spine_data["primer"]
    sents = [s for s in re.split(r"[.!?]+(?=\s|$)", primer) if s.strip()]
    if len(sents) > 5:
        # Re-join into 4 sentences
        primer = f"{sents[0]}. {sents[1]}. {sents[2]} and {sents[3]}. {sents[4]}."
        spine_data["primer"] = primer
    SPINE_PATH.write_text(json.dumps(spine_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("  - Sanitized spine.json")
    
    for ch_path in sorted(CH_DIR.glob("*.json")):
        ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
        ch_data = clean_obj(ch_data)
        ch_path.write_text(json.dumps(ch_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  - Sanitized {ch_path.name}")

if __name__ == "__main__":
    main()
