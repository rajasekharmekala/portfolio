#!/usr/bin/env python3
"""Standalone Options & Call-Convexity Desk Report Builder (`options_desk`).

Compiles a fast, beginner-clear Research Desk report (`docs/reports/<MKT>_Options_Desk.html`)
from `scripts/options_snapshot.py` output — AND can surgically refresh `#options-overlay`
inside an existing published `docs/blogs/<MKT>/<SYM>_dossier.html` without rewriting
the 15,000-word company dossier!
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path
from typing import Any, Dict

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_report import build  # noqa: E402
from options_snapshot import render_options_section_html  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def patch_existing_dossier_html(dossier_path: Path, options_pkg: Dict[str, Any]) -> bool:
    """Surgically insert or replace <section id='options-overlay'> inside an existing _dossier.html."""
    if not dossier_path.is_file():
        return False
    raw = dossier_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")
    new_sec = BeautifulSoup(
        render_options_section_html(
            options_pkg["options_plan"],
            options_pkg.get("multitimeframe_chart"),
            options_pkg.get("browser_sessions"),
        ),
        "html.parser",
    ).find("section", id="options-overlay")
    if new_sec is None:
        return False

    existing = soup.find("section", id="options-overlay")
    if existing is not None:
        existing.replace_with(new_sec)
    else:
        anchor = (
            soup.find("section", id="capital-redeployment")
            or soup.find("section", id="ch-9")
            or soup.find("section", id="ch-7")
        )
        if anchor is None:
            return False
        anchor.insert_after(new_sec)

    dossier_path.write_text(str(soup), encoding="utf-8")
    return True


def render_options_desk_report(snapshot_data: Dict[str, Any], as_of: str = "") -> str:
    mkt = str(snapshot_data.get("market") or "US").upper()
    cur = "₹" if mkt == "IN" else "$"
    as_of = as_of or dt.date.today().isoformat()
    packages: Dict[str, Any] = snapshot_data.get("packages") or {}

    actionable = [
        s for s, p in packages.items()
        if (p.get("options_plan") or {}).get("options_verdict") in {"LONG_CALL_LEAPS", "BULL_CALL_DEBIT_SPREAD"}
    ]
    open_cnt = sum(len((p.get("options_plan") or {}).get("open_positions_audit") or []) for p in packages.values())
    first_pkg = next(iter(packages.values()), {})
    rh_info = ((first_pkg.get("browser_sessions") or {}).get("robinhood") or {})
    rh_status = rh_info.get("note") or "Public options chain snapshot."

    kf_html = (
        '<dl class="key-figures">\n'
        f"<div><dt>Market</dt><dd>{'India (NSE F&amp;O)' if mkt == 'IN' else 'United States (Listed Options)'}</dd></div>\n"
        f"<div><dt>Symbols Screened</dt><dd>{len(packages)}</dd></div>\n"
        f"<div><dt>Actionable Call Setups</dt><dd>{len(actionable)} ({html.escape(', '.join(actionable) or 'None — Stand Aside')})</dd></div>\n"
        f"<div><dt>Open Contracts Audited</dt><dd>{open_cnt}</dd></div>\n"
        f"<div><dt>Live Broker Feed</dt><dd>{html.escape('Robinhood Connected' if rh_info.get('logged_in') else 'Public Chain (Broker Not Logged In)')}</dd></div>\n"
        "</dl>"
    )

    primer_html = (
        '<section class="primer" id="primer">\n'
        "<h2>How to Read This Options Desk Briefing (Beginner Guide)</h2>\n"
        "<p>Options let us risk a small, strictly capped dollar amount (50 to 60 bps of portfolio value) when a strong business pulls back to a major chart floor or coils for a breakout. "
        "Unlike shares, options have an expiration clock and implied-volatility pricing: when volatility is elevated after news, we use <strong>Bull Call Debit Spreads</strong> (selling a higher call to cut cost and time decay); when volatility is calm in US compounders, we use <strong>0.65–0.80 Delta LEAPS Calls</strong> (9+ months out). "
        f"{html.escape(rh_status)}</p>\n"
        "</section>"
    )

    summary_rows = []
    for sym, pkg in packages.items():
        plan = pkg.get("options_plan") or {}
        mtf = pkg.get("multitimeframe_chart") or {}
        tr = plan.get("recommended_trade") or {}
        spot = mtf.get("close")
        max_loss_txt = f"{cur}{tr['max_loss_total']:,.2f}" if isinstance(tr.get("max_loss_total"), (int, float)) else "—"
        be_txt = f"{cur}{tr['breakeven_at_expiry']:,.2f}" if isinstance(tr.get("breakeven_at_expiry"), (int, float)) else "—"
        summary_rows.append(
            f"<tr><td><strong>{html.escape(sym)}</strong></td>"
            f"<td>{html.escape(str(pkg.get('business_quality_verdict') or 'N/A'))}</td>"
            f"<td>{f'{cur}{spot:,.2f}' if isinstance(spot, (int, float)) else 'N/A'}</td>"
            f"<td>{html.escape(str(mtf.get('setup_archetype') or 'N/A'))}</td>"
            f"<td><strong>{html.escape(str(plan.get('options_verdict') or 'N/A'))}</strong></td>"
            f"<td>{max_loss_txt}</td>"
            f"<td>{be_txt}</td>"
            f"<td>{html.escape(str(tr.get('max_profit_total') or '—'))}</td></tr>"
        )

    overview_sec = (
        '<section class="chapter" id="desk-overview">\n'
        "<h2>1. Multi-Timeframe &amp; Call-Convexity Screening Matrix</h2>\n"
        '<div class="table-wrap"><table class="wikitable">'
        f"<caption>{mkt} Options &amp; Call-Convexity Summary ({html.escape(as_of)})</caption>"
        "<thead><tr><th>Symbol</th><th>Fundamental Gate</th><th>Spot</th><th>Chart Archetype (1W/1D/4H)</th><th>Options Verdict</th><th>Max Loss</th><th>Breakeven</th><th>Max Profit</th></tr></thead>"
        f"<tbody>{''.join(summary_rows)}</tbody></table></div>\n"
        "<p>Every setup above is gated first on Pass 1 business quality (blocking broken businesses from rebound calls) and second on bid-ask liquidity and IV-vs-HV20 pricing.</p>\n"
        "</section>"
    )

    detail_sections = [
        render_options_section_html(
            pkg["options_plan"],
            pkg.get("multitimeframe_chart"),
            pkg.get("browser_sessions"),
        ).replace('id="options-overlay"', f'id="options-{sym.lower()}"')
        for sym, pkg in packages.items()
    ]

    body = "\n\n".join([
        f"<h1>{'India (NSE F&O)' if mkt == 'IN' else 'US'} Tactical Options &amp; Call-Convexity Desk</h1>",
        kf_html,
        primer_html,
        overview_sec,
        *detail_sections,
    ])
    return build(body, market=mkt, kind="report", workflow="Options desk", as_of=as_of)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", required=True, help="Path to options_snapshot.py JSON output")
    ap.add_argument("--as-of", default="", help="Verified market session date (YYYY-MM-DD)")
    ap.add_argument("--out", required=True, help="Output HTML report path, e.g. docs/reports/US_Options_Desk.html")
    ap.add_argument("--patch-published-dossiers", action="store_true", help="Surgically update #options-overlay in existing docs/blogs/<MKT>/<SYM>_dossier.html files")
    args = ap.parse_args()

    snap = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    html_out = render_options_desk_report(snap, as_of=args.as_of)
    out_p = Path(args.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(html_out, encoding="utf-8")
    print(f"[+] Wrote standalone Options Desk report to {out_p}")

    if args.patch_published_dossiers:
        mkt = str(snap.get("market") or "US").upper()
        patched = 0
        for sym, pkg in (snap.get("packages") or {}).items():
            dp = REPO / "docs" / "blogs" / mkt / f"{sym}_dossier.html"
            if patch_existing_dossier_html(dp, pkg):
                patched += 1
        print(f"[+] Surgically refreshed #options-overlay in {patched} published dossier(s)")


if __name__ == "__main__":
    main()
