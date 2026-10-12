"""Regression tests for scripts/review_packet.py (build, delta mode, check)."""
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_packet as rp

FACTS = {
    "market": "XX", "asof": "2026-10-08",
    "regime": {"label": "Uptrend (narrow breadth)", "breadth_pct_above_50dma": 28.9},
    "macro": {}, "inputs": [],
    "instruments": {
        "ACME": {"close": 100.0, "stage": 2, "rsi14": 61.2, "sma50": 95.5, "sma200": 80.25, "hi52": 110.0, "atr14": 2.5,
                 "asof_bar": "2026-10-08", "kind": "stock", "roles": ["shortlist"]},
        "BETA": {"close": 50.0, "stage": 4, "rsi14": 33.0, "sma50": 55.0, "sma200": 60.0, "hi52": 70.0, "atr14": 1.5,
                 "asof_bar": "2026-10-08", "kind": "stock", "roles": ["holding"]},
    },
}
RESEARCH = {"items": [{"key": "guidance", "symbol": "ACME", "status": "found", "value": 12.5,
                       "source_url": "https://example.com/a", "as_of": "2026-10-01"}]}


def report(acme_close="100.00", total="150.00", asym="2.00", extra=""):
    return f"""<html><head><title>Report 2026-10-08</title></head><body>
<h1>Market report 2026-10-08</h1>
<p>Start here. The market is in an uptrend with 28.9% of stocks above their 50-day average.</p>
<h2>1. Holdings</h2>
<p>Intro paragraph for the table.</p>
<table class="wikitable"><tr><th>Name</th><th>Value</th></tr>
<tr><td>ACME</td><td>100.00</td></tr><tr><td>BETA</td><td>50.00</td></tr><tr><td>Total</td><td>{total}</td></tr></table>
<p>What the table means.</p>
<table class="wikitable"><tr><th>Name</th><th>CMP</th><th>Stop</th><th>Target</th><th>Asymmetry</th></tr>
<tr><td>ACME</td><td>100.00</td><td>95.00</td><td>110.00</td><td>{asym}</td></tr>
<tr><td>BETA</td><td>50.00</td><td>45.00</td><td>60.00</td><td>2.00</td></tr></table>
<h2>2. Case notes</h2>
<div class="casenote" data-symbol="ACME"><p><span class="verdict-keep">KEEP</span> ACME closed at {acme_close}, Stage 2, RSI 61.2.
Guidance of 12.5 percent growth is in the record. It also earned 37.9 percent margins. If it closes below 95.5 the view changes.{extra}</p></div>
<div class="casenote" data-symbol="BETA"><p><span class="verdict-exit">EXIT</span> BETA is Stage 4 at 50.00 and RSI 33.0. It fell below the 50-day.</p></div>
<h2>3. Notes</h2>
<p>Closing paragraph.</p>
</body></html>"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "facts.json").write_text(json.dumps(FACTS))
        (self.dir / "research.json").write_text(json.dumps(RESEARCH))

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, html, name="R_2026-10-08.html", out="r1", **kw):
        rep = self.dir / name
        rep.write_text(html)
        args = Namespace(report=str(rep), kind="market_intel", facts=str(self.dir / "facts.json"),
                         research=str(self.dir / "research.json"), out_dir=str(self.dir / out), round=1,
                         sibling=None, inputs_dir=None, symbol=None, prev_packet=None, prev_review=None,
                         cache_dir="none", allow_stale_asof=False, skip_checks=True)
        for k, v in kw.items():
            setattr(args, k, v)
        self.assertEqual(rp.build(args), 0)
        return rep, json.loads((self.dir / out / "packet.json").read_text())


class BuildTests(Base):
    def test_clean_report_has_no_mechanical_items_except_untraced_derived_numbers(self):
        _, pk = self.build(report())
        types = {i["type"] for i in pk["items"]}
        self.assertNotIn("ledger", types)
        self.assertNotIn("total", types)
        self.assertNotIn("asymmetry", types)
        self.assertNotIn("date", types)
        untraced = [t for i in pk["items"] if i["type"] == "number" for t, _ in i["tokens"]]
        self.assertTrue(any("37.9" in t for t in untraced))
        self.assertFalse(any(t.startswith("28.9") or t.startswith("12.5") or t.startswith("61.2") for t in untraced))

    def test_wrong_close_total_and_asymmetry_are_flagged(self):
        _, pk = self.build(report(acme_close="104.50", total="160.00", asym="3.50"))
        by = {}
        for i in pk["items"]:
            by.setdefault(i["type"], []).append(i)
        self.assertTrue(any("close 104.50" in i["problem"] for i in by["ledger"]))
        self.assertTrue(any("add to 150" in i["problem"] for i in by["total"]))
        self.assertTrue(any("ACME" in i["problem"] for i in by["asymmetry"]))
        self.assertEqual(len(by["ledger"]), 1)

    def test_session_date_mismatch(self):
        html = report().replace("2026-10-08", "2026-10-09")
        _, pk = self.build(html, name="R_2026-10-09.html")
        self.assertTrue(any(i["type"] == "date" for i in pk["items"]))

    def test_verdict_rows_and_files(self):
        _, pk = self.build(report())
        self.assertEqual(pk["verdict_rows"], 2)
        for n in ("review_packet.md", "conclusions_digest.md", "report_text.md", "packet.json"):
            self.assertTrue((self.dir / "r1" / n).is_file(), n)
        self.assertIn("EXIT", (self.dir / "r1" / "review_packet.md").read_text())

    def test_verdict_conflict_across_table_and_note(self):
        html = report().replace("<td>BETA</td><td>50.00</td></tr><tr><td>Total",
                                "<td>BETA</td><td>50.00</td><td>KEEP</td></tr><tr><td>Total")
        _, pk = self.build(html)
        self.assertTrue(any(i["type"] == "verdict_conflict" and "BETA" in i["problem"] for i in pk["items"]))


class DeltaTests(Base):
    def test_delta_lists_only_changed_sections_and_tracks_findings(self):
        rep, pk1 = self.build(report(extra=" It has 99.9 units."))
        review1 = {"verdict": "REVISE", "round": 1, "pass": "review", "findings": [
            {"severity": "REVISE", "kind": "mechanical", "location": "2. Case notes",
             "quote": "It has 99.9 units.", "fix": "remove"}]}
        (self.dir / "round_1_review.json").write_text(json.dumps(review1))
        rep.write_text(report())
        args = Namespace(report=str(rep), kind="market_intel", facts=str(self.dir / "facts.json"),
                         research=str(self.dir / "research.json"), out_dir=str(self.dir / "r2"), round=2,
                         sibling=None, inputs_dir=None, symbol=None, prev_packet=str(self.dir / "r1" / "packet.json"),
                         prev_review=str(self.dir / "round_1_review.json"),
                         cache_dir="none", allow_stale_asof=False, skip_checks=True)
        rp.build(args)
        pk2 = json.loads((self.dir / "r2" / "packet.json").read_text())
        self.assertEqual(pk2["mode"], "delta")
        self.assertEqual(pk2["changed_sections"], ["S2"])
        self.assertFalse(pk2["previous_findings"][0]["quote_still_in_report"])
        # untraced derived numbers (37.9) remain in the changed section, so code is not clean and an agent is needed
        self.assertTrue(pk2["agent_needed"])


    def test_mechanical_findings_fixed_and_code_clean_skips_the_agent(self):
        bad = report(acme_close="104.50").replace(" It also earned 37.9 percent margins.", "")
        rep, _ = self.build(bad)
        review1 = {"verdict": "REVISE", "round": 1, "pass": "review", "findings": [
            {"severity": "REVISE", "kind": "mechanical", "location": "2. Case notes",
             "quote": "ACME closed at 104.50", "fix": "use the ledger close"}]}
        (self.dir / "round_1_review.json").write_text(json.dumps(review1))
        rep.write_text(report().replace(" It also earned 37.9 percent margins.", ""))
        args = Namespace(report=str(rep), kind="market_intel", facts=str(self.dir / "facts.json"),
                         research=str(self.dir / "research.json"), out_dir=str(self.dir / "r2"), round=2,
                         sibling=None, inputs_dir=None, symbol=None, prev_packet=str(self.dir / "r1" / "packet.json"),
                         prev_review=str(self.dir / "round_1_review.json"),
                         cache_dir="none", allow_stale_asof=False, skip_checks=True)
        rp.build(args)
        pk2 = json.loads((self.dir / "r2" / "packet.json").read_text())
        self.assertEqual(pk2["item_ids"], [])
        self.assertFalse(pk2["agent_needed"])


class CheckTests(Base):
    def make(self, review):
        rep, pk = self.build(report())
        path = self.dir / "review.json"
        path.write_text(json.dumps(review))
        args = Namespace(review=str(path), packet=str(self.dir / "r1" / "packet.json"), report=str(rep))
        return rp.check(args), pk

    def good(self, pk):
        return {"verdict": "REVISE", "round": 1, "pass": "review", "verdict_rows_reviewed": pk["verdict_rows"],
                "items": [{"id": i, "result": "ok"} for i in pk["item_ids"]],
                "findings": [{"severity": "REVISE", "kind": "judgment", "location": "2. Case notes",
                              "quote": "It fell below the 50-day.", "fix": "explain the break"}]}

    def test_valid_review_passes(self):
        rep, pk = self.build(report())
        review = self.good(pk)
        path = self.dir / "review.json"
        path.write_text(json.dumps(review))
        self.assertEqual(rp.check(Namespace(review=str(path), packet=str(self.dir / "r1" / "packet.json"), report=str(rep))), 0)

    def test_invented_quote_missing_items_and_stale_report_fail(self):
        rep, pk = self.build(report())
        review = self.good(pk)
        review["findings"][0]["quote"] = "A sentence that is not in the report at all."
        review["items"] = review["items"][1:]
        review["verdict_rows_reviewed"] = 0
        path = self.dir / "review.json"
        path.write_text(json.dumps(review))
        self.assertEqual(rp.check(Namespace(review=str(path), packet=str(self.dir / "r1" / "packet.json"), report=str(rep))), 1)
        rep.write_text(report(acme_close="101.00"))
        review = self.good(pk)
        path.write_text(json.dumps(review))
        self.assertEqual(rp.check(Namespace(review=str(path), packet=str(self.dir / "r1" / "packet.json"), report=str(rep))), 1)


class UnitTests(unittest.TestCase):
    def test_matches_rounding_and_scale(self):
        self.assertTrue(rp.matches(340.0, 0, [340.42]))
        self.assertFalse(rp.matches(341.0, 0, [340.42]))
        self.assertFalse(rp.matches(46.9, 1, [4690000.0]))
        self.assertTrue(rp.matches(46.9, 1, [4690000.0], "lakh"))
        self.assertTrue(rp.matches(1.5, 1, [150.0]) is False)
        self.assertTrue(rp.matches(1.5, 1, [0.015], "%"))

    def test_extract_numbers_skips_dates_years_and_stage(self):
        toks = [r[0] for r in rp.extract_numbers("On 2026-10-08 in FY26 Stage 2 the stock closed at $1,234.50, up 3.2%, in 2026 with 5 names")]
        self.assertEqual(toks, ["$1,234.50", "3.2%"])


if __name__ == "__main__":
    unittest.main()
