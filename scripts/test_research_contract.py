"""
W6 acceptance: the research contract round-trips through the fetch cache and the
W3 citation gate.

  1. a sample company produces a complete record and its source page is in the
     fetch cache -> the citation validator ACCEPTS;
  2. the same record with a deliberately altered value -> REJECTED
     (VALUE NOT IN CACHED TEXT);
  3. a found record whose URL was never fetched -> REJECTED (URL NOT IN CACHE);
  4. an honest not_found record (3+ queries) -> accepted.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import citation_check as cc  # noqa: E402
import fetch_cache as fc     # noqa: E402

PAGE = """<html><head><title>AFCOM Holdings Ltd - Promoter shareholding</title></head>
<body>
<h1>AFCOM Holdings Ltd — Promoter shareholding</h1>
<table>
<tr><th>Promoter</th><th>Held</th><th>%</th><th>Pledged</th></tr>
<tr><td>Promoter Group</td><td>521432881</td><td>50.00%</td><td>0 (0.0%)</td></tr>
</table>
<p>Shareholding as on 30-06-2026.</p>
</body></html>
"""

URL = "https://trendlyne.example.com/equity/share-holding/afcom/latest/"
REPORT_DATE = "2026-10-08"


def make_report(path):
    refs = "\n".join(
        f'<li><a href="https://primary{i}.example.com/filing">{i}</a></li>'
        for i in range(1, 26))
    html = (f"<html><body><h1>W6 test dossier {REPORT_DATE}</h1>"
            f"<ul>{refs}</ul></body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def record(status="found", value=None, url=URL, as_of="2026-10-01", **kw):
    r = {
        "key": "promoter_pledge", "symbol": "AFCOM", "status": status,
        "value": value,
        "unit": {"pledge_pct_of_promoter_holding": "percent of promoter holding"},
        "quoted": "Promoter Group ... Pledged: 0 (0.0%)",
        "source_url": url,
        "retrieved_at": "2026-10-01T09:00:00",
        "as_of": as_of,
        "queries_tried": ["AFCOM promoter pledge latest shareholding 2026",
                          "site:trendlyne.com AFCOM pledge",
                          "AFCOM shareholding pledged 30-06-2026"],
        "sources_tried": ["Trendlyne", "Screener"],
    }
    r.update(kw)
    return r


class TestResearchContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache = os.path.join(self.tmp, "fetched")
        self._orig_cache_dir = fc.CACHE_DIR
        fc.CACHE_DIR = self.cache
        self.page = os.path.join(self.tmp, "page.html")
        with open(self.page, "w", encoding="utf-8") as f:
            f.write(PAGE)
        self.report = os.path.join(self.tmp, "report.html")
        make_report(self.report)

    def tearDown(self):
        fc.CACHE_DIR = self._orig_cache_dir

    def write_research(self, items):
        p = os.path.join(self.tmp, "research.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"items": items}, f)
        return p

    def build_cache(self, url=URL):
        entry = fc.fetch(url, text_file=self.page)
        fc.store(entry)
        return json.load(open(fc.cache_path(url), encoding="utf-8"))

    def test_complete_record_accepted(self):
        self.build_cache()
        rec = record(value={"pledge_pct_of_promoter_holding": "0.0%",
                            "period": "2026-06"})
        rp = self.write_research([rec])
        errors, _ = cc.check(self.report, [rp], self.cache,
                             min_sources=25, max_age_days=60)
        self.assertEqual(errors, [], f"expected acceptance, got: {errors}")

    def test_altered_value_rejected(self):
        self.build_cache()
        rec = record(value={"pledge_pct_of_promoter_holding": "12.5%",
                            "period": "2026-06"})
        rp = self.write_research([rec])
        errors, _ = cc.check(self.report, [rp], self.cache,
                             min_sources=25, max_age_days=60)
        joined = " | ".join(errors)
        self.assertTrue("VALUE NOT IN CACHED TEXT" in joined,
                        f"expected value-mismatch rejection, got: {joined}")

    def test_uncached_url_rejected(self):
        self.build_cache()
        rec = record(value={"pledge_pct_of_promoter_holding": "0.0%"},
                     url="https://elsewhere.example.com/never-fetched/")
        rp = self.write_research([rec])
        errors, _ = cc.check(self.report, [rp], self.cache,
                             min_sources=25, max_age_days=60)
        joined = " | ".join(errors)
        self.assertTrue("URL NOT IN CACHE" in joined,
                        f"expected url-mismatch rejection, got: {joined}")

    def test_stale_as_of_rejected(self):
        self.build_cache()
        rec = record(value={"pledge_pct_of_promoter_holding": "0.0%"},
                     as_of="2026-01-01")
        rp = self.write_research([rec])
        errors, _ = cc.check(self.report, [rp], self.cache,
                             min_sources=25, max_age_days=60)
        joined = " | ".join(errors)
        self.assertTrue("AS-OF" in joined,
                        f"expected staleness rejection, got: {joined}")

    def test_honest_not_found_accepted(self):
        rec = record(status="not_found", value=None, source_url=None, as_of=None)
        rec["reason"] = "metric_not_published"
        # not_found: no source_url / as_of requirements; 3 queries is the floor
        del rec["source_url"]
        del rec["as_of"]
        rp = self.write_research([rec])
        errors, _ = cc.check(self.report, [rp], self.cache,
                             min_sources=25, max_age_days=60)
        self.assertEqual(errors, [], f"expected acceptance, got: {errors}")

    def test_cache_entry_shape_and_hash(self):
        e = self.build_cache()
        self.assertEqual(e["url"], URL)
        self.assertEqual(e["status"], "ok")
        self.assertIn("retrieved_at", e)
        import hashlib
        self.assertEqual(e["sha256"],
                         hashlib.sha256(e["text"].encode()).hexdigest())
        self.assertIn("0.0%", e["text"])
        # re-store without force is a no-op
        self.assertEqual(fc.store(e), "cached")


if __name__ == "__main__":
    unittest.main()
