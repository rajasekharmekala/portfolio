#!/usr/bin/env python3
"""
W7/6.5 readability gate: the code checks that a book-standard company report
actually reads like the book standard says.

Checks (see .agents/skills/_shared/BOOK_STANDARD.md section 5):
  1. Flesch-Kincaid grade per chapter <= --max-grade (default 13)
  2. glossary terms (agents/config/glossary.json) defined at first use:
     first occurrence inside <dfn>, same paragraph carries the expansion
     (acronyms) or a defining sentence (phrase terms)
  3. no bare tables: every <table> is followed by an explanatory paragraph
     (>= 80 chars) before the next table or heading
  4. every <section class="estimate"> has the five working parts
  5. chapter 7 exists and carries >= 1 <p class="trigger"> (>= 20 chars each)
  6. banned filler phrases (REPORT_VOICE section 5) are absent; the primer has
     3-5 sentences; Notes and sources exist and are numbered

Usage: python3 scripts/readability_check.py docs/blogs/US/ADBE_dossier.html [--max-grade 13]
Exit 0 = pass, 1 = failures.
"""
import argparse
import json
import os
import re
import sys

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOSSARY_FILE = os.path.join(ROOT, ".agents", "config", "glossary.json")

BANNED = [
    "this section", "in this section", "the following table", "below is",
    "as the table shows", "it is important to note", "it should be noted",
    "let us explore", "we will examine", "furthermore", "moreover",
    "additionally", "in conclusion", "in summary", "overall, it is clear that",
    "delve", "landscape", "robust", "game-changer", "unlock", "navigate the",
    "speak for themselves", "letting the data speak for itself",
    "pending revalidation", "carried forward", "technical revalidation pending",
    "to be confirmed later",
]
ESTIMATE_PARTS = ["the number", "how it was calculated", "the inputs",
                  "the range", "if the number is off"]
DEFINE_MARKERS = [" is ", " are ", " means ", " stands for ", " \u2014 ", " - "]


def count_syllables(w):
    w = w.lower().strip("'")
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and n > 1:
        n -= 1
    return max(1, n)


def fk_grade(text):
    words = re.findall(r"[A-Za-z0-9']+", text)
    if not words:
        return 0.0
    sentences = max(1, len(re.findall(r"[.!?]+(?=\s|$)", text)))
    syll = sum(count_syllables(w) for w in words)
    return 0.39 * len(words) / sentences + 11.8 * syll / len(words) - 15.59


def sentence_count(text):
    return len([s for s in re.split(r"[.!?]+(?=\s|$)", text) if s.strip()])


def term_regex(term):
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])",
                      re.IGNORECASE)


def first_use_in_dfn(soup, term):
    """First prose text-node occurrence of term: return (node, in_dfn, paragraph)."""
    rx = term_regex(term)
    skip_tags = {"script", "style", "head", "title", "header", "footer", "nav",
                 "aside", "select", "button", "h1", "h2", "h3", "h4", "h5", "h6",
                 "dt", "th", "caption"}
    for node in soup.find_all(string=True):
        ancestors = [p.name for p in node.parents if p and p.name]
        if any(t in skip_tags for t in ancestors):
            continue
        if any("key-figures" in (p.get("class") or []) for p in node.parents if hasattr(p, "get")):
            continue
        if rx.search(str(node)):
            in_dfn = node.parent.name == "dfn" or \
                any(p.name == "dfn" for p in node.parent.parents)
            para = node.parent.find_parent(["p", "li", "td", "dd"])
            return node, in_dfn, para
    return None, False, None


def check_glossary(soup, glossary, errors):
    for entry in glossary.get("must_define", []):
        term = entry["term"]
        node, in_dfn, para = first_use_in_dfn(soup, term)
        if node is None:
            continue
        where = str(para.get_text(" ", strip=True)) if para else ""
        if not in_dfn:
            errors.append(f"GLOSSARY {term}: first use is not inside <dfn>")
        elif entry["expansion"].lower() not in where.lower():
            errors.append(f"GLOSSARY {term}: paragraph at first use lacks the "
                          f"expansion {entry['expansion']!r}")
    for term in glossary.get("plain", []):
        node, in_dfn, para = first_use_in_dfn(soup, term)
        if node is None:
            continue
        where = (" " + str(para.get_text(" ", strip=True)).lower() + " ") if para else " "
        if not in_dfn:
            errors.append(f"GLOSSARY {term}: first use is not inside <dfn>")
        elif not any(m in where for m in DEFINE_MARKERS):
            errors.append(f"GLOSSARY {term}: paragraph at first use has no "
                          "defining sentence")


def check_bare_tables(soup, errors):
    for t in soup.find_all("table"):
        ok = False
        for el in t.find_all_next():
            if el.name == "p":
                if len(el.get_text(" ", strip=True)) >= 80:
                    ok = True
                    break
            elif el.name in ("table", "h1", "h2", "h3", "h4", "h5", "h6", "section"):
                break
        if not ok:
            sec = t.find_parent("section")
            where = sec.get("id") if sec else "?"
            errors.append(f"TABLE: table in {where} has no explanatory "
                          "paragraph before the next table or heading")


def check_estimates(soup, errors):
    ests = soup.find_all("section", class_="estimate")
    if not ests:
        errors.append("ESTIMATE: no <section class=\"estimate\"> found in the report")
    for i, e in enumerate(ests, 1):
        h4 = " | ".join(h.get_text(" ", strip=True).lower()
                        for h in e.find_all("h4"))
        for part in ESTIMATE_PARTS:
            if part not in h4:
                errors.append(f"ESTIMATE #{i}: missing the {part!r} part")


def check_chapter7(soup, errors):
    ch7 = soup.find("section", id="ch-7") or \
        next((s for s in soup.find_all("section")
              if "what we would do" in
              (s.find("h2").get_text().lower() if s.find("h2") else "")), None)
    if not ch7:
        errors.append("CHAPTER 7: not found (id=\"ch-7\")")
        return
    triggers = ch7.find_all("p", class_="trigger")
    if not triggers:
        errors.append("CHAPTER 7: no <p class=\"trigger\"> — every decision must "
                      "name the price or event that would change it")
    for i, t in enumerate(triggers, 1):
        if len(t.get_text(" ", strip=True)) < 20:
            errors.append(f"CHAPTER 7: trigger #{i} is too short to name a "
                          "price or event")


def check_primer_and_notes(soup, errors):
    primer = soup.find("section", id="primer")
    if not primer:
        errors.append("PRIMER: not found (id=\"primer\")")
    else:
        n = sentence_count(primer.get_text(" ", strip=True))
        if not 3 <= n <= 5:
            errors.append(f"PRIMER: {n} sentences, standard is 3-5")
    notes = soup.find("section", id="notes")
    if not notes:
        errors.append("NOTES: not found (id=\"notes\")")
    else:
        ol = notes.find("ol")
        if not ol or ol.find_all("li") == []:
            errors.append("NOTES: sources must be a numbered <ol>")


def check_banned(soup, errors):
    text = " " + soup.get_text(" ", strip=True).lower() + " "
    for phrase in BANNED:
        if phrase in text:
            errors.append(f"VOICE: banned phrase {phrase!r} present")


def check_grade(soup, max_grade, errors):
    chapters = [soup.find("section", id="primer")] + \
        soup.find_all("section", class_="chapter")
    chapters = [c for c in chapters if c]
    if not chapters:
        errors.append("CHAPTERS: no .primer or .chapter sections found")
    for c in chapters:
        label = c.get("id") or (c.find("h2").get_text()[:24] if c.find("h2") else "?")
        g = fk_grade(c.get_text(" ", strip=True))
        if g > max_grade:
            errors.append(f"GRADE {label}: Flesch-Kincaid {g:.1f} > {max_grade}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--max-grade", type=float, default=13.0)
    ap.add_argument("--glossary", default=GLOSSARY_FILE)
    args = ap.parse_args()

    soup = BeautifulSoup(open(args.report, encoding="utf-8").read(), "html.parser")
    glossary = json.load(open(args.glossary, encoding="utf-8"))

    errors = []
    check_grade(soup, args.max_grade, errors)
    check_glossary(soup, glossary, errors)
    check_bare_tables(soup, errors)
    check_estimates(soup, errors)
    check_chapter7(soup, errors)
    check_primer_and_notes(soup, errors)
    check_banned(soup, errors)

    if errors:
        print(f"FAIL: {len(errors)} readability finding(s) in {args.report}")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"PASS: {args.report} (readability, max grade {args.max_grade})")


if __name__ == "__main__":
    main()
