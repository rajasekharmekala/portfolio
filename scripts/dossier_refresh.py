#!/usr/bin/env python3
"""Companion Dossier Refresh & Blind-Spot Brainstorm Engine.

Drives unbiased, token-efficient re-evaluation of previously underwritten companies:
  1. `bootstrap`      — Extracts canonical chapter JSON specs (`data/dossiers/<MKT>/<SYM>/`)
                        from existing published `_dossier.html` pages when no JSON spec exists yet.
  2. `prepare`        — Copies ONLY `ch01..ch06` + `business_quality.json` into `<RUN_DIR>/work/<SYM>/`,
                        locks the prior stop/verdict in `prior_anchor_locked.json`, and writes
                        `blind_refresh_packet.md` (100% stripped of prior verdicts, prices, targets,
                        and stops) with the 6-Vector Blind-Spot & Omission Brainstorm Matrix.
  3. `validate-audit` — Mechanically verifies `refresh_audit.json` BEFORE live prices/technicals are
                        unlocked: requires concrete re-tested assumptions, >= 2 researched blind spots
                        across distinct vectors, proof by SHA-256 hash diff that any `MATERIAL_PATCHED`
                        blind spot or `WEAKENED`/`BROKEN` assumption actually updated its owning chapter
                        JSON, and zero leaked verdict/timing tokens.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup, Tag

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dossier_schema import (  # noqa: E402
    BLIND_VERDICT_LEAK_RE,
    CANONICAL_10_CHAPTERS,
    enforce_stop_loss_ratchet,
    load_monograph_spec,
    persist_monograph_spec,
    strip_html,
    validate_blind_pass_dir,
)

REPO = Path(__file__).resolve().parents[1]

REFRESH_TIERS = {
    "TIER_1_TAPE_VALUATION",
    "TIER_2_QUARTERLY_OR_BLINDSPOT",
    "TIER_3_THESIS_BREAK",
}
ASSUMPTION_DISPOSITIONS = {"CONFIRMED", "UNCHANGED", "WEAKENED", "BROKEN"}
BLINDSPOT_VECTORS = {
    "CUSTOMER_SUPPLIER_CONCENTRATION",
    "FOOTNOTE_BALANCE_SHEET_FORENSICS",
    "UNIT_ECONOMICS_HIDDEN_FRICTION",
    "UNLISTED_OR_ADJACENT_COMPETITION",
    "REGULATORY_TARIFF_FX_EXPOSURE",
    "GOVERNANCE_INCENTIVES_CAPITAL_ALLOCATION",
}
BLINDSPOT_MATERIALITY = {"MATERIAL_PATCHED", "IMMATERIAL_VERIFIED"}


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_money(text: str) -> List[float]:
    cleaned = text.replace(",", "")
    return [float(m) for m in re.findall(r"(?:[₹$]\s*)?(\d+(?:\.\d+)?)", cleaned)]


def _scrub_blind_verdict_tokens(text: str) -> str:
    """Neutralize legacy verdict enum tokens when bootstrapping an older HTML dossier into Pass 1."""
    replacements = {
        "IMMEDIATE_BUY": "immediate deployment",
        "ACCUMULATE_ON_DIP": "pullback accumulation",
        "WAIT_FOR_SUPPORT": "patience on valuation/entry",
        "BUY_AT_CMP_NO_FOMO": "unextended trend",
        "WAIT_FOR_SUPPORT_PULLBACK": "extended trend",
        "WAIT_FOR_SUPPORT_RETEST": "consolidation retest",
        "AVOID_STAGE4_OR_BROKEN": "broken trend",
        "TIER_0": "unqualified tier",
        "TIER_1": "highest quality tier",
        "TIER_2": "core quality tier",
        "TIER_3": "conditional quality tier",
        "CORE_ALPHA": "long-duration compounding",
        "TACTICAL_MOMENTUM": "cyclical momentum",
        "LEVERAGED_SATELLITE": "satellite exposure",
    }
    out = text
    for token, repl in replacements.items():
        out = re.sub(rf"\b{re.escape(token)}\b", repl, out, flags=re.I)
    out = re.sub(r"support buy zone", "technical reference band", out, flags=re.I)
    out = re.sub(r"invalidation stop", "downside reference level", out, flags=re.I)
    return out


def bootstrap_from_html(
    dossier_html_path: Path,
    target_dir: Path,
    market: str,
    symbol: str,
) -> Path:
    """Parse a published 10-chapter _dossier.html into canonical JSON files under target_dir."""
    if not dossier_html_path.is_file():
        raise FileNotFoundError(f"Published dossier HTML not found: {dossier_html_path}")
    soup = BeautifulSoup(dossier_html_path.read_text(encoding="utf-8"), "html.parser")
    meta = {t.get("name"): t.get("content", "") for t in soup.select("meta[name]")}
    as_of = meta.get("research-as-of") or "2026-11-01"
    sector = meta.get("report-sector") or ""
    h1 = soup.select_one("main.report h1") or soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else f"{symbol} — Deep Investment & Business Monograph"

    # Extract key-figures metadata
    kf_map: Dict[str, str] = {}
    for div in soup.select("dl.key-figures > div"):
        dt_el, dd_el = div.find("dt"), div.find("dd")
        if dt_el and dd_el:
            kf_map[dt_el.get_text(" ", strip=True).lower()] = dd_el.get_text(" ", strip=True)

    verdict_raw = kf_map.get("new capital verdict") or kf_map.get("verdict") or "WAIT_FOR_SUPPORT"
    verdict = "WAIT_FOR_SUPPORT"
    for cand in ("IMMEDIATE_BUY", "ACCUMULATE_ON_DIP", "WAIT_FOR_SUPPORT", "REJECTED"):
        if cand in verdict_raw.upper().replace(" ", "_"):
            verdict = cand
            break
    arch_m = re.search(r"\(([A-Z0-9_]+)\)", verdict_raw)
    archetype = arch_m.group(1) if arch_m else "COMPOUNDER"
    bucket = (kf_map.get("strategy bucket") or "CORE_ALPHA").strip().upper()
    tier_m = re.search(r"(TIER_[0-3])", kf_map.get("risk-unit sizing", ""))
    tier = tier_m.group(1) if tier_m else ("TIER_0" if verdict == "REJECTED" else "TIER_2")

    zone_txt = next((v for k, v in kf_map.items() if "zone" in k or "band" in k), "")
    zone_nums = _parse_money(zone_txt)
    entry_low = zone_nums[0] if len(zone_nums) >= 1 else 90.0
    entry_high = zone_nums[1] if len(zone_nums) >= 2 else entry_low * 1.05
    stop_m = re.search(r"Stop:\s*[₹$]?\s*([\d,]+(?:\.\d+)?)", zone_txt, re.I)
    stop_loss = float(stop_m.group(1).replace(",", "")) if stop_m else (zone_nums[2] if len(zone_nums) >= 3 else round(entry_low * 0.9, 2))

    tgt_txt = next((v for k, v in kf_map.items() if "target" in k or "scenario" in k), "")
    tgt_nums = _parse_money(tgt_txt)
    if "bear" in tgt_txt.lower() and len(tgt_nums) >= 3:
        target_bear, target_base, target_bull = tgt_nums[0], tgt_nums[1], tgt_nums[2]
    elif len(tgt_nums) >= 2:
        target_base, target_bull = tgt_nums[0], tgt_nums[1]
        target_bear = round(stop_loss * 0.9, 2)
    else:
        target_base = round(entry_high * 1.25, 2)
        target_bull = round(entry_high * 1.5, 2)
        target_bear = round(stop_loss * 0.9, 2)
    if verdict != "REJECTED" and target_base <= entry_high:
        # Ensure bootstrapped non-rejected baseline has valid order; refresh will re-underwrite it
        target_base = round(entry_high + max(1.0, (entry_high - stop_loss) * 1.6), 2)
        target_bull = max(target_bull, round(target_base * 1.2, 2))

    primer_sec = soup.select_one("section.primer#primer p")
    primer_text = primer_sec.get_text(" ", strip=True) if primer_sec else f"{symbol} institutional monograph baseline."

    hold_sec = soup.select_one("section#holding-action")
    holding_action = (hold_sec.get("data-holding-action") if hold_sec else None) or "NOT_HELD"
    holding_p = hold_sec.find("p").get_text(" ", strip=True) if (hold_sec and hold_sec.find("p")) else "No position held."
    alerts = []
    if hold_sec and hold_sec.find("table"):
        for tr in hold_sec.find("table").select("tbody tr"):
            tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(tds) >= 3:
                sh = _parse_money(tds[1])
                alerts.append({"trigger": tds[0], "shares": sh[0] if sh else 0, "instruction": tds[2]})
    if not alerts:
        alerts = [{"trigger": f"Close below {stop_loss}", "shares": 0, "instruction": "Reassess thesis at structural stop."}]

    redeploy_sec = soup.select_one("section#capital-redeployment")
    cap_source = (redeploy_sec.get("data-capital-base") if redeploy_sec else None) or "Incremental capital under review"
    destinations = []
    if redeploy_sec and redeploy_sec.find("table"):
        for tr in redeploy_sec.find("table").select("tbody tr"):
            tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            dtype = tr.get("data-destination") or (tds[0].upper() if tds else "CASH")
            if dtype in {"CASH", "SHORTLIST", "OUTSIDE"} and len(tds) >= 11:
                pct_nums = _parse_money(tds[2])
                pct = pct_nums[0] if pct_nums else 0.0
                cand = tds[1] if tds[1] not in {"Cash reserve", "No selected shortlist name", "No selected outside name"} else None
                tb_nums = _parse_money(tds[6])
                as_nums = _parse_money(tds[7])
                row_obj: Dict[str, Any] = {
                    "destination_type": dtype,
                    "allocation_pct": pct,
                    "recommendation": tds[8],
                    "entry_condition": tds[9],
                    "rationale": tds[10],
                }
                if cand and dtype != "CASH":
                    row_obj["symbol"] = cand
                    row_obj["target_base"] = tb_nums[0] if tb_nums else 100.0
                    row_obj["asymmetry_ratio"] = as_nums[0] if as_nums else 2.0
                destinations.append(row_obj)
    if {d["destination_type"] for d in destinations} != {"CASH", "SHORTLIST", "OUTSIDE"}:
        destinations = [
            {"destination_type": "CASH", "allocation_pct": 100, "recommendation": "Retain cash", "rationale": "Baseline import.", "entry_condition": "Await refresh review."},
            {"destination_type": "SHORTLIST", "allocation_pct": 0, "recommendation": "None", "rationale": "Baseline import.", "entry_condition": "Await refresh review."},
            {"destination_type": "OUTSIDE", "allocation_pct": 0, "recommendation": "None", "rationale": "Baseline import.", "entry_condition": "Await refresh review."},
        ]

    # Extract chapters
    ch_sections = [
        s for s in soup.select("main.report section.chapter")
        if s.get("id") not in {"holding-action", "capital-redeployment", "gate-exceptions"}
    ]
    chapters: List[Dict[str, Any]] = []
    for idx, sec in enumerate(ch_sections[:10]):
        cid = "ch-0" if idx == 0 else (sec.get("id") or f"ch-{idx}")
        h2 = sec.find("h2")
        w_title = h2.get_text(" ", strip=True) if h2 else CANONICAL_10_CHAPTERS[idx][1]
        q_el = sec.select_one(".section-summary")
        question = re.sub(r"^Core Investor Question:\s*", "", q_el.get_text(" ", strip=True), flags=re.I) if q_el else ""

        web_blocks: List[Dict[str, Any]] = []
        book_paras: List[str] = []
        used_takeaway_ps: set[int] = set()

        for child in sec.children:
            if not isinstance(child, Tag):
                continue
            classes = child.get("class") or []
            if child.name == "h2" or "section-summary" in classes or "tradingview-widget-container" in classes:
                continue
            if child.name == "h3":
                t_txt = child.get_text(" ", strip=True)
                if "momentum screen and no-fomo" in t_txt.lower() or "no-fomo support entry zone" in t_txt.lower():
                    continue
                web_blocks.append({"type": "h3", "title": t_txt})
            elif child.name == "div" and "table-wrap" in classes:
                tbl = child.find("table")
                if not tbl:
                    continue
                cap = tbl.find("caption").get_text(" ", strip=True) if tbl.find("caption") else ""
                if any(skip in cap.lower() for skip in ("dated market-facts ledger for", "trend and no-fomo entry timing evaluation", "no-fomo execution levels and risk-unit")):
                    nxt = child.find_next_sibling()
                    if isinstance(nxt, Tag) and nxt.name == "p":
                        used_takeaway_ps.add(id(nxt))
                    continue
                headers = [th.get_text(" ", strip=True) for th in tbl.select("thead th")]
                rows = [[td.decode_contents().strip() for td in tr.find_all(["td", "th"])] for tr in tbl.select("tbody tr")]
                nxt = child.find_next_sibling()
                takeaway = ""
                if isinstance(nxt, Tag) and nxt.name == "p":
                    takeaway = nxt.decode_contents().strip()
                    used_takeaway_ps.add(id(nxt))
                web_blocks.append({"type": "table", "caption": cap, "headers": headers, "rows": rows, "takeaway": takeaway})
            elif child.name == "div" and ("callout" in classes or "case-note" in classes):
                c_title_el = child.select_one(".callout-title, .case-note-title")
                c_title = c_title_el.get_text(" ", strip=True) if c_title_el else ""
                c_ps = [p.decode_contents().strip() for p in child.find_all("p") if "callout-title" not in (p.get("class") or [])]
                variant = "case" if "case-note" in classes else ("warn" if "callout-warn" in classes else ("rule" if "callout-rule" in classes else "primer"))
                web_blocks.append({"type": "callout", "variant": variant, "title": c_title, "paragraphs": c_ps})
                book_paras.extend(strip_html(p) for p in c_ps if strip_html(p))
            elif child.name == "p":
                if id(child) in used_takeaway_ps:
                    continue
                if "trigger" in classes:
                    web_blocks.append({"type": "trigger", "html": child.decode_contents().strip()})
                else:
                    raw_h = child.decode_contents().strip()
                    web_blocks.append({"type": "p", "html": raw_h})
                    if strip_html(raw_h):
                        book_paras.append(strip_html(raw_h))

        if cid in {f"ch-{n}" for n in range(1, 7)}:
            for blk in web_blocks:
                for k in ("html", "text", "caption", "takeaway", "title"):
                    if isinstance(blk.get(k), str):
                        blk[k] = _scrub_blind_verdict_tokens(blk[k])
                if isinstance(blk.get("paragraphs"), list):
                    blk["paragraphs"] = [_scrub_blind_verdict_tokens(p) for p in blk["paragraphs"]]
                if isinstance(blk.get("rows"), list):
                    blk["rows"] = [[_scrub_blind_verdict_tokens(str(c)) for c in r] for r in blk["rows"]]
            book_paras = [_scrub_blind_verdict_tokens(p) for p in book_paras]

        chapters.append({
            "id": cid,
            "web_title": w_title,
            "book_title": CANONICAL_10_CHAPTERS[idx][1] if idx < len(CANONICAL_10_CHAPTERS) else w_title,
            "question": _scrub_blind_verdict_tokens(question) if cid in {f"ch-{n}" for n in range(1, 7)} else question,
            "epigraph": {"quote": question or w_title, "author": "Institutional Research Desk"},
            "web_blocks": web_blocks,
            "book_paragraphs": book_paras or [strip_html(primer_text)],
        })

    citations = [li.decode_contents().strip() for li in soup.select("#notes ol li")]
    bq_default = "FUNDAMENTAL_FAIL" if verdict == "REJECTED" else ("CYCLICAL_CONDITIONAL" if tier == "TIER_3" else "COMPOUNDER_PASS")
    kpi_default = "FAIL" if bq_default == "FUNDAMENTAL_FAIL" else ("PASS_WITH_WATCH" if bq_default == "CYCLICAL_CONDITIONAL" else "PASS")

    spec = {
        "symbol": symbol.upper(),
        "market": market.upper(),
        "as_of": as_of,
        "sector": sector,
        "title": title,
        "primer": primer_text,
        "verdict": verdict,
        "new_capital_verdict": verdict,
        "business_quality_verdict": bq_default,
        "kpi_health": kpi_default,
        "archetype": archetype,
        "strategy_bucket": bucket if bucket in {"CORE_ALPHA", "TACTICAL_MOMENTUM", "LEVERAGED_SATELLITE", "LEAPS_OPTIONS"} else "CORE_ALPHA",
        "conviction_tier": tier,
        "entry_zone_low": entry_low,
        "entry_zone_high": entry_high,
        "stop_loss": stop_loss,
        "target_base": target_base,
        "target_bull": target_bull,
        "target_bear": target_bear,
        "holding_action": holding_action,
        "holding_shares_to_sell": sum(a.get("shares", 0) for a in alerts) if holding_action in {"TRIM_INTO_STRENGTH", "TRIM_OVERWEIGHT", "EXIT_IMMEDIATELY", "EXIT_ON_BOUNCE"} else 0,
        "holding_rationale": holding_p,
        "holding_alerts": alerts,
        "redeployment_plan": {"capital_source": cap_source, "destinations": destinations},
        "citations": citations,
        "business_quality": {
            "symbol": symbol.upper(),
            "business_quality_verdict": bq_default,
            "kpi_health": kpi_default,
            "summary_rationale": _scrub_blind_verdict_tokens(
                f"Bootstrapped baseline operating synthesis for {symbol.upper()} from {as_of} monograph for refresh verification."
            ),
        },
        "chapters": chapters,
    }
    return persist_monograph_spec(spec, target_dir, mode="bootstrapped_from_html")


def prepare_refresh_workspace(
    market: str,
    symbol: str,
    out_dir: Path,
    repo_root: Path = REPO,
) -> Dict[str, Any]:
    """Create a verdict-stripped refresh workspace for Pass 1 Assumption Audit + Blind-Spot Brainstorm."""
    mkt = market.upper()
    sym = symbol.upper()
    canon_dir = repo_root / "data" / "dossiers" / mkt / sym
    if not (canon_dir / "spine.json").is_file():
        html_path = repo_root / "docs" / "blogs" / mkt / f"{sym}_dossier.html"
        bootstrap_from_html(html_path, canon_dir, mkt, sym)

    prior_spec = load_monograph_spec(canon_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "chapters").mkdir(parents=True, exist_ok=True)

    baseline_hashes: Dict[str, str] = {}
    for n in range(1, 7):
        src = canon_dir / "chapters" / f"ch0{n}.json"
        if not src.is_file():
            raise FileNotFoundError(f"Canonical spec missing {src}")
        dst = out_dir / "chapters" / f"ch0{n}.json"
        shutil.copy2(src, dst)
        baseline_hashes[f"ch-{n}"] = _sha256_path(dst)

    bq_src = canon_dir / "business_quality.json"
    bq_dst = out_dir / "business_quality.json"
    if bq_src.is_file():
        shutil.copy2(bq_src, bq_dst)
    else:
        bq_fallback = {
            "symbol": sym,
            "business_quality_verdict": prior_spec.get("business_quality_verdict") or "CYCLICAL_CONDITIONAL",
            "kpi_health": prior_spec.get("kpi_health") or "PASS_WITH_WATCH",
            "summary_rationale": f"Prior operating synthesis for {sym} awaiting refresh verification.",
        }
        bq_dst.write_text(json.dumps(bq_fallback, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    baseline_hashes["business_quality"] = _sha256_path(bq_dst)

    (out_dir / "baseline_hashes.json").write_text(
        json.dumps(baseline_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # Lock prior anchor strictly for code-level stop-ratchet and delta comparison in Pass 2
    prior_anchor = {
        "symbol": sym,
        "market": mkt,
        "as_of": prior_spec.get("as_of"),
        "verdict": prior_spec.get("new_capital_verdict") or prior_spec.get("verdict"),
        "holding_action": prior_spec.get("holding_action"),
        "conviction_tier": prior_spec.get("conviction_tier"),
        "entry_zone_low": prior_spec.get("entry_zone_low"),
        "entry_zone_high": prior_spec.get("entry_zone_high"),
        "stop_loss": prior_spec.get("stop_loss"),
        "target_base": prior_spec.get("target_base"),
        "citations": prior_spec.get("citations") or [],
    }
    (out_dir / "prior_anchor_locked.json").write_text(
        json.dumps(prior_anchor, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Build verdict-stripped blind_refresh_packet.md for the isolated Pass 1 audit subagent
    lines = [
        f"# Verdict-Stripped Assumption Audit & Blind-Spot Brainstorm Packet: {sym} ({mkt})",
        "",
        f"- **Prior Research Cutoff (`as_of`):** {prior_spec.get('as_of', 'unknown')}",
        "- **Information Barrier:** Prior portfolio verdicts, valuation targets, entry zones, and stop losses are intentionally stripped. Do NOT read `prior_anchor_locked.json`, `docs/blogs/`, `data/shortlist/`, or `data/watchlist/` during Pass 1.",
        "",
        "## Part 1 — Challenge & Re-Verify Existing Chapter 1–6 Claims Since Prior Cutoff",
        "Search all quarterly/annual filings, concall transcripts, NSE/BSE or SEC disclosures, insider transactions, and competitor developments since the prior cutoff. Score key claims in `refresh_audit.json -> assumptions_checked` (`CONFIRMED`, `UNCHANGED`, `WEAKENED`, or `BROKEN`).",
        "",
        "## Part 2 — Mandatory Blind-Spot & Omission Brainstorm (What Did the Original Dossier Miss?)",
        "Brainstorm and investigate at least **2 distinct blind-spot vectors** that the original Chapters 1–6 overlooked or under-analyzed:",
        "1. `CUSTOMER_SUPPLIER_CONCENTRATION` — unnamed top-customer dependence, distributor channel stuffing, single-source imported BOM/silicon risk.",
        "2. `FOOTNOTE_BALANCE_SHEET_FORENSICS` — contingent liabilities, related-party transactions, capitalized intangibles/CWIP, receivables aging, warrant/SBC overhang, lease obligations.",
        "3. `UNIT_ECONOMICS_HIDDEN_FRICTION` — warranty/field-service burn, customer churn, implementation/DSO drag, margin dilution as product mix shifts.",
        "4. `UNLISTED_OR_ADJACENT_COMPETITION` — private/PE-backed domestic rivals, Chinese supply-chain deflation, hyperscaler/OEM vertical integration.",
        "5. `REGULATORY_TARIFF_FX_EXPOSURE` — import duties, government tender dependence, environmental/FDA/compliance risk, currency mismatch.",
        "6. `GOVERNANCE_INCENTIVES_CAPITAL_ALLOCATION` — insider selling, promoter pledges, CFO/auditor turnover, M&A empire-building vs ROIC.",
        "",
        "For every `MATERIAL_PATCHED` blind spot or `WEAKENED`/`BROKEN` assumption, **update the owning `chapters/ch01.json..ch06.json` (both `web_blocks` and `book_paragraphs`) and `business_quality.json` directly**. Code verifies SHA-256 diffs on the patched chapter files.",
        "",
        "## Baseline Chapters 1–6 Digest (Verdict-Stripped)",
    ]
    for n in range(1, 7):
        ch = json.loads((out_dir / "chapters" / f"ch0{n}.json").read_text(encoding="utf-8"))
        lines.append(f"\n### ch-{n}: {ch.get('web_title', f'Chapter {n}')}")
        if ch.get("question"):
            lines.append(f"- **Question:** {ch['question']}")
        snippets = []
        for blk in ch.get("web_blocks", []):
            if blk.get("type") == "h3":
                snippets.append(f"  - Subheading: {blk.get('title')}")
            elif blk.get("type") == "table":
                snippets.append(f"  - Table: {blk.get('caption') or 'Data table'} ({len(blk.get('rows', []))} rows)")
            elif blk.get("type") == "p" and len(snippets) < 8:
                snippets.append(f"  - Claim excerpt: {strip_html(blk.get('html') or blk.get('text', ''))[:220]}...")
        lines.extend(snippets[:10])

    packet_path = out_dir / "blind_refresh_packet.md"
    packet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "symbol": sym,
        "market": mkt,
        "canonical_spec_dir": str(canon_dir),
        "work_dir": str(out_dir),
        "blind_packet": str(packet_path),
        "prior_as_of": prior_spec.get("as_of"),
    }


def validate_refresh_audit(work_dir: Path) -> List[str]:
    """Verify Pass 1 refresh_audit.json + proof-of-patch hashes + price-blind chapter integrity."""
    errors = validate_blind_pass_dir(work_dir)
    audit_path = work_dir / "refresh_audit.json"
    hashes_path = work_dir / "baseline_hashes.json"
    if not audit_path.is_file():
        return errors + [f"Missing refresh_audit.json in {work_dir}"]
    if not hashes_path.is_file():
        return errors + [f"Missing baseline_hashes.json in {work_dir} (run dossier_refresh.py prepare first)"]

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    baseline_hashes = json.loads(hashes_path.read_text(encoding="utf-8"))

    tier = audit.get("recommended_tier")
    if tier not in REFRESH_TIERS:
        errors.append(f"refresh_audit.recommended_tier must be one of {sorted(REFRESH_TIERS)}")

    raw_audit_str = json.dumps(audit, ensure_ascii=False)
    leak = BLIND_VERDICT_LEAK_RE.search(raw_audit_str)
    if leak:
        errors.append(f"refresh_audit.json leaks portfolio verdict/timing token {leak.group(0)!r} during price-blind Pass 1")

    assumptions = audit.get("assumptions_checked")
    if not isinstance(assumptions, list) or len(assumptions) < 3:
        errors.append("refresh_audit.assumptions_checked must audit at least 3 concrete baseline claims")
    else:
        for idx, item in enumerate(assumptions, 1):
            if not isinstance(item, dict):
                errors.append(f"assumptions_checked[{idx}] must be an object")
                continue
            ch_id = str(item.get("chapter") or "")
            disp = str(item.get("disposition") or "")
            if ch_id not in {f"ch-{n}" for n in range(1, 7)}:
                errors.append(f"assumptions_checked[{idx}].chapter must be ch-1..ch-6, got {ch_id!r}")
            if disp not in ASSUMPTION_DISPOSITIONS:
                errors.append(f"assumptions_checked[{idx}].disposition must be one of {sorted(ASSUMPTION_DISPOSITIONS)}")
            if len(str(item.get("claim") or "").strip()) < 15 or len(str(item.get("evidence") or "").strip()) < 20:
                errors.append(f"assumptions_checked[{idx}] requires substantive 'claim' and 'evidence'")
            if not str(item.get("source_url") or "").startswith(("http://", "https://")):
                errors.append(f"assumptions_checked[{idx}] requires verifiable http(s) 'source_url'")
            if disp in {"WEAKENED", "BROKEN"} and ch_id in baseline_hashes:
                ch_num = ch_id.split("-")[1]
                cur_hash = _sha256_path(work_dir / "chapters" / f"ch0{ch_num}.json")
                if cur_hash == baseline_hashes[ch_id]:
                    errors.append(
                        f"assumptions_checked[{idx}] marked {disp} on {ch_id}, "
                        f"but chapters/ch0{ch_num}.json was NOT updated"
                    )

    blind_spots = audit.get("blind_spots_discovered")
    if not isinstance(blind_spots, list) or len(blind_spots) < 2:
        errors.append("refresh_audit.blind_spots_discovered must evaluate at least 2 omitted/under-analyzed risk or moat vectors")
    else:
        seen_vectors = set()
        for idx, b in enumerate(blind_spots, 1):
            if not isinstance(b, dict):
                errors.append(f"blind_spots_discovered[{idx}] must be an object")
                continue
            vec = str(b.get("vector") or "")
            tch = str(b.get("target_chapter") or "")
            mat = str(b.get("materiality") or "")
            if vec not in BLINDSPOT_VECTORS:
                errors.append(f"blind_spots_discovered[{idx}].vector must be one of {sorted(BLINDSPOT_VECTORS)}")
            else:
                seen_vectors.add(vec)
            if tch not in {f"ch-{n}" for n in range(1, 7)}:
                errors.append(f"blind_spots_discovered[{idx}].target_chapter must be ch-1..ch-6, got {tch!r}")
            if mat not in BLINDSPOT_MATERIALITY:
                errors.append(f"blind_spots_discovered[{idx}].materiality must be MATERIAL_PATCHED or IMMATERIAL_VERIFIED")
            if len(str(b.get("what_was_missed") or "").strip()) < 20 or len(str(b.get("evidence") or "").strip()) < 20:
                errors.append(f"blind_spots_discovered[{idx}] requires substantive 'what_was_missed' and 'evidence'")
            if not str(b.get("source_url") or "").startswith(("http://", "https://")):
                errors.append(f"blind_spots_discovered[{idx}] requires verifiable http(s) 'source_url'")
            if mat == "MATERIAL_PATCHED" and tch in baseline_hashes:
                ch_num = tch.split("-")[1]
                cur_hash = _sha256_path(work_dir / "chapters" / f"ch0{ch_num}.json")
                if cur_hash == baseline_hashes[tch]:
                    errors.append(
                        f"blind_spots_discovered[{idx}] marked MATERIAL_PATCHED on {tch}, "
                        f"but chapters/ch0{ch_num}.json was NOT updated"
                    )
        if len(seen_vectors) < 2:
            errors.append("blind_spots_discovered must cover at least 2 distinct blind-spot vectors")

    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    boot = sub.add_parser("bootstrap", help="Import existing _dossier.html files into data/dossiers/<MKT>/<SYM>/")
    boot.add_argument("--market", choices=["IN", "US"], required=True)
    boot.add_argument("--symbol", default="", help="Single symbol to bootstrap (or use --all)")
    boot.add_argument("--all", action="store_true", help="Bootstrap all published dossiers in market lacking specs")
    boot.add_argument("--force", action="store_true", help="Overwrite existing canonical spec")

    prep = sub.add_parser("prepare", help="Prepare verdict-stripped Pass 1 refresh workspace")
    prep.add_argument("--market", choices=["IN", "US"], required=True)
    prep.add_argument("--symbol", required=True)
    prep.add_argument("--out-dir", required=True, help="Target <RUN_DIR>/work/<SYM> directory")

    val = sub.add_parser("validate-audit", help="Validate Pass 1 refresh_audit.json and chapter patch hashes")
    val.add_argument("--work-dir", required=True, help="Path to <RUN_DIR>/work/<SYM>")

    rat = sub.add_parser("check-ratchet", help="Verify held-position stop-loss ratchet before publishing")
    rat.add_argument("--work-dir", required=True)
    rat.add_argument("--positions", required=True)
    rat.add_argument("--snapshot", default="")

    args = ap.parse_args()
    if args.command == "bootstrap":
        mkt = args.market.upper()
        blogs_dir = REPO / "docs" / "blogs" / mkt
        targets = (
            [blogs_dir / f"{args.symbol.upper()}_dossier.html"]
            if args.symbol
            else sorted(blogs_dir.glob("*_dossier.html"))
        )
        if not targets:
            raise SystemExit("Specify --symbol or --all")
        count = 0
        for hp in targets:
            if not hp.is_file() or 'name="report-redirect"' in hp.read_text(encoding="utf-8", errors="replace"):
                continue
            sym = hp.stem.replace("_dossier", "").upper()
            dest = REPO / "data" / "dossiers" / mkt / sym
            if (dest / "spine.json").is_file() and not args.force:
                continue
            bootstrap_from_html(hp, dest, mkt, sym)
            count += 1
        print(f"Bootstrapped {count} canonical dossier spec(s) for {mkt}")
    elif args.command == "prepare":
        info = prepare_refresh_workspace(args.market, args.symbol, Path(args.out_dir))
        print(json.dumps(info, indent=2))
    elif args.command == "validate-audit":
        errs = validate_refresh_audit(Path(args.work_dir))
        if errs:
            print(f"REFRESH AUDIT CHECK: FAIL ({len(errs)} error(s))")
            for e in errs:
                print(" -", e)
            sys.exit(1)
        print(f"REFRESH AUDIT CHECK: PASS ({args.work_dir})")
    elif args.command == "check-ratchet":
        spec = load_monograph_spec(args.work_dir)
        positions = json.loads(Path(args.positions).read_text(encoding="utf-8"))
        sym = str(spec["symbol"]).upper()
        pos_row = next((r for r in positions.get("consolidated", []) if r.get("symbol", "").upper() == sym), None)
        qty = float(pos_row.get("quantity", 0)) if pos_row else 0.0
        close = None
        if args.snapshot and Path(args.snapshot).is_file():
            snaps = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
            close = ((snaps.get("snapshots") or {}).get(sym) or {}).get("tradingview", {}).get("close")
        errs = enforce_stop_loss_ratchet(spec, qty, close)
        if errs:
            print("STOP RATCHET CHECK: FAIL")
            for e in errs:
                print(" -", e)
            sys.exit(1)
        print(f"STOP RATCHET CHECK: PASS ({sym}, held_qty={qty:g})")


if __name__ == "__main__":
    main()
