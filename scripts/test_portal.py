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


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.docs = Path(self.temp.name).resolve() / "docs"
        (self.docs / "blogs").mkdir(parents=True)
        (self.docs / "reports").mkdir()
        self.dossier = self.docs / "blogs" / "TEST_dossier.html"
        self.dossier.write_text('<h1>Test Company (NASDAQ: TEST)</h1><table class="infobox"><tr><th>Verdict</th><td>WATCH</td></tr></table>')
        self.report = self.docs / "reports" / "US_Audit_2026-10-09.html"
        self.report.write_text('<h1>US Audit</h1>')

    def test_resolve_paths_and_fragments(self):
        for href in ("../blogs/TEST_dossier.html#thesis", "docs/blogs/TEST_dossier.html#thesis", "TEST_dossier.html#thesis", str(self.dossier) + "#thesis", self.dossier.as_uri() + "#thesis"):
            self.assertEqual(published_url(href, self.report, self.docs), "https://git.corp.adobe.com/pages/mereddy/ai-automations/blogs/TEST_dossier.html#thesis")
        self.assertEqual(published_url("../blogs/TEST_dossier.html?view=full#thesis", self.report, self.docs, absolute=False), "../blogs/TEST_dossier.html?view=full#thesis")

    def test_missing_and_escape_paths(self):
        self.assertIsNone(published_url("../../private.json", self.report, self.docs))
        self.assertIsNone(published_url("MISSING_dossier.html", self.report, self.docs))
        self.assertEqual(published_url("https://example.com/report", docs=self.docs), "https://example.com/report")
        self.assertEqual(published_url("#references", docs=self.docs), "#references")

    def test_email_and_idempotent_repair(self):
        original = "<p>Keep formatting</p><a class='x' href='TEST_dossier.html'>Test</a><a href='missing.html'>Missing</a>"
        result = rewrite_published_links(original, self.report, self.docs)
        self.assertIn('href="https://git.corp.adobe.com/pages/mereddy/ai-automations/blogs/TEST_dossier.html"', result)
        self.assertIn('aria-disabled="true"', result)
        self.assertTrue(result.startswith("<p>Keep formatting</p>"))
        self.assertEqual(rewrite_published_links(result, self.report, self.docs), result)

    def test_catalog_completion_and_stable_dates(self):
        with patch.object(portal, "DOCS", self.docs), patch.object(portal, "CATALOG", self.docs / "portal-data.json"), patch.object(portal, "UPDATES", self.docs / "portal-updates.json"), patch.object(portal, "git_dates", return_value={"blogs/TEST_dossier.html": "2026-10-08T12:00:00+00:00"}):
            initial = portal.build_catalog()
            self.assertEqual(len(initial["entries"]), 2)
            dossier = next(entry for entry in initial["entries"] if entry["kind"] == "dossier")
            self.assertEqual(dossier["market"], "US")
            self.assertEqual(dossier["verdict"], "WATCH")
            self.assertEqual(dossier["timestampSource"], "git")
            completed = portal.build_catalog([self.report], "Portfolio audit", "US", "Two positions need review", ["Review concentration"])
            entry = next(entry for entry in completed["entries"] if entry["kind"] == "report")
            self.assertEqual(entry["timestampSource"], "workflow")
            self.assertEqual(entry["summary"], "Two positions need review")
            self.assertEqual(entry["highlights"], ["Review concentration"])
            again = portal.build_catalog()
            self.assertEqual(next(item for item in again["entries"] if item["kind"] == "report")["updatedAt"], entry["updatedAt"])
            self.assertTrue(all((self.docs / item["url"]).is_file() for item in again["entries"]))


class EmailDigestTests(unittest.TestCase):
    def test_delivery_matrix(self):
        for kind in ("watchlist", "archive", "displacement"):
            self.assertFalse(should_email(kind))
            self.assertTrue(should_email(kind, shortlisted=["TEST"]))
            self.assertTrue(should_email(kind, displacements=["TEST replaces HELD"]))
        for kind in ("market-intelligence", "portfolio-audit"):
            self.assertTrue(should_email(kind))
        self.assertEqual(report_type("Indian Watchlist to Shortlist"), "watchlist")
        self.assertEqual(report_type("Archive Resurrection Review"), "archive")
        self.assertEqual(report_type("Rejected to Watchlist"), "archive")

    def test_skips_before_credentials_and_smtp(self):
        with patch.object(send_email, "load_env") as load_env, patch.object(send_email.smtplib, "SMTP_SSL") as smtp:
            self.assertFalse(send_email.send_email_html("Watchlist to Shortlist", "FULL REPORT"))
            self.assertFalse(send_email.send_email_html("Archive Resurrection", "FULL REPORT"))
            load_env.assert_not_called()
            smtp.assert_not_called()

    def test_digest_is_summary_only(self):
        source = Path(__file__).resolve().parents[1] / "docs" / "reports" / "US_Portfolio_Audit_2026-10-08.html"
        body, plain = build_digest("Portfolio audit", "FULL REPORT CONTENT", source,
                                   summary="Concentration needs review", highlights=["Review <risk>"],
                                   shortlisted=["TEST"], displacements=["TEST replaces HELD"])
        self.assertNotIn("FULL REPORT CONTENT", body)
        self.assertIn("Review &lt;risk&gt;", body)
        self.assertIn("New shortlist qualification: TEST", plain)
        self.assertIn("Eligible holding displacement: TEST replaces HELD", plain)
        self.assertIn("https://git.corp.adobe.com/pages/mereddy/ai-automations/reports/", body)
        with self.assertRaises(ValueError):
            build_digest("Audit", "Full report", None)
        with self.assertRaises(ValueError):
            build_digest("Audit", "Full report", "/tmp/not-published.html")


if __name__ == "__main__":
    unittest.main()
