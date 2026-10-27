"""Concurrent-run safety: claims, record-level merge, per-run worktrees and publishing."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record_merge as rm
import run_claims

SCRIPTS = Path(__file__).resolve().parent
COPIED = ("record_merge.py", "run_claims.py", "run_session.py", "publish_run.py")
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def rows(*symbols, status="RESEARCH_REQUIRED"):
    return [{"symbol": s, "status": status, "cmp": 1.0} for s in symbols]


class RecordMergeTests(unittest.TestCase):
    def test_different_symbols_merge(self):
        base = {"active": rows("A", "B", "C")}
        ours = {"active": [dict(r, status="COMPLETED") if r["symbol"] == "A" else r for r in base["active"]]}
        theirs = {"active": [dict(r, cmp=2.0) if r["symbol"] == "C" else r for r in base["active"]]}
        merged = rm.merge3(base, ours, theirs)
        by = {r["symbol"]: r for r in merged["active"]}
        self.assertEqual(by["A"]["status"], "COMPLETED")
        self.assertEqual(by["C"]["cmp"], 2.0)
        self.assertEqual([r["symbol"] for r in merged["active"]], ["A", "B", "C"])

    def test_different_fields_of_one_symbol_merge(self):
        base = {"active": [{"symbol": "A", "status": "X", "cmp": 1}]}
        ours = {"active": [{"symbol": "A", "status": "Y", "cmp": 1}]}
        theirs = {"active": [{"symbol": "A", "status": "X", "cmp": 2}]}
        self.assertEqual(rm.merge3(base, ours, theirs)["active"][0], {"symbol": "A", "status": "Y", "cmp": 2})

    def test_same_field_changed_differently_conflicts(self):
        base = {"active": [{"symbol": "A", "status": "X"}]}
        ours = {"active": [{"symbol": "A", "status": "Y"}]}
        theirs = {"active": [{"symbol": "A", "status": "Z"}]}
        with self.assertRaises(rm.MergeConflict) as caught:
            rm.merge3(base, ours, theirs)
        self.assertIn("[A].status", caught.exception.conflicts[0])

    def test_adds_deletes_and_moves(self):
        base = {"active": rows("A", "B"), "archive": []}
        ours = {"active": rows("A"), "archive": rows("B", status="REJECTED")}      # B archived
        theirs = {"active": rows("A", "B", "N"), "archive": []}                      # N added
        merged = rm.merge3(base, ours, theirs)
        self.assertEqual([r["symbol"] for r in merged["active"]], ["A", "N"])
        self.assertEqual([r["symbol"] for r in merged["archive"]], ["B"])

    def test_delete_versus_modify_conflicts(self):
        base = {"active": rows("A", "B")}
        with self.assertRaises(rm.MergeConflict):
            rm.merge3(base, {"active": rows("B")}, {"active": [dict(rows("A")[0], cmp=9), rows("B")[0]]})

    def test_same_symbol_added_identically_is_fine(self):
        base = {"active": rows("A")}
        both = {"active": rows("A", "N")}
        self.assertEqual(rm.merge3(base, both, json.loads(json.dumps(both))), both)

    def test_deliberate_reorder_is_kept(self):
        base = {"active": rows("A", "B", "C")}
        ours = {"active": rows("C", "A", "B")}
        theirs = {"active": [dict(r, cmp=3.0) if r["symbol"] == "B" else r for r in base["active"]]}
        merged = rm.merge3(base, ours, theirs)
        self.assertEqual([r["symbol"] for r in merged["active"]], ["C", "A", "B"])
        self.assertEqual(merged["active"][2]["cmp"], 3.0)

    def test_output_matches_repository_format(self):
        text = rm.dump({"a": ["é"]}, "")
        self.assertEqual(text, '{\n  "a": [\n    "é"\n  ]\n}\n')


class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["PORTFOLIO_CLAIMS_DIR"] = self.tmp

    def tearDown(self):
        os.environ.pop("PORTFOLIO_CLAIMS_DIR", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_singleton_refuses_second_run_and_is_per_market(self):
        run_claims.claim_singleton("market_intelligence", "US", "r1")
        run_claims.claim_singleton("market_intelligence", "US", "r1")          # same run: idempotent
        with self.assertRaises(run_claims.ClaimConflict):
            run_claims.claim_singleton("market_intelligence", "US", "r2")
        run_claims.claim_singleton("market_intelligence", "IN", "r2")          # other market is independent
        run_claims.claim_singleton("portfolio_audit", "US", "r2")              # other workflow is independent
        run_claims.release("r1")
        run_claims.claim_singleton("market_intelligence", "US", "r2")

    def test_batches_never_overlap_and_skip_held_names(self):
        pool = list("ABCDEFGHIJ")
        a, _ = run_claims.claim_batch("watchlist_to_shortlist", "US", "r1", 4, pool)
        b, skipped = run_claims.claim_batch("watchlist_to_shortlist", "US", "r2", 4, pool)
        self.assertEqual(a, list("ABCD"))
        self.assertEqual(b, list("EFGH"))
        self.assertEqual(set(skipped), set("ABCD"))
        again, _ = run_claims.claim_batch("watchlist_to_shortlist", "US", "r1", 4, pool)
        self.assertEqual(sorted(again), list("ABCD"))                          # a restart gets the same names
        c, _ = run_claims.claim_batch("watchlist_to_shortlist", "US", "r3", 4, pool)
        self.assertEqual(c, ["I", "J"])                                        # short batch, no widening

    def test_names_are_exclusive_across_workflows_and_markets_are_separate(self):
        run_claims.claim_batch("watchlist_to_shortlist", "US", "r1", 1, ["A"])
        with self.assertRaises(run_claims.ClaimConflict):
            run_claims.claim_names("company_report", "US", "r2", ["A"])
        run_claims.claim_names("company_report", "IN", "r2", ["A"])
        run_claims.release("r1", {"A"})
        run_claims.claim_names("company_report", "US", "r2", ["A"])

    def test_claim_names_is_all_or_nothing(self):
        run_claims.claim_names("company_report", "US", "r1", ["B"])
        with self.assertRaises(run_claims.ClaimConflict):
            run_claims.claim_names("company_report", "US", "r2", ["A", "B"])
        self.assertNotIn("name:US:A", run_claims.list_claims())

    def test_expired_claims_are_ignored(self):
        run_claims.claim_batch("watchlist_to_shortlist", "US", "dead", 2, ["A", "B"], ttl_hours=0)
        time.sleep(0.05)
        taken, _ = run_claims.claim_batch("watchlist_to_shortlist", "US", "r2", 2, ["A", "B"])
        self.assertEqual(taken, ["A", "B"])

    def test_heartbeat_keeps_a_claim_alive(self):
        run_claims.claim_singleton("portfolio_audit", "US", "r1", ttl_hours=1)
        self.assertEqual(run_claims.heartbeat("r1"), 1)
        self.assertEqual(run_claims.heartbeat("nobody"), 0)


class EndToEndTests(unittest.TestCase):
    """Real git: a bare origin, the main checkout, and two runs in their own worktrees."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.env = dict(os.environ, **GIT_ENV)
        self.env.pop("PORTFOLIO_CLAIMS_DIR", None)
        self.origin = self.tmp / "origin.git"
        self.main = self.tmp / "main"
        self.sh("git", "init", "-q", "--bare", "-b", "main", str(self.origin), cwd=self.tmp)
        self.sh("git", "clone", "-q", str(self.origin), str(self.main), cwd=self.tmp)
        self.sh("git", "checkout", "-q", "-b", "main", cwd=self.main)
        (self.main / "scripts").mkdir()
        for name in COPIED:
            shutil.copy(SCRIPTS / name, self.main / "scripts" / name)
        config = self.main / ".agents/config"
        config.mkdir(parents=True)
        (config / "portfolios.json").write_text(json.dumps({"US": {"sources": [
            {"id": "watchlist_active", "role": "watchlist", "kind": "records", "path": "data/watchlist/US.json"}]}}))
        (self.main / ".gitignore").write_text(".worktrees/\n__pycache__/\n")
        self.write(self.main, "data/watchlist/US.json", {"market": "US", "active": rows(*"ABCDEFGH"), "archive": []})
        self.write(self.main, "data/shortlist/US.json", {"market": "US", "sheets": {"Master_Shortlist": []}})
        (self.main / "docs/blogs/US").mkdir(parents=True)
        (self.main / "docs/blogs/US/.gitkeep").write_text("")
        self.sh("git", "add", "-A", cwd=self.main)
        self.sh("git", "commit", "-q", "-m", "seed", cwd=self.main)
        self.sh("git", "push", "-q", "origin", "main", cwd=self.main)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sh(self, *cmd, cwd, check=True):
        done = subprocess.run(cmd, cwd=cwd, env=self.env, capture_output=True, text=True)
        if check and done.returncode != 0:
            raise AssertionError(f"{cmd} -> {done.returncode}\n{done.stdout}\n{done.stderr}")
        return done

    def py(self, script, *args, cwd=None, check=True):
        cwd = cwd or self.main
        return self.sh(sys.executable, str(cwd / "scripts" / script), *args, cwd=cwd, check=check)

    @staticmethod
    def write(root, rel, data):
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    @staticmethod
    def read(root, rel):
        return json.loads((Path(root) / rel).read_text())

    def start(self, workflow, run_id):
        out = self.py("run_session.py", "start", "--workflow", workflow, "--market", "US", "--run-id", run_id)
        return Path(json.loads(out.stdout)["worktree"])

    def origin_file(self, rel):
        return json.loads(self.sh("git", "show", f"main:{rel}", cwd=self.origin).stdout)

    def publish(self, tree, run_id, check=True):
        return self.py("publish_run.py", "--run-id", run_id, "--market", "US", "--message", f"run {run_id}",
                       "--no-portal", "--no-validate", cwd=tree, check=check)

    def complete(self, tree, symbols, shortlist_row=None):
        path = "data/watchlist/US.json"
        data = self.read(tree, path)
        for row in data["active"]:
            if row["symbol"] in symbols:
                row["status"] = "COMPLETED"
                (tree / f"docs/blogs/US/{row['symbol']}_dossier.html").write_text(f"<html>{row['symbol']}</html>")
        self.write(tree, path, data)
        if shortlist_row:
            sheet = self.read(tree, "data/shortlist/US.json")
            sheet["sheets"]["Master_Shortlist"].append({"symbol": shortlist_row})
            self.write(tree, "data/shortlist/US.json", sheet)

    def test_two_runs_work_in_parallel_and_both_land_on_main(self):
        one, two = self.start("watchlist_to_shortlist", "r1"), self.start("watchlist_to_shortlist", "r2")
        self.assertNotEqual(one, two)
        got1 = json.loads(self.py("run_claims.py", "batch", "--workflow", "watchlist_to_shortlist", "--market", "US",
                                  "--run-id", "r1", "--size", "3", cwd=one).stdout)["symbols"]
        got2 = json.loads(self.py("run_claims.py", "batch", "--workflow", "watchlist_to_shortlist", "--market", "US",
                                  "--run-id", "r2", "--size", "3", cwd=two).stdout)["symbols"]
        self.assertEqual(got1, list("ABC"))
        self.assertEqual(got2, list("DEF"))

        self.complete(one, got1, shortlist_row="A")
        self.complete(two, got2, shortlist_row="D")
        self.publish(one, "r1")
        self.publish(two, "r2")                                  # origin moved under it: must merge, not clobber

        active = {r["symbol"]: r["status"] for r in self.origin_file("data/watchlist/US.json")["active"]}
        self.assertEqual(active, {**{s: "COMPLETED" for s in "ABCDEF"}, "G": "RESEARCH_REQUIRED", "H": "RESEARCH_REQUIRED"})
        self.assertEqual([r["symbol"] for r in self.origin_file("data/shortlist/US.json")["sheets"]["Master_Shortlist"]],
                         ["A", "D"])
        listing = self.sh("git", "ls-tree", "-r", "--name-only", "main", "docs/blogs/US", cwd=self.origin).stdout
        for symbol in "ABCDEF":
            self.assertIn(f"{symbol}_dossier.html", listing)
        parents = self.sh("git", "log", "--format=%P", "main", cwd=self.origin).stdout.split("\n")
        self.assertTrue(all(len(p.split()) <= 1 for p in parents), "history must stay linear")
        self.assertEqual(run_claims_list(self.main, self.env), "")      # claims released after the pushes

        # a third run now starts from the new origin and is offered only what is left
        three = self.start("watchlist_to_shortlist", "r3")
        got3 = json.loads(self.py("run_claims.py", "batch", "--workflow", "watchlist_to_shortlist", "--market", "US",
                                  "--run-id", "r3", "--size", "3", cwd=three).stdout)
        self.assertEqual(got3["symbols"], ["G", "H"])
        self.assertTrue(got3["short_batch"])

    def test_concurrent_batch_requests_never_overlap(self):
        trees = [self.start("watchlist_to_shortlist", f"p{i}") for i in range(4)]
        procs = [subprocess.Popen([sys.executable, str(t / "scripts/run_claims.py"), "batch", "--workflow",
                                   "watchlist_to_shortlist", "--market", "US", "--run-id", f"p{i}", "--size", "2",
                                   "--no-fetch"], cwd=t, env=self.env, stdout=subprocess.PIPE, text=True)
                 for i, t in enumerate(trees)]
        taken = [json.loads(p.communicate()[0])["symbols"] for p in procs]
        flat = [s for group in taken for s in group]
        self.assertEqual(len(flat), 8)
        self.assertEqual(len(set(flat)), 8)

    def test_second_singleton_run_is_refused(self):
        self.start("market_intelligence", "m1")
        refused = self.py("run_session.py", "start", "--workflow", "market_intelligence", "--market", "US",
                          "--run-id", "m2", check=False)
        self.assertEqual(refused.returncode, 3)
        self.assertIn("REFUSED", refused.stderr)
        self.assertFalse((self.main / ".worktrees/m2").exists())
        self.py("run_session.py", "finish", "--run-id", "m1")
        self.start("market_intelligence", "m3")

    def test_same_record_changed_by_both_is_refused_and_nothing_is_pushed(self):
        one, two = self.start("company_report", "c1"), self.start("company_report", "c2")
        for tree, verdict in ((one, "BUY"), (two, "SELL")):
            data = self.read(tree, "data/watchlist/US.json")
            data["active"][0]["status"] = verdict
            self.write(tree, "data/watchlist/US.json", data)
        self.publish(one, "c1")
        before = self.sh("git", "rev-parse", "main", cwd=self.origin).stdout
        refused = self.publish(two, "c2", check=False)
        self.assertEqual(refused.returncode, 5, refused.stderr)
        self.assertIn("[A].status", refused.stderr)
        self.assertEqual(self.sh("git", "rev-parse", "main", cwd=self.origin).stdout, before)
        self.assertEqual(self.sh("git", "branch", "--show-current", cwd=two).stdout.strip(), "run/c2")
        self.assertEqual(self.read(two, "data/watchlist/US.json")["active"][0]["status"], "SELL")

    def test_publishing_from_the_shared_checkout_is_refused(self):
        (self.main / "docs/x.html").write_text("x")
        refused = self.py("publish_run.py", "--run-id", "x", "--market", "US", "--message", "m", "--no-portal",
                          "--no-validate", cwd=self.main, check=False)
        self.assertEqual(refused.returncode, 2)

    def test_changes_outside_deliverable_paths_are_refused(self):
        tree = self.start("company_report", "s1")
        (tree / "stray.txt").write_text("x")
        refused = self.publish(tree, "s1", check=False)
        self.assertEqual(refused.returncode, 2)
        self.assertIn("stray.txt", refused.stderr)

    def test_newer_origin_page_is_not_overwritten_by_an_older_run(self):
        def page(asof, generated):
            return (f'<html><head><meta name="research-as-of" content="{asof}">'
                    f'<meta name="generated-at" content="{generated}"></head></html>')
        report = "docs/reports/US_Market_Intelligence.html"
        (self.main / "docs/reports").mkdir()
        (self.main / report).write_text(page("2026-10-14", "2026-10-14T20:00:00-07:00"))
        self.sh("git", "add", "-A", cwd=self.main)
        self.sh("git", "commit", "-q", "-m", "report", cwd=self.main)
        self.sh("git", "push", "-q", "origin", "main", cwd=self.main)
        older, newer = self.start("company_report", "o1"), self.start("company_report", "o2")
        (older / report).write_text(page("2026-10-15", "2026-10-15T10:00:00-07:00"))
        (newer / report).write_text(page("2026-10-16", "2026-10-16T10:00:00-07:00"))
        self.publish(newer, "o2")
        refused = self.publish(older, "o1", check=False)
        self.assertEqual(refused.returncode, 5)
        self.assertIn("later than this run", refused.stderr)
        self.assertIn("2026-10-16", self.sh("git", "show", f"main:{report}", cwd=self.origin).stdout)

    def test_finish_removes_worktree_and_claims(self):
        tree = self.start("watchlist_to_shortlist", "f1")
        self.py("run_claims.py", "batch", "--workflow", "watchlist_to_shortlist", "--market", "US", "--run-id", "f1",
                "--size", "2", cwd=tree)
        self.py("run_session.py", "finish", "--run-id", "f1")
        self.assertFalse(tree.exists())
        self.assertEqual(run_claims_list(self.main, self.env), "")

    def test_finish_from_inside_worktree_succeeds(self):
        tree = self.start("watchlist_to_shortlist", "f2")
        self.py("run_claims.py", "batch", "--workflow", "watchlist_to_shortlist", "--market", "US", "--run-id", "f2",
                "--size", "2", cwd=tree)
        self.py("run_session.py", "finish", "--run-id", "f2", cwd=tree)
        self.assertFalse(tree.exists())
        self.assertEqual(run_claims_list(self.main, self.env), "")

    def test_publish_automatically_cleans_up_worktree_on_success(self):
        tree = self.start("company_report", "pub1")
        path = "data/watchlist/US.json"
        data = self.read(tree, path)
        data["active"][0]["status"] = "BUY"
        self.write(tree, path, data)
        res = self.publish(tree, "pub1")
        self.assertEqual(res.returncode, 0)
        self.assertFalse(tree.exists())
        self.assertEqual(run_claims_list(self.main, self.env), "")

    def test_publish_with_keep_worktree_preserves_worktree(self):
        tree = self.start("company_report", "pub2")
        path = "data/watchlist/US.json"
        data = self.read(tree, path)
        data["active"][0]["status"] = "HOLD"
        self.write(tree, path, data)
        res = self.py("publish_run.py", "--run-id", "pub2", "--market", "US", "--message", "run pub2",
                      "--no-portal", "--no-validate", "--keep-worktree", cwd=tree)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(tree.exists())
        self.py("run_session.py", "finish", "--run-id", "pub2")
        self.assertFalse(tree.exists())


def run_claims_list(main, env):
    done = subprocess.run([sys.executable, str(main / "scripts/run_claims.py"), "list"], cwd=main, env=env,
                          capture_output=True, text=True)
    return "" if "no live claims" in done.stdout else done.stdout


if __name__ == "__main__":
    unittest.main()
