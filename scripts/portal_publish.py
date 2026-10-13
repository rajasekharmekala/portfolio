"""Public research catalog and deployment-safe report links."""
import argparse
import html
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from bs4 import BeautifulSoup

DOCS = Path(__file__).resolve().parents[1] / "docs"
BASE_URL = "https://git.corp.adobe.com/pages/mereddy/ai-automations/"
CATALOG = DOCS / "portal-data.json"
UPDATES = DOCS / "portal-updates.json"


def published_url(href, source=None, docs=DOCS, base_url=BASE_URL, absolute=True):
    parts = urlsplit(href)
    if parts.scheme == "file":
        parts = parts._replace(scheme="", netloc="")
    elif parts.scheme or parts.netloc or not parts.path:
        return href
    docs = Path(docs).resolve()
    source = Path(source).resolve() if source else docs / "index.html"
    path = unquote(parts.path)
    candidates = [source.parent / path, docs / path.lstrip("/")]
    for folder in ("docs", "blogs", "reports"):
        if folder + "/" in path:
            suffix = path.split(folder + "/", 1)[1]
            candidates.append(docs / suffix if folder == "docs" else docs / folder / suffix)
    if Path(path).name.endswith("_dossier.html"):
        # Prefer the canonical market subfolders over a legacy flat path
        # (which today is a redirect stub kept for old emailed links).
        candidates.append(docs / "blogs" / "IN" / Path(path).name)
        candidates.append(docs / "blogs" / "US" / Path(path).name)
        candidates.append(docs / "blogs" / Path(path).name)
    for candidate in candidates:
        resolved = candidate.resolve()
        try:
            relative = resolved.relative_to(docs)
        except ValueError:
            continue
        if resolved.is_file():
            if not absolute:
                return urlunsplit(("", "", quote(os.path.relpath(resolved, source.parent)), parts.query, parts.fragment))
            url = urlsplit(base_url.rstrip("/") + "/" + quote(relative.as_posix()))
            return urlunsplit((url.scheme, url.netloc, url.path, parts.query, parts.fragment))
    return None


def rewrite_published_links(content, source=None, docs=DOCS, base_url=BASE_URL, absolute=True):
    def replace_anchor(match):
        tag = match.group()
        attribute = re.search(r"\bhref\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
        if not attribute:
            return tag
        destination = published_url(html.unescape(attribute.group(2)), source, docs, base_url, absolute)
        replacement = 'href="' + html.escape(destination, quote=True) + '"' if destination is not None else 'aria-disabled="true"'
        return tag[:attribute.start()] + replacement + tag[attribute.end():]
    return re.sub(r"<a\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>", replace_anchor, content, flags=re.I)


def git_dates():
    result = subprocess.run(["git", "log", "--format=@%cI", "--name-only", "--", "docs/blogs", "docs/reports"], cwd=DOCS.parent, capture_output=True, text=True, check=True)
    dates = {}
    stamp = None
    for line in result.stdout.splitlines():
        if line.startswith("@"):
            stamp = line[1:]
        elif line.startswith("docs/") and stamp:
            dates.setdefault(line[5:], stamp)
    return dates


def read_entry(path, dates, updates):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    metadata = {tag.get("name"): tag.get("content", "") for tag in soup.select("meta[name]")}
    generated_at = None
    try:
        generated = datetime.fromisoformat(metadata.get("generated-at", ""))
        if generated.tzinfo is not None and generated.utcoffset() is not None:
            generated_at = generated.isoformat()
    except ValueError:
        pass
    for decoration in soup.select(".glossary-tip, .glossary-tooltip, .tooltip-text, .tooltiptext, .sr-only"):
        decoration.decompose()
    heading = soup.find("h1") or soup.find("title")
    title = heading.get_text(" ", strip=True) if heading else path.stem.replace("_", " ")
    info = {}
    for row in soup.select("table tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) == 2:
            label = cells[0].get_text(" ", strip=True).lower()
            if any(word in label for word in ("exchange", "ticker", "listing", "verdict", "recommendation", "sector", "decision", "market", "strategy")):
                info.setdefault(label, cells[1].get_text(" ", strip=True))
    relative = path.relative_to(DOCS).as_posix()
    completion = updates.get(relative, {})
    kind = metadata.get("report-kind") or ("dossier" if path.name.endswith("_dossier.html") else "report")
    # Dossiers live in market subfolders (blogs/IN/, blogs/US/); the folder is
    # the canonical market attribution and beats content sniffing.
    folder_market = None
    parts = relative.split("/")
    if len(parts) >= 3 and parts[0] == "blogs" and parts[1] in ("IN", "US"):
        folder_market = parts[1]
    exchange = " ".join(value for key, value in info.items() if any(word in key for word in ("exchange", "ticker", "listing")))
    evidence = path.stem + " " + title + " " + exchange + " " + soup.get_text(" ", strip=True)[:3500]
    symbol_market = None
    registry_path = DOCS.parent / "data" / "metadata" / "symbols.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        symbol_market = next((name for name in ("IN", "US") if path.stem.replace("_dossier", "") in registry.get(name, {}).get("symbols", {})), None)
    market = completion.get("market") or metadata.get("report-market") or folder_market or symbol_market or ("US" if re.search(r"\b(US|NASDAQ|NYSE|OTCQX)\b", evidence.replace("_", " ")) else "IN" if re.search(r"\b(Indian|India|NSE|BSE)\b", evidence.replace("_", " ")) else "Other")
    verdict = next((value for key, value in info.items() if any(word in key for word in ("verdict", "decision", "recommendation"))), "")
    badge = soup.select_one(".verdict-badge, .decision-badge")
    verdict = verdict or (badge.get_text(" ", strip=True) if badge else "Not specified")
    description = soup.find("meta", attrs={"name": "description"})
    paragraph = soup.select_one(".executive-summary p, section#executive-summary p")
    if paragraph is None:
        summary_heading = soup.find(["h2", "h3"], string=re.compile(r"executive|summary|verdict|underwriting|analyst primer", re.I))
        if summary_heading:
            for sibling in summary_heading.next_siblings:
                if getattr(sibling, "name", None) in ("h2", "h3"):
                    break
                if getattr(sibling, "name", None) == "p":
                    paragraph = sibling
                    break
    summary = completion.get("summary") or (paragraph.get_text(" ", strip=True) if paragraph else description.get("content", "") if description else "")
    report_date = re.search(r"20\d{2}-\d{2}-\d{2}", path.stem)
    workflow = re.sub(r"_?20\d{2}-\d{2}-\d{2}.*", "", path.stem).replace("_", " ")
    for pattern, name in (("Market.*Intelligence", "Market intelligence"), ("Portfolio.*Audit", "Portfolio audit"), ("Watchlist.*Shortlist", "Watchlist underwriting"), ("Options", "Options audit"), ("Displacement", "Displacement review"), ("Reject|Archive", "Archive review")):
        if re.search(pattern, workflow, re.I):
            workflow = name
            break
    return {"id": relative, "url": relative, "title": title[:220], "kind": kind,
            "symbol": path.stem.replace("_dossier", "") if kind == "dossier" else "", "market": market,
            "sector": info.get("macro sector", info.get("sector", "Not specified")), "verdict": verdict[:150], "summary": summary[:360],
            "generatedAt": generated_at,
            "layoutUpdatedAt": metadata.get("layout-updated-at") or None,
            "researchAsOf": metadata.get("research-as-of") or None,
            "updatedAt": completion.get("completedAt") or (datetime.fromisoformat(generated_at).astimezone(timezone.utc).isoformat() if generated_at else dates.get(relative)),
            "timestampSource": "workflow" if completion.get("completedAt") else "generated" if generated_at else "git" if dates.get(relative) else "unknown",
            "reportDate": metadata.get("research-as-of") or (report_date.group() if report_date else None),
            "workflow": completion.get("workflow") or metadata.get("report-workflow") or ("Company research" if kind == "dossier" else workflow),
            "highlights": completion.get("highlights", []), "completed": bool(completion)}


def require_modern_report(path, require_generated=False):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    design = soup.find("meta", attrs={"name": "report-design", "content": "research-desk-v1"})
    stamp = soup.select_one('.report-header time[datetime]')
    if not design or not stamp or not soup.select_one('.desk-masthead') or not soup.select_one('script[data-report-desk]'):
        raise ValueError(f"{path.name}: assemble with scripts/assemble_report.py before publishing; Research Desk layout and Pacific generation header are required")
    generated = datetime.fromisoformat(stamp["datetime"])
    if generated.tzinfo is None or generated.utcoffset() is None:
        raise ValueError(f"{path.name}: generation time must include a timezone")
    if require_generated:
        generation = soup.find("meta", attrs={"name": "generated-at"})
        if generation is None or generation.get("content") != stamp["datetime"]:
            raise ValueError(f"{path.name}: layout-only updates are not newly completed research; reassemble the final research body")
        if soup.select_one('meta[name="report-kind"][content="report"]') and re.search(r"20\d{2}-\d{2}-\d{2}", path.stem):
            raise ValueError(f"{path.name}: new workflow reports must use a stable filename without a date")
    return True


def build_catalog(completed=(), workflow=None, market=None, summary=None, highlights=(), repair_links=False):
    updates = json.loads(UPDATES.read_text()) if UPDATES.exists() else {}
    now = datetime.now(timezone.utc).isoformat()
    for filename in completed:
        path = Path(filename).resolve()
        relative = path.relative_to(DOCS).as_posix()
        if not path.is_file() or path.suffix != ".html" or not relative.startswith(("blogs/", "reports/")):
            raise ValueError("Completion must reference an existing published HTML report")
        require_modern_report(path, require_generated=True)
        updates[relative] = {"completedAt": now, "workflow": workflow, "market": market, "summary": summary, "highlights": list(highlights)}
    paths = sorted(set(DOCS.glob("blogs/**/*_dossier.html")) | set(DOCS.glob("reports/**/*.html")))
    paths = [path for path in paths if not BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").select_one('meta[name="report-redirect"]')]
    updates = {key: value for key, value in updates.items() if (DOCS / key).is_file()}
    dates = git_dates()
    entries = [read_entry(path, dates, updates) for path in paths]
    entries.sort(key=lambda entry: entry["updatedAt"] or "", reverse=True)
    catalog = {"schemaVersion": 1, "generatedAt": now, "baseUrl": BASE_URL, "entries": entries}
    UPDATES.write_text(json.dumps(updates, indent=2) + "\n", encoding="utf-8")
    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if repair_links:
        for path in paths:
            original = path.read_text(encoding="utf-8")
            repaired = rewrite_published_links(original, path, absolute=False)
            if repaired != original:
                path.write_text(repaired, encoding="utf-8")
    print(f"Catalog built: {len(entries)} published pages")
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed", nargs="+", default=[])
    parser.add_argument("--workflow")
    parser.add_argument("--market", choices=["IN", "US"])
    parser.add_argument("--summary")
    parser.add_argument("--highlight", action="append", default=[])
    parser.add_argument("--repair-links", action="store_true")
    args = parser.parse_args()
    if args.completed and not all((args.workflow, args.market, args.summary)):
        parser.error("--completed requires --workflow, --market, and --summary")
    build_catalog(args.completed, args.workflow, args.market, args.summary, args.highlight, args.repair_links)


if __name__ == "__main__":
    main()
