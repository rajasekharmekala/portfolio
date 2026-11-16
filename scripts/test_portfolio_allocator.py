#!/usr/bin/env python3
"""Unit and integration tests for `portfolio_allocator.py` and `portfolio_audit_builder.py`."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import portfolio_allocator as pa  # noqa: E402
import portfolio_audit_builder as pab  # noqa: E402
import portal_publish  # noqa: E402
import record_merge  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


class TestPortfolioAllocator(unittest.TestCase):
    def _synthetic_book(self):
        facts = {
            "market": "US",
            "asof": "2026-11-13",
            "regime": {"label": "Uptrend (narrow breadth)", "breadth_pct_above_50dma": 44.0},
            "instruments": {
                "VIX": {"kind": "index", "close": 18.5},
                "S&P 500": {"kind": "index", "close": 5950.0},
                "XLK": {"kind": "sector", "close": 230.0, "quadrant": "Leading"},
                "XLE": {"kind": "sector", "close": 88.0, "quadrant": "Lagging"},
                "MSFT": {"close": 520.0, "sma20": 516.0, "sma50": 512.0, "sma200": 475.0, "ema10w_approx": 514.0, "rsi14": 54.0, "atr14": 10.0, "stage": 2, "roles": ["holding"]},
                "MSTR": {"close": 150.0, "sma20": 146.0, "sma50": 142.0, "sma200": 125.0, "ema10w_approx": 144.0, "rsi14": 58.0, "atr14": 9.0, "stage": 2, "roles": ["holding"]},
                "MSTX": {"close": 40.0, "sma20": 39.0, "sma50": 37.0, "sma200": 30.0, "ema10w_approx": 38.0, "rsi14": 60.0, "atr14": 4.0, "stage": 2, "roles": ["holding"]},
                "FAS": {"close": 120.0, "sma20": 116.0, "sma50": 112.0, "sma200": 98.0, "ema10w_approx": 114.0, "rsi14": 59.0, "atr14": 3.5, "stage": 2, "roles": ["holding"]},
                "NBIL": {"close": 50.0, "sma20": 50.0, "sma50": 50.0, "sma200": 50.0, "rsi14": 50.0, "stage": 2, "roles": ["holding"]},
                "STUB": {"close": 15.0, "sma20": 15.0, "sma50": 15.0, "sma200": 15.0, "rsi14": 50.0, "stage": 2, "roles": ["holding"]},
                "BROKEN": {"close": 42.0, "sma20": 50.0, "sma50": 55.0, "sma200": 62.0, "ema10w_approx": 54.0, "rsi14": 31.0, "atr14": 2.5, "stage": 4, "roles": ["holding"]},
                "AVPT": {"close": 15.4, "sma20": 15.2, "sma50": 14.9, "sma200": 12.5, "ema10w_approx": 15.1, "rsi14": 56.0, "atr14": 0.6, "stage": 2, "roles": ["shortlist"]},
                "WEAKOIL": {"close": 30.0, "sma20": 29.8, "sma50": 29.5, "sma200": 28.0, "ema10w_approx": 29.6, "rsi14": 55.0, "atr14": 1.0, "stage": 2, "roles": ["shortlist"]},
            },
        }
        positions = {
            "accounts": [
                {"id": "schwab", "label": "Charles Schwab", "last_transaction": "2026-11-13", "positions": 4, "cash": 12000.0, "market_value": 41415.0},
                {"id": "robinhood", "label": "Robinhood", "last_transaction": "2026-11-13", "positions": 3, "cash": 3000.0, "market_value": 10600.0},
            ],
            "consolidated": [
                {"symbol": "MSFT", "accounts": [{"account": "schwab", "quantity": 50, "cost_basis": 23000.0, "market_value": 26000.0, "realized_pl": 0.0}], "quantity": 50.0, "market_value": 26000.0, "cost_basis": 23000.0, "cost_complete": True, "priced": True},
                {"symbol": "MSTR", "accounts": [{"account": "schwab", "quantity": 20, "cost_basis": 2600.0, "market_value": 3000.0, "realized_pl": 0.0}], "quantity": 20.0, "market_value": 3000.0, "cost_basis": 2600.0, "cost_complete": True, "priced": True},
                {"symbol": "FAS", "accounts": [{"account": "robinhood", "quantity": 30, "cost_basis": 3300.0, "market_value": 3600.0, "realized_pl": 0.0}], "quantity": 30.0, "market_value": 3600.0, "cost_basis": 3300.0, "cost_complete": True, "priced": True},
                {"symbol": "BROKEN", "accounts": [{"account": "schwab", "quantity": 100, "cost_basis": 5800.0, "market_value": 4200.0, "realized_pl": 0.0}], "quantity": 100.0, "market_value": 4200.0, "cost_basis": 5800.0, "cost_complete": True, "priced": True},
                {"symbol": "MSTX", "accounts": [{"account": "robinhood", "quantity": 50, "cost_basis": 2100.0, "market_value": 2000.0, "realized_pl": 0.0}], "quantity": 50.0, "market_value": 2000.0, "cost_basis": 2100.0, "cost_complete": True, "priced": True},
                {"symbol": "NBIL", "accounts": [{"account": "robinhood", "quantity": 100, "cost_basis": 5000.0, "market_value": 5000.0, "realized_pl": 0.0}], "quantity": 100.0, "market_value": 5000.0, "cost_basis": 5000.0, "cost_complete": True, "priced": True},
                {"symbol": "STUB", "accounts": [{"account": "schwab", "quantity": 10, "cost_basis": 150.0, "market_value": 150.0, "realized_pl": 0.0}], "quantity": 10.0, "market_value": 150.0, "cost_basis": 150.0, "cost_complete": True, "priced": True},
            ],
            "equities_value": 43950.0,
            "cash_total": 18000.0,
            "options_value": 3050.0,
            "options_rows": [
                {
                    "contract_symbol": "AMZN270617C00300000",
                    "underlying": "AMZN",
                    "contracts": 2,
                    "dte": 220,
                    "delta_delta": 0.42,
                    "cost_basis_usd": 3800.0,
                    "current_mv_usd": 3050.0,
                    "market_value": 3050.0,
                    "underlying_cmp_usd": 215.0,
                    "invalidation_stop_usd": 198.0,
                    "broker_account": "Robinhood",
                }
            ],
            "net_worth": 65000.0,
            "portfolio_risk_and_overlap": {
                "portfolio_beta_weighted": 1.12,
                "effective_market_exposure_pct": 92.4,
                "lockstep_clusters": [],
            },
        }
        shortlist = {
            "market": "US",
            "active": [
                {
                    "symbol": "AVPT",
                    "company_name": "AvePoint, Inc.",
                    "strategy_bucket": "CORE_ALPHA",
                    "conviction_tier": "TIER_2",
                    "macro_sector": "Technology",
                    "cmp": 15.4,
                    "entry_zone_low": 14.8,
                    "entry_zone_high": 15.6,
                    "stop_loss": 13.5,
                    "target_base": 21.0,
                    "asymmetry_ratio": 2.9,
                    "action_verdict": "IMMEDIATE_BUY",
                    "weinstein_stage": "STAGE_2",
                    "gate_status": "PASSED",
                    "kpi_health": "PASS",
                    "research_dossier_path": "blogs/US/AVPT_dossier.html",
                },
                {
                    "symbol": "WEAKOIL",
                    "company_name": "Weak Oil Services",
                    "strategy_bucket": "TACTICAL_MOMENTUM",
                    "conviction_tier": "TIER_3",
                    "macro_sector": "Energy Oil & Gas",
                    "cmp": 30.0,
                    "entry_zone_low": 29.0,
                    "entry_zone_high": 30.5,
                    "stop_loss": 27.0,
                    "target_base": 36.0,
                    "asymmetry_ratio": 2.0,
                    "action_verdict": "IMMEDIATE_BUY",
                    "weinstein_stage": "STAGE_2",
                    "gate_status": "PASSED",
                    "kpi_health": "PASS",
                    "research_dossier_path": "blogs/US/WEAKOIL_dossier.html",
                },
            ],
        }
        return facts, positions, shortlist

    def test_reconciliation_tracking_and_overlap_rules(self):
        facts, positions, shortlist = self._synthetic_book()
        res = pa.allocate_portfolio("US", facts, positions, shortlist_data=shortlist)

        # 1. Exact 100% reconciliation
        cur_sum = round(sum(r["current_value"] for r in res["money_bridge"]), 2)
        tgt_sum = round(sum(r["target_value"] for r in res["money_bridge"]), 2)
        self.assertEqual(cur_sum, 65000.0)
        self.assertEqual(tgt_sum, 65000.0)

        # 2. STUB ($150 / $65,000 = 0.23% < 0.35%) is isolated as tracking
        track_syms = [t["symbol"] for t in res["tracking_positions"]]
        self.assertEqual(track_syms, ["STUB"])
        held_syms = {h["symbol"]: h for h in res["holding_decisions"]}
        self.assertNotIn("STUB", held_syms)

        # 3. Single-stock 2x ETF MSTX overlapping MSTR is exited; Stage 4 BROKEN is exited; FAS sector 3x kept
        self.assertEqual(held_syms["MSTX"]["verdict"], "EXIT")
        self.assertEqual(held_syms["BROKEN"]["verdict"], "EXIT")
        self.assertEqual(held_syms["FAS"]["verdict"], "KEEP_COMPOUNDING")
        self.assertEqual(held_syms["NBIL"]["verdict"], "HOLD_CASH_EQUIVALENT")
        self.assertEqual(held_syms["NBIL"]["open_heat_pct"], 0.0)

        # 4. Runaway MSFT (40% > 22% cap) trimmed down; AMZN legacy option above stop is grandfathered
        self.assertEqual(held_syms["MSFT"]["verdict"], "TRIM_PROFIT_BOOKING")
        self.assertEqual(res["options_decisions"][0]["verdict"], "GRANDFATHERED_HOLD")

        # 5. Asymmetric sector rotation: AVPT (Leading Tech) funded starter; WEAKOIL (Lagging Energy Tactical) blocked!
        ch_by_sym = {c["symbol"]: c for c in res["challenger_decisions"]}
        self.assertGreater(ch_by_sym["AVPT"]["funded_shares"], 0)
        self.assertEqual(ch_by_sym["WEAKOIL"]["entry_action"], "DEFERRED_GATE_BLOCKED")
        self.assertEqual(ch_by_sym["WEAKOIL"]["funded_shares"], 0)

    def test_short_timeframe_hysteresis_and_monotonic_convergence(self):
        facts, positions, shortlist = self._synthetic_book()
        run1 = pa.allocate_portfolio("US", facts, positions, shortlist_data=shortlist)

        # Same-day rerun with persisted state must be 100% deterministic
        run1_repeat = pa.allocate_portfolio(
            "US", facts, positions, shortlist_data=shortlist, prior_state=run1["persisted_state"]
        )
        self.assertEqual(
            [(h["symbol"], h["verdict"], h["target_quantity"]) for h in run1["holding_decisions"]],
            [(h["symbol"], h["verdict"], h["target_quantity"]) for h in run1_repeat["holding_decisions"]],
        )

        # Simulate User executing Run 1's recommended edits cleanly, then rerunning 1 day later with +1.1% market wiggle
        facts_day2 = copy.deepcopy(facts)
        facts_day2["asof"] = "2026-11-14"
        for k, v in facts_day2["instruments"].items():
            if "close" in v and k not in {"VIX", "NBIL"}:
                v["close"] = round(v["close"] * 1.011, 2)

        pos_day2 = copy.deepcopy(positions)
        new_cons = []
        cash_delta = 0.0
        for h in pos_day2["consolidated"]:
            sym = h["symbol"]
            if sym == "STUB":
                new_cons.append(h)
                continue
            hd1 = next(x for x in run1["holding_decisions"] if x["symbol"] == sym)
            tgt_q = hd1["target_quantity"]
            cash_delta += hd1["capital_liberated"] - hd1["capital_deployed"]
            if tgt_q > 0:
                px2 = facts_day2["instruments"][sym]["close"]
                h["quantity"] = tgt_q
                h["market_value"] = round(tgt_q * px2, 2)
                new_cons.append(h)

        # Add executed AVPT starter shares from Run 1
        avpt_c1 = next(c for c in run1["challenger_decisions"] if c["symbol"] == "AVPT")
        if avpt_c1["funded_shares"] > 0:
            px_avpt2 = facts_day2["instruments"]["AVPT"]["close"]
            avpt_mv2 = round(avpt_c1["funded_shares"] * px_avpt2, 2)
            cash_delta -= avpt_c1["funded_value"]
            new_cons.append({
                "symbol": "AVPT",
                "accounts": [{"account": "schwab", "quantity": avpt_c1["funded_shares"], "cost_basis": avpt_c1["funded_value"], "market_value": avpt_mv2, "realized_pl": 0.0}],
                "quantity": float(avpt_c1["funded_shares"]),
                "market_value": avpt_mv2,
                "cost_basis": avpt_c1["funded_value"],
                "cost_complete": True,
                "priced": True,
            })

        pos_day2["consolidated"] = new_cons
        pos_day2["cash_total"] = round(pos_day2["cash_total"] + cash_delta, 2)
        pos_day2["equities_value"] = round(sum(x["market_value"] for x in new_cons), 2)
        pos_day2["net_worth"] = round(pos_day2["equities_value"] + pos_day2["cash_total"] + pos_day2["options_value"], 2)

        run2 = pa.allocate_portfolio(
            "US", facts_day2, pos_day2, shortlist_data=shortlist, prior_state=run1["persisted_state"]
        )

        # Convergence score must jump higher and actionable trades on edited holdings drop to zero!
        self.assertGreater(
            run2["stability_and_convergence"]["convergence_score_pct"],
            run1["stability_and_convergence"]["convergence_score_pct"],
        )
        self.assertEqual(run2["stability_and_convergence"]["actionable_trades_count"], 0)
        self.assertEqual(run2["stability_and_convergence"]["convergence_score_pct"], 100.0)
        self.assertGreaterEqual(len(run2["stability_and_convergence"]["completed_edits_since_prior"]), 3)

        # Upward-only stop ratchet: stops on retained shares never drop below Run 1's effective_stop
        r1_stops = {h["symbol"]: h["effective_stop"] for h in run1["holding_decisions"]}
        for h2 in run2["holding_decisions"]:
            if h2["symbol"] in r1_stops:
                self.assertGreaterEqual(h2["effective_stop"], r1_stops[h2["symbol"]])

        # Persisted state merges cleanly via record_merge.py
        merged = record_merge.merge3(run1["persisted_state"], run2["persisted_state"], run1["persisted_state"])
        self.assertEqual(merged["as_of_date"], "2026-11-14")

    def test_live_repo_in_and_us_compile_and_validate(self):
        for mkt in ("IN", "US"):
            facts, positions, snap = pa.build_from_repo_fallback(mkt, as_of="2026-11-13")
            # Seed synthetic research needs satisfaction so validate_report.py can verify end-to-end
            facts["research_file"] = f"research_{mkt}_2026-11-13.json"
            facts["research_needs"] = []
            shortlist = pa._load_json(REPO / "data" / "shortlist" / f"{mkt}.json")
            watchlist = pa._load_json(REPO / "data" / "watchlist" / f"{mkt}.json")
            alloc = pa.allocate_portfolio(mkt, facts, positions, snapshots=snap, shortlist_data=shortlist, watchlist_data=watchlist)

            cur_sum = round(sum(r["current_value"] for r in alloc["money_bridge"]), 2)
            tgt_sum = round(sum(r["target_value"] for r in alloc["money_bridge"]), 2)
            self.assertEqual(cur_sum, alloc["net_worth"])
            self.assertEqual(tgt_sum, alloc["net_worth"])
            if mkt == "IN":
                track = {t["symbol"] for t in alloc["tracking_positions"]}
                self.assertIn("KROSS", track)
                self.assertIn("SSWL", track)
                self.assertIn("MARINE", track)
                by_sym = {h["symbol"]: h for h in alloc["holding_decisions"]}
                self.assertEqual(by_sym["SEDEMAC"]["delta_shares"], -100.0)
                self.assertEqual(by_sym["ASTRAMICRO"]["delta_shares"], -90.0)
                self.assertEqual(by_sym["LAURUSLABS"]["delta_shares"], -15.0)
                self.assertEqual(by_sym["RNITAI"]["verdict"], "EXIT")
                self.assertEqual(by_sym["TANFACIND"]["verdict"], "EXIT")
                self.assertEqual(by_sym["JYOTICNC"]["verdict"], "EXIT")
                self.assertEqual(by_sym["NETWEB"]["verdict"], "KEEP_COMPOUNDING")
                self.assertEqual(by_sym["APARINDS"]["verdict"], "KEEP_COMPOUNDING")
                self.assertEqual(alloc["portfolio_summary"]["active_unique_risk_underlyings_count"], 12)
                self.assertGreater(
                    alloc["portfolio_summary"]["current_open_heat_pct"],
                    alloc["portfolio_summary"]["target_open_heat_pct"],
                )

            with tempfile.TemporaryDirectory() as td:
                td_p = Path(td)
                facts_p = td_p / f"facts_{mkt}_2026-11-13.json"
                res_p = td_p / f"research_{mkt}_2026-11-13.json"
                alloc_p = td_p / f"allocation_{mkt}_2026-11-13.json"
                out_html = td_p / f"{mkt}_Portfolio_Audit.html"

                research_items = [
                    {
                        "key": f"src_{i}",
                        "symbol": "PORTFOLIO",
                        "status": "found",
                        "value": "verified",
                        "as_of": "2026-11-13",
                        "source_url": f"https://www.sec.gov/edgar/reference-{mkt.lower()}-{i}",
                    }
                    for i in range(1, 15)
                ]
                facts_p.write_text(json.dumps(facts), encoding="utf-8")
                res_p.write_text(json.dumps({"items": research_items}), encoding="utf-8")
                alloc_p.write_text(json.dumps(alloc), encoding="utf-8")

                built = pab.compile_portfolio_audit(
                    alloc=alloc,
                    facts_path=str(facts_p),
                    research_paths=[str(res_p)],
                    out_html_path=out_html,
                )
                self.assertTrue(out_html.is_file())
                html_txt = out_html.read_text(encoding="utf-8")
                self.assertIn("book-audio-bar", html_txt)
                self.assertIn(f"{mkt}_Portfolio_Audit_book.pdf", html_txt)
                self.assertTrue(portal_publish.require_modern_report(out_html, require_generated=True))

                proc = subprocess.run(
                    [
                        str(REPO / ".venv" / "bin" / "python"),
                        str(REPO / "scripts" / "validate_report.py"),
                        "--report", str(out_html),
                        "--kind", "portfolio_audit",
                        "--facts", str(facts_p),
                        "--research", str(res_p),
                        "--allocation", str(alloc_p),
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, msg=f"{mkt} validate_report failed:\n{proc.stdout}\n{proc.stderr}")

                rproc = subprocess.run(
                    [
                        str(REPO / ".venv" / "bin" / "python"),
                        str(REPO / "scripts" / "readability_check.py"),
                        str(out_html),
                        "--max-grade", "13.0",
                    ],
                    capture_output=True,
                    text=True,
                )
                r_bad = [
                    ln for ln in (rproc.stdout + "\n" + rproc.stderr).splitlines()
                    if ln.strip().startswith("- ") and not ln.strip().startswith(("- ESTIMATE", "- CHAPTER 7", "- PRIMER", "- NOTES"))
                ]
                self.assertEqual(r_bad, [], msg=f"{mkt} readability_check failed:\n" + "\n".join(r_bad))


if __name__ == "__main__":
    unittest.main()
