"use strict";

(() => {
  const byId = id => document.getElementById(id);
  const state = {
    entries: [],
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
    return `
      <a class="dossier-row" href="${escapeHtml(e.url)}">
        <div class="dossier-code">
          <span class="market-pill market-${escapeHtml(e.market)}">${escapeHtml(e.market)}</span>
          <span class="symbol-pill">${escapeHtml(e.symbol || e.title.slice(0, 8))}</span>
        </div>
        <div>
          <div class="dossier-title">${escapeHtml(e.symbol || e.title)}</div>
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

  function render() {
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
