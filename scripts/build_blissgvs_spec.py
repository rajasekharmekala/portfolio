#!/usr/bin/env python3
"""
scripts/build_blissgvs_spec.py - Assembly script for BLISSGVS Monograph Spec.
Outputs:
  work/BLISSGVS/spine.json
  work/BLISSGVS/chapters/ch00.json .. ch09.json
"""
import json
import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from blissgvs_data import SPINE_DATA
from blissgvs_ch00_ch02 import get_ch00, get_ch01, get_ch02
from blissgvs_ch03_ch05 import get_ch03, get_ch04, get_ch05
from blissgvs_ch06_ch09 import get_ch06, get_ch07, get_ch08, get_ch09
from dossier_schema import validate_monograph_spec, load_monograph_spec

OUT_DIR = Path("work/BLISSGVS")
CH_DIR = OUT_DIR / "chapters"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CH_DIR.mkdir(parents=True, exist_ok=True)

print("Authoring Bliss GVS monograph chapters...")

chapters = [
    ("ch00.json", get_ch00()),
    ("ch01.json", get_ch01()),
    ("ch02.json", get_ch02()),
    ("ch03.json", get_ch03()),
    ("ch04.json", get_ch04()),
    ("ch05.json", get_ch05()),
    ("ch06.json", get_ch06()),
    ("ch07.json", get_ch07()),
    ("ch08.json", get_ch08()),
    ("ch09.json", get_ch09()),
]

for filename, ch_data in chapters:
    p = CH_DIR / filename
    p.write_text(json.dumps(ch_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  - Wrote {p} ({len(p.read_text(encoding='utf-8')):,} bytes)")

# Write spine.json
spine_file = OUT_DIR / "spine.json"
spine_file.write_text(json.dumps(SPINE_DATA, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"  - Wrote {spine_file}")

# Enrich chapters with deep analytical web blocks
from enrich_monograph_web_blocks import main as run_enrichment
run_enrichment()

# Validate loaded spec
spec = load_monograph_spec(OUT_DIR)
errors, stats = validate_monograph_spec(spec, min_total_words=11000)

print("\n--- Spec Validation Stats ---")
print(f"Mode: {stats.get('mode')}")
print(f"Chapter Count: {stats.get('chapter_count')}")
print(f"Web Dossier Words: {stats.get('web_words'):,}")
print(f"Book / Audiobook Words: {stats.get('book_words'):,}")
print(f"Estimated Audio Minutes: ~{stats.get('estimated_audio_minutes')} mins")

if errors:
    print(f"\n[!] Validation Errors ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\n[+] SUCCESS: Monograph spec passed all validation checks!")
