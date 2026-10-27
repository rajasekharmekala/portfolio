#!/usr/bin/env python3
"""Publish one run's deliverables to origin/main without clobbering any other run.

Run it from inside the run's worktree (see run_session.py). It:
  1. commits the run's changes on its run branch (only paths under docs/, data/, .agents/, scripts/);
  2. fetches origin and replays that commit onto the newest origin/main, file by file:
       - untouched by anyone else: taken as is;
       - data/**/*.json changed by both: merged record by record (record_merge.py);
       - docs/**/*.html changed by both: the later research-as-of / generated-at wins, otherwise refused;
       - anything else changed by both: refused;
  3. regenerates the public catalog (docs/portal-*.json) on top of origin's copy, never merges it;
  4. validates the data, makes one linear commit, and pushes it as a fast-forward (never forced);
     a rejected push is retried from step 2 with the newer origin/main;
  5. releases the run's claims and cleans up the worktree and branch (unless --keep-worktree is passed), only after the push has succeeded.
On any refusal nothing is pushed, claims stay held, and the run branch keeps every change.
Exit codes: 0 published (or nothing to publish), 2 bad input, 4 validation failed, 5 refused/conflict,
6 push failed.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record_merge
import run_claims
import run_session

ALLOWED_PREFIXES = ("docs/", "data/", ".agents/", "scripts/")
ALLOWED_FILES = {"AGENTS.md", "README.md", ".gitignore"}
CATALOG_FILES = ("docs/portal-data.json", "docs/portal-updates.json")


class Refused(Exception):
    pass


class ValidationFailed(Exception):
    pass


class Git:
    def __init__(self, root):
        self.root = Path(root)

    def run(self, *args, check=True, binary=False):
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=not binary)
        if check and result.returncode != 0:
            err = result.stderr if not binary else result.stderr.decode("utf-8", "replace")
            raise RuntimeError(f"git {' '.join(args)} failed: {err.strip()}")
        return result

    def out(self, *args, check=True):
        return self.run(*args, check=check).stdout.strip()

    def blob(self, ref, path):
        result = self.run("show", f"{ref}:{path}", check=False, binary=True)
        return result.stdout if result.returncode == 0 else None


def meta(html, name):
    for pattern in (rf'<meta[^>]*\bname=["\']{name}["\'][^>]*\bcontent=["\']([^"\']*)',
                    rf'<meta[^>]*\bcontent=["\']([^"\']*)["\'][^>]*\bname=["\']{name}["\']'):
        found = re.search(pattern, html, re.I)
        if found:
            return found.group(1)
    return None


def may_override(path, ours, theirs):
    """The 'Overriding earlier publications' rule: same or later research-as-of AND later generated-at."""
    o, t = ours.decode("utf-8", "replace"), theirs.decode("utf-8", "replace")
    o_asof, t_asof = meta(o, "research-as-of"), meta(t, "research-as-of")
    try:
        o_gen = datetime.fromisoformat(meta(o, "generated-at") or "")
    except ValueError:
        raise Refused(f"{path}: this run's page has no generated-at stamp, so it cannot replace a newer page")
    try:
        t_gen = datetime.fromisoformat(meta(t, "generated-at") or "")
    except ValueError:
        t_gen = None
    if t_asof and (not o_asof or o_asof < t_asof):
        raise Refused(f"{path}: origin holds research-as-of {t_asof}, later than this run's {o_asof}")
    if t_gen and o_gen <= t_gen:
        raise Refused(f"{path}: origin's page was generated at {t_gen.isoformat()}, not earlier than this run's {o_gen.isoformat()}")


def resolve(path, base, ours, theirs):
    """Content for a path both this run and origin changed; raises Refused/MergeConflict."""
    if path.startswith("data/") and path.endswith(".json"):
        decode = lambda b: "" if b is None else b.decode("utf-8")
        merged = record_merge.merge_texts(decode(base), decode(ours), decode(theirs))
        return None if merged is None else merged.encode("utf-8")
    if path.startswith("docs/") and path.endswith(".html") and ours is not None and theirs is not None:
        may_override(path, ours, theirs)
        return ours
    raise Refused(f"{path}: changed by this run and by another run, and it cannot be merged automatically")


def check_scope(git):
    changed = []
    for line in git.run("status", "--porcelain", "-uall").stdout.splitlines():
        changed.append(line[3:].split(" -> ")[-1].strip('"'))
    stray = [p for p in changed if p not in ALLOWED_FILES and not p.startswith(ALLOWED_PREFIXES)]
    if stray:
        raise ValueError("changes outside docs/, data/, .agents/, scripts/ will not be published: " + ", ".join(stray))
    return changed


def commit_run(git, message):
    check_scope(git)
    git.run("restore", "--source=HEAD", "--staged", "--worktree", "--", *CATALOG_FILES, check=False)
    git.run("add", "-A")
    if git.run("diff", "--cached", "--quiet", check=False).returncode == 0:
        return False
    git.run("commit", "-q", "-m", message)
    return True


def apply_run(git, run_commit, target, completed, args):
    """Build the publication on top of `target` from `run_commit`. Returns (changed_paths, superseded)."""
    base = git.out("merge-base", run_commit, target)
    git.run("switch", "-q", "--detach", target)
    superseded = []
    names = git.run("diff", "--name-only", "--no-renames", base, run_commit).stdout.splitlines()
    for path in names:
        if path in CATALOG_FILES:
            continue
        b, o, t = (git.blob(ref, path) for ref in (base, run_commit, target))
        if o == t:
            continue
        if b == t:
            result = o
        else:
            result = resolve(path, b, o, t)
            if t is not None and result is not None and result != t and path.endswith(".html"):
                superseded.append(f"{path}@{git.out('log', '-1', '--format=%h', target, '--', path)}")
        target_file = git.root / path
        if result is None:
            target_file.unlink(missing_ok=True)
        else:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_bytes(result)
    if not args.no_portal:
        command = [sys.executable, "scripts/build_dossier_portal.py", "--repair-links"]
        if completed:
            command += ["--completed", *completed, "--workflow", args.workflow, "--market", args.market,
                        "--summary", args.summary]
            for line in args.highlight:
                command += ["--highlight", line]
        done = subprocess.run(command, cwd=git.root, capture_output=True, text=True)
        if done.returncode != 0:
            raise RuntimeError("catalog build failed: " + (done.stderr or done.stdout).strip()[-600:])
    return base, superseded


def validate(root, market):
    for command in ([sys.executable, "scripts/validate_data.py"],
                    [sys.executable, "scripts/data_layer.py", "--market", market, "--validate"]):
        done = subprocess.run(command, cwd=root, capture_output=True, text=True)
        if done.returncode != 0:
            raise ValidationFailed(f"{' '.join(command[1:])} failed:\n" + (done.stdout + done.stderr).strip()[-800:])


def publish(args):
    git = Git(args.root)
    current = git.run("symbolic-ref", "-q", "--short", "HEAD", check=False).stdout.strip()
    if current == args.branch:
        raise ValueError(f"refusing to publish from the shared {args.branch} checkout; run from the run's worktree")
    run_branch = current or f"run/{args.run_id}"
    message = args.message
    if current:
        commit_run(git, message)
    elif git.run("status", "--porcelain", "-uall").stdout.strip():
        raise ValueError("detached HEAD with local changes; switch back to the run branch first")
    run_commit = git.out("rev-parse", run_branch)
    completed = [str(Path(p)) for p in args.completed]
    for attempt in range(1, args.max_attempts + 1):
        git.run("fetch", "-q", "origin", args.branch)
        target = git.out("rev-parse", f"origin/{args.branch}")
        try:
            base, superseded = apply_run(git, run_commit, target, completed, args)
            if not args.no_validate:
                validate(git.root, args.market)
            git.run("add", "-A")
            if git.run("diff", "--cached", "--quiet", check=False).returncode == 0:
                result = {"status": "NOTHING_TO_PUBLISH", "base": target, "attempts": attempt}
                break
            trailer = f"\n\nRun-Id: {args.run_id}\nBased-On: {target}"
            if superseded:
                trailer += "\nSupersedes: " + ", ".join(superseded)
            git.run("commit", "-q", "-m", message + trailer)
            published = git.out("rev-parse", "HEAD")
            if args.dry_run:
                result = {"status": "DRY_RUN", "commit": published, "base": target, "attempts": attempt}
                break
            pushed = git.run("push", "-q", "origin", f"{published}:refs/heads/{args.branch}", check=False)
            if pushed.returncode == 0:
                result = {"status": "PUBLISHED", "commit": published, "base": target, "attempts": attempt,
                          "superseded": superseded}
                break
            if attempt == args.max_attempts:
                raise RuntimeError("push rejected after %d attempts: %s" % (attempt, pushed.stderr.strip()))
            time.sleep(min(2 * attempt, 6))
        except (Refused, record_merge.MergeConflict, ValidationFailed, RuntimeError):
            git.run("switch", "-q", "-f", run_branch, check=False)
            raise
    else:
        raise RuntimeError("publish did not complete")
    if result["status"] in ("PUBLISHED", "NOTHING_TO_PUBLISH") and not args.keep_claims:
        result["released_claims"] = run_claims.release(args.run_id)
    result["run_commit"] = run_commit
    if args.manifest:
        manifest = Path(args.manifest).resolve()
        data = json.loads(manifest.read_text()) if manifest.exists() else {}
        data["publication"] = result
        manifest.write_text(json.dumps(data, indent=2) + "\n")
    if result["status"] in ("PUBLISHED", "NOTHING_TO_PUBLISH") and not args.keep_worktree and not args.dry_run:
        cleanup = run_session.finish(args.run_id, keep_worktree=False)
        result["worktree_cleaned"] = cleanup.get("worktree_removed", False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--market", required=True, choices=run_claims.MARKETS)
    parser.add_argument("--message", required=True, help="commit message")
    parser.add_argument("--workflow", help="stable workflow name for the catalog (needed with --completed)")
    parser.add_argument("--completed", nargs="*", default=[], help="published HTML paths this run completed")
    parser.add_argument("--summary")
    parser.add_argument("--highlight", action="append", default=[])
    parser.add_argument("--branch", default="main")
    parser.add_argument("--root", default=".", help="the run's worktree (default: current directory)")
    parser.add_argument("--manifest", help="write the publication result into this manifest.json")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--keep-claims", action="store_true")
    parser.add_argument("--keep-worktree", action="store_true", help="keep the worktree and branch after publishing (default: remove on successful publish)")
    parser.add_argument("--dry-run", action="store_true", help="build and commit locally, do not push, release or clean worktree")
    parser.add_argument("--no-portal", action="store_true", help="skip the catalog rebuild (tests only)")
    parser.add_argument("--no-validate", action="store_true", help="skip data validation (tests only)")
    args = parser.parse_args()
    if args.completed and not (args.workflow and args.summary):
        parser.error("--completed requires --workflow and --summary")
    try:
        args.root = Git(args.root).out("rev-parse", "--show-toplevel")
        result = publish(args)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)
    except ValidationFailed as error:
        print(f"VALIDATION FAILED: nothing was pushed; the run branch and claims are kept.\n{error}", file=sys.stderr)
        sys.exit(4)
    except (Refused, record_merge.MergeConflict) as error:
        lines = error.conflicts if isinstance(error, record_merge.MergeConflict) else [str(error)]
        print("REFUSED: nothing was pushed; the run branch and claims are kept.", file=sys.stderr)
        for line in lines:
            print("  " + line, file=sys.stderr)
        sys.exit(5)
    except RuntimeError as error:
        print(f"FAILED: nothing was published; the run branch and claims are kept.\n{error}", file=sys.stderr)
        sys.exit(6)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
