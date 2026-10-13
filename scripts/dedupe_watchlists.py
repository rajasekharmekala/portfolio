#!/usr/bin/env python3
"""
Deduplicate watchlist records for IN and US markets.

1. Within 'archive': deduplicates symbols, retaining the record with the most recent as_of_date.
2. Across 'active' and 'archive': resolves overlaps cleanly:
   - If REJECTED or archive record has a newer rejection date, retains in archive and purges from active.
   - If active posture (ACCUMULATE_ON_DIP, KEEP_COMPOUNDING, etc.) is current, retains in active and purges from archive.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def dedupe_file(rel_path):
    p = REPO / rel_path
    data = json.loads(p.read_text(encoding="utf-8"))
    
    active_rows = data.get("active", [])
    archive_rows = data.get("archive", [])
    
    print(f"\nProcessing {rel_path}...")
    print(f"  Initial rows: active={len(active_rows)}, archive={len(archive_rows)}")
    
    # 1. Deduplicate within archive
    archive_by_sym = {}
    for r in archive_rows:
        sym = (r.get("symbol") or r.get("Symbol")).strip().upper()
        archive_by_sym.setdefault(sym, []).append(r)
        
    deduped_archive = []
    for sym, rows in archive_by_sym.items():
        if len(rows) == 1:
            deduped_archive.append(rows[0])
        else:
            sorted_rows = sorted(rows, key=lambda x: str(x.get("as_of_date") or ""), reverse=True)
            deduped_archive.append(sorted_rows[0])
            
    print(f"  Archive after internal dedupe: {len(deduped_archive)} (purged {len(archive_rows) - len(deduped_archive)} duplicates)")
    
    # 2. Resolve cross-list overlap between active and archive
    archive_sym_map = { (r.get("symbol") or r.get("Symbol")).strip().upper(): r for r in deduped_archive }
    active_sym_map = { (r.get("symbol") or r.get("Symbol")).strip().upper(): r for r in active_rows }
    
    overlaps = set(active_sym_map.keys()) & set(archive_sym_map.keys())
    print(f"  Cross-list overlapping symbols: {len(overlaps)}")
    
    final_active = []
    final_archive_syms_to_remove = set()
    
    for r in active_rows:
        sym = (r.get("symbol") or r.get("Symbol")).strip().upper()
        if sym in overlaps:
            arc_row = archive_sym_map[sym]
            act_verdict = r.get("action_verdict") or r.get("status")
            arc_verdict = arc_row.get("action_verdict") or arc_row.get("status")
            
            act_date = str(r.get("as_of_date") or "")
            arc_date = str(arc_row.get("as_of_date") or "")
            
            if act_verdict == "REJECTED" or (arc_verdict == "REJECTED" and arc_date >= act_date):
                # Stock is rejected, keep in archive only
                continue
            else:
                # Stock is active/buy/compounding, keep in active and drop from archive
                final_active.append(r)
                final_archive_syms_to_remove.add(sym)
        else:
            final_active.append(r)
            
    final_archive = [
        r for r in deduped_archive
        if (r.get("symbol") or r.get("Symbol")).strip().upper() not in final_archive_syms_to_remove
    ]
    
    data["active"] = final_active
    data["archive"] = final_archive
    
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  Final rows: active={len(final_active)}, archive={len(final_archive)}")
    remaining_overlap = set((r.get("symbol") or r.get("Symbol")).strip().upper() for r in final_active) & \
                        set((r.get("symbol") or r.get("Symbol")).strip().upper() for r in final_archive)
    print(f"  Remaining overlap: {len(remaining_overlap)}")

def main():
    for f in ["data/watchlist/IN.json", "data/watchlist/US.json"]:
        dedupe_file(f)

if __name__ == "__main__":
    main()
