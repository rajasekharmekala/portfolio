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

import argparse
import datetime as dt
import json
import re
import sys
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
    ("ch-0", "0. Executive Thesis, Dual Verdict & Opportunity Matrix"),
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
BUSINESS_QUALITY_VERDICTS = {"COMPOUNDER_PASS", "CYCLICAL_CONDITIONAL", "FUNDAMENTAL_FAIL"}
KPI_HEALTH_VALUES = {"PASS", "PASS_WITH_WATCH", "FAIL"}
PARALLEL_ROLES = {"MOAT_SCALING", "FAILURE_BASE_RATE", "CYCLE_VALUATION"}
CLICHE_PARALLELS = {
    "apple", "berkshire hathaway", "constellation software", "danaher",
    "bajaj finance", "titan company",
}
BLIND_CHAPTER_IDS = {"ch-1", "ch-2", "ch-3", "ch-4", "ch-5", "ch-6"}
BLIND_VERDICT_LEAK_RE = re.compile(
    r"\b(?:IMMEDIATE_BUY|ACCUMULATE_ON_DIP|WAIT_FOR_SUPPORT|BUY_AT_CMP_NO_FOMO|"
    r"WAIT_FOR_SUPPORT_PULLBACK|WAIT_FOR_SUPPORT_RETEST|AVOID_STAGE4_OR_BROKEN|"
    r"TIER_[0-3]|CORE_ALPHA|TACTICAL_MOMENTUM|LEVERAGED_SATELLITE|"
    r"support buy zone|invalidation stop)\b",
    re.I,
)


def load_monograph_spec(spec_path: str | Path) -> Dict[str, Any]:
    """Load a monograph spec from either a directory (spine.json + chapters/*.json) or a JSON file."""
    p = Path(spec_path)
    if p.is_dir():
        spine_file = p / "spine.json"
        if not spine_file.exists():
            raise FileNotFoundError(f"Directory spec {p} is missing spine.json")
        spec = json.loads(spine_file.read_text(encoding="utf-8"))
        bq_file = p / "business_quality.json"
        if bq_file.is_file():
            bq = json.loads(bq_file.read_text(encoding="utf-8"))
            spec.setdefault("business_quality", bq)
            if bq.get("business_quality_verdict"):
                spec.setdefault("business_quality_verdict", bq["business_quality_verdict"])
            if bq.get("kpi_health"):
                spec.setdefault("kpi_health", bq["kpi_health"])
        ra_file = p / "refresh_audit.json"
        if ra_file.is_file():
            spec.setdefault("refresh_audit", json.loads(ra_file.read_text(encoding="utf-8")))
        pa_file = p / "prior_anchor_locked.json"
        if pa_file.is_file():
            spec.setdefault("prior_anchor", json.loads(pa_file.read_text(encoding="utf-8")))
        opt_file = p / "options_plan.json"
        if opt_file.is_file():
            spec.setdefault("options_package", json.loads(opt_file.read_text(encoding="utf-8")))
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


SHELL_CORRUPT_COMMA_RE = re.compile(r"(?:^|[\s(\[–—\-])(?:,\d{3})+\b")
SHELL_CORRUPT_MAG_RE = re.compile(r"(?:~|\(\s*)[MBK]\+?(?=\s|\)|Valuation|Cr|;|\.|,|$)")
MANGLED_COLON_RE = re.compile(r"\.\s*:\s")
MANGLED_HOWEVER_RE = re.compile(
    r"\.\s+However,\s+(?:faces|has|have|was|were|is|are|remained|remains|fell|lacks|trades|stands|suffered|delivered|achieved|operates)\b"
)
MANGLED_IN_ADDITION_RE = re.compile(r"\.\s+In addition,\s+[a-z]")
HTTP_URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.I)


def _check_text_integrity(raw_text: str, location: str, errors: List[str]) -> None:
    plain = strip_html(raw_text)
    if not plain:
        return
    m_comma = SHELL_CORRUPT_COMMA_RE.search(plain)
    if m_comma:
        errors.append(
            f"{location}: corrupted number fragment {m_comma.group(0).strip()!r} "
            "(likely unquoted shell $variable expansion; write JSON directly without bash heredocs)"
        )
    m_mag = SHELL_CORRUPT_MAG_RE.search(plain)
    if m_mag:
        errors.append(
            f"{location}: corrupted currency magnitude {m_mag.group(0).strip()!r} "
            "(likely unquoted shell $variable expansion)"
        )
    if MANGLED_COLON_RE.search(plain):
        errors.append(f"{location}: mangled punctuation '. :' detected (do not run regex sentence splitters)")
    if MANGLED_HOWEVER_RE.search(plain):
        errors.append(f"{location}: subjectless '. However, <verb>' fragment detected (do not split clauses mechanically)")


def _parse_num(cell: Any) -> float | None:
    s = re.sub(r"[,₹$%\s+]", "", strip_html(str(cell or "")))
    s = s.replace("\u2212", "-")
    m = re.match(r"^-?\d+(?:\.\d+)?$", s)
    return float(m.group(0)) if m else None


def _validate_waterfall_table(blk: Dict[str, Any], cid: str, errors: List[str]) -> None:
    caption = strip_html(blk.get("caption", ""))
    headers = [strip_html(str(h)) for h in blk.get("headers", [])]
    joined_meta = (caption + " " + " ".join(headers)).lower()
    if "waterfall" not in joined_meta and "per ₹100" not in joined_meta and "per $100" not in joined_meta:
        return
    rows = blk.get("rows", [])
    has_pct_col = len(headers) >= 3 and ("%" in headers[2] or "share" in headers[2].lower())
    cfo_val = capex_val = fcf_val = None
    for r in rows:
        if not isinstance(r, list) or len(r) < 2:
            continue
        label = strip_html(str(r[0]))
        amt = _parse_num(r[1])
        if amt is None:
            continue
        if has_pct_col and len(r) >= 3:
            pct = _parse_num(r[2])
            if pct is not None and abs(amt - pct) > 0.35:
                errors.append(f"Chapter {cid} waterfall row {label!r}: per-100 amount ({amt}) disagrees with % column ({pct}%)")
        note = strip_html(" ".join(str(x) for x in r[2:]))
        ratio_claim = re.search(
            r"[₹$]?\s*(\d+(?:\.\d+)?)\s*(?:Cr|crore|B|M|million|billion)?\s+on\s+[₹$]?\s*(\d+(?:\.\d+)?)",
            note,
            re.I,
        )
        if ratio_claim:
            num_v, den_v = float(ratio_claim.group(1)), float(ratio_claim.group(2))
            if den_v > 0:
                implied = (num_v / den_v) * 100.0
                if abs(implied - abs(amt)) > 2.0:
                    errors.append(
                        f"Chapter {cid} waterfall row {label!r}: stated {amt} per 100 contradicts note "
                        f"({num_v} on {den_v} = {implied:.1f}%)"
                    )
        low_lbl = label.lower()
        if "cash flow from operations" in low_lbl or "(cfo)" in low_lbl or low_lbl == "cfo":
            cfo_val = amt
        elif "capital expenditure" in low_lbl or "capex" in low_lbl:
            capex_val = -abs(amt) if amt > 0 else amt
        elif "free cash flow" in low_lbl or "(fcf)" in low_lbl or low_lbl == "fcf":
            fcf_val = amt
    if cfo_val is not None and capex_val is not None and fcf_val is not None:
        if abs((cfo_val + capex_val) - fcf_val) > 0.6:
            errors.append(
                f"Chapter {cid} waterfall cash-flow mismatch: CFO ({cfo_val:+.2f}) + Capex ({capex_val:+.2f}) "
                f"= {cfo_val + capex_val:+.2f}, not FCF ({fcf_val:+.2f})"
            )


def validate_monograph_spec(
    spec: Dict[str, Any],
    min_total_words: int | None = None,
    min_web_words: int = 8500,
    min_book_words: int = 10000,
) -> Tuple[List[str], Dict[str, Any]]:
    """Validate that a 10-chapter monograph spec meets institutional depth and dual-edition rules."""
    eff_web_floor = min_total_words if min_total_words is not None else min_web_words
    eff_book_floor = min_total_words if min_total_words is not None else min_book_words
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

    bq_verdict = spec.get("business_quality_verdict")
    if bq_verdict is not None:
        if bq_verdict not in BUSINESS_QUALITY_VERDICTS:
            errors.append(f"business_quality_verdict must be one of {sorted(BUSINESS_QUALITY_VERDICTS)}")
        elif bq_verdict == "FUNDAMENTAL_FAIL" and spec.get("new_capital_verdict") != "REJECTED":
            errors.append(
                "FUNDAMENTAL_FAIL business_quality_verdict requires new_capital_verdict = 'REJECTED' "
                "(do not hedge failed business/cash-flow fundamentals with WAIT_FOR_SUPPORT)"
            )

    # Anti-hedging math gate: non-rejected calls must offer >= 1.5:1 reward-to-risk from the support zone
    if spec.get("new_capital_verdict") in {"IMMEDIATE_BUY", "ACCUMULATE_ON_DIP", "WAIT_FOR_SUPPORT"}:
        cmp_val = spec.get("cmp")
        if not isinstance(cmp_val, (int, float)) or isinstance(cmp_val, bool) or cmp_val <= 0:
            errors.append(
                f"{spec['new_capital_verdict']} requires a positive numeric cmp (current price) "
                "so the homepage can show the distance to the entry zone"
            )
        ez_low = spec.get("entry_zone_low")
        ez_high = spec.get("entry_zone_high")
        sl_val = spec.get("stop_loss")
        tb_val = spec.get("target_base")
        nums_ok = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (ez_low, ez_high, sl_val, tb_val))
        if not nums_ok:
            errors.append(
                f"{spec['new_capital_verdict']} requires numeric entry_zone_low, entry_zone_high, stop_loss, and target_base"
            )
        else:
            if ez_high < ez_low or ez_low <= sl_val:
                errors.append(
                    f"Invalid support/stop ordering: require entry_zone_high ({ez_high}) >= entry_zone_low ({ez_low}) > stop_loss ({sl_val})"
                )
            elif tb_val <= ez_high:
                errors.append(
                    f"Anti-hedging gate failed for {spec['new_capital_verdict']}: target_base ({tb_val}) <= entry_zone_high ({ez_high}); "
                    "expected return in the buy/watch zone is non-positive — assign REJECTED instead of hedging"
                )
            else:
                sup_asym = (tb_val - ez_high) / (ez_high - sl_val)
                if sup_asym < 1.5 - 1e-6:
                    errors.append(
                        f"Anti-hedging gate failed for {spec['new_capital_verdict']}: support-zone asymmetry is {sup_asym:.2f}:1 (< 1.50:1); "
                        "assign REJECTED when even a pullback to support lacks asymmetric reward-to-risk"
                    )

    if spec.get("primer"):
        _check_text_integrity(str(spec["primer"]), "spine.primer", errors)
    if isinstance(spec.get("holding_rationale"), str):
        _check_text_integrity(spec["holding_rationale"], "spine.holding_rationale", errors)

    web_words = 0
    book_words = 0
    chapter_stats = []
    ch4_urls: set[str] = set()
    parallel_roles_seen: List[str] = []

    for idx, ch in enumerate(chapters):
        cid = ch.get("id", f"ch-{idx}")
        w_cnt = 0
        chapter_texts: List[str] = []
        for blk in ch.get("web_blocks", []):
            btype = blk.get("type", "p")
            if btype in ("p", "trigger"):
                raw_t = blk.get("html") or blk.get("text", "")
                w_cnt += word_count(raw_t)
                chapter_texts.append(raw_t)
                if cid == "ch-4":
                    ch4_urls.update(u.rstrip(".,;)") for u in HTTP_URL_RE.findall(raw_t))
            elif btype == "callout":
                w_cnt += word_count(blk.get("title", ""))
                chapter_texts.append(blk.get("title", ""))
                for cp in blk.get("paragraphs", []):
                    w_cnt += word_count(cp)
                    chapter_texts.append(cp)
                    if cid == "ch-4":
                        ch4_urls.update(u.rstrip(".,;)") for u in HTTP_URL_RE.findall(cp))
            elif btype == "parallel":
                role = str(blk.get("role") or "").upper()
                comp = strip_html(str(blk.get("company") or ""))
                reg = strip_html(str(blk.get("region_era") or ""))
                mech = str(blk.get("mechanism") or "")
                out_nums = str(blk.get("outcome_numbers") or "")
                lesson = str(blk.get("lesson_for_symbol") or "")
                if role not in PARALLEL_ROLES:
                    errors.append(f"Chapter {cid}: parallel block role must be one of {sorted(PARALLEL_ROLES)}, got {role!r}")
                else:
                    parallel_roles_seen.append(role)
                if not comp or not reg or len(strip_html(mech)) < 20 or len(strip_html(lesson)) < 20:
                    errors.append(f"Chapter {cid}: parallel block requires company, region_era, mechanism, and lesson_for_symbol")
                if not re.search(r"\d", strip_html(out_nums)):
                    errors.append(f"Chapter {cid}: parallel block for {comp!r} requires concrete historical figures in 'outcome_numbers'")
                if comp.lower().strip() in CLICHE_PARALLELS and not blk.get("direct_competitor_or_customer"):
                    errors.append(
                        f"Chapter {cid}: cliché mega-cap analogy {comp!r} rejected; select a dynamic, situation-specific structural twin"
                    )
                for p_txt in (comp, reg, mech, out_nums, lesson):
                    w_cnt += word_count(p_txt)
                    chapter_texts.append(p_txt)
            elif btype == "table":
                w_cnt += word_count(blk.get("caption", "")) + word_count(blk.get("takeaway", ""))
                chapter_texts.extend([blk.get("caption", ""), blk.get("takeaway", "")])
                for r in blk.get("rows", []):
                    for cell in r:
                        cs = str(cell)
                        w_cnt += word_count(cs)
                        chapter_texts.append(cs)
                        if cid == "ch-4":
                            ch4_urls.update(u.rstrip(".,;)") for u in HTTP_URL_RE.findall(cs))
                _validate_waterfall_table(blk, cid, errors)
            elif btype == "waterfall":
                rev = blk.get("revenue")
                if not isinstance(rev, (int, float)) or isinstance(rev, bool) or rev <= 0:
                    errors.append(f"Chapter {cid}: waterfall block requires positive numeric 'revenue'")
                w_cnt += word_count(blk.get("caption", "")) + word_count(blk.get("takeaway", "")) + 140
                chapter_texts.extend([blk.get("caption", ""), blk.get("takeaway", "")])
            elif btype in ("snapshot_financials", "peer_snapshot_table"):
                w_cnt += word_count(blk.get("caption", "")) + word_count(blk.get("takeaway", "")) + 160
                chapter_texts.extend([blk.get("caption", ""), blk.get("takeaway", "")])
            elif btype == "estimate":
                for k in ("the_number", "how_calculated", "the_inputs", "the_range", "if_off"):
                    w_cnt += word_count(blk.get(k, ""))
                    chapter_texts.append(blk.get(k, ""))

        b_cnt = 0
        ep = ch.get("epigraph") or {}
        if isinstance(ep, dict):
            b_cnt += word_count(ep.get("quote", "")) + word_count(ep.get("author", ""))
        for bp in ch.get("book_paragraphs", []):
            b_cnt += word_count(bp)
            chapter_texts.append(bp)
            if "<table" in bp.lower() or "<sup" in bp.lower():
                errors.append(f"Chapter {cid}: book_paragraphs must not contain raw <table> or <sup> tags")
        for c in ch.get("book_callouts", []):
            b_cnt += word_count(c.get("title", "")) + word_count(c.get("quote", "")) + word_count(c.get("text", ""))
            chapter_texts.extend([c.get("title", ""), c.get("quote", ""), c.get("text", "")])
            for b in c.get("bullets", []):
                b_cnt += word_count(b)
                chapter_texts.append(b)
        for sub in ch.get("book_subsections", []):
            b_cnt += word_count(sub.get("title", ""))
            for bp in sub.get("paragraphs", []):
                b_cnt += word_count(bp)
                chapter_texts.append(bp)
                if "<table" in bp.lower() or "<sup" in bp.lower():
                    errors.append(f"Chapter {cid}: book_subsections must not contain raw <table> or <sup> tags")
            for c in sub.get("callouts", []):
                b_cnt += word_count(c.get("title", "")) + word_count(c.get("quote", "")) + word_count(c.get("text", ""))
                chapter_texts.extend([c.get("title", ""), c.get("quote", ""), c.get("text", "")])
                for b in c.get("bullets", []):
                    b_cnt += word_count(b)
                    chapter_texts.append(b)

        joined_ch = " ".join(str(x) for x in chapter_texts if x)
        _check_text_integrity(joined_ch, f"Chapter {cid}", errors)
        if bq_verdict is not None and cid in BLIND_CHAPTER_IDS:
            leak = BLIND_VERDICT_LEAK_RE.search(strip_html(joined_ch))
            if leak:
                errors.append(
                    f"Chapter {cid} (price-blind fundamental chapter) contains verdict/timing token {leak.group(0)!r}; "
                    "keep portfolio verdicts, tiers, and entry zones strictly in ch-7..ch-9 and ch-0"
                )
        in_add_count = len(MANGLED_IN_ADDITION_RE.findall(strip_html(joined_ch)))
        if in_add_count >= 3:
            errors.append(
                f"Chapter {cid}: {in_add_count} mechanical '. In addition, ...' fragments detected "
                "(write natural sentences instead of running regex sentence splitters)"
            )

        web_words += w_cnt
        book_words += b_cnt
        chapter_stats.append({"id": cid, "web_words": w_cnt, "book_words": b_cnt})

    if len(parallel_roles_seen) >= 2 and "FAILURE_BASE_RATE" not in parallel_roles_seen:
        errors.append(
            "When 2+ situational parallel blocks are used, at least one must have role='FAILURE_BASE_RATE' "
            "to test historical downside/failure base rates rather than bull-only analogies"
        )

    if eff_web_floor > 0:
        cites = spec.get("citations") or []
        if len(cites) < 25:
            errors.append(f"citations must include at least 25 primary sources, got {len(cites)}")
        cite_urls = {
            u.split("#")[0].rstrip(".,;)/")
            for c in cites
            for u in HTTP_URL_RE.findall(str(c))
        }
        if len(cite_urls) < 15:
            errors.append(
                f"citations must include at least 15 distinct http(s) primary source URLs, got {len(cite_urls)} "
                "(plain-text bibliography lines without URLs are insufficient)"
            )
        if "ch-4" in chapter_ids and len(ch4_urls) < 3:
            errors.append(
                f"Chapter ch-4 External Learning Hub must include at least 3 clickable http(s) resource URLs, got {len(ch4_urls)}"
            )

    if web_words < eff_web_floor:
        errors.append(f"Web dossier word count ({web_words:,}) is below target floor ({eff_web_floor:,})")
    if book_words < eff_book_floor:
        errors.append(f"Book/Audiobook word count ({book_words:,}) is below target floor ({eff_book_floor:,})")

    return errors, {
        "mode": "10_chapter_monograph",
        "chapter_count": len(chapters),
        "web_words": web_words,
        "book_words": book_words,
        "estimated_audio_minutes": round(book_words / 155),
        "chapters": chapter_stats,
    }


def validate_blind_pass_dir(spec_dir: str | Path) -> List[str]:
    """Verify Pass 1 (ch-1..ch-6 + business_quality.json) completed cleanly BEFORE valuation/verdict files exist."""
    root = Path(spec_dir)
    errors: List[str] = []
    if not root.is_dir():
        return [f"Spec directory does not exist: {root}"]

    # Premature verdict/valuation files are forbidden during Pass 1
    if (root / "spine.json").exists():
        errors.append("Premature spine.json present during Pass 1: do not author spine.json until after Chapter 9")
    ch_dir = root / "chapters"
    if not ch_dir.is_dir():
        return errors + [f"Missing chapters/ directory in {root}"]
    for premature in ("ch00.json", "ch07.json", "ch08.json", "ch09.json"):
        if (ch_dir / premature).exists():
            errors.append(f"Premature {premature} present during Pass 1: complete blind ch01..ch06 first")

    bq_file = root / "business_quality.json"
    if not bq_file.is_file():
        errors.append("Missing business_quality.json from Pass 1")
    else:
        bq = json.loads(bq_file.read_text(encoding="utf-8"))
        if bq.get("business_quality_verdict") not in BUSINESS_QUALITY_VERDICTS:
            errors.append(f"business_quality.business_quality_verdict must be one of {sorted(BUSINESS_QUALITY_VERDICTS)}")
        if bq.get("kpi_health") not in KPI_HEALTH_VALUES:
            errors.append(f"business_quality.kpi_health must be one of {sorted(KPI_HEALTH_VALUES)}")
        rationale = str(bq.get("summary_rationale") or "").strip()
        if len(rationale) < 40:
            errors.append("business_quality.summary_rationale must provide a substantive price-blind synthesis")
        else:
            _check_text_integrity(rationale, "business_quality.summary_rationale", errors)
            leak = BLIND_VERDICT_LEAK_RE.search(rationale)
            if leak:
                errors.append(f"business_quality.summary_rationale leaks portfolio verdict/timing token {leak.group(0)!r}")

    for n in range(1, 7):
        cf = ch_dir / f"ch0{n}.json"
        if not cf.is_file():
            errors.append(f"Missing blind-pass chapter file: chapters/ch0{n}.json")
            continue
        ch = json.loads(cf.read_text(encoding="utf-8"))
        cid = ch.get("id", "")
        if cid != f"ch-{n}":
            errors.append(f"chapters/ch0{n}.json must have id 'ch-{n}', got {cid!r}")
        blobs: List[str] = []
        for blk in ch.get("web_blocks", []):
            btype = blk.get("type", "p")
            if btype in ("p", "trigger"):
                blobs.append(blk.get("html") or blk.get("text", ""))
            elif btype == "callout":
                blobs.append(blk.get("title", ""))
                blobs.extend(blk.get("paragraphs", []))
            elif btype == "table":
                blobs.extend([blk.get("caption", ""), blk.get("takeaway", "")])
                for r in blk.get("rows", []):
                    blobs.extend(str(c) for c in r)
                _validate_waterfall_table(blk, cid, errors)
            elif btype == "waterfall":
                rev = blk.get("revenue")
                if not isinstance(rev, (int, float)) or isinstance(rev, bool) or rev <= 0:
                    errors.append(f"Chapter {cid}: waterfall block requires positive numeric 'revenue'")
        blobs.extend(ch.get("book_paragraphs", []))
        for sub in ch.get("book_subsections", []):
            blobs.extend(sub.get("paragraphs", []))
        joined = " ".join(str(x) for x in blobs if x)
        _check_text_integrity(joined, f"Chapter ch-{n}", errors)
        leak = BLIND_VERDICT_LEAK_RE.search(strip_html(joined))
        if leak:
            errors.append(
                f"Chapter ch-{n} leaks portfolio verdict/timing token {leak.group(0)!r} during price-blind Pass 1"
            )
    return errors


def enforce_stop_loss_ratchet(
    spec: Dict[str, Any],
    held_quantity: float,
    live_close: float | None = None,
) -> List[str]:
    """Enforce upward-only stop ratchet on held Stage 2 positions (never widen stops downward on losers)."""
    prior = spec.get("prior_anchor")
    if not isinstance(prior, dict) or held_quantity <= 0 or spec.get("split_adjusted"):
        return []
    prior_stop = prior.get("stop_loss")
    new_stop = spec.get("stop_loss")
    if not isinstance(prior_stop, (int, float)) or not isinstance(new_stop, (int, float)):
        return []
    action = str(spec.get("holding_action") or "").upper()
    exit_actions = {"EXIT_IMMEDIATELY", "EXIT_ON_BOUNCE"}
    errors: List[str] = []
    if new_stop < float(prior_stop) - 0.01 and action not in exit_actions:
        errors.append(
            f"Stop-loss ratchet violation for held position ({held_quantity:g} shares): "
            f"new stop_loss ({new_stop}) lowers prior structural stop ({prior_stop}); "
            "trail stops upward behind rising support or set holding_action to EXIT_IMMEDIATELY / EXIT_ON_BOUNCE"
        )
    if isinstance(live_close, (int, float)) and live_close <= float(prior_stop) and action not in exit_actions:
        errors.append(
            f"Prior structural stop ({prior_stop}) breached at close {live_close} on held position ({held_quantity:g} shares): "
            "holding_action must be EXIT_IMMEDIATELY or EXIT_ON_BOUNCE"
        )
    return errors


def persist_monograph_spec(spec: Dict[str, Any], target_dir: str | Path, mode: str = "full_underwrite") -> Path:
    """Persist canonical spine.json, business_quality.json, chapters/ch00..ch09.json, and revision_log.json."""
    out = Path(target_dir)
    ch_out = out / "chapters"
    ch_out.mkdir(parents=True, exist_ok=True)

    transient_keys = {"chapters", "business_quality", "refresh_audit", "prior_anchor", "options_package", "facts_path", "research_paths"}
    spine_clean = {k: v for k, v in spec.items() if k not in transient_keys}
    (out / "spine.json").write_text(json.dumps(spine_clean, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if isinstance(spec.get("options_package"), dict) and spec["options_package"]:
        (out / "options_plan.json").write_text(json.dumps(spec["options_package"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    bq = spec.get("business_quality")
    if isinstance(bq, dict) and bq:
        (out / "business_quality.json").write_text(json.dumps(bq, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif spec.get("business_quality_verdict"):
        bq_synth = {
            "symbol": str(spec.get("symbol", "")).upper(),
            "business_quality_verdict": spec["business_quality_verdict"],
            "kpi_health": spec.get("kpi_health") or "PASS_WITH_WATCH",
            "summary_rationale": strip_html(spec.get("primer") or spec.get("holding_rationale") or ""),
        }
        (out / "business_quality.json").write_text(json.dumps(bq_synth, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    chapters = spec.get("chapters") or []
    for idx, ch in enumerate(chapters):
        raw_cid = ch.get("id") or f"ch-{idx}"
        norm_cid = "ch-0" if (idx == 0 and raw_cid == "primer") else raw_cid
        ch_copy = {**ch, "id": norm_cid}
        (ch_out / f"ch{idx:02d}.json").write_text(json.dumps(ch_copy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rev_path = out / "revision_log.json"
    rev_data = {"symbol": str(spec["symbol"]).upper(), "market": str(spec["market"]).upper(), "history": []}
    if rev_path.is_file():
        try:
            loaded = json.loads(rev_path.read_text(encoding="utf-8"))
            if isinstance(loaded.get("history"), list):
                rev_data["history"] = loaded["history"]
        except ValueError:
            pass

    ra = spec.get("refresh_audit") if isinstance(spec.get("refresh_audit"), dict) else {}
    rev_entry = {
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "as_of": spec.get("as_of"),
        "mode": ra.get("recommended_tier") or mode,
        "verdict": spec.get("new_capital_verdict") or spec.get("verdict"),
        "holding_action": spec.get("holding_action"),
        "conviction_tier": spec.get("conviction_tier"),
        "business_quality_verdict": spec.get("business_quality_verdict"),
        "entry_zone_low": spec.get("entry_zone_low"),
        "entry_zone_high": spec.get("entry_zone_high"),
        "stop_loss": spec.get("stop_loss"),
        "target_base": spec.get("target_base"),
        "blind_spots_patched": [
            b.get("what_was_missed")
            for b in (ra.get("blind_spots_discovered") or [])
            if isinstance(b, dict) and b.get("materiality") == "MATERIAL_PATCHED"
        ],
        "assumptions_changed": [
            f"{a.get('disposition')}: {a.get('claim')}"
            for a in (ra.get("assumptions_checked") or [])
            if isinstance(a, dict) and a.get("disposition") in {"WEAKENED", "BROKEN", "CONFIRMED"}
        ],
    }
    rev_data["history"].append(rev_entry)
    rev_path.write_text(json.dumps(rev_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate monograph specs and price-blind Pass 1 checkpoints.")
    ap.add_argument("--check-blind-pass", help="Validate <RUN_DIR>/work/<SYM> after Pass 1 (ch01..ch06 + business_quality.json)")
    ap.add_argument("--check-spec", help="Validate full monograph spec directory or JSON file")
    args = ap.parse_args()
    if args.check_blind_pass:
        errs = validate_blind_pass_dir(args.check_blind_pass)
        if errs:
            print(f"BLIND PASS CHECK: FAIL ({len(errs)} error(s))")
            for e in errs:
                print(" -", e)
            sys.exit(1)
        print(f"BLIND PASS CHECK: PASS ({args.check_blind_pass})")
        return
    if args.check_spec:
        spec = load_monograph_spec(args.check_spec)
        errs, stats = validate_monograph_spec(spec)
        if errs:
            print(f"SPEC CHECK: FAIL ({len(errs)} error(s))")
            for e in errs:
                print(" -", e)
            sys.exit(1)
        print(f"SPEC CHECK: PASS (web={stats.get('web_words', 0):,}w, book={stats.get('book_words', 0):,}w)")
        return
    ap.error("Specify --check-blind-pass or --check-spec")


if __name__ == "__main__":
    main()
