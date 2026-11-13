"use strict";

(() => {
  const byId = id => document.getElementById(id);
  const state = {
    entries: [],
    queues: null,
    holdings: {},
    market: "ALL",
    stage: "ALL",
    sector: "ALL",
    status: "ALL",
    verdict: "ALL",
    sort: { key: "market", dir: "asc" },
    search: "",
    viewMode: "tree",
    activeTab: "performance",
    perf: null,
    perfProfileId: null,
    perfPeriod: "1Y",
  };

  const TABS = [
    { id: "performance", hash: "#performance", searchPlaceholder: "" },
    { id: "pipeline", hash: "#pipeline", searchPlaceholder: "Search ticker, company, sector…" },
    { id: "reports", hash: "#reports", searchPlaceholder: "Search report title, market, summary…" },
    { id: "dossiers", hash: "#monographs", searchPlaceholder: "Search ticker, company, summary…" },
  ];
  const DEFAULT_TAB = "performance";

  const HASH_TO_TAB = {
    "#pipeline": "pipeline",
    "#pipeline-heading": "pipeline",
    "#performance": "performance",
    "#performance-heading": "performance",
    "#reports": "reports",
    "#reports-heading": "reports",
    "#monographs": "dossiers",
    "#dossiers": "dossiers",
    "#dossiers-heading": "dossiers",
  };

  function resolveTabFromHash(hash) {
    const key = String(hash || "").toLowerCase();
    if (!key) return DEFAULT_TAB;
    if (key === "#top") return null;
    return HASH_TO_TAB[key] || DEFAULT_TAB;
  }

  const escapeHtml = value =>
    String(value ?? "").replace(/[&<>"']/g, c => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c]));

  function formatDate(value) {
    if (!value) return "Latest";
    const d = new Date(value);
    if (!Number.isFinite(d.getTime())) return "Latest";
    return new Intl.DateTimeFormat("en-US", {
      month: "short", day: "numeric", year: "numeric", timeZone: "America/Los_Angeles",
    }).format(d);
  }

  function formatDateTime(value) {
    if (!value) return "Latest";
    const d = new Date(value);
    if (!Number.isFinite(d.getTime())) return "Latest";
    return new Intl.DateTimeFormat("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "numeric", minute: "2-digit", timeZoneName: "short", timeZone: "America/Los_Angeles",
    }).format(d);
  }

  function verdictClass(v) {
    if (!v || v === "Not specified") return "verdict-neutral";
    const upper = v.toUpperCase();
    if (upper.includes("BUY") || upper.includes("ACCUMULATE") || upper.includes("COMPOUND") || upper.includes("PASSED")) return "verdict-good";
    if (upper.includes("WAIT") || upper.includes("TRIM") || upper.includes("REPLACE") || upper.includes("HOLD") || upper.includes("WATCH")) return "verdict-warn";
    if (upper.includes("REJECT") || upper.includes("AVOID") || upper.includes("STAGE 4") || upper.includes("FAIL")) return "verdict-bad";
    return "verdict-neutral";
  }

  function stageClass(stage) {
    if (stage === "STAGE_2") return "stage-2";
    if (stage === "STAGE_1") return "stage-1";
    if (stage === "STAGE_3") return "stage-3";
    if (stage === "STAGE_4") return "stage-4";
    return "stage-none";
  }

  const stageLabel = stage => stage ? stage.replace("_", " ") : "—";
  const statusLabel = status =>
    status === "HELD" ? "Held" : status === "SHORTLIST" ? "Shortlist" : status === "WATCHLIST" ? "Watchlist" : "Tracked";

  // ---- Build one unified, de-duplicated pipeline row per (market, symbol) ----
  function buildPipeline() {
    const rows = new Map(); // key -> row
    const held = state.holdings || {};

    function ensure(market, symbol, company) {
      const key = `${market}:${symbol}`;
      if (!rows.has(key)) {
        rows.set(key, {
          market, symbol, company: company || symbol,
          stages: new Set(), sectors: new Set(), statuses: new Set(),
          verdict: null, dossierUrl: null,
        });
      }
      const row = rows.get(key);
      if (company && (!row.company || row.company === symbol)) row.company = company;
      return row;
    }

    const queueData = state.queues || {};
    for (const market of ["US", "IN"]) {
      const group = queueData[market] || {};
      for (const kind of ["watchlist", "shortlist"]) {
        const bucket = group[kind];
        if (!bucket || !bucket.available || !Array.isArray(bucket.rows)) continue;
        for (const r of bucket.rows) {
          const row = ensure(market, r.symbol, r.company);
          if (r.stage) row.stages.add(r.stage);
          if (r.sector) row.sectors.add(r.sector);
          row.statuses.add(kind === "shortlist" ? "SHORTLIST" : "WATCHLIST");
          if (r.dossierUrl) {
            row.dossierUrl = r.dossierUrl;
            if (r.verdict && r.verdict !== "Not specified") row.verdict = r.verdict;
          }
        }
      }
    }

    for (const market of ["US", "IN"]) {
      for (const symbol of (held[market] || [])) {
        const row = ensure(market, symbol, symbol);
        row.statuses.add("HELD");
      }
    }

    // Published monographs are the authoritative source of truth for single-name underwriting verdicts and links.
    for (const e of state.entries) {
      if (e.kind !== "dossier" || !e.symbol) continue;
      const row = ensure(e.market, e.symbol, e.symbol);
      if (e.verdict && e.verdict !== "Not specified") row.verdict = e.verdict;
      if (e.sector && e.sector !== "Not specified") row.sectors.add(e.sector);
      if (e.url) row.dossierUrl = e.url;
    }

    return [...rows.values()].map(r => ({
      market: r.market,
      symbol: r.symbol,
      company: r.company,
      stage: pickStage(r.stages),
      sector: [...r.sectors][0] || null,
      statuses: [...r.statuses],
      status: primaryStatus([...r.statuses]),
      verdict: r.dossierUrl ? r.verdict : null,
      dossierUrl: r.dossierUrl,
    }));
  }

  function pickStage(stages) {
    const order = ["STAGE_2", "STAGE_1", "STAGE_3", "STAGE_4"];
    for (const s of order) if (stages.has(s)) return s;
    return [...stages][0] || null;
  }

  // Held outranks Shortlist outranks Watchlist for the single Status column,
  // but the full set is kept so the Status filter can match any membership.
  function primaryStatus(statuses) {
    if (statuses.includes("HELD")) return "HELD";
    if (statuses.includes("SHORTLIST")) return "SHORTLIST";
    if (statuses.includes("WATCHLIST")) return "WATCHLIST";
    return "HELD";
  }

  function pipelineMatch(row) {
    if (state.market !== "ALL" && row.market !== state.market) return false;
    if (state.stage !== "ALL" && row.stage !== state.stage) return false;
    if (state.sector !== "ALL" && row.sector !== state.sector) return false;
    if (state.status !== "ALL" && row.status !== state.status) return false;
    if (state.verdict !== "ALL" && row.verdict !== state.verdict) return false;
    if (state.search) {
      const q = state.search.toLowerCase();
      const text = [row.symbol, row.company, row.sector, row.verdict, row.stage, row.market]
        .join(" ").toLowerCase();
      if (!text.includes(q)) return false;
    }
    return true;
  }

  // Ascending puts the most favourable value first: Stage 2 before 4, Immediate Buy before Avoid,
  // Held before Shortlist before Watchlist. Missing values sort last in both directions.
  const STAGE_RANK = { STAGE_2: 0, STAGE_1: 1, STAGE_3: 2, STAGE_4: 3 };
  const STATUS_RANK = { HELD: 0, SHORTLIST: 1, WATCHLIST: 2 };
  const VERDICT_RANK = {
    "IMMEDIATE BUY": 0,
    "ACCUMULATE ON DIP": 1,
    "KEEP COMPOUNDING": 2,
    "WAIT FOR SUPPORT": 3,
    "WATCHLIST / HOLD": 4,
    "TRIM / HARVEST": 5,
    "AVOID / REJECTED": 6,
  };

  const PIPELINE_COLUMNS = [
    { key: "ticker", label: "Ticker" },
    { key: "company", label: "Company", className: "col-company" },
    { key: "market", label: "Market" },
    { key: "stage", label: "Stage" },
    { key: "sector", label: "Sector", className: "col-sector" },
    { key: "status", label: "Status" },
    { key: "verdict", label: "Verdict" },
    { key: "monograph", label: "Monograph" },
  ];

  function sortValue(key, row) {
    switch (key) {
      case "ticker": return row.symbol || "";
      case "company": return row.company && row.company !== row.symbol ? row.company : null;
      case "stage": return row.stage ? (STAGE_RANK[row.stage] ?? 9) : null;
      case "sector": return row.sector || null;
      // Held names with more memberships first; the direction flips the whole order.
      case "status": return STATUS_RANK[row.status] * 3 + (3 - row.statuses.length);
      case "verdict": return row.verdict ? (VERDICT_RANK[row.verdict] ?? 7) : null;
      case "monograph": return row.dossierUrl ? 0 : 1;
      default: return row.market;
    }
  }

  function sortPipeline(list) {
    const { key, dir } = state.sort;
    const sign = dir === "desc" ? -1 : 1;
    return [...list].sort((a, b) => {
      const va = sortValue(key, a);
      const vb = sortValue(key, b);
      let cmp;
      if (va === null || vb === null) {
        cmp = (va === null) - (vb === null);
      } else if (typeof va === "number") {
        cmp = (va - vb) * sign;
      } else {
        cmp = String(va).localeCompare(String(vb)) * sign;
      }
      return cmp || (a.symbol || "").localeCompare(b.symbol || "") || a.market.localeCompare(b.market);
    });
  }

  function pipelineHeadRow() {
    const cells = PIPELINE_COLUMNS.map(col => {
      const active = state.sort.key === col.key;
      const ariaSort = active ? (state.sort.dir === "desc" ? "descending" : "ascending") : "none";
      const cls = col.className ? ` class="${col.className}"` : "";
      return `<th scope="col"${cls} aria-sort="${ariaSort}"><button type="button" class="th-sort" data-sort-key="${col.key}">${escapeHtml(col.label)}<span class="sort-ind" aria-hidden="true"></span></button></th>`;
    });
    return `<tr>${cells.join("")}</tr>`;
  }

  const SECTIONS = [
    { status: "HELD", id: "holdings", label: "Holdings" },
    { status: "SHORTLIST", id: "shortlist", label: "Shortlist" },
    { status: "WATCHLIST", id: "watchlist", label: "Watchlist" },
  ];

  function isFiltered() {
    return state.market !== "ALL" || state.stage !== "ALL" || state.sector !== "ALL"
      || state.status !== "ALL" || state.verdict !== "ALL" || Boolean(state.search);
  }

  function isCurrentTabFiltered() {
    if (state.activeTab === "pipeline") return isFiltered();
    if (state.activeTab === "dossiers") {
      return state.market !== "ALL" || state.verdict !== "ALL" || Boolean(state.search);
    }
    if (state.activeTab === "reports") {
      return state.market !== "ALL" || Boolean(state.search);
    }
    return false;
  }

  function pipelineRowHtml(row) {
    const company = row.company && row.company !== row.symbol ? escapeHtml(row.company) : "";
    const tickerLink = row.dossierUrl
      ? `<a class="pipe-ticker" href="${escapeHtml(row.dossierUrl)}">${escapeHtml(row.symbol)}</a>`
      : `<span class="pipe-ticker">${escapeHtml(row.symbol)}</span>`;
    const statusTitle = row.statuses.map(statusLabel).join(" · ");
    const secondary = row.statuses.filter(s => s !== row.status);
    const statusCell = `<span class="status-pill status-${row.status.toLowerCase()}">${statusLabel(row.status)}</span>` +
      secondary.map(s => ` <span class="status-more" title="${escapeHtml(statusTitle)}">${statusLabel(s)}</span>`).join("");
    const verdict = row.verdict && row.verdict !== "Not specified"
      ? `<span class="verdict-pill ${verdictClass(row.verdict)}">${escapeHtml(row.verdict)}</span>`
      : '<span class="pipe-muted" title="Underwriting pending">—</span>';
    const mono = row.dossierUrl
      ? `<a class="pipe-doc" href="${escapeHtml(row.dossierUrl)}">Read &rarr;</a>`
      : '<span class="pipe-muted">—</span>';
    return `<tr>
      <td>${tickerLink}</td>
      <td class="pipe-company col-company">${company || '<span class="pipe-muted">&mdash;</span>'}</td>
      <td><span class="market-pill market-${escapeHtml(row.market)}">${escapeHtml(row.market)}</span></td>
      <td><span class="stage-pill ${stageClass(row.stage)}">${escapeHtml(stageLabel(row.stage))}</span></td>
      <td class="pipe-sector col-sector">${row.sector ? escapeHtml(row.sector) : '<span class="pipe-muted">&mdash;</span>'}</td>
      <td class="pipe-status-cell">${statusCell}</td>
      <td>${verdict}</td>
      <td>${mono}</td>
    </tr>`;
  }

  function renderBranchTable(items, label) {
    if (!items.length) {
      const scope = isFiltered() ? " match the current filters" : " yet";
      return `<p class="branch-empty">No ${escapeHtml(label.toLowerCase())} names${scope}.</p>`;
    }
    return `<div class="branch-table-wrap"><table class="pipeline-table"><thead>${pipelineHeadRow()}</thead><tbody>${items.map(pipelineRowHtml).join("")}</tbody></table></div>`;
  }

  // Each name sits in exactly one section (its primary status), so section counts sum to the tracked total.
  function renderTree(all) {
    const treeEl = byId("pipeline-tree");
    if (!treeEl) return;

    const filtered = sortPipeline(all.filter(pipelineMatch));
    const filtering = isFiltered();

    for (const section of SECTIONS) {
      const items = filtered.filter(r => r.status === section.status);
      const branch = byId(`branch-${section.id}`);
      const count = byId(`count-${section.id}`);
      const content = byId(`content-${section.id}`);
      if (count) {
        const inMkt = mkt => items.filter(r => r.market === mkt).length;
        count.textContent = `${items.length} names · IN ${inMkt("IN")} · US ${inMkt("US")}`;
      }
      if (content) content.innerHTML = renderBranchTable(items, section.label);
      if (branch) branch.hidden = filtering && items.length === 0;
    }

    updateToggleAllButton();
  }

  function updateToggleAllButton() {
    const toggleAllBtn = byId("toggle-all-branches");
    if (!toggleAllBtn) return;
    const branches = document.querySelectorAll(".accordion-branch");
    if (!branches.length) return;
    const allOpen = Array.from(branches).every(b => b.open);
    toggleAllBtn.textContent = allOpen ? "Collapse All Branches" : "Expand All Branches";
    toggleAllBtn.setAttribute("aria-expanded", String(allOpen));
  }

  function renderPipeline(all) {
    const body = byId("pipeline-body");
    const meta = byId("pipeline-meta");
    const counts = byId("pipeline-counts");
    const emptyNote = byId("pipeline-empty");
    if (!body) return;

    const filtered = sortPipeline(all.filter(pipelineMatch));

    if (counts) {
      const byMarket = m => filtered.filter(r => r.market === m).length;
      const byStatus = s => filtered.filter(r => r.status === s).length;
      counts.textContent = `${filtered.length} names shown · US ${byMarket("US")} · IN ${byMarket("IN")} · Watchlist ${byStatus("WATCHLIST")} · Shortlist ${byStatus("SHORTLIST")} · Held ${byStatus("HELD")}`;
    }
    if (meta) meta.textContent = `${filtered.length} of ${all.length} tracked names`;

    const head = byId("pipeline-head");
    if (head) head.innerHTML = pipelineHeadRow();
    body.innerHTML = filtered.map(pipelineRowHtml).join("");

    if (emptyNote) {
      const none = filtered.length === 0;
      emptyNote.hidden = !none;
      emptyNote.textContent = none ? "No tracked names match these filters." : "";
    }
  }

  function filterEntries(kind) {
    return state.entries.filter(e => {
      if (kind && e.kind !== kind) return false;
      if (state.market !== "ALL" && e.market !== state.market) return false;
      if (kind === "dossier" && state.verdict !== "ALL" && e.verdict !== state.verdict) return false;
      if (state.search) {
        const q = state.search.toLowerCase();
        const text = [e.title, e.symbol, e.market, e.workflow, e.verdict, e.summary, e.sector]
          .join(" ").toLowerCase();
        if (!text.includes(q)) return false;
      }
      return true;
    });
  }

  function renderCard(e, isRecent = false) {
    const className = isRecent ? "recent-item" : "report-card";
    const hasVerdict = e.verdict && e.verdict !== "Not specified";
    const label = e.workflow || (e.kind === "dossier" ? "Company Research" : "Operating Report");
    return `
      <a class="${className}" href="${escapeHtml(e.url)}">
        <div class="card-top">
          <div class="badge-row">
            <span class="market-pill market-${escapeHtml(e.market)}">${escapeHtml(e.market)}</span>
            ${e.symbol ? `<span class="symbol-pill">${escapeHtml(e.symbol)}</span>` : ""}
            ${hasVerdict ? `<span class="verdict-pill ${verdictClass(e.verdict)}">${escapeHtml(e.verdict)}</span>` : ""}
          </div>
          <span class="stamp">${escapeHtml(formatDate(e.updatedAt || e.generatedAt))}</span>
        </div>
        <div class="card-title">${escapeHtml(e.title)}</div>
        ${e.summary ? `<p class="card-summary">${escapeHtml(e.summary)}</p>` : ""}
        <div class="card-foot">
          <span>${escapeHtml(label)}</span>
          <span>Read &rarr;</span>
        </div>
      </a>
    `;
  }

  function renderDossierRow(e) {
    const hasVerdict = e.verdict && e.verdict !== "Not specified";
    const sub = e.sector && e.sector !== "Not specified" ? e.sector : "Company monograph";
    const pdf = e.pdfUrl
      ? `<a class="dossier-pdf" href="${escapeHtml(e.pdfUrl)}" target="_blank" rel="noopener">PDF</a>`
      : "";
    return `
      <div class="dossier-row" role="listitem">
        <div class="dossier-ticker-col">
          <a class="dossier-symbol" href="${escapeHtml(e.url)}">${escapeHtml(e.symbol || "—")}</a>
          <span class="market-pill market-${escapeHtml(e.market)}">${escapeHtml(e.market)}</span>
        </div>
        <div class="dossier-main">
          <a class="dossier-title-link" href="${escapeHtml(e.url)}">${escapeHtml(e.title)}</a>
          <div class="dossier-sub">${escapeHtml(sub)}</div>
        </div>
        <div class="dossier-meta">
          ${hasVerdict ? `<span class="verdict-pill ${verdictClass(e.verdict)}">${escapeHtml(e.verdict)}</span>` : ""}
          ${pdf}
        </div>
        <div class="dossier-date">${escapeHtml(formatDate(e.updatedAt || e.generatedAt))}</div>
      </div>
    `;
  }

  function renderStats(pipeline) {
    const statsEl = byId("portal-stats");
    if (!statsEl) return;
    const publishedDossiers = state.entries.filter(e => e.kind === "dossier").length;
    const reports = state.entries.filter(e => e.kind === "report").length;
    const countStatus = s => pipeline.filter(r => r.status === s).length;

    statsEl.innerHTML = `
      <div><dt>Tracked</dt><dd>${pipeline.length}</dd></div>
      <div><dt>Watchlist</dt><dd>${countStatus("WATCHLIST")}</dd></div>
      <div><dt>Shortlist</dt><dd>${countStatus("SHORTLIST")}</dd></div>
      <div><dt>Held</dt><dd>${countStatus("HELD")}</dd></div>
      <div><dt>Monographs</dt><dd>${publishedDossiers}</dd></div>
      <div><dt>Reports</dt><dd>${reports}</dd></div>
    `;
  }

  function render() {
    const pipeline = buildPipeline();
    const sortSelect = byId("sort-select");
    if (sortSelect) sortSelect.value = state.sort.key;
    renderStats(pipeline);
    renderPipeline(pipeline);
    renderTree(pipeline);

    const reports = filterEntries("report");
    const dossiers = filterEntries("dossier");

    const reportMeta = byId("report-meta");
    if (reportMeta) reportMeta.textContent = `${reports.length} report${reports.length === 1 ? "" : "s"}`;
    const reportList = byId("report-list");
    if (reportList) reportList.innerHTML = reports.map(e => renderCard(e)).join("");

    const reportEmpty = byId("report-empty");
    if (reportEmpty) {
      const allReportsCount = state.entries.filter(e => e.kind === "report").length;
      const none = reports.length === 0;
      reportEmpty.hidden = !none;
      reportEmpty.textContent = none
        ? (allReportsCount === 0
          ? "No operating reports are published right now."
          : "No operating reports match these filters.")
        : "";
    }

    const dossierMeta = byId("dossier-meta");
    if (dossierMeta) dossierMeta.textContent = `${dossiers.length} monograph${dossiers.length === 1 ? "" : "s"}`;
    const dossierList = byId("dossier-list");
    if (dossierList) dossierList.innerHTML = dossiers.map(renderDossierRow).join("");

    const dossierEmpty = byId("dossier-empty");
    if (dossierEmpty) {
      const allDossiersCount = state.entries.filter(e => e.kind === "dossier").length;
      const none = dossiers.length === 0;
      dossierEmpty.hidden = !none;
      dossierEmpty.textContent = none
        ? (allDossiersCount === 0
          ? "No monographs are published right now; they are being regenerated from scratch under the new evidence-first workflow."
          : "No monographs match these filters.")
        : "";
    }

    const emptyState = byId("empty-state");
    if (emptyState) emptyState.hidden = state.entries.length > 0;

    const resetBtn = byId("reset-filters");
    if (resetBtn) {
      resetBtn.hidden = !isCurrentTabFiltered();
    }
  }

  function fillSelect(select, values, allLabel, formatter = v => v) {
    if (!select) return;
    select.innerHTML = `<option value="ALL">${escapeHtml(allLabel)}</option>` +
      values.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(formatter(v))}</option>`).join("");
  }

  function populateFilters(pipeline) {
    const stages = [...new Set(pipeline.map(r => r.stage).filter(Boolean))];
    const stageOrder = ["STAGE_1", "STAGE_2", "STAGE_3", "STAGE_4"];
    stages.sort((a, b) => stageOrder.indexOf(a) - stageOrder.indexOf(b));
    fillSelect(byId("stage-filter"), stages, "All stages", stageLabel);

    const sectors = [...new Set(pipeline.map(r => r.sector).filter(Boolean))].sort();
    fillSelect(byId("sector-filter"), sectors, "All sectors");

    const verdicts = [...new Set([
      ...pipeline.map(r => r.verdict),
      ...state.entries.filter(e => e.kind === "dossier").map(e => e.verdict),
    ].filter(v => v && v !== "Not specified"))].sort();
    fillSelect(byId("verdict-filter"), verdicts, "All verdicts");
  }

  function wireFilter(id, key, transform = v => v) {
    const el = byId(id);
    if (!el) return;
    el.addEventListener("change", () => {
      state[key] = transform(el.value);
      render();
    });
  }

  function activateTab(tabId, { pushHash = false, scrollTop = false } = {}) {
    const tabConfig = TABS.find(t => t.id === tabId) || TABS[0];
    const activeId = tabConfig.id;
    state.activeTab = activeId;

    document.querySelectorAll(".navtabs [data-tab]").forEach(tab => {
      const selected = tab.dataset.tab === activeId;
      tab.classList.toggle("active", selected);
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });

    TABS.forEach(t => {
      const panel = byId(`panel-${t.id}`);
      if (panel) panel.hidden = t.id !== activeId;
    });

    const subnavbar = byId("subnavbar");
    if (subnavbar) subnavbar.hidden = activeId === "performance";

    const philosophy = byId("desk-philosophy");
    if (philosophy) philosophy.hidden = activeId !== "pipeline";

    document.querySelectorAll("[data-tab-scope]").forEach(el => {
      const scopes = (el.dataset.tabScope || "").split(/\s+/).filter(Boolean);
      el.hidden = !scopes.includes(activeId);
    });

    const searchInput = byId("search-input");
    if (searchInput && tabConfig.searchPlaceholder) {
      searchInput.placeholder = tabConfig.searchPlaceholder;
    }

    const resetBtn = byId("reset-filters");
    if (resetBtn) {
      resetBtn.hidden = !isCurrentTabFiltered();
    }

    if (pushHash && window.location.hash !== tabConfig.hash) {
      history.pushState(null, "", tabConfig.hash);
    }

    if (scrollTop && window.scrollY > 140) {
      window.scrollTo({ top: 0, behavior: "auto" });
    }
  }

  function setupTabs() {
    const tabs = Array.from(document.querySelectorAll(".navtabs [data-tab]"));
    tabs.forEach(tab => {
      tab.addEventListener("click", ev => {
        ev.preventDefault();
        activateTab(tab.dataset.tab, { pushHash: true, scrollTop: true });
      });
      tab.addEventListener("keydown", ev => {
        const idx = tabs.indexOf(tab);
        let next = -1;
        if (ev.key === "ArrowRight") next = (idx + 1) % tabs.length;
        else if (ev.key === "ArrowLeft") next = (idx - 1 + tabs.length) % tabs.length;
        else if (ev.key === "Home") next = 0;
        else if (ev.key === "End") next = tabs.length - 1;
        if (next >= 0) {
          ev.preventDefault();
          const nextTab = tabs[next];
          activateTab(nextTab.dataset.tab, { pushHash: true, scrollTop: true });
          nextTab.focus();
        }
      });
    });

    window.addEventListener("hashchange", () => {
      const mapped = resolveTabFromHash(window.location.hash);
      if (mapped) activateTab(mapped);
    });

    document.querySelectorAll('a[href="#top"]').forEach(link => {
      link.addEventListener("click", ev => {
        ev.preventDefault();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });

    const rawHash = window.location.hash;
    const initial = resolveTabFromHash(rawHash) || DEFAULT_TAB;
    activateTab(initial);
    if (rawHash && HASH_TO_TAB[rawHash.toLowerCase()]) {
      const canonical = TABS.find(t => t.id === initial)?.hash;
      if (canonical && rawHash !== canonical) {
        history.replaceState(null, "", canonical);
      }
      window.scrollTo(0, 0);
    }
  }

  function setupFilters() {
    document.querySelectorAll("#market-filters button.segment").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#market-filters button.segment").forEach(b => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        state.market = btn.dataset.market || "ALL";
        render();
      });
    });

    const searchInput = byId("search-input");
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        state.search = searchInput.value.trim();
        render();
      });
    }

    window.addEventListener("keydown", e => {
      const tag = document.activeElement?.tagName;
      if (e.key === "/" && state.activeTab !== "performance" && document.activeElement !== searchInput
          && tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") {
        e.preventDefault();
        searchInput?.focus();
      }
    });

    wireFilter("stage-filter", "stage");
    wireFilter("sector-filter", "sector");
    wireFilter("status-filter", "status");
    wireFilter("verdict-filter", "verdict");

    const sortSelect = byId("sort-select");
    if (sortSelect) {
      sortSelect.addEventListener("change", () => {
        state.sort = { key: sortSelect.value, dir: "asc" };
        render();
      });
    }

    const pipelinePanel = byId("panel-pipeline");
    if (pipelinePanel) {
      pipelinePanel.addEventListener("click", ev => {
        const button = ev.target.closest(".th-sort");
        if (!button) return;
        const key = button.dataset.sortKey;
        const index = Array.from(pipelinePanel.querySelectorAll(".th-sort")).indexOf(button);
        state.sort = state.sort.key === key
          ? { key, dir: state.sort.dir === "asc" ? "desc" : "asc" }
          : { key, dir: "asc" };
        render();
        pipelinePanel.querySelectorAll(".th-sort")[index]?.focus({ preventScroll: true });
      });
    }

    const resetBtn = byId("reset-filters");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        state.market = "ALL"; state.stage = "ALL"; state.sector = "ALL";
        state.status = "ALL"; state.verdict = "ALL"; state.search = "";
        if (searchInput) searchInput.value = "";
        ["stage-filter", "sector-filter", "status-filter", "verdict-filter"].forEach(id => {
          const el = byId(id); if (el) el.value = "ALL";
        });
        document.querySelectorAll("#market-filters button.segment").forEach(b => {
          b.classList.toggle("is-active", b.dataset.market === "ALL");
        });
        render();
      });
    }

    const btnTree = byId("view-mode-tree");
    const btnTable = byId("view-mode-table");
    const treeWrap = byId("pipeline-tree");
    const tableWrap = byId("pipeline-table-wrap");

    if (btnTree && btnTable && treeWrap && tableWrap) {
      btnTree.addEventListener("click", () => {
        state.viewMode = "tree";
        btnTree.classList.add("is-active");
        btnTable.classList.remove("is-active");
        treeWrap.hidden = false;
        tableWrap.hidden = true;
      });
      btnTable.addEventListener("click", () => {
        state.viewMode = "table";
        btnTable.classList.add("is-active");
        btnTree.classList.remove("is-active");
        treeWrap.hidden = true;
        tableWrap.hidden = false;
      });
    }

    const toggleAllBtn = byId("toggle-all-branches");
    if (toggleAllBtn) {
      toggleAllBtn.addEventListener("click", () => {
        const branches = document.querySelectorAll(".accordion-branch");
        const allOpen = Array.from(branches).every(b => b.open);
        const targetOpen = !allOpen;
        branches.forEach(b => { b.open = targetOpen; });
        updateToggleAllButton();
      });
    }

    document.addEventListener("toggle", event => {
      if (event.target && event.target.classList && event.target.classList.contains("accordion-branch")) {
        updateToggleAllButton();
      }
    }, { capture: true });
  }

  // ---- Portfolio Performance, Timelines & XIRR ----
  const PERIOD_KEYS = ["1M", "3M", "6M", "1Y", "YTD", "ALL"];

  function fmtMoney(val, currency, signed = false) {
    if (val === null || val === undefined || !Number.isFinite(val)) return "—";
    const abs = Math.abs(val);
    const locale = currency === "INR" ? "en-IN" : "en-US";
    const sym = currency === "INR" ? "₹" : "$";
    const formatted = abs.toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (signed) {
      return (val >= 0 ? "+" : "-") + sym + formatted;
    }
    return (val < 0 ? "-" : "") + sym + formatted;
  }

  function fmtCompactMoney(val, currency) {
    if (val === null || val === undefined || !Number.isFinite(val)) return "—";
    const sign = val < 0 ? "-" : "";
    const abs = Math.abs(val);
    const sym = currency === "INR" ? "₹" : "$";
    if (currency === "INR") {
      if (abs >= 1e7) return `${sign}${sym}${(abs / 1e7).toFixed(2)}Cr`;
      if (abs >= 1e5) return `${sign}${sym}${(abs / 1e5).toFixed(1)}L`;
      if (abs >= 1e3) return `${sign}${sym}${(abs / 1e3).toFixed(0)}k`;
      return `${sign}${sym}${abs.toFixed(0)}`;
    }
    if (abs >= 1e6) return `${sign}${sym}${(abs / 1e6).toFixed(2)}M`;
    if (abs >= 1e3) return `${sign}${sym}${(abs / 1e3).toFixed(1)}k`;
    return `${sign}${sym}${abs.toFixed(0)}`;
  }

  function fmtPct(val, signed = true) {
    if (val === null || val === undefined || !Number.isFinite(val)) return "N/A";
    const pct = (val * 100).toFixed(2);
    return signed && val > 0 ? `+${pct}%` : `${pct}%`;
  }

  function buildTimelineChart(containerId, readoutId, points, seriesConfigs, currency, zeroLine = false) {
    const container = byId(containerId);
    const readout = byId(readoutId);
    if (!container || !points.length) {
      if (container) container.innerHTML = `<p class="branch-empty">No timeline data for this window.</p>`;
      return;
    }

    const W = 560, H = 220;
    const pad = { top: 14, right: 16, bottom: 28, left: 62 };
    const pw = W - pad.left - pad.right;
    const ph = H - pad.top - pad.bottom;

    let minY = Infinity, maxY = -Infinity;
    for (const pt of points) {
      for (const s of seriesConfigs) {
        const v = s.getValue(pt);
        if (Number.isFinite(v)) {
          if (v < minY) minY = v;
          if (v > maxY) maxY = v;
        }
      }
    }
    if (zeroLine) {
      minY = Math.min(minY, 0);
      maxY = Math.max(maxY, 0);
    }
    if (!Number.isFinite(minY) || !Number.isFinite(maxY)) return;
    if (Math.abs(maxY - minY) < 1e-6) {
      minY -= 1;
      maxY += 1;
    } else {
      const span = maxY - minY;
      minY -= span * 0.06;
      maxY += span * 0.06;
    }

    const xFor = i => pad.left + (points.length === 1 ? pw / 2 : (i / (points.length - 1)) * pw);
    const yFor = v => pad.top + ((maxY - v) / (maxY - minY)) * ph;

    // Y gridlines (4 ticks)
    let gridSvg = "";
    for (let t = 0; t <= 4; t++) {
      const v = minY + ((maxY - minY) * t) / 4;
      const y = yFor(v).toFixed(1);
      gridSvg += `<line x1="${pad.left}" y1="${y}" x2="${W - pad.right}" y2="${y}" stroke="#e2e8f0" stroke-width="1"/>`;
      gridSvg += `<text x="${pad.left - 6}" y="${Number(y) + 3}" text-anchor="end" font-size="10" fill="#64748b">${escapeHtml(fmtCompactMoney(v, currency))}</text>`;
    }

    // Zero baseline if requested
    if (zeroLine && minY < 0 && maxY > 0) {
      const zy = yFor(0).toFixed(1);
      gridSvg += `<line x1="${pad.left}" y1="${zy}" x2="${W - pad.right}" y2="${zy}" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="3,3"/>`;
    }

    // X ticks (start, mid, end)
    const xTicks = points.length === 1 ? [0] : [0, Math.floor((points.length - 1) / 2), points.length - 1];
    let xSvg = "";
    for (const idx of xTicks) {
      const x = xFor(idx).toFixed(1);
      const anchor = idx === 0 ? "start" : idx === points.length - 1 ? "end" : "middle";
      xSvg += `<text x="${x}" y="${H - 8}" text-anchor="${anchor}" font-size="10" fill="#64748b">${escapeHtml(points[idx].date)}</text>`;
    }

    // Series paths
    let pathsSvg = "";
    for (const s of seriesConfigs) {
      const coords = points.map((pt, i) => `${xFor(i).toFixed(1)},${yFor(s.getValue(pt)).toFixed(1)}`);
      const dPath = `M ${coords.join(" L ")}`;
      const color = s.dynamicColor ? s.dynamicColor(points[points.length - 1]) : s.color;
      if (s.fill && points.length > 1) {
        const baseY = zeroLine ? yFor(0).toFixed(1) : (pad.top + ph).toFixed(1);
        const areaD = `${dPath} L ${xFor(points.length - 1).toFixed(1)},${baseY} L ${xFor(0).toFixed(1)},${baseY} Z`;
        pathsSvg += `<path d="${areaD}" fill="${color}" fill-opacity="0.11"/>`;
      }
      pathsSvg += `<path d="${dPath}" fill="none" stroke="${color}" stroke-width="${s.width || 2}"${s.dashed ? ' stroke-dasharray="5,4"' : ""}/>`;
    }

    const uid = containerId.replace(/[^a-zA-Z0-9_-]/g, "");
    const dotsSvg = seriesConfigs.map((s, idx) => {
      const color = s.dynamicColor ? s.dynamicColor(points[points.length - 1]) : s.color;
      return `<circle id="${uid}-dot-${idx}" r="4" fill="${color}" stroke="#ffffff" stroke-width="1.5" style="display:none"/>`;
    }).join("");

    container.innerHTML = `
      <svg class="perf-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${escapeHtml(seriesConfigs.map(s => s.label).join(" and "))} chart">
        ${gridSvg}
        ${xSvg}
        ${pathsSvg}
        <line id="${uid}-cross" x1="0" y1="${pad.top}" x2="0" y2="${pad.top + ph}" stroke="#475569" stroke-width="1" stroke-dasharray="2,2" style="display:none"/>
        ${dotsSvg}
        <rect id="${uid}-hit" x="${pad.left}" y="${pad.top}" width="${pw}" height="${ph}" fill="transparent"/>
      </svg>
    `;

    const showAt = idx => {
      const pt = points[idx];
      if (!pt) return;
      if (readout) {
        readout.innerHTML = `<strong>${escapeHtml(pt.date)}</strong>` + seriesConfigs.map(s => {
          const val = s.getValue(pt);
          const cls = s.signed ? (val >= 0 ? "perf-pos" : "perf-neg") : "";
          return `<span>${escapeHtml(s.label)}: <strong class="${cls}">${escapeHtml(fmtMoney(val, currency, Boolean(s.signed)))}</strong></span>`;
        }).join("");
      }
    };

    showAt(points.length - 1);

    const hit = byId(`${uid}-hit`);
    const cross = byId(`${uid}-cross`);
    if (hit && cross) {
      const svgEl = container.querySelector("svg");
      hit.addEventListener("pointermove", ev => {
        const rect = svgEl.getBoundingClientRect();
        const svgX = ((ev.clientX - rect.left) / rect.width) * W;
        const ratio = Math.max(0, Math.min(1, (svgX - pad.left) / pw));
        const idx = Math.round(ratio * (points.length - 1));
        const xPos = xFor(idx).toFixed(1);
        cross.setAttribute("x1", xPos);
        cross.setAttribute("x2", xPos);
        cross.style.display = "block";
        seriesConfigs.forEach((s, sIdx) => {
          const dot = byId(`${uid}-dot-${sIdx}`);
          if (dot) {
            dot.setAttribute("cx", xPos);
            dot.setAttribute("cy", yFor(s.getValue(points[idx])).toFixed(1));
            dot.style.display = "block";
          }
        });
        showAt(idx);
      });
      hit.addEventListener("pointerleave", () => {
        cross.style.display = "none";
        seriesConfigs.forEach((_, sIdx) => {
          const dot = byId(`${uid}-dot-${sIdx}`);
          if (dot) dot.style.display = "none";
        });
        showAt(points.length - 1);
      });
    }
  }

  function renderPerformance() {
    const perf = state.perf;
    const panel = byId("perf-panel");
    const tablist = byId("perf-tablist");
    const periodBar = byId("perf-periods");
    const metaEl = byId("perf-meta");
    if (!perf || !Array.isArray(perf.profiles) || !perf.profiles.length || !panel || !tablist) {
      if (metaEl) metaEl.textContent = "Performance data unavailable";
      return;
    }

    if (!state.perfProfileId || !perf.profiles.some(p => p.id === state.perfProfileId)) {
      state.perfProfileId = perf.profiles[0].id;
    }
    const profile = perf.profiles.find(p => p.id === state.perfProfileId);
    const cur = profile.currency;
    const sum = profile.summary;
    const pKey = PERIOD_KEYS.includes(state.perfPeriod) ? state.perfPeriod : "1Y";
    const period = profile.periods[pKey] || profile.periods["ALL"];

    if (metaEl) {
      metaEl.textContent = `As of ${profile.asOf} • ${profile.market} (${cur})`;
    }

    // Render Profile Tabs
    tablist.innerHTML = perf.profiles.map(p => {
      const selected = p.id === profile.id;
      return `<button type="button" class="perf-tab" role="tab" id="tab-${escapeHtml(p.id)}" aria-selected="${selected}"${selected ? ' tabindex="0"' : ' tabindex="-1"'} data-profile="${escapeHtml(p.id)}">${escapeHtml(p.name)}<span class="perf-tab-cur">${escapeHtml(p.currency)}</span></button>`;
    }).join("");

    tablist.querySelectorAll(".perf-tab").forEach(btn => {
      btn.addEventListener("click", () => {
        state.perfProfileId = btn.dataset.profile;
        renderPerformance();
      });
      btn.addEventListener("keydown", ev => {
        const tabs = Array.from(tablist.querySelectorAll(".perf-tab"));
        const i = tabs.indexOf(btn);
        let next = -1;
        if (ev.key === "ArrowRight") next = (i + 1) % tabs.length;
        else if (ev.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
        else if (ev.key === "Home") next = 0;
        else if (ev.key === "End") next = tabs.length - 1;
        if (next >= 0) {
          ev.preventDefault();
          state.perfProfileId = tabs[next].dataset.profile;
          renderPerformance();
          byId(`tab-${state.perfProfileId}`)?.focus();
        }
      });
    });

    // Render Period Buttons
    if (periodBar) {
      periodBar.innerHTML = PERIOD_KEYS.map(k =>
        `<button type="button" class="perf-period-btn${k === pKey ? " is-active" : ""}" data-period="${k}">${k}</button>`
      ).join("");
      periodBar.querySelectorAll(".perf-period-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          state.perfPeriod = btn.dataset.period;
          renderPerformance();
        });
      });
    }

    // KPI Cards
    const overallCls = sum.overallNetPnl >= 0 ? "is-positive" : "is-negative";
    const overallValCls = sum.overallNetPnl >= 0 ? "pos" : "neg";
    const periodCls = period.equityPnl >= 0 ? "is-positive" : "is-negative";
    const periodValCls = period.equityPnl >= 0 ? "pos" : "neg";
    const showXirr = Boolean(period.xirrEligible);
    const annualized = showXirr ? (period.accountXirr ?? period.equityXirr) : null;
    const headlineVal = showXirr ? annualized : period.returnPct;
    const hasHeadline = headlineVal !== null && headlineVal !== undefined;
    const headlineCls = hasHeadline ? (headlineVal >= 0 ? "is-positive" : "is-negative") : "";
    const headlineValCls = hasHeadline ? (headlineVal >= 0 ? "pos" : "neg") : "";
    const headlineLabel = showXirr ? `${pKey} XIRR (Annualized)` : `${pKey} Return (Not Annualized)`;
    const headlineSub = showXirr
      ? (profile.hasDatedDeposits && period.accountXirr !== null ? `Equity XIRR: ${fmtPct(period.equityXirr)}` : "Equity buy/sell cashflow XIRR")
      : "Under one year invested, so no annualized rate";
    const overallSub = [
      `Return: ${fmtPct(sum.overallReturnOnCapital)}`,
      `Equity P&L: ${fmtMoney(sum.equityTotalPnl, cur, true)}`,
      ...(Math.abs(sum.closedPosCash) > 0.005 ? [`Closed-position cash: ${fmtMoney(sum.closedPosCash, cur, true)}`] : []),
      ...(Math.abs(sum.optionsPnl) > 0.005 ? [`Options P&L: ${fmtMoney(sum.optionsPnl, cur, true)}`] : []),
    ].join(" • ");
    const benchSub = [
      `${period.startDate} → ${period.endDate}`,
      ...(period.benchmarkCagr !== null && period.benchmarkCagr !== undefined ? [`CAGR ${fmtPct(period.benchmarkCagr)}`] : []),
    ].join(" • ");

    const kpisHtml = `
      <div class="perf-kpi-grid">
        <div class="perf-kpi-card">
          <div class="perf-kpi-label">Current Account Value</div>
          <div class="perf-kpi-value">${escapeHtml(fmtMoney(sum.totalAccountValue, cur))}</div>
          <div class="perf-kpi-sub">${escapeHtml(`Equities ${fmtMoney(sum.equityMarketValue, cur)} + Cash ${fmtMoney(sum.cash, cur)}${sum.optionsMarketValue ? ` + Options ${fmtMoney(sum.optionsMarketValue, cur)}` : ""}`)}</div>
        </div>
        <div class="perf-kpi-card">
          <div class="perf-kpi-label">${escapeHtml(profile.capitalLabel || "Total Money Put In")}</div>
          <div class="perf-kpi-value">${escapeHtml(fmtMoney(sum.capitalPutIn, cur))}</div>
          <div class="perf-kpi-sub">${escapeHtml(`Open Cost Basis: ${fmtMoney(sum.openCostBasis, cur)}`)}</div>
        </div>
        <div class="perf-kpi-card ${overallCls}">
          <div class="perf-kpi-label">Overall P&amp;L vs Put In</div>
          <div class="perf-kpi-value ${overallValCls}">${escapeHtml(fmtMoney(sum.overallNetPnl, cur, true))}</div>
          <div class="perf-kpi-sub">${escapeHtml(overallSub)}</div>
        </div>
        <div class="perf-kpi-card ${periodCls}">
          <div class="perf-kpi-label">${escapeHtml(pKey)} Active Equity P&amp;L</div>
          <div class="perf-kpi-value ${periodValCls}">${escapeHtml(fmtMoney(period.equityPnl, cur, true))}</div>
          <div class="perf-kpi-sub">${escapeHtml(`Realized ${fmtMoney(period.realizedPnl, cur, true)} • Unrealized ${fmtMoney(period.unrealizedPnl, cur, true)}`)}</div>
        </div>
        <div class="perf-kpi-card ${headlineCls}">
          <div class="perf-kpi-label">${escapeHtml(headlineLabel)}</div>
          <div class="perf-kpi-value ${headlineValCls}">${escapeHtml(fmtPct(headlineVal))}</div>
          <div class="perf-kpi-sub">${escapeHtml(headlineSub)}</div>
        </div>
        <div class="perf-kpi-card">
          <div class="perf-kpi-label">${escapeHtml(pKey)} ${escapeHtml(period.benchmarkLabel || "Benchmark")}</div>
          <div class="perf-kpi-value ${period.benchmarkReturn !== null && period.benchmarkReturn >= 0 ? "pos" : period.benchmarkReturn !== null ? "neg" : ""}">${escapeHtml(fmtPct(period.benchmarkReturn))}</div>
          <div class="perf-kpi-sub">${escapeHtml(benchSub)}</div>
        </div>
      </div>
    `;

    // Window P&L at date t, matching the KPI: equity value less window-start value less net purchases since window start
    const rawPts = (profile.timeline || []).filter(pt => pt.date >= period.startDate && pt.date <= period.endDate);
    const chartPts = rawPts.map(pt => ({
      ...pt,
      windowActivePnl: pt.equityMv - period.startEquityMv
        - ((pt.cumBuys - period.baseBuys) - (pt.cumSells - period.baseSells)),
    }));

    const xirrText = (val, eligible) => (!eligible ? "<1Y" : (val === null || val === undefined ? "N/A" : fmtPct(val)));
    const periodRowsHtml = PERIOD_KEYS.map(k => {
      const m = profile.periods[k];
      if (!m) return "";
      const cls = v => (v >= 0 ? "perf-pos" : "perf-neg");
      const eqXCls = m.equityXirr !== null && m.xirrEligible ? cls(m.equityXirr) : "";
      const acXCls = m.accountXirr !== null && m.xirrEligible ? cls(m.accountXirr) : "";
      const bmCls = m.benchmarkReturn !== null ? cls(m.benchmarkReturn) : "";
      return `<tr class="perf-period-row${k === pKey ? " is-selected" : ""}" data-period="${k}">
        <td><strong>${k}</strong></td>
        <td>${escapeHtml(m.startDate)} &rarr; ${escapeHtml(m.endDate)}</td>
        <td class="perf-num ${cls(m.equityPnl)}">${escapeHtml(fmtMoney(m.equityPnl, cur, true))}</td>
        <td class="perf-num">${escapeHtml(fmtMoney(m.realizedPnl, cur, true))}</td>
        <td class="perf-num">${escapeHtml(fmtMoney(m.unrealizedPnl, cur, true))}</td>
        <td class="perf-num">${escapeHtml(fmtMoney(m.closedPosCash, cur, true))}</td>
        <td class="perf-num ${cls(m.netPnl)}">${escapeHtml(fmtMoney(m.netPnl, cur, true))}</td>
        <td class="perf-num ${m.returnPct !== null ? cls(m.returnPct) : ""}">${escapeHtml(fmtPct(m.returnPct))}</td>
        <td class="perf-num ${eqXCls}">${escapeHtml(xirrText(m.equityXirr, m.xirrEligible))}</td>
        <td class="perf-num ${acXCls}">${escapeHtml(xirrText(m.accountXirr, m.xirrEligible))}</td>
        <td class="perf-num ${bmCls}">${escapeHtml(fmtPct(m.benchmarkReturn))}</td>
      </tr>`;
    }).join("");

    const holdingsRowsHtml = (profile.holdings || []).map(h => {
      const uCls = h.unrealizedPnl >= 0 ? "perf-pos" : "perf-neg";
      const rCls = h.realizedPnl >= 0 ? "perf-pos" : "perf-neg";
      return `<tr>
        <td><strong>${escapeHtml(h.symbol)}</strong></td>
        <td class="perf-num">${escapeHtml(fmtMoney(h.costBasis, cur))}</td>
        <td class="perf-num">${escapeHtml(fmtMoney(h.marketValue, cur))}</td>
        <td class="perf-num ${uCls}">${escapeHtml(fmtMoney(h.unrealizedPnl, cur, true))}</td>
        <td class="perf-num ${uCls}">${escapeHtml(fmtPct(h.unrealizedPct))}</td>
        <td class="perf-num ${rCls}">${escapeHtml(fmtMoney(h.realizedPnl, cur, true))}</td>
      </tr>`;
    }).join("");

    const optionPositions = (profile.optionsBook && profile.optionsBook.positions) || [];
    const optionsRowsHtml = optionPositions.map(o => {
      const uCls = o.unrealizedPnl >= 0 ? "perf-pos" : "perf-neg";
      return `<tr>
        <td><strong>${escapeHtml(o.contract)}</strong></td>
        <td>${escapeHtml(o.type)}</td>
        <td>${escapeHtml(o.expiry)}</td>
        <td class="perf-num">${escapeHtml(String(o.contracts))}</td>
        <td class="perf-num">${escapeHtml(fmtMoney(o.costBasis, cur))}</td>
        <td class="perf-num">${escapeHtml(fmtMoney(o.marketValue, cur))}</td>
        <td class="perf-num ${uCls}">${escapeHtml(fmtMoney(o.unrealizedPnl, cur, true))}</td>
        <td class="perf-num ${uCls}">${escapeHtml(fmtPct(o.unrealizedPct))}</td>
      </tr>`;
    }).join("");
    const optionsHtml = optionPositions.length ? `
      <details class="perf-holdings-details">
        <summary>${escapeHtml(`Options Book, recorded marks (${optionPositions.length} contracts • Value ${fmtMoney(sum.optionsMarketValue, cur)} • Cost ${fmtMoney(sum.optionsCostBasis, cur)} • Unrealized ${fmtMoney(sum.optionsUnrealizedPnl, cur, true)})`)}</summary>
        <div class="perf-holdings-body">
          <div class="pipeline-scroll" role="region" tabindex="0" aria-label="Options book">
            <table class="pipeline-table">
              <thead>
                <tr>
                  <th scope="col">Contract</th>
                  <th scope="col">Type</th>
                  <th scope="col">Expiry</th>
                  <th scope="col" class="perf-num">Contracts</th>
                  <th scope="col" class="perf-num">Cost Basis</th>
                  <th scope="col" class="perf-num">Recorded Value</th>
                  <th scope="col" class="perf-num">Unrealized P&amp;L</th>
                  <th scope="col" class="perf-num">Return %</th>
                </tr>
              </thead>
              <tbody>${optionsRowsHtml}</tbody>
            </table>
          </div>
        </div>
      </details>` : "";

    const notes = [...(profile.notes || [])];
    if (profile.equityFirstTradeDate) {
      notes.unshift(`Equity trades in the export begin ${profile.equityFirstTradeDate}; windows that start earlier are measured from that first trade.`);
    }
    if ((period.missingStartMarks || []).length) {
      notes.push(`${pKey} start-date price is missing for ${period.missingStartMarks.join(", ")}; cost basis is used for those shares in this window.`);
    }
    const notesHtml = notes.length
      ? `<ul class="perf-notes">${notes.map(n => `<li>${escapeHtml(n)}</li>`).join("")}</ul>`
      : "";

    panel.innerHTML = `
      ${kpisHtml}
      <div class="perf-charts-grid">
        <div class="perf-chart-card">
          <div class="perf-chart-head">
            <h3 class="perf-chart-title">Equity Value vs. Cost Basis (${escapeHtml(pKey)})</h3>
            <div class="perf-chart-legend">
              <span><i class="legend-dot" style="background:#174a61"></i>Equity Value</span>
              <span><i class="legend-dot" style="background:#b87333"></i>Cost Basis</span>
            </div>
          </div>
          <div class="perf-chart-readout" id="perf-readout-val"></div>
          <div class="perf-svg-wrap" id="perf-chart-val"></div>
        </div>
        <div class="perf-chart-card">
          <div class="perf-chart-head">
            <h3 class="perf-chart-title">${escapeHtml(pKey)} Active Equity P&amp;L Timeline</h3>
            <div class="perf-chart-legend">
              <span><i class="legend-dot" style="background:${period.equityPnl >= 0 ? "#145a32" : "#9e2a2b"}"></i>Cumulative P&amp;L</span>
            </div>
          </div>
          <div class="perf-chart-readout" id="perf-readout-pnl"></div>
          <div class="perf-svg-wrap" id="perf-chart-pnl"></div>
        </div>
      </div>

      <div class="pipeline-scroll perf-period-table-wrap" role="region" tabindex="0" aria-label="P&amp;L and returns across periods">
        <table class="pipeline-table">
          <thead>
            <tr>
              <th scope="col">Period</th>
              <th scope="col">Window</th>
              <th scope="col" class="perf-num">Active Equity P&amp;L</th>
              <th scope="col" class="perf-num">Realized</th>
              <th scope="col" class="perf-num">Unrealized</th>
              <th scope="col" class="perf-num">Closed-Pos Cash</th>
              <th scope="col" class="perf-num">Net P&amp;L</th>
              <th scope="col" class="perf-num">Return</th>
              <th scope="col" class="perf-num">Equity XIRR</th>
              <th scope="col" class="perf-num">Account XIRR</th>
              <th scope="col" class="perf-num">${escapeHtml(profile.benchmarkLabel || "Benchmark")}</th>
            </tr>
          </thead>
          <tbody>${periodRowsHtml}</tbody>
        </table>
      </div>

      <details class="perf-holdings-details">
        <summary>Open Positions P&amp;L Breakdown (${(profile.holdings || []).length} symbols &bull; Realized ${escapeHtml(fmtMoney(sum.equityRealizedPnl, cur, true))} &bull; Unrealized ${escapeHtml(fmtMoney(sum.unrealizedPnl, cur, true))})</summary>
        <div class="perf-holdings-body">
          <div class="pipeline-scroll" role="region" tabindex="0" aria-label="Open positions P&amp;L">
            <table class="pipeline-table">
              <thead>
                <tr>
                  <th scope="col">Symbol</th>
                  <th scope="col" class="perf-num">Cost Basis</th>
                  <th scope="col" class="perf-num">Market Value</th>
                  <th scope="col" class="perf-num">Unrealized P&amp;L</th>
                  <th scope="col" class="perf-num">Return %</th>
                  <th scope="col" class="perf-num">Realized P&amp;L</th>
                </tr>
              </thead>
              <tbody>${holdingsRowsHtml}</tbody>
            </table>
          </div>
        </div>
      </details>

      ${optionsHtml}

      ${notesHtml}
    `;

    panel.querySelectorAll(".perf-period-row").forEach(row => {
      row.addEventListener("click", () => {
        state.perfPeriod = row.dataset.period;
        renderPerformance();
      });
    });

    buildTimelineChart(
      "perf-chart-val",
      "perf-readout-val",
      chartPts,
      [
        { label: "Equity Value", color: "#174a61", width: 2.2, fill: true, getValue: pt => pt.equityMv },
        { label: "Cost Basis", color: "#b87333", width: 1.8, dashed: true, getValue: pt => pt.costBasis },
      ],
      cur,
      false
    );

    buildTimelineChart(
      "perf-chart-pnl",
      "perf-readout-pnl",
      chartPts,
      [
        {
          label: `${pKey} Active P&L`,
          color: "#145a32",
          dynamicColor: last => (last.windowActivePnl >= 0 ? "#145a32" : "#9e2a2b"),
          width: 2.2,
          fill: true,
          signed: true,
          getValue: pt => pt.windowActivePnl,
        },
      ],
      cur,
      true
    );
  }

  async function init() {
    setupTabs();
    setupFilters();
    const metaEl = byId("catalog-meta");

    try {
      const [catRes, perfRes] = await Promise.allSettled([
        fetch(`portal-data.json?t=${Date.now()}`, { cache: "no-store" }),
        fetch(`portal-performance.json?t=${Date.now()}`, { cache: "no-store" }),
      ]);

      if (catRes.status !== "fulfilled" || !catRes.value.ok) {
        throw new Error(`HTTP ${catRes.status === "fulfilled" ? catRes.value.status : "network"}`);
      }
      const data = await catRes.value.json();
      state.entries = Array.isArray(data.entries) ? data.entries : [];
      state.queues = data.queues || null;
      state.holdings = data.holdings || {};

      if (metaEl) {
        metaEl.textContent = `Catalog updated: ${formatDateTime(data.generatedAt || new Date())} • ${state.entries.length} published pages`;
      }

      populateFilters(buildPipeline());
      render();

      if (perfRes.status === "fulfilled" && perfRes.value.ok) {
        state.perf = await perfRes.value.json();
        renderPerformance();
      } else {
        const pMeta = byId("perf-meta");
        if (pMeta) pMeta.textContent = "Run scripts/build_performance.py to populate";
      }
    } catch (err) {
      console.error("Failed to load catalog:", err);
      if (metaEl) metaEl.textContent = "Catalog offline. Refresh to retry.";
      const emptyState = byId("empty-state");
      if (emptyState) emptyState.hidden = false;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
