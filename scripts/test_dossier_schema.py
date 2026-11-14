import datetime
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup

import citation_check
from dossier_schema import validate_blind_pass_dir, validate_monograph_spec
from dossier_builder_template import (
    _decision_panels,
    _linkify_html_fragment,
    _render_waterfall_block,
    render_10chapter_monograph_editions,
)
from readability_check import check_dossier_decisions, check_grade, check_prose_integrity
from dossier_refresh import (
    bootstrap_from_html,
    prepare_refresh_workspace,
    validate_refresh_audit,
)
from options_desk_builder import patch_existing_dossier_html, render_options_desk_report
from options_snapshot import probe_browser_sessions, structure_options_setup
import portal_publish
import run_claims
from stock_snapshot import _strip_price_fields_for_blind_pass
from sync_dossier_pipeline import apply_pipeline_transition, verify_review_and_quality_gates


def valid_spec():
    return {
        "symbol": "TEST",
        "market": "US",
        "as_of": "2026-11-09",
        "title": "Test dossier",
        "verdict": "WAIT_FOR_SUPPORT",
        "new_capital_verdict": "WAIT_FOR_SUPPORT",
        "archetype": "COMPOUNDER",
        "strategy_bucket": "CORE_ALPHA",
        "conviction_tier": "TIER_2",
        "cmp": 92.0,
        "entry_zone_low": 90,
        "entry_zone_high": 95,
        "stop_loss": 85,
        "target_base": 120,
        "target_bull": 140,
        "target_bear": 70,
        "citations": [],
        "holding_action": "NOT_HELD",
        "holding_shares_to_sell": 0,
        "holding_rationale": "No current position is held.",
        "holding_alerts": [{"trigger": "Close at or below $85", "instruction": "Reassess entry thesis; no holding to sell", "shares": 0}],
        "redeployment_plan": {
            "capital_source": "Incremental capital under review",
            "destinations": [
                {"destination_type": "CASH", "allocation_pct": 100, "recommendation": "Retain as cash", "rationale": "No equity entry clears the current gate.", "entry_condition": "Reassess at the next support review."},
                {"destination_type": "SHORTLIST", "allocation_pct": 0, "recommendation": "No shortlist order", "rationale": "No active shortlist candidate has a superior actionable setup.", "entry_condition": "Reassess after a fresh snapshot."},
                {"destination_type": "OUTSIDE", "allocation_pct": 0, "recommendation": "No outside order", "rationale": "No researched peer clears the current gates.", "entry_condition": "Underwrite only after a confirmed setup."},
            ],
        },
        "chapters": [{"id": "ch-9", "web_blocks": [], "book_paragraphs": []}],
    }


class DossierDecisionSchemaTests(unittest.TestCase):
    def test_requires_cash_shortlist_and_outside_redeployment_and_full_reconciliation(self):
        errors, _ = validate_monograph_spec(valid_spec(), min_total_words=0)
        self.assertEqual(errors, [])

    def test_rejects_redeployment_that_omits_cash(self):
        spec = valid_spec()
        spec["redeployment_plan"]["destinations"] = spec["redeployment_plan"]["destinations"][1:]
        errors, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("assess CASH, SHORTLIST, and OUTSIDE" in error for error in errors))

    def test_rejects_not_held_with_nonzero_sell_quantity(self):
        spec = valid_spec()
        spec["holding_shares_to_sell"] = 1
        errors, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("NOT_HELD requires" in error for error in errors))

    def test_rejects_mismatched_new_capital_verdict(self):
        spec = valid_spec()
        spec["new_capital_verdict"] = "IMMEDIATE_BUY"
        errors, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("must match" in error for error in errors))

    def test_compiler_panels_show_actual_shares_action_and_three_destinations(self):
        spec = valid_spec()
        spec.update({
            "holding_action": "TRIM_INTO_STRENGTH",
            "holding_shares_to_sell": 2,
            "holding_rationale": "Reduce concentration while preserving the thesis.",
            "holding_alerts": [{"trigger": "Price reaches", "trigger_price": 110, "shares": 2,
                                "instruction": "Sell the trim tranche."}],
        })
        positions = {"net_worth": 200, "consolidated": [{
            "symbol": "TEST", "quantity": 5, "market_value": 100, "cost_basis": 90, "gain": 10,
            "accounts": [{"account": "Broker", "quantity": 5}],
        }]}
        _, holding_html, redeploy_html, _ = _decision_panels(spec, "US", "TEST", positions, {}, {})
        soup = BeautifulSoup(holding_html + redeploy_html, "html.parser")
        self.assertIn("recommend selling 2 shares and retaining 3", soup.get_text(" ", strip=True))
        self.assertEqual({row.get("data-destination") for row in soup.select("#capital-redeployment tr[data-destination]")},
                         {"CASH", "SHORTLIST", "OUTSIDE"})
        errors = []
        check_dossier_decisions(soup, errors)
        self.assertEqual(errors, [])

    def test_rejects_shell_variable_corruption_and_mangled_sanitizer_prose(self):
        spec = valid_spec()
        spec["chapters"] = [{
            "id": "ch-9",
            "web_blocks": [
                {"type": "p", "text": "Cocoa futures breached ,000/MT while rival valuations hit ~M+ Valuation."},
                {"type": "p", "text": "Kody commands a premium. : trailing earnings stalled. However, faces margin pressure."},
                {"type": "p", "text": "A. In addition, b. In addition, c. In addition, d."},
            ],
            "book_paragraphs": [],
        }]
        errors, _ = validate_monograph_spec(spec, min_total_words=0)
        joined = " | ".join(errors)
        self.assertIn("corrupted number fragment", joined)
        self.assertIn("corrupted currency magnitude", joined)
        self.assertIn("mangled punctuation", joined)
        self.assertIn("subjectless '. However, <verb>'", joined)
        self.assertIn("mechanical '. In addition, ...'", joined)

        html_doc = (
            '<main><section id="primer"><p>Thesis.</p></section>'
            '<section id="primer"><p>Breached ,000/MT. : bad split.</p></section></main>'
        )
        r_errors = []
        check_prose_integrity(BeautifulSoup(html_doc, "html.parser"), r_errors)
        r_joined = " | ".join(r_errors)
        self.assertIn("DUPLICATE SECTION ID", r_joined)
        self.assertIn("SHELL CORRUPTION", r_joined)
        self.assertIn("MANGLED PROSE", r_joined)

    def test_validates_waterfall_math_and_renders_deterministic_waterfall(self):
        spec = valid_spec()
        spec["chapters"] = [{
            "id": "ch-3",
            "web_blocks": [{
                "type": "table",
                "caption": "Worked $100 Revenue-to-FCF Waterfall",
                "headers": ["Line Item", "Amount per $100", "Share (%)", "Notes"],
                "rows": [
                    ["Profit Before Tax (PBT)", "24.80", "24.8%", "($26M on $84M revenue in FY26)"],
                    ["Cash Flow from Operations (CFO)", "14.29", "14.3%", "Audited CFO"],
                    ["Capital Expenditures (Capex)", "-28.00", "-28.0%", "Audited Capex"],
                    ["Free Cash Flow (FCF)", "-53.00", "-53.0%", "Broken FCF"],
                ],
                "takeaway": "Broken waterfall table.",
            }],
            "book_paragraphs": [],
        }, {"id": "ch-9", "web_blocks": [], "book_paragraphs": []}]
        errors, _ = validate_monograph_spec(spec, min_total_words=0)
        joined = " | ".join(errors)
        self.assertIn("contradicts note", joined)
        self.assertIn("waterfall cash-flow mismatch", joined)

        wf_html = _render_waterfall_block(
            {"period": "FY26", "unit": "Cr", "revenue": 84.0, "cogs": 38.9, "employee_cost": 14.6,
             "other_opex": 6.5, "da": 3.0, "interest": 2.0, "other_income": 7.0, "tax": 9.0,
             "cfo": 12.0, "capex": 86.0},
            "IN", "TEST", max_cite=5,
        )
        wf_text = BeautifulSoup(wf_html, "html.parser").get_text(" ", strip=True)
        # CFO (12/84 = 14.29) + Capex (-86/84 = -102.38) = FCF (-74/84 = -88.10)
        self.assertIn("14.29", wf_text)
        self.assertIn("-102.38", wf_text)
        self.assertIn("-88.10", wf_text)

    def test_enforces_url_floor_on_citations_and_learning_hub(self):
        spec = valid_spec()
        spec["citations"] = [f"Plain text reference {i} with no URL" for i in range(1, 26)]
        spec["chapters"] = [
            {"id": "ch-4", "web_blocks": [{"type": "p", "text": " ".join(["word"] * 20)}], "book_paragraphs": [" ".join(["word"] * 20)]},
            {"id": "ch-9", "web_blocks": [{"type": "p", "text": " ".join(["word"] * 20)}], "book_paragraphs": [" ".join(["word"] * 20)]},
        ]
        errors, _ = validate_monograph_spec(spec, min_web_words=10, min_book_words=10)
        joined = " | ".join(errors)
        self.assertIn("at least 15 distinct http(s) primary source URLs", joined)
        self.assertIn("Chapter ch-4 External Learning Hub must include at least 3 clickable http(s) resource URLs", joined)

        with tempfile.TemporaryDirectory() as tmp:
            rep = Path(tmp) / "unlinked_dossier.html"
            li = "".join(f"<li>Plain citation {i}</li>" for i in range(26))
            rep.write_text(f'<html><body><h2 id="references">Notes</h2><ol>{li}</ol></body></html>', encoding="utf-8")
            c_errors, _ = citation_check.check(str(rep), [], None, min_sources=25, max_age_days=60)
            self.assertTrue(any("URL FLOOR" in e for e in c_errors))

    def test_compiler_dedups_primer_id_autolinks_injects_tv_and_emits_sector(self):
        self.assertEqual(
            _linkify_html_fragment("Revenue grew [1, 2] in [2026]; see https://sec.gov/filing.", max_cite=5),
            'Revenue grew <sup class="reference"><a href="#cite_note-1">[1]</a>, <a href="#cite_note-2">[2]</a></sup> '
            'in [2026]; see <a href="https://sec.gov/filing" target="_blank" rel="noopener">https://sec.gov/filing</a>.',
        )

        spec = valid_spec()
        spec["primer"] = "Test Co builds power systems. Revenue grew 30% in FY26. Margins expanded steadily."
        spec["citations"] = [f"Filing {i}: https://sec{i}.example.com/10k" for i in range(1, 26)]
        filler = " ".join(["institutional"] * 950)
        book_filler = " ".join(["narrative"] * 1150)
        spec["chapters"] = [
            {"id": "primer", "web_title": "0. Executive Thesis", "web_blocks": [{"type": "p", "text": filler + " [1]"}], "book_paragraphs": [book_filler]},
            *[{"id": f"ch-{i}", "web_title": f"{i}. Chapter", "web_blocks": [
                {"type": "p", "text": filler + (" https://a.example.com/1 https://b.example.com/2 https://c.example.com/3" if i == 4 else "")}
            ], "book_paragraphs": [book_filler]} for i in range(1, 9)],
            {"id": "ch-9", "web_title": "9. Synthesis", "web_blocks": [
                {"type": "p", "text": filler},
                {"type": "trigger", "text": "Close below $85 invalidates the thesis and requires full exit."},
            ], "book_paragraphs": [book_filler]},
        ]
        snapshots = {"snapshots": {"TEST": {
            "tradingview": {"close": 100.0, "sector": "Technology", "exchange": "NASDAQ"},
            "stage2_evaluation": {"weinstein_stage": "STAGE_2", "entry_timing_posture": "BUY_AT_CMP_NO_FOMO",
                                  "support_buy_zone": [90.0, 95.0], "invalidation_stop": 85.0},
        }}}
        with tempfile.TemporaryDirectory() as tmp, patch("dossier_builder_template.build_pdf_book"):
            out = Path(tmp) / "TEST_dossier.html"
            render_10chapter_monograph_editions(
                spec, facts={}, snapshots=snapshots, positions={"consolidated": [], "net_worth": 1000},
                shortlist={"active": []}, out_dossier_path=out,
            )
            soup = BeautifulSoup(out.read_text(encoding="utf-8"), "html.parser")

        sec_ids = [s.get("id") for s in soup.select("main.report section[id]")]
        self.assertEqual(sec_ids.count("primer"), 1)
        self.assertIn("ch-0", sec_ids)
        self.assertIsNotNone(soup.select_one("#ch-8 .tradingview-widget-container"))
        self.assertIsNotNone(soup.select_one('meta[name="report-sector"][content="Technology"]'))
        self.assertIsNotNone(soup.select_one('#ch-0 sup.reference a[href="#cite_note-1"]'))
        self.assertGreaterEqual(len(soup.select('#notes a[href^="https://"]')), 25)
        kf_text = soup.select_one("dl.key-figures").get_text(" ", strip=True)
        self.assertIn("Technical Screen Signal", kf_text)
        self.assertIn("technical ceiling only", kf_text)
        self.assertIn("Bear $70.00 / Base $120.00 / Bull $140.00", kf_text)

    def test_blind_pass_strips_prices_and_blocks_premature_verdict_anchoring(self):
        raw_card = {
            "source_url": "https://www.screener.in/company/TEST/",
            "sector": "Industrials",
            "industry": "Electrical Equipment",
            "about": "Manufactures industrial generators.",
            "roce_pct": 28.4,
            "roe_pct": 22.1,
            "stock_pe": 128.0,
            "book_value": 159.0,
            "ratios": {
                "Market Cap": "2,240",
                "Current Price": "1,551",
                "Stock P/E": "128",
                "ROCE": "28.4%",
                "ROE": "22.1%",
            },
            "cons": ["Stock is trading at 9.76 times its book value", "Debtor days have increased from 120 to 192 days."],
            "tables": {"profit_loss": {"headers": ["Mar 2026"], "rows": {"Sales": ["84"]}}},
        }
        blind = _strip_price_fields_for_blind_pass(raw_card)
        self.assertNotIn("stock_pe", blind)
        self.assertNotIn("Stock P/E", blind["ratios"])
        self.assertNotIn("Current Price", blind["ratios"])
        self.assertIn("ROCE", blind["ratios"])
        self.assertEqual(blind["cons"], ["Debtor days have increased from 120 to 192 days."])

        with tempfile.TemporaryDirectory() as tmp:
            wdir = Path(tmp) / "TEST"
            (wdir / "chapters").mkdir(parents=True)
            (wdir / "business_quality.json").write_text(json.dumps({
                "business_quality_verdict": "COMPOUNDER_PASS",
                "kpi_health": "PASS",
                "summary_rationale": "Strong ROCE of 28%, clean cash conversion above 90% of PAT, and sticky OEM qualification moat.",
            }), encoding="utf-8")
            for i in range(1, 7):
                (wdir / "chapters" / f"ch0{i}.json").write_text(json.dumps({
                    "id": f"ch-{i}",
                    "web_blocks": [{"type": "p", "text": "Pure operational analysis of customer contracts and cash conversion."}],
                    "book_paragraphs": ["Pure narrative walkthrough of the factory floor."],
                }), encoding="utf-8")
            self.assertEqual(validate_blind_pass_dir(wdir), [])

            # Premature spine.json or leaked verdict token in ch-2 must fail Pass 1
            (wdir / "spine.json").write_text("{}", encoding="utf-8")
            (wdir / "chapters" / "ch02.json").write_text(json.dumps({
                "id": "ch-2",
                "web_blocks": [{"type": "p", "text": "We assign WAIT_FOR_SUPPORT in TIER_2 due to rich valuation."}],
                "book_paragraphs": [],
            }), encoding="utf-8")
            errs = validate_blind_pass_dir(wdir)
            joined = " | ".join(errs)
            self.assertIn("Premature spine.json", joined)
            self.assertIn("leaks portfolio verdict/timing token", joined)

    def test_anti_hedging_and_technical_ceiling_gates(self):
        # 1. FUNDAMENTAL_FAIL cannot be hedged as WAIT_FOR_SUPPORT
        spec1 = valid_spec()
        spec1["business_quality_verdict"] = "FUNDAMENTAL_FAIL"
        errs1, _ = validate_monograph_spec(spec1, min_total_words=0)
        self.assertTrue(any("FUNDAMENTAL_FAIL" in e for e in errs1))

        # 2. Target base <= entry_zone_high (e.g. KODYTECH ₹1,450 target vs ₹1,543 zone) is rejected
        spec2 = valid_spec()
        spec2["entry_zone_low"] = 1467
        spec2["entry_zone_high"] = 1543
        spec2["stop_loss"] = 1213
        spec2["target_base"] = 1450
        errs2, _ = validate_monograph_spec(spec2, min_total_words=0)
        self.assertTrue(any("Anti-hedging gate failed" in e for e in errs2))

        # 3. Technical timing ceiling CAP_WAIT_FOR_SUPPORT blocks IMMEDIATE_BUY
        spec3 = valid_spec()
        spec3["verdict"] = "IMMEDIATE_BUY"
        spec3["new_capital_verdict"] = "IMMEDIATE_BUY"
        snaps = {"snapshots": {"TEST": {
            "tradingview": {"close": 115.0},
            "stage2_evaluation": {"weinstein_stage": "STAGE_2", "entry_timing_posture": "WAIT_FOR_SUPPORT_PULLBACK",
                                  "technical_timing_gate": "CAP_WAIT_FOR_SUPPORT"},
        }}}
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Technical ceiling violation"):
                render_10chapter_monograph_editions(
                    spec3, snapshots=snaps, positions={"consolidated": [], "net_worth": 1000},
                    shortlist={"active": []}, out_dossier_path=Path(tmp) / "TEST_dossier.html",
                )

    def test_actionable_monograph_requires_positive_numeric_cmp(self):
        spec = valid_spec()
        spec.pop("cmp", None)
        errs, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("requires a positive numeric cmp" in e for e in errs))
        spec["cmp"] = 0
        errs, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("requires a positive numeric cmp" in e for e in errs))
        spec = valid_spec()
        spec["new_capital_verdict"] = "REJECTED"
        spec.pop("cmp", None)
        errs, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertFalse(any("requires a positive numeric cmp" in e for e in errs))

    def test_rejected_monograph_requires_known_rejection_reason_classes(self):
        spec = valid_spec()
        spec["verdict"] = spec["new_capital_verdict"] = "REJECTED"
        errs, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("REJECTED requires rejection_reasons" in e for e in errs))
        spec["rejection_reasons"] = []
        errs, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("REJECTED requires rejection_reasons" in e for e in errs))
        spec["rejection_reasons"] = ["VALUATION", "GUESSWORK"]
        errs, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertTrue(any("REJECTED requires rejection_reasons" in e for e in errs))
        spec["rejection_reasons"] = ["VALUATION", "CASH_FLOW"]
        errs, _ = validate_monograph_spec(spec, min_total_words=0)
        self.assertFalse(any("rejection_reasons" in e for e in errs))

    def test_tightened_dossier_readability_grade_and_sentence_cap(self):
        # Regular chapter > 15.0 fails, while #gate-exceptions between 15.0 and 16.5 passes; >24 word avg fails
        long_sent = (
            "The company manufactures industrial automation controllers and distributes integrated "
            "power conversion modules across regional enterprise customers while expanding factory "
            "utilization and maintaining strict contractual delivery schedules across every plant."
        )
        run_on = " ".join([long_sent] * 4)
        legal = (
            "As of September 30, 2026, promoter shares remain pledged to Catalyst Trusteeship Limited under acquisition debentures. "
            "This debt reflects parent acquisition financing rather than operating distress, yet exceeds our standard threshold."
        )
        soup = BeautifulSoup(
            f'<main><section id="primer"><p>Short crisp sentence one. Short crisp sentence two. Short crisp sentence three.</p></section>'
            f'<section class="chapter" id="ch-1"><p>{run_on}</p></section>'
            f'<section class="chapter" id="gate-exceptions"><p>{legal}</p></section></main>',
            "html.parser",
        )
        errs = []
        check_grade(soup, 15.0, errs, prose_only=True)
        joined = " | ".join(errs)
        self.assertIn("GRADE ch-1", joined)
        self.assertIn("SENTENCE LENGTH", joined)
        self.assertNotIn("GRADE gate-exceptions", joined)

    def test_deterministic_pipeline_sync_promote_monitor_discard_and_review_gate(self):
        snapshots = {"snapshots": {"TEST": {
            "tradingview": {"close": 96.0, "company_name": "Test Systems Inc", "sector": "Technology",
                            "industry": "Semiconductors", "market_cap": 15.0, "pe_ttm": 28.0, "roe_pct": 24.0,
                            "rsi_14_daily": 58.0},
            "stage2_evaluation": {"weinstein_stage": "STAGE_2", "entry_timing_posture": "BUY_AT_CMP_NO_FOMO"},
        }}}
        wl_init = {"active": [{
            "symbol": "TEST", "company_name": "Test Systems Inc", "source_type": "SCANNER",
            "status": "RESEARCH_REQUIRED", "action_verdict": "RESEARCH_REQUIRED",
            "kpi_health": "PENDING", "gate_status": "PENDING", "strategy_bucket": "CORE_ALPHA",
            "as_of_date": "2026-11-01", "research_cycle": 2,
        }]}
        sl_init = {"market": "US", "active": []}

        # 1. Qualified TIER_1 COMPOUNDER_PASS -> PROMOTE_TO_SHORTLIST (and mark watchlist COMPLETED at cycle 2)
        promote_spec = {
            **valid_spec(),
            "verdict": "IMMEDIATE_BUY",
            "new_capital_verdict": "IMMEDIATE_BUY",
            "conviction_tier": "TIER_1",
            "business_quality_verdict": "COMPOUNDER_PASS",
            "kpi_health": "PASS",
            "primer": "High-ROIC semiconductor leader in early Stage 2.",
        }
        r1 = apply_pipeline_transition(promote_spec, snapshots, wl_init, sl_init, today_iso="2026-11-12")
        self.assertEqual(r1["transition"], "PROMOTE_TO_SHORTLIST")
        self.assertEqual(len(r1["shortlist"]["active"]), 1)
        self.assertEqual(r1["shortlist"]["active"][0]["action_verdict"], "IMMEDIATE_BUY")
        self.assertEqual(r1["watchlist"]["active"][0]["status"], "COMPLETED")
        self.assertEqual(r1["watchlist"]["active"][0]["research_cycle"], 2)

        # 2. Conditional TIER_3 WAIT_FOR_SUPPORT -> KEEP_ON_WATCHLIST (and demote from shortlist)
        monitor_spec = {
            **valid_spec(),
            "conviction_tier": "TIER_3",
            "business_quality_verdict": "CYCLICAL_CONDITIONAL",
            "kpi_health": "PASS_WITH_WATCH",
        }
        r2 = apply_pipeline_transition(monitor_spec, snapshots, r1["watchlist"], r1["shortlist"], today_iso="2026-11-12")
        self.assertEqual(r2["transition"], "KEEP_ON_WATCHLIST")
        self.assertEqual(r2["shortlist"]["active"], [])
        self.assertEqual(r2["watchlist"]["active"][0]["status"], "COMPLETED")
        self.assertEqual(r2["watchlist"]["active"][0]["shortlist_action"], "MONITOR_ON_WATCHLIST")

        # 3. REJECTED -> DISCARD from both watchlist and shortlist
        reject_spec = {
            **valid_spec(),
            "verdict": "REJECTED",
            "new_capital_verdict": "REJECTED",
            "conviction_tier": "TIER_0",
            "business_quality_verdict": "FUNDAMENTAL_FAIL",
            "kpi_health": "FAIL",
        }
        r3 = apply_pipeline_transition(reject_spec, snapshots, r1["watchlist"], r1["shortlist"], today_iso="2026-11-12")
        self.assertEqual(r3["transition"], "DISCARD")
        self.assertEqual(r3["watchlist"]["active"], [])
        self.assertEqual(r3["shortlist"]["active"], [])

        # 4. Reviewer & Red-Team gate blocks unapproved dossiers and passes approved ones
        with tempfile.TemporaryDirectory() as tmp, patch("dossier_builder_template.build_pdf_book"):
            tdir = Path(tmp)
            dossier_file = tdir / "TEST_dossier.html"
            filler = " ".join(["The plant ships clean power racks to cloud buyers."] * 140)
            b_filler = " ".join(["You and I can see how the factory builds each unit on time."] * 140)
            full_spec = {
                **promote_spec,
                "primer": (
                    "Test Systems builds clean power racks for cloud data centers. "
                    "Sales grew 32% this year while cash flow stayed above net income. "
                    "We rate the stock an immediate buy with strong risk-reward."
                ),
                "citations": [f"SEC Filing {i}: https://sec{i}.example.com/10k" for i in range(1, 26)],
                "chapters": [
                    {"id": "ch-0", "web_title": "0. Executive Thesis", "web_blocks": [{"type": "p", "text": filler}], "book_paragraphs": [b_filler]},
                    *[{"id": f"ch-{i}", "web_title": f"{i}. Chapter", "web_blocks": [
                        {"type": "p", "text": filler + (" https://a.example.com/1 https://b.example.com/2 https://c.example.com/3" if i == 4 else "")}
                    ], "book_paragraphs": [b_filler]} for i in range(1, 7)],
                    {"id": "ch-7", "web_title": "7. Valuation", "web_blocks": [{"type": "p", "text": filler}], "book_paragraphs": [b_filler]},
                    {"id": "ch-8", "web_title": "8. Tape", "web_blocks": [{"type": "p", "text": filler}], "book_paragraphs": [b_filler]},
                    {"id": "ch-9", "web_title": "9. Synthesis", "web_blocks": [
                        {"type": "p", "text": filler},
                        {"type": "trigger", "text": "Daily close below $85 invalidates the Stage 2 breakout."},
                    ], "book_paragraphs": [b_filler]},
                ],
            }
            render_10chapter_monograph_editions(
                full_spec, snapshots=snapshots, positions={"consolidated": [], "net_worth": 1000},
                shortlist={"active": []}, out_dossier_path=dossier_file,
            )
            rev_dir = tdir / "review"
            (rev_dir / "round_1").mkdir(parents=True)
            (rev_dir / "round_1" / "round_1_review.json").write_text('{"verdict": "REVISE"}', encoding="utf-8")
            (rev_dir / "round_1" / "round_1_red_team.json").write_text('{"verdict": "APPROVE"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not APPROVE"):
                verify_review_and_quality_gates(dossier_file, review_dir=rev_dir)

            (rev_dir / "round_1" / "round_1_review.json").write_text('{"verdict": "APPROVE"}', encoding="utf-8")
            verify_review_and_quality_gates(dossier_file, review_dir=rev_dir)

    def test_companion_dossier_refresh_blindspot_brainstorm_and_stop_ratchet_e2e(self):
        with tempfile.TemporaryDirectory() as tmp, patch("dossier_builder_template.build_pdf_book"):
            repo = Path(tmp)
            (repo / "docs" / "blogs" / "US").mkdir(parents=True)
            (repo / "data" / "dossiers" / "US").mkdir(parents=True)
            (repo / "data" / "shortlist").mkdir(parents=True)
            (repo / "data" / "accounts" / "US").mkdir(parents=True)

            filler = " ".join(["The plant ships clean power racks to cloud buyers."] * 140)
            b_filler = " ".join(["You and I can see how the factory builds each unit on time."] * 140)
            init_spec = {
                **valid_spec(),
                "as_of": "2026-10-01",
                "verdict": "ACCUMULATE_ON_DIP",
                "new_capital_verdict": "ACCUMULATE_ON_DIP",
                "holding_action": "KEEP_COMPOUNDING",
                "holding_shares_to_sell": 0,
                "holding_rationale": "Retain active core position above structural stop.",
                "conviction_tier": "TIER_1",
                "business_quality_verdict": "COMPOUNDER_PASS",
                "kpi_health": "PASS",
                "primer": (
                    "Test Systems builds clean power racks for cloud data centers. "
                    "Sales grew 32% this year while cash flow stayed above net income. "
                    "We accumulate on pullbacks with disciplined risk management."
                ),
                "citations": [f"SEC Filing {i}: https://sec{i}.example.com/10k" for i in range(1, 26)],
                "chapters": [
                    {"id": "ch-0", "web_title": "0. Executive Thesis", "web_blocks": [{"type": "p", "text": filler}], "book_paragraphs": [b_filler]},
                    *[{"id": f"ch-{i}", "web_title": f"{i}. Chapter", "web_blocks": [
                        {"type": "p", "text": filler + (" https://a.example.com/1 https://b.example.com/2 https://c.example.com/3" if i == 4 else "")}
                    ], "book_paragraphs": [b_filler]} for i in range(1, 7)],
                    {"id": "ch-7", "web_title": "7. Valuation", "web_blocks": [{"type": "p", "text": filler}], "book_paragraphs": [b_filler]},
                    {"id": "ch-8", "web_title": "8. Tape", "web_blocks": [{"type": "p", "text": filler}], "book_paragraphs": [b_filler]},
                    {"id": "ch-9", "web_title": "9. Synthesis", "web_blocks": [
                        {"type": "p", "text": filler},
                        {"type": "trigger", "text": "Daily close below $85 invalidates the Stage 2 breakout."},
                    ], "book_paragraphs": [b_filler]},
                ],
            }
            snapshots_v1 = {"snapshots": {"TEST": {
                "tradingview": {"close": 96.0, "sector": "Technology", "exchange": "NASDAQ"},
                "stage2_evaluation": {"weinstein_stage": "STAGE_2", "entry_timing_posture": "BUY_AT_CMP_NO_FOMO",
                                      "support_buy_zone": [90.0, 95.0], "invalidation_stop": 85.0},
            }}}
            held_positions = {"net_worth": 5000, "consolidated": [{
                "symbol": "TEST", "quantity": 10, "market_value": 960, "cost_basis": 800, "gain": 160,
                "accounts": [{"account": "Schwab", "quantity": 10}],
            }]}
            html_out = repo / "docs" / "blogs" / "US" / "TEST_dossier.html"
            render_10chapter_monograph_editions(
                init_spec, snapshots=snapshots_v1, positions=held_positions,
                shortlist={"active": []}, out_dossier_path=html_out,
            )

            # Bootstrap legacy HTML into canonical spec directory cleanly
            boot_dir = repo / "data" / "dossiers" / "US" / "TEST"
            bootstrap_from_html(html_out, boot_dir, "US", "TEST")
            self.assertTrue((boot_dir / "spine.json").is_file())
            self.assertTrue((boot_dir / "revision_log.json").is_file())

            # Prepare verdict-stripped refresh workspace
            work_dir = repo / "work" / "TEST"
            prep_info = prepare_refresh_workspace("US", "TEST", work_dir, repo_root=repo)
            packet_txt = Path(prep_info["blind_packet"]).read_text(encoding="utf-8")
            self.assertIn("CUSTOMER_SUPPLIER_CONCENTRATION", packet_txt)
            self.assertNotIn("ACCUMULATE_ON_DIP", packet_txt)
            self.assertFalse((work_dir / "spine.json").exists())
            self.assertFalse((work_dir / "chapters" / "ch09.json").exists())

            # Fake audit claiming MATERIAL_PATCHED without editing ch03.json must FAIL hash check
            audit_data = {
                "recommended_tier": "TIER_2_QUARTERLY_OR_BLINDSPOT",
                "assumptions_checked": [
                    {"chapter": "ch-2", "claim": "Cloud data center rack revenue mix above 60%", "disposition": "CONFIRMED",
                     "evidence": "Q3 10-Q confirmed 64% cloud mix.", "source_url": "https://sec.example.com/q3"},
                    {"chapter": "ch-5", "claim": "Management guided DSO under 65 days", "disposition": "WEAKENED",
                     "evidence": "Q3 DSO rose to 74 days on hyperscaler payment terms.", "source_url": "https://sec.example.com/q3-ar"},
                    {"chapter": "ch-6", "claim": "Operating cash conversion exceeds 90% of net income", "disposition": "UNCHANGED",
                     "evidence": "TTM CFO/PAT held at 93%.", "source_url": "https://sec.example.com/q3-cf"},
                ],
                "blind_spots_discovered": [
                    {"vector": "CUSTOMER_SUPPLIER_CONCENTRATION", "target_chapter": "ch-3",
                     "what_was_missed": "Original dossier omitted single-source silicon carbide MOSFET supplier reliance.",
                     "materiality": "MATERIAL_PATCHED",
                     "evidence": "10-K Item 1A discloses 82% SiC MOSFET supply from one fab.", "source_url": "https://sec.example.com/10k-risk"},
                    {"vector": "REGULATORY_TARIFF_FX_EXPOSURE", "target_chapter": "ch-4",
                     "what_was_missed": "Evaluated Section 301 tariff exposure on Mexican sub-assemblies.",
                     "materiality": "IMMATERIAL_VERIFIED",
                     "evidence": "USMCA-compliant North American assembly exempts 96% of COGS.", "source_url": "https://sec.example.com/usmca"},
                ],
            }
            (work_dir / "refresh_audit.json").write_text(json.dumps(audit_data, indent=2), encoding="utf-8")
            unpatched_errs = validate_refresh_audit(work_dir)
            self.assertTrue(any("ch03.json was NOT updated" in e for e in unpatched_errs))
            self.assertTrue(any("ch05.json was NOT updated" in e for e in unpatched_errs))

            # Patch ch03.json and ch05.json with the newly discovered blind spot & Q3 DSO update -> PASS!
            for ch_num, note in ((3, "Single-source fab supplies 82% of SiC power modules [26]."),
                                 (5, "Q3 DSO rose to 74 days on extended hyperscaler terms [26].")):
                cf = work_dir / "chapters" / f"ch0{ch_num}.json"
                cdata = json.loads(cf.read_text(encoding="utf-8"))
                cdata["web_blocks"].append({"type": "p", "text": note})
                cdata["book_paragraphs"].append(note.replace(" [26]", ""))
                cf.write_text(json.dumps(cdata, indent=2), encoding="utf-8")
            self.assertEqual(validate_refresh_audit(work_dir), [])

            # Pass 2: Author ch07..ch09, spine, ch00 — verify lowering held stop ($85 -> $80) is BLOCKED
            for ch_num, extra in ((0, ""), (7, ""), (8, ""), (9, "")):
                blocks = [{"type": "p", "text": filler}]
                if ch_num == 9:
                    blocks.append({"type": "trigger", "text": "Daily close below $90 triggers immediate exit."})
                (work_dir / "chapters" / f"ch0{ch_num}.json").write_text(json.dumps({
                    "id": f"ch-{ch_num}", "web_title": f"{ch_num}. Chapter",
                    "web_blocks": blocks, "book_paragraphs": [b_filler],
                }), encoding="utf-8")

            bad_spine = {
                **init_spec,
                "as_of": "2026-11-12",
                "stop_loss": 80.0,  # Illegally lowered below prior $85.0 on held shares!
                "citations": init_spec["citations"] + ["Q3 10-Q: https://sec.example.com/q3"],
            }
            bad_spine.pop("chapters", None)
            (work_dir / "spine.json").write_text(json.dumps(bad_spine, indent=2), encoding="utf-8")
            from dossier_schema import load_monograph_spec
            loaded_bad = load_monograph_spec(work_dir)
            with self.assertRaisesRegex(ValueError, "Stop-loss ratchet violation"):
                render_10chapter_monograph_editions(
                    loaded_bad, snapshots=snapshots_v1, positions=held_positions,
                    shortlist={"active": []}, out_dossier_path=html_out,
                )

            # Ratchet stop UP ($85 -> $90) as stock advances to $106 -> compiles & injects #revision-audit-summary!
            good_spine = {
                **bad_spine,
                "entry_zone_low": 96.0,
                "entry_zone_high": 100.0,
                "stop_loss": 90.0,
                "target_base": 135.0,
                "target_bull": 160.0,
            }
            (work_dir / "spine.json").write_text(json.dumps(good_spine, indent=2), encoding="utf-8")
            snapshots_v2 = {"snapshots": {"TEST": {
                "tradingview": {"close": 106.0, "sector": "Technology", "exchange": "NASDAQ"},
                "stage2_evaluation": {"weinstein_stage": "STAGE_2", "entry_timing_posture": "WAIT_FOR_SUPPORT_PULLBACK",
                                      "technical_timing_gate": "CAP_WAIT_FOR_SUPPORT",
                                      "support_buy_zone": [96.0, 100.0], "invalidation_stop": 90.0},
            }}}
            loaded_good = load_monograph_spec(work_dir)
            render_10chapter_monograph_editions(
                loaded_good, snapshots=snapshots_v2, positions=held_positions,
                shortlist={"active": []}, out_dossier_path=html_out, persist_spec_dir=boot_dir,
            )
            refreshed_soup = BeautifulSoup(html_out.read_text(encoding="utf-8"), "html.parser")
            rev_banner = refreshed_soup.select_one("#revision-audit-summary")
            self.assertIsNotNone(rev_banner)
            self.assertIn("silicon carbide MOSFET", rev_banner.get_text(" ", strip=True))
            self.assertIn("$85.00", rev_banner.get_text(" ", strip=True))
            self.assertIn("$90.00", rev_banner.get_text(" ", strip=True))
            rev_log = json.loads((boot_dir / "revision_log.json").read_text(encoding="utf-8"))
            self.assertEqual(len(rev_log["history"]), 2)

            # Verify refresh_queue_info prioritizes held/shortlisted stalest dossiers
            older_html = repo / "docs" / "blogs" / "US" / "OLDER_dossier.html"
            older_html.write_text('<meta name="research-as-of" content="2026-09-01"><h1>Older</h1>', encoding="utf-8")
            (repo / "data" / "shortlist" / "US.json").write_text(
                json.dumps({"market": "US", "active": [{"symbol": "TEST"}]}), encoding="utf-8"
            )
            with patch.object(run_claims, "REPO", repo):
                ordered, _, _ = run_claims.refresh_queue_info("US", ref="WORKTREE")
            self.assertEqual(ordered, ["TEST", "OLDER"])

    def test_situational_parallels_reject_cliches_and_require_failure_base_rate(self):
        # 1. Cliché mega-cap + missing FAILURE_BASE_RATE twin must be rejected
        bad_spec = valid_spec()
        bad_spec["chapters"] = [{
            "id": "ch-9",
            "web_blocks": [
                {"type": "parallel", "role": "MOAT_SCALING", "company": "Danaher", "region_era": "US (1990s-2020s)",
                 "mechanism": "Serial industrial M&A roll-up playbook.", "outcome_numbers": "Compounded 20% for 30 years.",
                 "lesson_for_symbol": "Shows serial acquisitions can work."},
                {"type": "parallel", "role": "MOAT_SCALING", "company": "AAK AB", "region_era": "Sweden (2010-2025)",
                 "mechanism": "Specialty vegetable fats co-development with global chocolatiers.",
                 "outcome_numbers": "Expanded EBIT/kg by 65% over 10 years.",
                 "lesson_for_symbol": "Co-developed formulations lock in confectionery margins."},
            ],
            "book_paragraphs": [],
        }]
        errs, _ = validate_monograph_spec(bad_spec, min_total_words=0)
        joined = " | ".join(errs)
        self.assertIn("cliché mega-cap analogy", joined)
        self.assertIn("FAILURE_BASE_RATE", joined)

        # 2. Dynamic scaling twin + failure-mode base-rate twin passes cleanly
        good_spec = valid_spec()
        good_spec["chapters"] = [{
            "id": "ch-9",
            "web_blocks": [
                {"type": "parallel", "role": "MOAT_SCALING", "company": "AAK AB", "region_era": "Sweden (2010-2025)",
                 "mechanism": "Specialty cocoa-butter equivalent co-development with global confectionery OEMs.",
                 "outcome_numbers": "Expanded operating profit per kilo by 65% with 18% ROIC.",
                 "lesson_for_symbol": "Proves specialty formulation moat scales when working capital stays disciplined."},
                {"type": "parallel", "role": "FAILURE_BASE_RATE", "company": "Knightscope", "region_era": "US (2022-2025)",
                 "mechanism": "Autonomous security hardware scaled with heavy field-maintenance burn and equity dilution.",
                 "outcome_numbers": "Gross margin stayed negative (-28%) and shares de-rated >90% from IPO.",
                 "lesson_for_symbol": "Hardware fleet growth destroys equity value unless DSO and field service turn cash-positive."},
            ],
            "book_paragraphs": [],
        }]
        errs2, _ = validate_monograph_spec(good_spec, min_total_words=0)
        self.assertEqual(errs2, [])

    def test_options_engine_dislocation_spread_leaps_interlocks_and_standalone_desk(self):
        fake_chains = {
            "optionable": True,
            "expiries": ["2027-01-15", "2027-10-15"],
            "chains": {
                "2027-01-15": [
                    {"contract": "TEST270115C95", "expiry": "2027-01-15", "dte": 64, "strike": 95.0, "bid": 8.2, "ask": 8.6, "mid": 8.4, "last": 8.4, "open_interest": 850, "iv": 0.48, "spread_pct": 0.047},
                    {"contract": "TEST270115C100", "expiry": "2027-01-15", "dte": 64, "strike": 100.0, "bid": 5.4, "ask": 5.8, "mid": 5.6, "last": 5.6, "open_interest": 1200, "iv": 0.46, "spread_pct": 0.071},
                    {"contract": "TEST270115C115", "expiry": "2027-01-15", "dte": 64, "strike": 115.0, "bid": 1.5, "ask": 1.7, "mid": 1.6, "last": 1.6, "open_interest": 950, "iv": 0.44, "spread_pct": 0.125},
                ],
                "2027-10-15": [
                    {"contract": "TEST271015C90", "expiry": "2027-10-15", "dte": 337, "strike": 90.0, "bid": 19.5, "ask": 20.5, "mid": 20.0, "last": 20.0, "open_interest": 600, "iv": 0.31, "spread_pct": 0.05},
                    {"contract": "TEST271015C100", "expiry": "2027-10-15", "dte": 337, "strike": 100.0, "bid": 13.8, "ask": 14.2, "mid": 14.0, "last": 14.0, "open_interest": 720, "iv": 0.30, "spread_pct": 0.028},
                ],
            },
        }

        # 1. Dislocation below 50D SMA at 200D shelf + elevated IV -> Bull Call Debit Spread (with open contract audit)
        disloc_mtf = {"setup_archetype": "DISLOCATION_AT_MAJOR_SHELF", "major_shelf": 94.0, "pivot_r1": 115.0,
                      "setup_summary": "Pulled back into 200D SMA shelf ($94) on news while 4H RSI curls up."}
        near_exp = (datetime.date.today() + datetime.timedelta(days=20)).isoformat()
        past_exp = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        spread_plan = structure_options_setup(
            "TEST", "US", spot=100.0, mtf=disloc_mtf, chain_data=fake_chains, hv20=0.32,
            business_quality_verdict="COMPOUNDER_PASS", target_base=115.0, target_bull=130.0,
            stop_underlying=92.0, net_worth=200000.0,
            open_positions=[
                {"contract_symbol": "TEST_NEAR_C110", "type": "Call", "strike_usd": 110,
                 "expiry_date": near_exp, "dte": 99, "contracts": 2, "invalidation_stop_usd": 90},
                {"contract_symbol": "TEST_EXP_C105", "type": "Call", "strike_usd": 105,
                 "expiry_date": past_exp, "dte": 31, "contracts": 1, "invalidation_stop_usd": 90},
            ],
        )
        self.assertEqual(spread_plan["options_verdict"], "BULL_CALL_DEBIT_SPREAD")
        self.assertEqual(spread_plan["open_positions_audit"][0]["action"], "ROLL_OR_CLOSE")
        self.assertEqual(spread_plan["open_positions_audit"][1]["action"], "EXPIRED_REMOVE_FROM_LEDGER")
        tr = spread_plan["recommended_trade"]
        self.assertEqual(len(tr["legs"]), 2)
        self.assertGreater(tr["max_loss_total"], 0)
        self.assertEqual(len(tr["scenarios"]), 4)
        self.assertTrue(any("maximum you can lose" in s for s in tr["beginner_explainer"]))

        # 2. Calm IV + Stage 2 VCP squeeze on US compounder -> 0.70-delta LEAPS Call
        vcp_mtf = {"setup_archetype": "STAGE2_VCP_VOLATILITY_SQUEEZE", "major_shelf": 96.0, "pivot_r1": 115.0}
        calm_chains = copy.deepcopy(fake_chains) if "copy" in globals() else json.loads(json.dumps(fake_chains))
        for r in calm_chains["chains"]["2027-01-15"]:
            r["iv"] = 0.29
        leaps_plan = structure_options_setup(
            "TEST", "US", spot=100.0, mtf=vcp_mtf, chain_data=calm_chains, hv20=0.32,
            business_quality_verdict="COMPOUNDER_PASS", target_base=120.0, target_bull=140.0,
        )
        self.assertEqual(leaps_plan["options_verdict"], "LONG_CALL_LEAPS")
        self.assertGreaterEqual(leaps_plan["recommended_trade"]["dte"], 240)

        # 3. FUNDAMENTAL_FAIL blocks rebound calls even at a shelf
        fail_plan = structure_options_setup(
            "TEST", "US", spot=100.0, mtf=disloc_mtf, chain_data=fake_chains, hv20=0.32,
            business_quality_verdict="FUNDAMENTAL_FAIL",
        )
        self.assertEqual(fail_plan["options_verdict"], "NO_OPTIONS_EDGE")
        self.assertIsNone(fail_plan["recommended_trade"])

        # 4. Non-F&O Indian SME -> NOT_OPTIONABLE_OR_ILLIQUID
        sme_plan = structure_options_setup(
            "KODYTECH", "IN", spot=1551.0, mtf=vcp_mtf, chain_data={"optionable": False, "chains": {}}, hv20=0.40,
        )
        self.assertEqual(sme_plan["options_verdict"], "NOT_OPTIONABLE_OR_ILLIQUID")

        # 5. Graceful browser probe when disabled/logged out + Standalone Options Desk report + Zero-rewrite dossier patch
        b_status = probe_browser_sessions("TEST", "US", enabled=False)
        self.assertFalse(b_status["robinhood"]["logged_in"])

        snap_bundle = {
            "market": "US",
            "packages": {
                "TEST": {
                    "symbol": "TEST",
                    "market": "US",
                    "business_quality_verdict": "COMPOUNDER_PASS",
                    "browser_sessions": b_status,
                    "multitimeframe_chart": disloc_mtf,
                    "options_plan": spread_plan,
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            desk_path = Path(tmp) / "US_Options_Desk.html"
            desk_html = render_options_desk_report(snap_bundle, as_of="2026-11-12")
            desk_path.write_text(desk_html, encoding="utf-8")
            self.assertTrue(portal_publish.require_modern_report(desk_path, require_generated=True))
            self.assertIn("Beginner Guide: How This Call Trade Works in Plain Dollars", desk_html)

            # Surgically patch #options-overlay into an existing dossier HTML without rewriting chapters
            dummy_dossier = Path(tmp) / "TEST_dossier.html"
            dummy_dossier.write_text(
                '<html><body><main class="report"><section class="chapter" id="ch-9"><h2>9. Synthesis</h2></section></main></body></html>',
                encoding="utf-8",
            )
            self.assertTrue(patch_existing_dossier_html(dummy_dossier, snap_bundle["packages"]["TEST"]))
            patched_soup = BeautifulSoup(dummy_dossier.read_text(encoding="utf-8"), "html.parser")
            self.assertIsNotNone(patched_soup.select_one('section#options-overlay[data-options-verdict="BULL_CALL_DEBIT_SPREAD"]'))


if __name__ == "__main__":
    unittest.main()
