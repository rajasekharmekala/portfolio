"use strict";

(() => {
  const byId = id => document.getElementById(id);
  const state = {
    entries: [],
    queues: null,
    market: "ALL",
    verdict: "ALL",
    sort: "updated",
    search: "",
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
      month: "short",
      day: "numeric",
      year: "numeric",
      timeZone: "America/Los_Angeles",
    }).format(d);
  }

  function formatDateTime(value) {
    if (!value) return "Latest";
    const d = new Date(value);
    if (!Number.isFinite(d.getTime())) return "Latest";
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short",
      timeZone: "America/Los_Angeles",
    }).format(d);
  }

  function verdictClass(v) {
    if (!v || v === "Not specified") return "verdict-neutral";
    const upper = v.toUpperCase();
    if (upper.includes("BUY") || upper.includes("ACCUMULATE") || upper.includes("COMPOUND") || upper.includes("PASSED")) {
      return "verdict-good";
    }
    if (upper.includes("WAIT") || upper.includes("TRIM") || upper.includes("REPLACE") || upper.includes("HOLD") || upper.includes("WATCH")) {
      return "verdict-warn";
    }
    if (upper.includes("REJECT") || upper.includes("AVOID") || upper.includes("STAGE 4") || upper.includes("FAIL")) {
      return "verdict-bad";
    }
    return "verdict-neutral";
  }

  function filterEntries() {
    return state.entries.filter(e => {
      if (state.market !== "ALL" && e.market !== state.market) return false;
      if (state.verdict !== "ALL" && e.verdict !== state.verdict) return false;
      if (state.search) {
        const q = state.search.toLowerCase();
        const text = [
          e.title,
          e.symbol,
          e.market,
          e.workflow,
          e.verdict,
          e.summary,
          e.sector,
        ].join(" ").toLowerCase();
        if (!text.includes(q)) return false;
      }
      return true;
    });
  }

  function sortEntries(list) {
    const sorted = [...list];
    if (state.sort === "symbol") {
      sorted.sort((a, b) => (a.symbol || a.title).localeCompare(b.symbol || b.title));
    } else if (state.sort === "title") {
      sorted.sort((a, b) => a.title.localeCompare(b.title));
    } else {
      sorted.sort((a, b) => (b.updatedAt || b.generatedAt || "").localeCompare(a.updatedAt || a.generatedAt || ""));
    }
    return sorted;
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
    const sub = e.sector && e.sector !== "Not specified" ? e.sector : "Stage 2 Leader";
    const bookBadge = e.bookUrl
      ? ` <span class="symbol-pill" role="link" tabindex="0" title="Open Audiobook &amp; Book Edition" onclick="event.preventDefault(); event.stopPropagation(); window.location.href='${escapeHtml(e.bookUrl)}'">Book / Audio</span>`
      : "";
    const epubBadge = e.epubUrl
      ? ` <span class="symbol-pill" role="link" tabindex="0" title="Download EPUB 3 E-Book" onclick="event.preventDefault(); event.stopPropagation(); window.location.href='${escapeHtml(e.epubUrl)}'">EPUB</span>`
      : "";
    return `
      <a class="dossier-row" href="${escapeHtml(e.url)}">
        <div class="dossier-code">
          <span class="market-pill market-${escapeHtml(e.market)}">${escapeHtml(e.market)}</span>
          <span class="symbol-pill">${escapeHtml(e.symbol || e.title.slice(0, 8))}</span>
        </div>
        <div>
          <div class="dossier-title">${escapeHtml(e.symbol || e.title)}${bookBadge}${epubBadge}</div>
          <div class="dossier-sub">${escapeHtml(sub)}</div>
        </div>
        <p class="dossier-summary">${escapeHtml(e.summary || e.title)}</p>
        <div>
          ${hasVerdict ? `<span class="verdict-pill ${verdictClass(e.verdict)}">${escapeHtml(e.verdict)}</span>` : ""}
        </div>
        <div class="dossier-date">${escapeHtml(formatDate(e.updatedAt || e.generatedAt))}</div>
      </a>
    `;
  }

  function queueMatch(row) {
    if (state.verdict !== "ALL" && row.verdict !== state.verdict) return false;
    if (!state.search) return true;
    return [row.symbol, row.company, row.status, row.verdict, row.gateStatus]
      .join(" ").toLowerCase().includes(state.search.toLowerCase());
  }

  function queueSymbol(row) {
    const symbol = escapeHtml(row.symbol);
    const safe = /^blogs\/(IN|US)\/[A-Za-z0-9._-]+_dossier\.html$/.test(row.dossierUrl || "");
    return safe ? `<a href="${escapeHtml(row.dossierUrl)}">${symbol}</a>` : symbol;
  }

  function queueTable(market, kind, data) {
    const label = kind === "watchlist" ? "Watchlist" : "Shortlist";
    if (!data || !data.available || !Array.isArray(data.rows)) return `<p class="queue-empty">${label} data unavailable.</p>`;
    const rows = data.rows.filter(queueMatch);
    if (!data.rows.length) return `<p class="queue-empty">No active ${label.toLowerCase()} names.</p>`;
    if (!rows.length) return `<p class="queue-empty">No ${label.toLowerCase()} names match these filters.</p>`;
    const headings = kind === "watchlist"
      ? "<th scope=\"col\">Stock</th><th scope=\"col\">Cycle</th><th scope=\"col\">Status</th><th scope=\"col\">Queue</th><th scope=\"col\">Last researched</th>"
      : "<th scope=\"col\">Stock</th><th scope=\"col\">Decision</th><th scope=\"col\">Gate</th><th scope=\"col\">As of</th>";
    const body = rows.map(row => {
      const name = `<strong>${queueSymbol(row)}</strong><span class="queue-company">${escapeHtml(row.company)}</span>`;
      if (kind === "watchlist") {
        const tone = row.status === "Completed" ? "verdict-good" : row.status === "Pending" ? "verdict-warn" : "verdict-neutral";
        return `<tr><td>${name}</td><td>${escapeHtml(row.cycle)}</td><td><span class="verdict-pill ${tone}">${escapeHtml(row.status)}</span></td><td>${escapeHtml(row.queuePosition ?? "—")}</td><td>${escapeHtml(row.lastResearched || "—")}</td></tr>`;
      }
      const verdict = row.verdict && row.verdict !== "Not specified" ? row.verdict : "Not specified";
      const gate = row.gateStatus ? row.gateStatus.replace(/_/g, " ") : "Not specified";
      return `<tr><td>${name}</td><td><span class="verdict-pill ${verdictClass(verdict)}">${escapeHtml(verdict)}</span></td><td>${escapeHtml(gate)}</td><td>${escapeHtml(row.asOf || "—")}</td></tr>`;
    }).join("");
    return `<div class="queue-scroll" role="region" tabindex="0" aria-label="${escapeHtml(market)} ${label} table"><table class="queue-table"><caption class="sr-only">${escapeHtml(market)} ${label}</caption><thead><tr>${headings}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  function renderQueues() {
    const root = byId("queue-list");
    const meta = byId("queue-meta");
    if (!root) return;
    if (!state.queues || typeof state.queues !== "object") {
      root.innerHTML = '<p class="queue-empty">Queue status is unavailable until the catalog is rebuilt.</p>';
      if (meta) meta.textContent = "Status unavailable";
      return;
    }
    const markets = ["US", "IN"].filter(m => state.market === "ALL" || state.market === m);
    root.innerHTML = markets.map(market => {
      const group = state.queues[market] || {};
      const watch = group.watchlist;
      const short = group.shortlist;
      const all = watch && watch.available && Array.isArray(watch.rows) ? watch.rows : [];
      const pending = all.filter(row => row.status === "Pending").length;
      const completed = all.filter(row => row.status === "Completed").length;
      const unknown = all.length - pending - completed;
      const cycle = watch && watch.available ? (watch.targetCycle ? `Next target: cycle ${escapeHtml(watch.targetCycle)}${watch.rollover ? " (next round)" : ""}` : "No active cycle") : "Cycle unavailable";
      const count = watch && watch.available && Array.isArray(watch.rows) ? `${pending} pending · ${completed} completed${unknown ? ` · ${unknown} unknown` : ""} total` : "Watchlist unavailable";
      const shortlistCount = short && short.available && Array.isArray(short.rows) ? `${short.rows.length} active total` : "Unavailable";
      return `<section class="queue-market" aria-labelledby="queue-${market}"><div class="queue-market-head"><h3 id="queue-${market}"><span class="market-pill market-${market}">${market}</span> ${market === "US" ? "United States" : "India"}</h3><span>${cycle}</span></div><div class="queue-subhead"><h4>Watchlist</h4><span>${count}</span></div>${queueTable(market, "watchlist", watch)}<div class="queue-subhead"><h4>Shortlist</h4><span>${shortlistCount}</span></div>${queueTable(market, "shortlist", short)}</section>`;
    }).join("");
    if (meta) meta.textContent = "Updated with the published catalog";
  }

  function render() {
    renderQueues();
    const filtered = filterEntries();
    const sorted = sortEntries(filtered);

    const reports = sorted.filter(e => e.kind === "report");
    const dossiers = sorted.filter(e => e.kind === "dossier");
    const recent = sorted.slice(0, 6);

    // Update Stats Hero
    const totalPages = state.entries.length;
    const intelCount = state.entries.filter(e => (e.workflow || "").toLowerCase().includes("intelligence")).length;
    const auditCount = state.entries.filter(e => e.kind === "report" && !(e.workflow || "").toLowerCase().includes("intelligence")).length;
    const monographCount = state.entries.filter(e => e.kind === "dossier").length;

    const statsEl = byId("portal-stats");
    if (statsEl) {
      statsEl.innerHTML = `
        <div><dt>Published</dt><dd>${totalPages} pages</dd></div>
        <div><dt>Market Intel</dt><dd>${intelCount} reports</dd></div>
        <div><dt>Shortlist &amp; Audits</dt><dd>${auditCount} reports</dd></div>
        <div><dt>Monographs</dt><dd>${monographCount} books</dd></div>
      `;
    }

    // Update Section Head Metas
    const recentMeta = byId("recent-meta");
    if (recentMeta) recentMeta.textContent = `Showing ${recent.length} recent publications`;

    const reportMeta = byId("report-meta");
    if (reportMeta) reportMeta.textContent = `${reports.length} workflow reports available`;

    const dossierMeta = byId("dossier-meta");
    if (dossierMeta) dossierMeta.textContent = `${dossiers.length} monograph dossiers available`;

    // Render Lists
    const recentList = byId("recent-list");
    if (recentList) {
      recentList.innerHTML = recent.map(e => renderCard(e, true)).join("");
    }

    const reportList = byId("report-list");
    if (reportList) {
      reportList.innerHTML = reports.map(e => renderCard(e, false)).join("");
    }

    const dossierList = byId("dossier-list");
    if (dossierList) {
      dossierList.innerHTML = dossiers.map(renderDossierRow).join("");
    }

    // Toggle Empty State
    const emptyState = byId("empty-state");
    if (emptyState) {
      emptyState.hidden = sorted.length > 0;
      if (!emptyState.hidden && state.entries.length) {
        emptyState.querySelector("h2").textContent = "No matching publications";
        emptyState.querySelector("p").textContent = "Try another filter; the research queue may still contain matching names.";
      }
    }

    // Toggle Reset Button
    const resetBtn = byId("reset-filters");
    if (resetBtn) {
      const isFiltered = state.market !== "ALL" || state.verdict !== "ALL" || Boolean(state.search);
      resetBtn.hidden = !isFiltered;
    }
  }

  function setupFilters() {
    // Market Segmented Buttons
    document.querySelectorAll("#market-filters button.segment").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#market-filters button.segment").forEach(b => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        state.market = btn.dataset.market || "ALL";
        render();
      });
    });

    // Search Input
    const searchInput = byId("search-input");
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        state.search = searchInput.value.trim();
        render();
      });
    }

    // Global / shortcut key
    window.addEventListener("keydown", e => {
      if (e.key === "/" && document.activeElement !== searchInput) {
        e.preventDefault();
        searchInput?.focus();
      }
    });

    // Verdict Filter
    const verdictSelect = byId("verdict-filter");
    if (verdictSelect) {
      verdictSelect.addEventListener("change", () => {
        state.verdict = verdictSelect.value;
        render();
      });
    }

    // Sort Select
    const sortSelect = byId("sort-select");
    if (sortSelect) {
      sortSelect.addEventListener("change", () => {
        state.sort = sortSelect.value;
        render();
      });
    }

    // Reset Button
    const resetBtn = byId("reset-filters");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        state.market = "ALL";
        state.verdict = "ALL";
        state.search = "";
        if (searchInput) searchInput.value = "";
        if (verdictSelect) verdictSelect.value = "ALL";
        document.querySelectorAll("#market-filters button.segment").forEach(b => {
          b.classList.toggle("is-active", b.dataset.market === "ALL");
        });
        render();
      });
    }
  }

  function populateVerdictDropdown() {
    const select = byId("verdict-filter");
    if (!select) return;
    const verdicts = [...new Set(state.entries.map(e => e.verdict))]
      .filter(v => v && v !== "Not specified")
      .sort();
    select.innerHTML = '<option value="ALL">All verdicts</option>' +
      verdicts.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
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

      if (metaEl) {
        metaEl.textContent = `Catalog updated: ${formatDateTime(data.generatedAt || new Date())} • ${state.entries.length} published pages`;
      }

      populateVerdictDropdown();
      render();
    } catch (err) {
      console.error("Failed to load catalog:", err);
      if (metaEl) {
        metaEl.textContent = "Catalog offline. Refresh to retry.";
      }
      renderQueues();
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
