#!/usr/bin/env python3
"""
Canonical Schema & Loader for 10-Chapter Institutional Company Monographs
(Web Research Dossier + Narrative Audiobook/Book Edition).

Supports both:
  1. Multi-stage directory specs: <RUN_DIR>/work/<SYM>/ containing spine.json
     and chapters/ch00.json .. chapters/ch09.json (recommended for 12,000-18,000 word depth).
  2. Single-file JSON specs: <RUN_DIR>/work/<SYM>_spec.json (either 10-chapter `chapters`
     list or legacy `ch1`..`ch7` keys).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

REQUIRED_SPINE_FIELDS = (
    "symbol",
    "market",
    "as_of",
    "title",
    "verdict",
    "archetype",
    "strategy_bucket",
    "conviction_tier",
    "entry_zone_low",
    "entry_zone_high",
    "stop_loss",
    "target_base",
    "target_bull",
    "target_bear",
    "citations",
)

CANONICAL_10_CHAPTERS = [
    ("primer", "Prologue: The Business, The Price & Our Independent Verdict"),
    ("ch-1", "1. Origin, Corporate Evolution & Past Stock Cycles"),
    ("ch-2", "2. What the Company Does: Segments, Revenue Mix & Concrete Examples"),
    ("ch-3", "3. Distribution, Supply Chain & Unit Economics"),
    ("ch-4", "4. Industry Structure, Competitive Moat & External Learning Hub"),
    ("ch-5", "5. Leading Operational KPIs, Structural Potential & CEO Walk-the-Talk"),
    ("ch-6", "6. 10-Year Financial Forensics, Cash Conversion & Balance Sheet"),
    ("ch-7", "7. Why the Price Is What It Is: Valuation, Reverse DCF & Peer Comps"),
    ("ch-8", "8. Stage 2 Technical Structure, Institutional Flow & Momentum Setup"),
    ("ch-9", "9. Both Sides of the Aisle, Likely Outcomes & No-FOMO Action Plan"),
]

# The synthesis chapter that carries the Bull/Bear steelman and the
# probability-weighted outcomes. The spine verdict and price levels are derived
# from this chapter, not the other way round.
SYNTHESIS_CHAPTER_ID = "ch-9"
HOLDING_ACTIONS = {
    "KEEP_COMPOUNDING", "HOLD_WITH_HARD_STOP", "TRIM_INTO_STRENGTH", "TRIM_OVERWEIGHT",
    "EXIT_IMMEDIATELY", "EXIT_ON_BOUNCE", "NOT_HELD", "DEFER",
}
REDEPLOYMENT_TYPES = {"CASH", "SHORTLIST", "OUTSIDE"}


def load_monograph_spec(spec_path: str | Path) -> Dict[str, Any]:
    """Load a monograph spec from either a directory (spine.json + chapters/*.json) or a JSON file."""
    p = Path(spec_path)
    if p.is_dir():
        spine_file = p / "spine.json"
        if not spine_file.exists():
            raise FileNotFoundError(f"Directory spec {p} is missing spine.json")
        spec = json.loads(spine_file.read_text(encoding="utf-8"))
        chapters_dir = p / "chapters"
        chapters: List[Dict[str, Any]] = []
        if chapters_dir.is_dir():
            for ch_file in sorted(chapters_dir.glob("*.json")):
                chapters.append(json.loads(ch_file.read_text(encoding="utf-8")))
        if chapters:
            spec["chapters"] = chapters
        return spec

    spec = json.loads(p.read_text(encoding="utf-8"))
    if "chapters" not in spec and (p.parent / "chapters").is_dir():
        chapters = [
            json.loads(cf.read_text(encoding="utf-8"))
            for cf in sorted((p.parent / "chapters").glob("*.json"))
        ]
        if chapters:
            spec["chapters"] = chapters
    return spec


def strip_html(text: str) -> str:
    txt = re.sub(r"<sup[^>]*>.*?</sup>", "", text or "", flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\[\d+(?:[,\u2013\-]\s*\d+)*\]", "", txt)
    return re.sub(r"\s+", " ", txt).strip()


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9₹$%'.\-]+", strip_html(text)))


def validate_monograph_spec(spec: Dict[str, Any], min_total_words: int = 11000) -> Tuple[List[str], Dict[str, Any]]:
    """Validate that a 10-chapter monograph spec meets institutional depth and dual-edition rules."""
    errors: List[str] = []
    for field in REQUIRED_SPINE_FIELDS:
        if field not in spec or spec[field] is None:
            errors.append(f"Missing required spine field: {field}")

    chapters = spec.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        return errors, {"mode": "legacy", "web_words": 0, "book_words": 0}

    for field in ("new_capital_verdict", "holding_action", "holding_shares_to_sell", "holding_rationale", "holding_alerts", "redeployment_plan"):
        if field not in spec or spec[field] is None:
            errors.append(f"Missing required decision field: {field}")
    if spec.get("holding_action") not in HOLDING_ACTIONS:
        errors.append(f"holding_action must be one of {sorted(HOLDING_ACTIONS)}")
    if spec.get("new_capital_verdict") != spec.get("verdict"):
        errors.append("new_capital_verdict must match the evidence-derived dossier verdict")
    if spec.get("new_capital_verdict") not in {"IMMEDIATE_BUY", "ACCUMULATE_ON_DIP", "WAIT_FOR_SUPPORT", "REJECTED"}:
        errors.append("new_capital_verdict must be IMMEDIATE_BUY, ACCUMULATE_ON_DIP, WAIT_FOR_SUPPORT, or REJECTED")
    if not isinstance(spec.get("holding_rationale"), str) or not spec["holding_rationale"].strip():
        errors.append("holding_rationale must explain the action")
    shares_to_sell = spec.get("holding_shares_to_sell")
    if not isinstance(shares_to_sell, (int, float)) or isinstance(shares_to_sell, bool) or shares_to_sell < 0:
        errors.append("holding_shares_to_sell must be a non-negative number")
    if spec.get("holding_action") == "NOT_HELD" and shares_to_sell != 0:
        errors.append("NOT_HELD requires holding_shares_to_sell = 0")
    if spec.get("holding_action") in {"TRIM_INTO_STRENGTH", "TRIM_OVERWEIGHT", "EXIT_IMMEDIATELY", "EXIT_ON_BOUNCE"} and shares_to_sell == 0:
        errors.append("trim and exit actions require a positive holding_shares_to_sell")
    alerts = spec.get("holding_alerts")
    if not isinstance(alerts, list) or not alerts:
        errors.append("holding_alerts must contain at least one executable price or event trigger")
    elif any(not isinstance(a, dict) or not str(a.get("trigger", "")).strip()
             or not str(a.get("instruction", "")).strip()
             or not isinstance(a.get("shares"), (int, float)) or isinstance(a.get("shares"), bool)
             or a.get("shares", -1) < 0 for a in alerts):
        errors.append("each holding_alerts row requires trigger, instruction, and non-negative shares")
    if isinstance(alerts, list) and any(
            a.get("trigger_price") is not None
            and (not isinstance(a.get("trigger_price"), (int, float)) or isinstance(a.get("trigger_price"), bool))
            for a in alerts if isinstance(a, dict)):
        errors.append("holding alert trigger_price must be numeric when supplied")
    plan = spec.get("redeployment_plan")
    if not isinstance(plan, dict) or not str(plan.get("capital_source", "")).strip():
        errors.append("redeployment_plan requires a capital_source")
    else:
        destinations = plan.get("destinations")
        if not isinstance(destinations, list) or not destinations:
            errors.append("redeployment_plan.destinations must not be empty")
        else:
            types = set()
            total = 0.0
            for row in destinations:
                if not isinstance(row, dict):
                    errors.append("each redeployment destination must be an object")
                    continue
                dest_type = row.get("destination_type")
                types.add(dest_type)
                if dest_type not in REDEPLOYMENT_TYPES:
                    errors.append(f"destination_type must be one of {sorted(REDEPLOYMENT_TYPES)}")
                pct = row.get("allocation_pct")
                if not isinstance(pct, (int, float)) or isinstance(pct, bool) or not 0 <= pct <= 100:
                    errors.append("each redeployment allocation_pct must be between 0 and 100")
                else:
                    total += pct
                for key in ("recommendation", "rationale", "entry_condition"):
                    if not isinstance(row.get(key), str) or not row[key].strip():
                        errors.append(f"redeployment destination requires {key}")
                if dest_type in {"SHORTLIST", "OUTSIDE"} and (row.get("symbol") or pct):
                    if not isinstance(row.get("symbol"), str) or not row["symbol"].strip():
                        errors.append("a named equity redeployment requires symbol")
                    for key in ("target_base", "asymmetry_ratio"):
                        if not isinstance(row.get(key), (int, float)) or isinstance(row.get(key), bool):
                            errors.append(f"named equity redeployment requires numeric {key}")
            if not REDEPLOYMENT_TYPES <= types:
                errors.append("redeployment_plan must assess CASH, SHORTLIST, and OUTSIDE options")
            if abs(total - 100.0) > 0.01:
                errors.append(f"redeployment allocations must total 100%, got {total:.2f}%")

    # Evidence-first gate: the synthesis chapter must exist, and when the spine
    # declares a decision_basis it must point at that chapter. A spine whose
    # verdict predates the research is exactly what this guards against.
    chapter_ids = {ch.get("id") for ch in chapters if ch.get("id")}
    if SYNTHESIS_CHAPTER_ID not in chapter_ids:
        errors.append(
            f"Missing synthesis chapter {SYNTHESIS_CHAPTER_ID!r}: the verdict and price "
            "levels must be derived from the Bull/Bear outcomes chapter, not declared first"
        )
    decision_basis = spec.get("decision_basis")
    if decision_basis not in (None, "") and decision_basis != SYNTHESIS_CHAPTER_ID:
        errors.append(
            f"decision_basis must reference {SYNTHESIS_CHAPTER_ID!r}, got {decision_basis!r}"
        )

    web_words = 0
    book_words = 0
    chapter_stats = []

    for idx, ch in enumerate(chapters):
        cid = ch.get("id", f"ch-{idx}")
        w_cnt = 0
        for blk in ch.get("web_blocks", []):
            btype = blk.get("type", "p")
            if btype in ("p", "trigger"):
                w_cnt += word_count(blk.get("html") or blk.get("text", ""))
            elif btype == "callout":
                w_cnt += word_count(blk.get("title", ""))
                for cp in blk.get("paragraphs", []):
                    w_cnt += word_count(cp)
            elif btype == "table":
                w_cnt += word_count(blk.get("caption", "")) + word_count(blk.get("takeaway", ""))
                for r in blk.get("rows", []):
                    for cell in r:
                        w_cnt += word_count(str(cell))
            elif btype == "estimate":
                for k in ("the_number", "how_calculated", "the_inputs", "the_range", "if_off"):
                    w_cnt += word_count(blk.get(k, ""))

        b_cnt = 0
        ep = ch.get("epigraph") or {}
        if isinstance(ep, dict):
            b_cnt += word_count(ep.get("quote", "")) + word_count(ep.get("author", ""))
        for bp in ch.get("book_paragraphs", []):
            b_cnt += word_count(bp)
            if "<table" in bp.lower() or "<sup" in bp.lower():
                errors.append(f"Chapter {cid}: book_paragraphs must not contain raw <table> or <sup> tags")
        for c in ch.get("book_callouts", []):
            b_cnt += word_count(c.get("title", "")) + word_count(c.get("quote", "")) + word_count(c.get("text", ""))
            for b in c.get("bullets", []):
                b_cnt += word_count(b)
        for sub in ch.get("book_subsections", []):
            b_cnt += word_count(sub.get("title", ""))
            for bp in sub.get("paragraphs", []):
                b_cnt += word_count(bp)
                if "<table" in bp.lower() or "<sup" in bp.lower():
                    errors.append(f"Chapter {cid}: book_subsections must not contain raw <table> or <sup> tags")
            for c in sub.get("callouts", []):
                b_cnt += word_count(c.get("title", "")) + word_count(c.get("quote", "")) + word_count(c.get("text", ""))
                for b in c.get("bullets", []):
                    b_cnt += word_count(b)

        web_words += w_cnt
        book_words += b_cnt
        chapter_stats.append({"id": cid, "web_words": w_cnt, "book_words": b_cnt})

    if web_words < min_total_words:
        errors.append(f"Web dossier word count ({web_words:,}) is below target floor ({min_total_words:,})")
    if book_words < min_total_words:
        errors.append(f"Book/Audiobook word count ({book_words:,}) is below target floor ({min_total_words:,})")

    return errors, {
        "mode": "10_chapter_monograph",
        "chapter_count": len(chapters),
        "web_words": web_words,
        "book_words": book_words,
        "estimated_audio_minutes": round(book_words / 155),
        "chapters": chapter_stats,
    }
