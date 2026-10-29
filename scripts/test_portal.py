"""Focused publishing and homepage catalog regression tests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import portal_publish as portal
from portal_publish import published_url, rewrite_published_links
from email_digest import report_type, should_email, build_digest
import send_email
from assemble_report import build
from bs4 import BeautifulSoup
from datetime import datetime, timezone


class ReportDesignTests(unittest.TestCase):
    def test_new_report_has_pacific_header_and_embedded_design(self):
        result = build('<h1>Report</h1>', generated_at=datetime(2026, 10, 9, 20, 30, tzinfo=timezone.utc))
        self.assertIn('2026-10-09T13:30:00-07:00', result)
        self.assertIn('01:30 PM PDT', result)
        self.assertIn('research-desk-v1', result)
        self.assertIn('Generated Date:', result)
        winter = build('<h1>Report</h1>', generated_at=datetime(2026, 1, 9, 20, 30, tzinfo=timezone.utc))
        self.assertIn('12:30 PM PST', winter)
        with self.assertRaises(ValueError):
            build('<h1>Report</h1>', generated_at=datetime(2026, 1, 9))

    def test_named_reports_preserve_all_research_on_reassembly(self):
        samples = [
            ("US_Market_Intelligence.html", '<h1>US Market Intelligence</h1><h2 id="exec">Executive Summary</h2><p>Content <a href="https://finviz.com/quote.ashx?t=NVDA">NVDA</a>.</p><table class="wikitable"><tr><th>Ticker</th><th>Price</th></tr><tr><td>NVDA</td><td>120</td></tr></table>'),
            ("HAL_dossier.html", '<h1>Hindustan Aeronautics Ltd (NSE: HAL)</h1><h2 id="business">Business Monograph</h2><p>Aerospace &amp; Defence <a href="https://www.screener.in/company/HAL/">Screener</a>.</p><table class="wikitable"><tr><th>Metric</th><th>Value</th></tr><tr><td>ROE</td><td>28%</td></tr></table>'),
        ]
        for name, raw_html in samples:
            with self.subTest(report=name):
                first_pass = build(raw_html, market='US' if name.startswith('US') else 'IN',
                                   kind='dossier' if 'dossier' in name else 'report', layout_only=True)
                original = BeautifulSoup(first_pass, 'html.parser')
                content = original.select_one('main.report') or original.select_one('.report') or original.body
                for decoration in content.select('.report-generated, .report-as-of, script, style, link'):
                    decoration.decompose()
                rendered = BeautifulSoup(build(str(content), layout_only=True), 'html.parser')
                for decoration in rendered.main.select('.report-generated, .report-as-of'):
                    decoration.decompose()
                self.assertEqual(content.get_text(' ', strip=True), rendered.main.get_text(' ', strip=True))
                self.assertEqual([anchor['href'] for anchor in content.select('a[href]')],
                                 [anchor['href'] for anchor in rendered.main.select('a[href]')])
                self.assertEqual([table.get_text(' ', strip=True) for table in content.select('table')],
                                 [table.get_text(' ', strip=True) for table in rendered.main.select('table')])
                self.assertTrue({node['id'] for node in content.select('[id]')} <= {node['id'] for node in rendered.main.select('[id]')})
                self.assertIsNone(rendered.select_one('meta[name="generated-at"]'))

    def test_layout_check_rejects_legacy_and_accepts_assembled_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.html'
            path.write_text('<h1>Old shell</h1>')
            with self.assertRaisesRegex(ValueError, 'assemble'):
                portal.require_modern_report(path)
            path.write_text(build('<h1>Modern report</h1>'))
            portal.require_modern_report(path, require_generated=True)
            path.write_text(build('<h1>Existing research</h1>', layout_only=True))
            portal.require_modern_report(path)
            with self.assertRaisesRegex(ValueError, 'not newly completed'):
                portal.require_modern_report(path, require_generated=True)


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.docs = Path(self.temp.name).resolve() / "docs"
        (self.docs / "blogs").mkdir(parents=True)
        (self.docs / "reports").mkdir()
        self.dossier = self.docs / "blogs" / "TEST_dossier.html"
        self.dossier.write_text('<h1>Test Company (NASDAQ: TEST)</h1><table class="infobox"><tr><th>Verdict</th><td>WATCH</td></tr></table>')
        self.report = self.docs / "reports" / "US_Audit.html"
        self.report.write_text('<h1>US Audit</h1>')

    def test_resolve_paths_and_fragments(self):
        for href in ("../blogs/TEST_dossier.html#thesis", "docs/blogs/TEST_dossier.html#thesis", "TEST_dossier.html#thesis", str(self.dossier) + "#thesis", self.dossier.as_uri() + "#thesis"):
            self.assertEqual(published_url(href, self.report, self.docs), "https://rajasekharmekala.github.io/portfolio/blogs/TEST_dossier.html#thesis")
        self.assertEqual(published_url("../blogs/TEST_dossier.html?view=full#thesis", self.report, self.docs, absolute=False), "../blogs/TEST_dossier.html?view=full#thesis")

    def test_missing_and_escape_paths(self):
        self.assertIsNone(published_url("../../private.json", self.report, self.docs))
        self.assertIsNone(published_url("MISSING_dossier.html", self.report, self.docs))
        self.assertEqual(published_url("https://example.com/report", docs=self.docs), "https://example.com/report")
        self.assertEqual(published_url("#references", docs=self.docs), "#references")

    def test_email_and_idempotent_repair(self):
        original = "<p>Keep formatting</p><a class='x' href='TEST_dossier.html'>Test</a><a href='missing.html'>Missing</a>"
        result = rewrite_published_links(original, self.report, self.docs)
        self.assertIn('href="https://rajasekharmekala.github.io/portfolio/blogs/TEST_dossier.html"', result)
        self.assertIn('aria-disabled="true"', result)
        self.assertTrue(result.startswith("<p>Keep formatting</p>"))
        self.assertEqual(rewrite_published_links(result, self.report, self.docs), result)

    def test_catalog_completion_and_stable_dates(self):
        with patch.object(portal, "DOCS", self.docs), patch.object(portal, "CATALOG", self.docs / "portal-data.json"), patch.object(portal, "UPDATES", self.docs / "portal-updates.json"), patch.object(portal, "git_dates", return_value={"blogs/TEST_dossier.html": "2026-10-08T12:00:00+00:00"}):
            initial = portal.build_catalog()
            self.assertEqual(len(initial["entries"]), 2)
            dossier = next(entry for entry in initial["entries"] if entry["kind"] == "dossier")
            self.assertEqual(dossier["market"], "US")
            self.assertEqual(dossier["verdict"], "WATCHLIST / HOLD")
            self.assertEqual(dossier["timestampSource"], "git")
            with self.assertRaisesRegex(ValueError, "assemble"):
                portal.build_catalog([self.report], "Portfolio audit", "US", "Two positions need review")
            self.report.write_text(build('<h1>US Audit</h1>', market='US', workflow='Portfolio audit'))
            completed = portal.build_catalog([self.report], "Portfolio audit", "US", "Two positions need review", ["Review concentration"])
            entry = next(entry for entry in completed["entries"] if entry["kind"] == "report")
            self.assertEqual(entry["timestampSource"], "workflow")
            self.assertEqual(entry["summary"], "Two positions need review")
            self.assertEqual(entry["highlights"], ["Review concentration"])
            again = portal.build_catalog()
            self.assertEqual(next(item for item in again["entries"] if item["kind"] == "report")["updatedAt"], entry["updatedAt"])
            self.assertTrue(all((self.docs / item["url"]).is_file() for item in again["entries"]))

    def test_redirect_pages_are_not_catalog_entries(self):
        alias = self.docs / 'reports' / 'dated_report.html'
        alias.write_text('<meta name="report-redirect" content="US_Audit_2026-10-09.html"><a href="US_Audit_2026-10-09.html">Report</a>')
        with patch.object(portal, 'DOCS', self.docs), patch.object(portal, 'CATALOG', self.docs / 'portal-data.json'), patch.object(portal, 'UPDATES', self.docs / 'portal-updates.json'), patch.object(portal, 'git_dates', return_value={}):
            catalog = portal.build_catalog()
        self.assertEqual(len(catalog['entries']), 2)
        self.assertNotIn('reports/dated_report.html', [entry['url'] for entry in catalog['entries']])

    def test_market_subfolder_dossiers(self):
        (self.docs / "blogs" / "IN").mkdir(parents=True)
        (self.docs / "blogs" / "US").mkdir(parents=True)
        # US-sounding content in the IN folder stays IN: the folder wins.
        ind = self.docs / "blogs" / "IN" / "TESTIN_dossier.html"
        ind.write_text('<h1>Test India (NASDAQ: TESTIN)</h1><table class="infobox"><tr><th>Exchange</th><td>NSE</td></tr></table>')
        usd = self.docs / "blogs" / "US" / "TESTUS_dossier.html"
        usd.write_text('<h1>Test US (NASDAQ: TESTUS)</h1>')
        # Redirect stub at the legacy flat path stays out of the catalog.
        stub = self.docs / "blogs" / "TESTIN_dossier.html"
        stub.write_text('<meta name="report-redirect" content="IN/TESTIN_dossier.html"><meta http-equiv="refresh" content="0; url=IN/TESTIN_dossier.html">')
        with patch.object(portal, "DOCS", self.docs), patch.object(portal, "CATALOG", self.docs / "portal-data.json"), patch.object(portal, "UPDATES", self.docs / "portal-updates.json"), patch.object(portal, "git_dates", return_value={}):
            catalog = portal.build_catalog()
        urls = {entry["url"]: entry for entry in catalog["entries"]}
        self.assertIn("blogs/IN/TESTIN_dossier.html", urls)
        self.assertIn("blogs/US/TESTUS_dossier.html", urls)
        self.assertNotIn("blogs/TESTIN_dossier.html", urls)
        self.assertEqual(urls["blogs/IN/TESTIN_dossier.html"]["market"], "IN")
        self.assertEqual(urls["blogs/US/TESTUS_dossier.html"]["market"], "US")
        self.assertEqual(published_url("TESTIN_dossier.html", self.report, self.docs),
                         "https://rajasekharmekala.github.io/portfolio/blogs/IN/TESTIN_dossier.html")


class EmailDigestTests(unittest.TestCase):
    def test_delivery_matrix(self):
        self.assertFalse(should_email("watchlist"))
        self.assertFalse(should_email("watchlist", shortlisted=["TEST"]))
        self.assertFalse(should_email("watchlist", displacements=["TEST replaces HELD"]))
        for kind in ("archive", "displacement"):
            self.assertFalse(should_email(kind))
            self.assertTrue(should_email(kind, shortlisted=["TEST"]))
            self.assertTrue(should_email(kind, displacements=["TEST replaces HELD"]))
        for kind in ("market-intelligence", "portfolio-audit"):
            self.assertTrue(should_email(kind))
        self.assertEqual(report_type("Indian Watchlist to Shortlist"), "watchlist")
        self.assertEqual(report_type("US Watchlist to Shortlist"), "watchlist")
        self.assertEqual(report_type("Archive Resurrection Review"), "archive")
        self.assertEqual(report_type("Rejected to Watchlist"), "archive")

    def test_skips_before_credentials_and_smtp(self):
        with patch.object(send_email, "load_env") as load_env, patch.object(send_email.smtplib, "SMTP_SSL") as smtp:
            self.assertFalse(send_email.send_email_html("Watchlist to Shortlist", "FULL REPORT"))
            self.assertFalse(send_email.send_email_html("Watchlist to Shortlist", "FULL REPORT", shortlisted=["TEST"]))
            self.assertFalse(send_email.send_email_html("Archive Resurrection", "FULL REPORT"))
            load_env.assert_not_called()
            smtp.assert_not_called()

    def test_digest_is_summary_only(self):
        source = Path(__file__).resolve().parents[1] / "docs" / "reports" / "US_Market_Intelligence.html"
        created = False
        if not source.exists():
            source.write_text(build("<h1>US Market Intelligence</h1>", market="US"), encoding="utf-8")
            created = True
        try:
            body, plain = build_digest("Portfolio audit", "FULL REPORT CONTENT", source,
                                       summary="Concentration needs review", highlights=["Review <risk>"],
                                       shortlisted=["TEST"], displacements=["TEST replaces HELD"])
        finally:
            if created and source.exists():
                source.unlink()
        self.assertNotIn("FULL REPORT CONTENT", body)
        self.assertIn("Review &lt;risk&gt;", body)
        self.assertIn("New shortlist qualification: TEST", plain)
        self.assertIn("Eligible holding displacement: TEST replaces HELD", plain)
        self.assertIn("https://rajasekharmekala.github.io/portfolio/reports/", body)
        with self.assertRaises(ValueError):
            build_digest("Audit", "Full report", None)
        with self.assertRaises(ValueError):
            build_digest("Audit", "Full report", "/tmp/not-published.html")


if __name__ == "__main__":
    unittest.main()
