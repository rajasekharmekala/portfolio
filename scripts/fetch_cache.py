#!/usr/bin/env python3
"""
Execution cache for cited research: stores each fetched source page as one JSON
per URL under scripts/.cache/fetched/, in the exact shape scripts/citation_check.py
reads (load_cache: one JSON per URL with {url, retrieved_at, text}).

Usage:
  python3 scripts/fetch_cache.py --url https://example.com/filing
  python3 scripts/fetch_cache.py --research scripts/.cache/research_IN_2026-10-08.json
  python3 scripts/fetch_cache.py --research ... --force          # re-fetch even if cached
  python3 scripts/fetch_cache.py --url <u> --text-file page.html # offline: cache from a local file
  python3 scripts/fetch_cache.py --list                          # show cached URLs

Cache entry:
  { "url", "retrieved_at" (ISO), "status" ("ok"|"error"), "http_status",
    "sha256" (of the stored text), "content_type", "text" (extracted text) }

The stored text must be the source as actually fetched: citation_check.py proves
every research value against it (VALUE NOT IN CACHED TEXT), so hand-editing a
cache entry defeats the audit.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "scripts", ".cache", "fetched")
MAX_BYTES = 20_000_000
# SEC EDGAR requires a "name email" User-Agent; a generic browser UA gets 403.
UA = "portfolio-research admin@example.com"


def norm_url(url: str) -> str:
    return url.split("#")[0].split("?")[0].rstrip("/")


def cache_path(url: str) -> str:
    return os.path.join(CACHE_DIR, hashlib.sha1(norm_url(url).encode()).hexdigest() + ".json")


def html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for t in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            t.decompose()
        return soup.get_text(separator=" ", strip=True)
    except ImportError:
        return re.sub(r"<[^>]+>", " ", html)


def fetch(url: str, text_file: str = None) -> dict:
    retrieved_at = dt.datetime.now().isoformat(timespec="seconds")
    entry = {"url": url, "retrieved_at": retrieved_at, "status": "ok"}
    if text_file:
        raw = open(text_file, encoding="utf-8", errors="replace").read()
        entry["content_type"] = "local-file"
        entry["http_status"] = None
    else:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json,text/plain,*/*"})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read(MAX_BYTES).decode("utf-8", errors="replace")
                entry["http_status"] = r.status
                entry["content_type"] = r.headers.get("Content-Type", "")
        except Exception as e:  # noqa: BLE001 - record, do not crash the batch
            entry.update(status="error", error=str(e), text="")
            return entry
    text = html_to_text(raw) if "<html" in raw[:2000].lower() or "<!doctype" in raw[:2000].lower() else raw
    entry["text"] = text
    entry["sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    entry["text_chars"] = len(text)
    return entry


def store(entry: dict, force: bool = False) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = cache_path(entry["url"])
    if os.path.exists(path) and not force:
        return "cached"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
    return "stored" if entry["status"] == "ok" else "error"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--research", action="append", default=[],
                    help="research JSON whose found items' source_url to fetch")
    ap.add_argument("--text-file", help="with --url: build the cache entry from a local file instead of the network")
    ap.add_argument("--force", action="store_true", help="re-fetch even if already cached")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        for f in sorted(glob.glob(os.path.join(CACHE_DIR, "*.json"))):
            e = json.load(open(f, encoding="utf-8"))
            print(f"{e.get('retrieved_at', '?')}  {e.get('status', '?'):<5}  {e.get('url')}")
        return

    urls = list(args.url)
    for rp in args.research:
        d = json.load(open(rp, encoding="utf-8"))
        items = d.get("items", d) if isinstance(d, dict) else d
        for it in items:
            if it.get("status") == "found" and it.get("source_url", "").startswith("http"):
                urls.append(it["source_url"])

    if not urls:
        sys.exit("nothing to do: pass --url and/or --research")

    for i, u in enumerate(urls, 1):
        entry = fetch(u, args.text_file if len(urls) == 1 else None)
        result = store(entry, args.force)
        extra = f" {entry['text_chars']} chars" if entry["status"] == "ok" else f" {entry.get('error')}"
        print(f"[{i}/{len(urls)}] {result:<6} {u}{extra}")


if __name__ == "__main__":
    main()
