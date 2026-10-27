#!/usr/bin/env python3
"""Give each workflow run its own git worktree, so concurrent runs never share a working tree.

  start   claim the run (singleton workflows are refused when another live run holds them), fetch
          origin, and create .worktrees/<run_id> on branch run/<run_id> cut from origin/main.
          `.venv` and `.env` are symlinked in from the main checkout. Prints JSON.
  finish  release the run's claims and remove its worktree and branch.
  list    show the live claims and the run worktrees.

Per-company workflows then take their names with `run_claims.py batch` from inside the worktree.
Every command of the run (scripts, validators, the ledger build) runs with the worktree as its
working directory; the main checkout is never touched by a run.
"""
import os
import argparse
import json
import secrets
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_claims

LINKED = (".venv", ".env")


def git(*args, cwd=run_claims.REPO, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def main_checkout():
    common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    return common.parent


def new_run_id(market, workflow):
    return f"{market}-{workflow}-{time.strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(2)}"


def worktree_path(run_id):
    return main_checkout() / ".worktrees" / run_id


def start(workflow, market, run_id=None, ttl_hours=run_claims.DEFAULT_TTL_HOURS, branch="main"):
    if workflow not in run_claims.SINGLETON_WORKFLOWS | run_claims.NAME_WORKFLOWS:
        raise ValueError(f"unknown workflow {workflow}")
    run_id = run_id or new_run_id(market, workflow)
    claimed = None
    if workflow in run_claims.SINGLETON_WORKFLOWS:
        claimed = run_claims.claim_singleton(workflow, market, run_id, ttl_hours)
    try:
        fetched = git("fetch", "origin", branch, check=False)
        if fetched.returncode != 0:
            raise RuntimeError("git fetch origin failed: " + fetched.stderr.strip())
        path = worktree_path(run_id)
        git("worktree", "add", "-b", f"run/{run_id}", str(path), f"origin/{branch}")
        root = main_checkout()
        for name in LINKED:
            if (root / name).exists() and not (path / name).exists():
                (path / name).symlink_to(root / name)
        base = git("rev-parse", "HEAD", cwd=path).stdout.strip()
    except Exception:
        run_claims.release(run_id)
        raise
    return {"run_id": run_id, "worktree": str(path), "branch": f"run/{run_id}", "base_commit": base,
            "singleton_claim": claimed}


def finish(run_id, keep_worktree=False):
    released = run_claims.release(run_id)
    removed = False
    path = worktree_path(run_id)
    if not keep_worktree and path.exists():
        root = main_checkout()
        for name in LINKED:
            link = path / name
            if link.is_symlink():
                link.unlink()
        try:
            os.chdir(root)
        except OSError:
            pass
        git("worktree", "remove", "--force", str(path), cwd=root)
        git("branch", "-D", f"run/{run_id}", cwd=root, check=False)
        removed = True
    return {"run_id": run_id, "released_claims": released, "worktree_removed": removed}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("start")
    s.add_argument("--workflow", required=True)
    s.add_argument("--market", required=True, choices=run_claims.MARKETS)
    s.add_argument("--run-id")
    s.add_argument("--branch", default="main")
    s.add_argument("--ttl-hours", type=float, default=run_claims.DEFAULT_TTL_HOURS)
    f = sub.add_parser("finish")
    f.add_argument("--run-id", required=True)
    f.add_argument("--keep-worktree", action="store_true")
    sub.add_parser("list")
    args = parser.parse_args()
    try:
        if args.command == "start":
            print(json.dumps(start(args.workflow, args.market, args.run_id, args.ttl_hours, args.branch), indent=2))
        elif args.command == "finish":
            print(json.dumps(finish(args.run_id, args.keep_worktree), indent=2))
        else:
            print(git("worktree", "list").stdout, end="")
            for key, v in sorted(run_claims.list_claims().items()):
                print(f"claim {key:<46} run={v['run_id']}")
    except run_claims.ClaimConflict as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
