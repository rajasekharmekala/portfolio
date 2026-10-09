#!/usr/bin/env python3
"""
W1 — Schema validation for portfolio data records.

Validates every record in:
    data/shortlist/{US,IN}.json   (all sheets; Swap_Decision_Matrix uses its own schema)
    data/watchlist/{US,IN}.json   (active + archive)

against the draft-07 schemas in scripts/schemas/. Also warns when a
research_dossier_path does not resolve to an existing file under the repo.

Exit code 1 if any record fails its schema, 0 otherwise.

Run:  .venv/bin/python scripts/validate_data.py
"""

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except ImportError:
    sys.stderr.write("jsonschema is not installed. Run: .venv/bin/pip install jsonschema\n")
    sys.exit(2)

REPO = Path(__file__).resolve().parent.parent
SCHEMAS = REPO / "scripts" / "schemas"


def load_validator(name):
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def validate_rows(rows, validator, label):
    errors = []
    for i, row in enumerate(rows):
        symbol = row.get("symbol") or row.get("incumbent_holding") or f"#{i}"
        errs = sorted(validator.iter_errors(row), key=lambda e: e.path)
        for e in errs:
            loc = ".".join(str(p) for p in e.path) or "(root)"
            errors.append(f"  {label}[{i}] {symbol}: {loc}: {e.message[:120]}")
    return errors


def main():
    shortlist_v = load_validator("shortlist_record.schema.json")
    swap_v = load_validator("swap_decision.schema.json")
    watch_v = load_validator("watchlist_record.schema.json")

    total_errors = 0
    total_rows = 0
    missing_dossiers = 0

    for market in ("US", "IN"):
        # ---- shortlist
        path = REPO / "data" / "shortlist" / f"{market}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for sheet, rows in data["sheets"].items():
            validator = swap_v if sheet == "Swap_Decision_Matrix" else shortlist_v
            errs = validate_rows(rows, validator, f"{market}/{sheet}")
            total_rows += len(rows)
            total_errors += len(errs)
            for e in errs[:10]:
                print(e)
            if len(errs) > 10:
                print(f"  ... and {len(errs) - 10} more errors in {market}/{sheet}")

        # ---- watchlist
        path = REPO / "data" / "watchlist" / f"{market}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for bucket in ("active", "archive"):
            errs = validate_rows(data[bucket], watch_v, f"{market}/watchlist/{bucket}")
            total_rows += len(data[bucket])
            total_errors += len(errs)
            for e in errs[:10]:
                print(e)
            if len(errs) > 10:
                print(f"  ... and {len(errs) - 10} more errors in {market}/watchlist/{bucket}")

    # ---- dossier path existence (warnings only)
    for market in ("US", "IN"):
        path = REPO / "data" / "shortlist" / f"{market}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for sheet, rows in data["sheets"].items():
            if sheet == "Swap_Decision_Matrix":
                continue
            for row in rows:
                p = row.get("research_dossier_path")
                if p and not (REPO / p).exists():
                    missing_dossiers += 1
                    if missing_dossiers <= 10:
                        print(f"  [warn] {market}/{sheet} {row.get('symbol')}: dossier not found: {p}")

    print(f"\nrows checked: {total_rows}, schema errors: {total_errors}, missing dossier files: {missing_dossiers}")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
