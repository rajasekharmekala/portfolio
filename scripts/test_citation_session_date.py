import datetime
import tempfile
import unittest
from pathlib import Path

from citation_check import report_date


class SessionDateTest(unittest.TestCase):
    def test_session_metadata_wins_over_stable_or_dated_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report_2026-11-01.html"
            report.write_text('<meta content="2026-10-30" name="research-as-of">')
            self.assertEqual(report_date(report), datetime.date(2026, 10, 30))

    def test_historical_dated_filename_still_works(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report_2026-10-30.html"
            report.write_text("<html></html>")
            self.assertEqual(report_date(report), datetime.date(2026, 10, 30))


if __name__ == "__main__":
    unittest.main()
