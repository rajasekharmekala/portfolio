import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


VALIDATOR = Path(__file__).with_name("validate_report.py")


class ValidatorSectionTests(unittest.TestCase):
    def run_validator(self, html, *options):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "section.html"
            report.write_text(html, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), "--report", str(report),
                 "--kind", "market_intel", *options],
                capture_output=True, text=True, check=False,
            )

    def test_partial_does_not_require_whole_report_case_note_count(self):
        result = self.run_validator("<h1>Report</h1><p>Session note.</p>", "--partial")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("RESULT: PASS", result.stdout)

    def test_full_report_still_requires_case_notes(self):
        result = self.run_validator("<h1>Report</h1><p>Session note.</p>")
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("FAIL  CASE NOTES:", result.stdout)
        self.assertIn("RESULT: FAIL", result.stdout)

    def test_partial_still_checks_present_case_note_quality(self):
        result = self.run_validator('<div class="casenote">Too short.</div>', "--partial")
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("FAIL  CASE NOTE TOO SHORT", result.stdout)

    def test_table_wrapper_with_accessibility_attributes_is_recognized(self):
        table = '<table><tr><th>Heading</th></tr><tr><td>Value</td></tr></table>'
        wrapped = self.run_validator(f'<div role="region" class="table-wrap" tabindex="0">{table}</div>')
        self.assertNotIn("not inside <div", wrapped.stdout)
        unwrapped = self.run_validator(table)
        self.assertIn("not inside <div", unwrapped.stdout)


if __name__ == "__main__":
    unittest.main()
