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
    sort: "market",
    search: "",
    viewMode: "tree",
  };

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
    if (state.status !== "ALL" && !row.statuses.includes(state.status)) return false;
    if (state.verdict !== "ALL" && row.verdict !== state.verdict) return false;
    if (state.search) {
      const q = state.search.toLowerCase();
      const text = [row.symbol, row.company, row.sector, row.verdict, row.stage, row.market]
        .join(" ").toLowerCase();
      if (!text.includes(q)) return false;
    }
    return true;
  }

  function sortPipeline(list) {
    const sorted = [...list];
    const stageRank = { STAGE_2: 0, STAGE_1: 1, STAGE_3: 2, STAGE_4: 3 };
    if (state.sort === "stage") {
      sorted.sort((a, b) =>
        (stageRank[a.stage] ?? 9) - (stageRank[b.stage] ?? 9) ||
        (a.symbol || "").localeCompare(b.symbol || ""));
    } else if (state.sort === "sector") {
      sorted.sort((a, b) =>
        (a.sector || "~").localeCompare(b.sector || "~") ||
        (a.symbol || "").localeCompare(b.symbol || ""));
    } else {
      sorted.sort((a, b) =>
        a.market.localeCompare(b.market) || (a.symbol || "").localeCompare(b.symbol || ""));
    }
    return sorted;
  }

  function renderBranchTable(items, kind) {
    if (!items.length) {
      return `<p class="branch-empty">No ${escapeHtml(kind)} names match the current filters.</p>`;
    }
    const byMarket = {
      IN: items.filter(r => r.market === "IN"),
      US: items.filter(r => r.market === "US"),
    };
    let html = "";
    for (const [mkt, mktItems] of Object.entries(byMarket)) {
      if (!mktItems.length) continue;
      const mktTitle = mkt === "IN" ? "🇮🇳 India Equities (NSE/BSE · Zerodha)" : "🇺🇸 United States Equities (NYSE/NASDAQ · Schwab & Robinhood)";
      html += `
        <div class="market-subgroup">
          <div class="market-subhead">
            <span class="market-subhead-title">${escapeHtml(mktTitle)}</span>
            <span class="market-subhead-count">${mktItems.length} name${mktItems.length === 1 ? "" : "s"}</span>
          </div>
          <div class="pipeline-scroll" role="region" tabindex="0" aria-label="${escapeHtml(kind)} ${escapeHtml(mkt)} table">
            <table class="pipeline-table">
              <thead>
                <tr>
                  <th scope="col">Ticker</th>
                  <th scope="col">Company</th>
                  <th scope="col">Stage</th>
                  <th scope="col">Sector</th>
                  <th scope="col">Verdict</th>
                  <th scope="col">Monograph</th>
                </tr>
              </thead>
              <tbody>
                ${mktItems.map(row => {
                  const company = row.company && row.company !== row.symbol ? escapeHtml(row.company) : "";
                  const tickerLink = row.dossierUrl
                    ? `<a class="pipe-ticker" href="${escapeHtml(row.dossierUrl)}">${escapeHtml(row.symbol)}</a>`
                    : `<span class="pipe-ticker">${escapeHtml(row.symbol)}</span>`;
                  const verdict = row.verdict && row.verdict !== "Not specified"
                    ? `<span class="verdict-pill ${verdictClass(row.verdict)}">${escapeHtml(row.verdict)}</span>`
                    : '<span class="pipe-muted" title="Underwriting pending">—</span>';
                  const mono = row.dossierUrl
                    ? `<a class="pipe-doc" href="${escapeHtml(row.dossierUrl)}">Read &rarr;</a>`
                    : '<span class="pipe-muted">—</span>';
                  return `<tr>
                    <td>${tickerLink}</td>
                    <td class="pipe-company">${company || '<span class="pipe-muted">&mdash;</span>'}</td>
                    <td><span class="stage-pill ${stageClass(row.stage)}">${escapeHtml(stageLabel(row.stage))}</span></td>
                    <td class="pipe-sector">${row.sector ? escapeHtml(row.sector) : '<span class="pipe-muted">&mdash;</span>'}</td>
                    <td>${verdict}</td>
                    <td>${mono}</td>
                  </tr>`;
                }).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }
    return html;
  }

  function renderTree(all) {
    const treeEl = byId("pipeline-tree");
    if (!treeEl) return;

    const filtered = sortPipeline(all.filter(pipelineMatch));

    const watchlistItems = filtered.filter(r => r.statuses.includes("WATCHLIST"));
    const shortlistItems = filtered.filter(r => r.statuses.includes("SHORTLIST"));
    const holdingsItems = filtered.filter(r => r.statuses.includes("HELD"));

    const countW = byId("count-watchlist");
    const countS = byId("count-shortlist");
    const countH = byId("count-holdings");

    if (countW) {
      const inW = watchlistItems.filter(r => r.market === "IN").length;
      const usW = watchlistItems.filter(r => r.market === "US").length;
      countW.textContent = `${watchlistItems.length} names · IN ${inW} · US ${usW}`;
    }
    if (countS) {
      const inS = shortlistItems.filter(r => r.market === "IN").length;
      const usS = shortlistItems.filter(r => r.market === "US").length;
      countS.textContent = `${shortlistItems.length} names · IN ${inS} · US ${usS}`;
    }
    if (countH) {
      const inH = holdingsItems.filter(r => r.market === "IN").length;
      const usH = holdingsItems.filter(r => r.market === "US").length;
      countH.textContent = `${holdingsItems.length} names · IN ${inH} · US ${usH}`;
    }

    const contentW = byId("content-watchlist");
    const contentS = byId("content-shortlist");
    const contentH = byId("content-holdings");

    if (contentW) contentW.innerHTML = renderBranchTable(watchlistItems, "Watchlist");
    if (contentS) contentS.innerHTML = renderBranchTable(shortlistItems, "Shortlist");
    if (contentH) contentH.innerHTML = renderBranchTable(holdingsItems, "Holdings");

    if (state.search || state.status !== "ALL") {
      const bW = byId("branch-watchlist");
      const bS = byId("branch-shortlist");
      const bH = byId("branch-holdings");
      if (bW) bW.open = watchlistItems.length > 0;
      if (bS) bS.open = shortlistItems.length > 0;
      if (bH) bH.open = holdingsItems.length > 0;
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
      const byStatus = s => filtered.filter(r => r.statuses.includes(s)).length;
      counts.textContent = `${filtered.length} names shown · US ${byMarket("US")} · IN ${byMarket("IN")} · Watchlist ${byStatus("WATCHLIST")} · Shortlist ${byStatus("SHORTLIST")} · Held ${byStatus("HELD")}`;
    }
    if (meta) meta.textContent = `${filtered.length} of ${all.length} tracked names`;

    body.innerHTML = filtered.map(row => {
      const company = row.company && row.company !== row.symbol ? escapeHtml(row.company) : "";
      const tickerLink = row.dossierUrl
        ? `<a class="pipe-ticker" href="${escapeHtml(row.dossierUrl)}">${escapeHtml(row.symbol)}</a>`
        : `<span class="pipe-ticker">${escapeHtml(row.symbol)}</span>`;
      const primary = row.status;
      const extra = row.statuses.filter(s => s !== primary);
      const statusTitle = row.statuses.map(statusLabel).join(" · ");
      const statusCell = `<span class="status-pill status-${primary.toLowerCase()}" title="${escapeHtml(statusTitle)}">${statusLabel(primary)}</span>` +
        (extra.length ? ` <span class="status-more" title="${escapeHtml(statusTitle)}">+${extra.length}</span>` : "");
      const verdict = row.verdict && row.verdict !== "Not specified"
        ? `<span class="verdict-pill ${verdictClass(row.verdict)}">${escapeHtml(row.verdict)}</span>`
        : '<span class="pipe-muted" title="Underwriting pending">—</span>';
      const mono = row.dossierUrl
        ? `<a class="pipe-doc" href="${escapeHtml(row.dossierUrl)}">Read &rarr;</a>`
        : '<span class="pipe-muted">—</span>';
      return `<tr>
        <td>${tickerLink}</td>
        <td class="pipe-company">${company || '<span class="pipe-muted">&mdash;</span>'}</td>
        <td><span class="market-pill market-${escapeHtml(row.market)}">${escapeHtml(row.market)}</span></td>
        <td><span class="stage-pill ${stageClass(row.stage)}">${escapeHtml(stageLabel(row.stage))}</span></td>
        <td class="pipe-sector">${row.sector ? escapeHtml(row.sector) : '<span class="pipe-muted">&mdash;</span>'}</td>
        <td>${statusCell}</td>
        <td>${verdict}</td>
        <td>${mono}</td>
      </tr>`;
    }).join("");

    if (emptyNote) {
      const none = filtered.length === 0;
      emptyNote.hidden = !none;
      emptyNote.textContent = none ? "No tracked names match these filters." : "";
    }
  }

  function filterEntries() {
    return state.entries.filter(e => {
      if (state.market !== "ALL" && e.market !== state.market) return false;
      if (state.verdict !== "ALL" && e.verdict !== state.verdict) return false;
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
    const heldTotal = (state.holdings?.US?.length || 0) + (state.holdings?.IN?.length || 0);
    const watchTotal = (state.queues?.US?.watchlist?.rows?.length || 0) + (state.queues?.IN?.watchlist?.rows?.length || 0);
    const shortTotal = (state.queues?.US?.shortlist?.rows?.length || 0) + (state.queues?.IN?.shortlist?.rows?.length || 0);

    statsEl.innerHTML = `
      <div><dt>Tracked</dt><dd>${pipeline.length}</dd></div>
      <div><dt>Watchlist</dt><dd>${watchTotal}</dd></div>
      <div><dt>Shortlist</dt><dd>${shortTotal}</dd></div>
      <div><dt>Held</dt><dd>${heldTotal}</dd></div>
      <div><dt>Monographs</dt><dd>${publishedDossiers}</dd></div>
      <div><dt>Reports</dt><dd>${reports}</dd></div>
    `;
  }

  function render() {
    const pipeline = buildPipeline();
    renderStats(pipeline);
    renderPipeline(pipeline);
    renderTree(pipeline);

    const filteredEntries = filterEntries();
    const reports = filteredEntries.filter(e => e.kind === "report");
    const dossiers = filteredEntries.filter(e => e.kind === "dossier");

    const reportMeta = byId("report-meta");
    if (reportMeta) reportMeta.textContent = `${reports.length} report${reports.length === 1 ? "" : "s"}`;
    const reportList = byId("report-list");
    if (reportList) reportList.innerHTML = reports.map(e => renderCard(e)).join("");

    const dossierMeta = byId("dossier-meta");
    if (dossierMeta) dossierMeta.textContent = `${dossiers.length} monograph${dossiers.length === 1 ? "" : "s"}`;
    const dossierList = byId("dossier-list");
    if (dossierList) dossierList.innerHTML = dossiers.map(renderDossierRow).join("");

    const dossierEmpty = byId("dossier-empty");
    if (dossierEmpty) {
      const none = dossiers.length === 0;
      dossierEmpty.hidden = !none;
      dossierEmpty.textContent = none
        ? "No monographs are published right now; they are being regenerated from scratch under the new evidence-first workflow."
        : "";
    }

    const emptyState = byId("empty-state");
    if (emptyState) emptyState.hidden = state.entries.length > 0;

    const resetBtn = byId("reset-filters");
    if (resetBtn) {
      const isFiltered = state.market !== "ALL" || state.stage !== "ALL" || state.sector !== "ALL"
        || state.status !== "ALL" || state.verdict !== "ALL" || Boolean(state.search);
      resetBtn.hidden = !isFiltered;
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
      if (e.key === "/" && document.activeElement !== searchInput) {
        e.preventDefault();
        searchInput?.focus();
      }
    });

    wireFilter("stage-filter", "stage");
    wireFilter("sector-filter", "sector");
    wireFilter("status-filter", "status");
    wireFilter("verdict-filter", "verdict");
    wireFilter("sort-select", "sort");

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

  async function init() {
    setupFilters();
    const metaEl = byId("catalog-meta");

    try {
      const res = await fetch(`portal-data.json?t=${Date.now()}`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      state.entries = Array.isArray(data.entries) ? data.entries : [];
      state.queues = data.queues || null;
      state.holdings = data.holdings || {};

      if (metaEl) {
        metaEl.textContent = `Catalog updated: ${formatDateTime(data.generatedAt || new Date())} • ${state.entries.length} published pages`;
      }

      populateFilters(buildPipeline());
      render();
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
