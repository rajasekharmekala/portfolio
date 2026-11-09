import subprocess
import json
import hashlib
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

from review_packet import KINDS, check, check_label
from bs4 import BeautifulSoup
from readability_check import check_grade


class Stage2GateTest(unittest.TestCase):
    def test_empty_stage2_report_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.html"
            report.write_text("<html><body><h1>Stage 2</h1></body></html>")
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("validate_report.py")),
                 "--report", str(report), "--kind", "stage2_sector_momentum"],
                capture_output=True, text=True, check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("STAGE2 SECTION MISSING", result.stdout)
        self.assertIn("STAGE2 INPUT", result.stdout)
        self.assertIn("STAGE2 CANDIDATES", result.stdout)
        self.assertIn("RESULT: FAIL", result.stdout)

    def test_review_packet_accepts_stage2_kind(self):
        self.assertIn("stage2_sector_momentum", KINDS)

    def test_review_packet_does_not_hide_citation_exception(self):
        self.assertEqual(check_label({"ok": True, "lines": ["WARN EXCEPTION AS-OF ABC"]}), "PASS WITH EXCEPTIONS")

    def test_review_rejects_changed_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report, evidence, packet, review = [root / name for name in ("report.html", "snapshot.json", "packet.json", "review.json")]
            report.write_text("<h1>Report</h1>")
            evidence.write_text("changed")
            report_hash = hashlib.sha256(report.read_bytes()).hexdigest()
            packet.write_text(json.dumps({"report_sha256": report_hash, "files": {"snapshots": str(evidence)},
                                          "file_sha256": {"snapshots": "old-hash"}, "item_ids": []}))
            review.write_text(json.dumps({"verdict": "APPROVE", "round": 1, "pass": "review", "findings": []}))
            output = io.StringIO()
            with redirect_stdout(output):
                result = check(SimpleNamespace(review=str(review), packet=str(packet), report=str(report)))
        self.assertEqual(result, 1)
        self.assertIn("STALE: snapshots evidence changed", output.getvalue())

    def test_stage2_readability_grades_prose_not_sector_table(self):
        soup = BeautifulSoup('<section class="chapter"><p>Stocks can rise. Prices can fall.</p>'
                             '<table>' + '<tr><td>telecommunication industrial classification</td></tr>' * 100
                             + '</table></section>', 'html.parser')
        errors = []
        check_grade(soup, 13.0, errors, prose_only=True)
        self.assertEqual(errors, [])

    def test_stage2_readability_still_checks_bare_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.html"
            report.write_text('<section class="chapter"><p>Stocks can rise.</p><table><tr><td>1</td></tr></table></section>')
            result = subprocess.run([sys.executable, str(Path(__file__).with_name("readability_check.py")),
                                     str(report), "--kind", "stage2_sector_momentum"],
                                    capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("TABLE:", result.stdout)
        self.assertNotIn("CHAPTER 7:", result.stdout)

    def test_extended_stock_cannot_be_labeled_immediate_buy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.html"
            report.write_text('<meta name="research-as-of" content="2026-10-30"><h1>Downtrend</h1>'
                              '<div class="casenote" data-symbol="TEST">Case</div>'
                              '<table><tr><th>Symbol</th><th>Timing screen</th></tr>'
                              '<tr><td>TEST</td><td>IMMEDIATE BUY</td></tr>'
                              '<tr><td>OTHER</td><td>WAIT</td></tr></table>')
            facts = root / "facts.json"
            facts.write_text(json.dumps({"asof": "2026-10-30", "instruments": {}, "regime": {"label": "Downtrend"}}))
            research = root / "research.json"
            research.write_text(json.dumps({"items": [{"symbol": "TEST", "status": "found"}]}))
            snapshots = root / "snapshots.json"
            snapshots.write_text(json.dumps({"snapshots": {"TEST": {
                "tradingview": {"ema10_weekly": 100, "rsi_14_daily": 74, "pe_ttm": 20, "revenue_yoy_growth_ttm_pct": 10},
                "stage2_evaluation": {"extension_from_10w_ema_pct": 11, "extension_from_50d_sma_pct": 5, "technical_timing_gate": "CLEAR_FOR_CONSIDERATION"}}}}))
            dashboard = root / "dashboard.json"
            dashboard.write_text(json.dumps({"market": "IN", "summary": {"last_updated": "2026-10-31"}, "extracted_at": "2026-11-01"}))
            result = subprocess.run([sys.executable, str(Path(__file__).with_name("validate_report.py")),
                "--report", str(report), "--kind", "stage2_sector_momentum", "--facts", str(facts),
                "--research", str(research), "--snapshots", str(snapshots), "--stage2-file", str(dashboard)],
                capture_output=True, text=True, check=False)
        self.assertIn("STAGE2 ENTRY RULE: TEST", result.stdout)
        self.assertIn("STAGE2 COVERAGE:", result.stdout)
        self.assertIn("STAGE2 FILTERS:", result.stdout)


if __name__ == "__main__":
    unittest.main()
