# Portfolio Research System (`docs/Portfolio Research System/`)

This directory contains the canonical investment constitution, research databases, KPI libraries, and holding review frameworks.

---

## 1. Operating Constitution & Philosophy
- [00_Investment_Philosophy_and_Portfolio_Operating_Constitution.md](00_Investment_Philosophy_and_Portfolio_Operating_Constitution.md) — Master investment rules, 4-engine return architecture, support-aware entry discipline, and risk controls.
- [01_Master_Portfolio_Dashboard.md](01_Master_Portfolio_Dashboard.md) — Portfolio-level overview and allocation tracking.
- [09_Transcript_to_Portfolio_Research_Workflow.md](09_Transcript_to_Portfolio_Research_Workflow.md) — Multi-agent research architecture.
- [10_Bucket_Aware_Portfolio_Action_Requirements.md](10_Bucket_Aware_Portfolio_Action_Requirements.md) — Action requirements and decision hierarchy per strategy book.

---

## 2. Research Databases & Strategy Books
- [02_Core_Holdings_Database.md](02_Core_Holdings_Database.md) — **Core Alpha** high-conviction 3–5 year compounders (Target: 35%–40%).
- [03_Short_Term_and_Momentum_Database.md](03_Short_Term_and_Momentum_Database.md) — **Tactical Momentum** Stage 2 breakout & catalyst swings (Target: 45%–50%).
- [04_Leveraged_Holdings_Database.md](04_Leveraged_Holdings_Database.md) — Leveraged and thematic instruments.
- [06_Quarterly_Portfolio_Reviews.md](06_Quarterly_Portfolio_Reviews.md) — Historical thesis reviews and audit notes.
- [07_Research_and_KPI_Library.md](07_Research_and_KPI_Library.md) — Fine-grained fundamental KPIs and industry metrics.

> **Options Book & Tactical Call-Convexity:** Canonical open option contracts live in `data/options/{IN,US}.json` and are evaluated through the single standalone `.agents/workflows/options_desk.md` workflow (`.agents/skills/options_desk/SKILL.md` + `scripts/options_snapshot.py`).

---

## 3. Canonical Agentic Workflows (`.agents/workflows/`)
- [`.agents/workflows/market_intelligence.md`](../.agents/workflows/market_intelligence.md) — Daily Market Intelligence & Stage 2 Sector/Stock Screening (`IN` / `US`).
- [`.agents/workflows/portfolio_audit.md`](../.agents/workflows/portfolio_audit.md) — Forensic Portfolio Audit & Capital Reallocation (`IN` / `US`).
- [`.agents/workflows/company_report.md`](../.agents/workflows/company_report.md) — Inaugural 10-Chapter Blind-First Company Monograph (`IN` / `US`).
- [`.agents/workflows/dossier_refresh.md`](../.agents/workflows/dossier_refresh.md) — Companion Dossier Refresh, Blind-Spot Brainstorm & Stop-Loss Ratchet (`IN` / `US`).
- [`.agents/workflows/options_desk.md`](../.agents/workflows/options_desk.md) — Standalone Tactical Options & Call-Convexity Desk (`IN` / `US`).
