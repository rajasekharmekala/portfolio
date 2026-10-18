#!/usr/bin/env python3
"""Record-level three-way merge for the JSON record files in data/.

Two runs that start from the same origin/main may each edit data/watchlist/US.json. A text merge
cannot tell that they touched different companies; this merge can. Lists of objects that carry a
unique "symbol" are merged by symbol, objects are merged field by field, and anything both sides
changed differently is reported as a conflict instead of being guessed.

Usage (also works as a git merge driver, `%O %A %B`; the result is written over OURS):
  .venv/bin/python scripts/record_merge.py BASE OURS THEIRS [--out FILE]
Exit code 0 merged, 1 conflict (nothing written).
"""
import argparse
import json
import sys
from pathlib import Path

MISSING = object()
IDENTITY_KEY = "symbol"


class MergeConflict(Exception):
    def __init__(self, conflicts):
        self.conflicts = conflicts
        super().__init__("; ".join(conflicts))


def _keyed(*lists):
    """True when every list holds only objects with a unique IDENTITY_KEY (a missing list is fine)."""
    for items in lists:
        if items is MISSING:
            continue
        if not isinstance(items, list):
            return False
        seen = set()
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get(IDENTITY_KEY), str):
                return False
            if item[IDENTITY_KEY] in seen:
                return False
            seen.add(item[IDENTITY_KEY])
    return True


def _order(base_keys, ours_keys, theirs_keys):
    """Key order for the merged list: keep whichever side deliberately reordered, else theirs."""
    base_set, ours_set, theirs_set = set(base_keys), set(ours_keys), set(theirs_keys)

    def reordered(side, side_set):
        common = base_set & side_set
        return [k for k in side if k in common] != [k for k in base_keys if k in common]

    first, second = (ours_keys, theirs_keys) if reordered(ours_keys, ours_set) and not reordered(theirs_keys, theirs_set) \
        else (theirs_keys, ours_keys)
    return first, second


def _merge_keyed(base, ours, theirs, path, conflicts):
    base = [] if base is MISSING else base
    by = lambda items: {item[IDENTITY_KEY]: item for item in items}
    b, o, t = by(base), by(ours), by(theirs)
    first, second = _order([i[IDENTITY_KEY] for i in base], [i[IDENTITY_KEY] for i in ours],
                           [i[IDENTITY_KEY] for i in theirs])
    sequence = []
    for key in list(first) + [k for k in second if k not in first]:
        if key not in sequence:
            sequence.append(key)
    merged = []
    for key in sequence:
        value = merge3(b.get(key, MISSING), o.get(key, MISSING), t.get(key, MISSING), f"{path}[{key}]", conflicts)
        if value is not MISSING:
            merged.append(value)
    return merged


def merge3(base, ours, theirs, path="$", conflicts=None):
    """Merge; returns MISSING for a deletion. Conflicts are appended to `conflicts` (theirs is kept)."""
    top = conflicts is None
    conflicts = [] if top else conflicts
    if ours == theirs:
        result = ours
    elif base == ours:
        result = theirs
    elif base == theirs:
        result = ours
    elif isinstance(ours, dict) and isinstance(theirs, dict) and (base is MISSING or isinstance(base, dict)):
        base_dict = {} if base is MISSING else base
        result = {}
        for key in list(theirs) + [k for k in ours if k not in theirs]:
            value = merge3(base_dict.get(key, MISSING), ours.get(key, MISSING), theirs.get(key, MISSING),
                           f"{path}.{key}", conflicts)
            if value is not MISSING:
                result[key] = value
    elif isinstance(ours, list) and isinstance(theirs, list) and _keyed(base, ours, theirs):
        result = _merge_keyed(base, ours, theirs, path, conflicts)
    else:
        conflicts.append(f"{path}: both runs changed it differently")
        result = theirs
    if top and conflicts:
        raise MergeConflict(conflicts)
    return result


def dump(data, like_text=""):
    """Serialise the way the repository's record files are written (indent 2, trailing newline)."""
    ensure_ascii = False
    if like_text:
        try:
            parsed = json.loads(like_text)
            if json.dumps(parsed, indent=2, ensure_ascii=True) + "\n" == like_text \
                    and json.dumps(parsed, indent=2, ensure_ascii=False) + "\n" != like_text:
                ensure_ascii = True
        except ValueError:
            pass
    return json.dumps(data, indent=2, ensure_ascii=ensure_ascii) + "\n"


def merge_texts(base_text, ours_text, theirs_text):
    """Merge three file contents (a missing file is ''). Returns merged text, or None for a deletion."""
    load = lambda text: json.loads(text) if text.strip() else MISSING
    merged = merge3(load(base_text), load(ours_text), load(theirs_text))
    return None if merged is MISSING else dump(merged, theirs_text or ours_text)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base")
    parser.add_argument("ours")
    parser.add_argument("theirs")
    parser.add_argument("--out", help="write here instead of over OURS")
    args = parser.parse_args()
    read = lambda name: Path(name).read_text(encoding="utf-8")
    try:
        merged = merge_texts(read(args.base), read(args.ours), read(args.theirs))
    except MergeConflict as error:
        for line in error.conflicts:
            print("CONFLICT", line, file=sys.stderr)
        sys.exit(1)
    if merged is not None:
        Path(args.out or args.ours).write_text(merged, encoding="utf-8")


if __name__ == "__main__":
    main()
