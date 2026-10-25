"""Event-gated, short email digests for published research reports."""
import html
import re
from pathlib import Path

from bs4 import BeautifulSoup
from portal_publish import BASE_URL, published_url, read_entry

TYPES = ("market-intelligence", "portfolio-audit", "watchlist", "archive", "displacement", "other")


def report_type(subject, source=None):
    text = (subject + " " + (str(source) if source else "")).lower().replace("_", " ").replace("-", " ")
    if "market" in text and "intelligence" in text:
        return "market-intelligence"
    if "portfolio" in text and "audit" in text:
        return "portfolio-audit"
    if "displacement" in text or "displace" in text:
        return "displacement"
    if "archive" in text or "resurrection" in text or ("reject" in text and "watchlist" in text):
        return "archive"
    if "watchlist" in text or "shortlist" in text or "dossier" in text:
        return "watchlist"
    return "other"


def should_email(kind, shortlisted=(), displacements=()):
    if kind == "watchlist":
        return False
    if kind in ("market-intelligence", "portfolio-audit"):
        return True
    if kind in ("archive", "displacement"):
        return any(str(item).strip() for item in (*shortlisted, *displacements))
    return True


def build_digest(subject, content, source, summary=None, highlights=(), shortlisted=(), displacements=()):
    if source is None:
        raise ValueError("Summary emails require source_path pointing to the published report")
    destination = published_url(str(Path(source).resolve()))
    if not destination or not destination.startswith(BASE_URL):
        raise ValueError("Email report must exist under docs/ before delivery")
    if not summary:
        entry = read_entry(Path(source).resolve(), {}, {})
        summary = entry["summary"]
    if not summary:
        soup = BeautifulSoup(content, "html.parser")
        for node in soup.select("script, style, nav, .tooltip, .glossary-tip"):
            node.decompose()
        paragraph = soup.find("p")
        summary = paragraph.get_text(" ", strip=True) if paragraph else "The latest research report is available on the Research Desk."
    summary = re.sub(r"\s+", " ", summary).strip()[:600]
    bullets = [f"New shortlist qualification: {str(symbol).strip()[:120]}" for symbol in shortlisted if str(symbol).strip()]
    bullets.extend(f"Eligible holding displacement: {str(event).strip()[:240]}" for event in displacements if str(event).strip())
    bullets.extend(str(item)[:240] for item in highlights[:5])
    escape = html.escape
    items = "".join(f"<li>{escape(item)}</li>" for item in bullets)
    body = ('<!doctype html><html><body style="font-family:Helvetica,Arial,sans-serif;color:#202923;max-width:640px;margin:24px auto;padding:20px;line-height:1.6">'
            f'<h1 style="font-size:22px">{escape(subject)}</h1><p>{escape(summary)}</p>'
            + (f"<ul>{items}</ul>" if items else "")
            + f'<p><a href="{escape(destination, quote=True)}">Read the complete report on GitHub Pages</a></p></body></html>')
    plain = subject + "\n\n" + summary + "\n\n" + "\n".join("- " + item for item in bullets) + "\n\nFull report: " + destination
    return body, plain
