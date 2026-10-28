#!/usr/bin/env python3
"""Claims that keep concurrent workflow runs off each other's work.

Two kinds of claim, kept in one JSON file inside the repository's shared git directory (so every
git worktree of this checkout sees the same ledger) and guarded by an exclusive file lock:

  singleton  one live run per (workflow, market) for whole-report workflows. A second run is refused.
  name       one live run per (market, symbol) for per-company work, across every workflow. Batches
             skip names another live run holds, so two runs never work on the same company.

A claim lives until its run releases it (publish_run.py does so after a successful push), or until
its heartbeat is older than its TTL, so a crashed run cannot hold names forever.

Usage:
  run_claims.py singleton --workflow market_intelligence --market US --run-id RUN
  run_claims.py batch --workflow watchlist_to_shortlist --market US --run-id RUN --size 4 [--pool watchlist|archive]
  run_claims.py names --workflow company_report --market US --run-id RUN SYMBOL...
  run_claims.py heartbeat --run-id RUN
  run_claims.py release --run-id RUN [--symbol SYMBOL ...]
  run_claims.py list
Exit codes: 0 ok, 3 refused because another live run holds the claim.
"""
import argparse
import contextlib
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_TTL_HOURS = 6.0
SINGLETON_WORKFLOWS = {"market_intelligence", "portfolio_audit", "options_audit", "displacement"}
NAME_WORKFLOWS = {"watchlist_to_shortlist", "reject_to_watchlist", "company_report"}
ELIGIBLE_WATCHLIST_STATUS = {"RESEARCH_REQUIRED", "PENDING_RESEARCH", "PENDING"}
MARKETS = ("IN", "US")


class ClaimConflict(Exception):
    def __init__(self, key, owner):
        self.key, self.owner = key, owner
        super().__init__(f"{key} is held by run {owner['run_id']} ({owner['workflow']}, claimed {owner['claimed_at']})")


def _git(*args, cwd=REPO, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def claims_dir():
    override = os.environ.get("PORTFOLIO_CLAIMS_DIR")
    if override:
        return Path(override)
    common = _git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return Path(common) / "portfolio-claims"


def _now():
    return time.time()


def _iso(stamp):
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(stamp))


@contextlib.contextmanager
def _locked():
    folder = claims_dir()
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "claims.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = folder / "claims.json"
        claims = json.loads(path.read_text()) if path.exists() else {}
        now = _now()
        claims = {k: v for k, v in claims.items() if now - v["heartbeat_epoch"] <= v["ttl_seconds"]}
        yield claims
        tmp = folder / "claims.json.tmp"
        tmp.write_text(json.dumps(claims, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, path)


def _entry(workflow, market, run_id, ttl_hours):
    now = _now()
    return {"run_id": run_id, "workflow": workflow, "market": market, "claimed_at": _iso(now),
            "claimed_epoch": now, "heartbeat_epoch": now, "ttl_seconds": int(ttl_hours * 3600)}


def _check_market(market):
    if market not in MARKETS:
        raise ValueError(f"market must be one of {MARKETS}")


def singleton_key(workflow, market):
    return f"singleton:{market}:{workflow}"


def name_key(market, symbol):
    return f"name:{market}:{symbol}"


def claim_singleton(workflow, market, run_id, ttl_hours=DEFAULT_TTL_HOURS):
    _check_market(market)
    if workflow not in SINGLETON_WORKFLOWS:
        raise ValueError(f"{workflow} is not a singleton workflow ({sorted(SINGLETON_WORKFLOWS)})")
    key = singleton_key(workflow, market)
    with _locked() as claims:
        owner = claims.get(key)
        if owner and owner["run_id"] != run_id:
            raise ClaimConflict(key, owner)
        claims[key] = _entry(workflow, market, run_id, ttl_hours)
    return key


def claim_names(workflow, market, run_id, symbols, ttl_hours=DEFAULT_TTL_HOURS):
    """All or nothing: either every symbol is claimed for this run or none is."""
    _check_market(market)
    with _locked() as claims:
        for symbol in symbols:
            owner = claims.get(name_key(market, symbol))
            if owner and owner["run_id"] != run_id:
                raise ClaimConflict(name_key(market, symbol), owner)
        for symbol in symbols:
            claims[name_key(market, symbol)] = _entry(workflow, market, run_id, ttl_hours)
    return list(symbols)


def claim_batch(workflow, market, run_id, size, candidates, ttl_hours=DEFAULT_TTL_HOURS):
    """Take the first `size` candidates (in the order given) that no other live run holds.

    A run that already holds names for this workflow gets exactly those back, so a restart never
    widens its batch. Returns (symbols, skipped) where skipped maps symbol -> holding run id.
    """
    _check_market(market)
    if workflow not in NAME_WORKFLOWS:
        raise ValueError(f"{workflow} does not claim names ({sorted(NAME_WORKFLOWS)})")
    skipped = {}
    with _locked() as claims:
        held = [k.split(":", 2)[2] for k, v in claims.items()
                if k.startswith(f"name:{market}:") and v["run_id"] == run_id and v["workflow"] == workflow]
        if held:
            return held, skipped
        taken = []
        for symbol in candidates:
            if len(taken) == size:
                break
            owner = claims.get(name_key(market, symbol))
            if owner and owner["run_id"] != run_id:
                skipped[symbol] = owner["run_id"]
                continue
            taken.append(symbol)
        for symbol in taken:
            claims[name_key(market, symbol)] = _entry(workflow, market, run_id, ttl_hours)
    return taken, skipped


def heartbeat(run_id):
    count = 0
    with _locked() as claims:
        for value in claims.values():
            if value["run_id"] == run_id:
                value["heartbeat_epoch"] = _now()
                count += 1
    return count


def release(run_id, symbols=None):
    removed = []
    with _locked() as claims:
        for key in list(claims):
            if claims[key]["run_id"] != run_id:
                continue
            if symbols and not (key.startswith("name:") and key.split(":", 2)[2] in symbols):
                continue
            removed.append(key)
            del claims[key]
    return removed


def list_claims():
    with _locked() as claims:
        return dict(claims)


def _watchlist_path(market):
    sources = json.loads((REPO / ".agents/config/portfolios.json").read_text())[market]["sources"]
    return next(s["path"] for s in sources if s["role"] == "watchlist")


def _row_cycle(row):
    c = row.get("research_cycle")
    if isinstance(c, int) and 1 <= c < 1000:
        return c
    return 1


def _is_pending_row(row):
    return (
        row.get("status") in ELIGIBLE_WATCHLIST_STATUS
        or row.get("deep_research_status") in ("PENDING", "RESEARCH_REQUIRED")
    )


def watchlist_queue_info(market, pool="watchlist", ref="origin/main"):
    """Return (ordered_symbols, target_cycle, rollover) for `pool` ('watchlist' or 'archive').

    For 'watchlist' (`watchlist.active`):
      1. Any row explicitly marked pending (`status` in ELIGIBLE_WATCHLIST_STATUS or
         `deep_research_status` in {'PENDING', 'RESEARCH_REQUIRED'}) is eligible first in sequential order.
      2. When `max_cycle > 1` (a multi-cycle round-robin pass is already underway), completed rows with
         `research_cycle < max_cycle` are eligible next in sequential order so every company completes
         `max_cycle` before the next rollover.
      3. Round-Robin Rollover: when ZERO rows in `watchlist.active` match (1) or (2) — meaning every
         company in `watchlist.active` has completed `max_cycle` — the queue automatically rolls over
         to `target_cycle = max_cycle + 1` from the top of `watchlist.active` (`rollover = True`).
    For 'archive' (`watchlist.archive`):
      Skips rows flagged `PERMANENT_REJECT` in notes/status, and orders by `(research_cycle, last_researched_date, index)`
      so the oldest/lowest-cycle archive names are triaged first in round-robin order.
    """
    rel = _watchlist_path(market)
    text = None
    if ref != "WORKTREE":
        shown = _git("show", f"{ref}:{rel}", check=False)
        if shown.returncode == 0:
            text = shown.stdout
        else:
            print(f"warning: cannot read {ref}:{rel}; using the working file", file=sys.stderr)
    if text is None:
        text = (REPO / rel).read_text(encoding="utf-8")
    data = json.loads(text)
    if pool == "archive":
        arch = data.get("archive", [])
        eligible_arch = [
            (idx, r) for idx, r in enumerate(arch)
            if "PERMANENT_REJECT" not in str(r.get("notes") or "")
            and r.get("status") != "PERMANENT_REJECT"
        ]
        min_c = min((_row_cycle(r) for _, r in eligible_arch), default=1)
        max_c = max((_row_cycle(r) for _, r in eligible_arch), default=1)
        rollover = bool(eligible_arch) and min_c == max_c and all(
            r.get("status") not in ELIGIBLE_WATCHLIST_STATUS for _, r in eligible_arch
        )
        target_cycle = (max_c + 1) if rollover else max_c
        eligible_arch.sort(key=lambda pair: (_row_cycle(pair[1]), str(pair[1].get("last_researched_date") or ""), pair[0]))
        return [r["symbol"] for _, r in eligible_arch], target_cycle, rollover

    active = data.get("active", [])
    if not active:
        return [], 1, False
    max_cycle = max((_row_cycle(r) for r in active), default=1)
    pending = [r for r in active if _is_pending_row(r)]
    lagging = [r for r in active if not _is_pending_row(r) and _row_cycle(r) < max_cycle]
    eligible = pending + lagging
    if eligible:
        return [r["symbol"] for r in eligible], max_cycle, False
    # All active rows have completed max_cycle -> roll over to max_cycle + 1 in top-to-bottom order
    return [r["symbol"] for r in active], max_cycle + 1, True


def candidate_symbols(market, pool, ref="origin/main"):
    """Ordered candidate names for a batch, read from `ref` (default: the freshly fetched origin/main).

    ref "WORKTREE" reads the working file. If the ref cannot be resolved the working file is used.
    """
    symbols, _, _ = watchlist_queue_info(market, pool, ref)
    return symbols


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, workflow=True, market=True):
        if workflow:
            p.add_argument("--workflow", required=True)
        if market:
            p.add_argument("--market", required=True, choices=MARKETS)
        p.add_argument("--run-id", required=True)
        p.add_argument("--ttl-hours", type=float, default=DEFAULT_TTL_HOURS)

    common(sub.add_parser("singleton"))
    batch = sub.add_parser("batch")
    common(batch)
    batch.add_argument("--size", type=int, required=True)
    batch.add_argument("--pool", choices=["watchlist", "archive"], default="watchlist")
    batch.add_argument("--ref", default="origin/main", help="git ref to read eligibility from, or WORKTREE")
    batch.add_argument("--no-fetch", action="store_true")
    names = sub.add_parser("names")
    common(names)
    names.add_argument("symbols", nargs="+")
    beat = sub.add_parser("heartbeat")
    beat.add_argument("--run-id", required=True)
    rel = sub.add_parser("release")
    rel.add_argument("--run-id", required=True)
    rel.add_argument("--symbol", action="append")
    sub.add_parser("list")
    args = parser.parse_args()

    try:
        if args.command == "singleton":
            print(json.dumps({"claimed": claim_singleton(args.workflow, args.market, args.run_id, args.ttl_hours)}))
        elif args.command == "batch":
            if not args.no_fetch and args.ref != "WORKTREE":
                fetched = _git("fetch", "origin", check=False)
                if fetched.returncode != 0:
                    print("warning: git fetch origin failed; eligibility may be stale", file=sys.stderr)
            candidates, target_cycle, rollover = watchlist_queue_info(args.market, args.pool, args.ref)
            symbols, skipped = claim_batch(args.workflow, args.market, args.run_id, args.size, candidates, args.ttl_hours)
            print(json.dumps({"symbols": symbols, "skipped_held_by_other_runs": skipped,
                              "short_batch": len(symbols) < args.size,
                              "target_research_cycle": target_cycle,
                              "round_robin_rollover": rollover}))
        elif args.command == "names":
            print(json.dumps({"claimed": claim_names(args.workflow, args.market, args.run_id, args.symbols, args.ttl_hours)}))
        elif args.command == "heartbeat":
            print(json.dumps({"renewed": heartbeat(args.run_id)}))
        elif args.command == "release":
            print(json.dumps({"released": release(args.run_id, set(args.symbol) if args.symbol else None)}))
        elif args.command == "list":
            claims = list_claims()
            for key, v in sorted(claims.items()):
                print(f"{key:<48} run={v['run_id']} workflow={v['workflow']} claimed={v['claimed_at']}")
            if not claims:
                print("no live claims")
    except ClaimConflict as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
