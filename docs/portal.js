"use strict";
const byId = id => document.getElementById(id);
const state = { entries: [], market: "All", limit: 12, read: {} };
try { state.read = JSON.parse(localStorage.getItem("research-read-v1") || "{}"); } catch { state.read = {}; }
if (!state.read || typeof state.read !== "object" || Array.isArray(state.read)) state.read = {};
const escapeText = value => String(value ?? "").replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character]));
const version = entry => entry.updatedAt || entry.reportDate || "undated";
const unread = entry => state.read[entry.id] !== version(entry);
const dateText = value => value && Number.isFinite(Date.parse(value)) ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Date unavailable";
const safeUrl = value => typeof value === "string" && /^(blogs|reports)\/[A-Za-z0-9_./%& -]+\.html$/.test(value) && !value.includes("..") ? value.split("/").map(part => encodeURIComponent(decodeURIComponent(part))).join("/") : null;
function link(entry, label = entry.title) { return `<a data-entry="${escapeText(entry.id)}" href="${escapeText(safeUrl(entry.url))}">${escapeText(label)}</a>`; }
function stamp(entry) { return `<time title="${escapeText(entry.timestampSource === "workflow" ? "Workflow completion" : entry.timestampSource === "git" ? "Last Git commit" : "No timestamp recorded")}">${escapeText(dateText(entry.updatedAt))}</time>`; }
function filtered() {
  const query = byId("search").value.trim().toLowerCase();
  return state.entries.filter(entry => (state.market === "All" || entry.market === state.market) && [entry.title, entry.symbol, entry.sector, entry.workflow, entry.verdict, entry.summary].join(" ").toLowerCase().includes(query));
}
function activity() {
  const days = byId("period").value;
  return filtered().filter(entry => (!byId("unread-only").checked || unread(entry)) && (days === "all" || (Date.parse(entry.updatedAt) >= Date.now() - Number(days) * 86400000)));
}
function saveRead(entries) {
  entries.forEach(entry => { state.read[entry.id] = version(entry); });
  try { localStorage.setItem("research-read-v1", JSON.stringify(state.read)); } catch { /* Read state remains available for this session. */ }
}
function render() {
  const entries = filtered();
  const recent = activity();
  const visible = recent.slice(0, state.limit);
  const latest = new Map();
  entries.filter(entry => entry.kind === "report").forEach(entry => {
    const key = `${entry.market}:${entry.workflow.toLowerCase()}`;
    if (!latest.has(key)) latest.set(key, entry);
  });
  const metrics = [[entries.length, "Published pages"], [entries.filter(unread).length, "Unread updates"], [entries.filter(entry => Date.parse(entry.updatedAt) >= Date.now() - 86400000).length, "Updated in 24 hours"], [latest.size, "Workflow reports"]];
  byId("metrics").innerHTML = metrics.map(([count, label]) => `<div><strong>${count}</strong><span>${label}</span></div>`).join("");
  byId("recent-list").innerHTML = visible.map(entry => `<article class="activity-row ${unread(entry) ? "is-unread" : ""}"><div class="activity-date">${stamp(entry)}<span>${escapeText(entry.market)} / ${entry.kind === "dossier" ? "Dossier" : "Report"}</span></div><div class="activity-main"><div class="activity-title">${link(entry)}${unread(entry) ? '<span class="unread-dot" title="Unread update" aria-label="Unread update"></span>' : ""}</div><p class="workflow">${escapeText(entry.workflow)}${entry.completed ? " / Completed" : ""}</p>${entry.summary ? `<p class="summary">${escapeText(entry.summary)}</p>` : ""}${entry.highlights?.length ? `<ul class="highlights">${entry.highlights.map(highlight => `<li>${escapeText(highlight)}</li>`).join("")}</ul>` : ""}</div><span class="verdict">${escapeText(entry.verdict)}</span></article>`).join("") || '<p class="empty">No updates match these filters.</p>';
  byId("more").hidden = recent.length <= state.limit;
  byId("mark-read").disabled = !visible.some(unread);
  byId("report-count").textContent = `${latest.size} latest reports`;
  byId("report-list").innerHTML = [...latest.values()].map(entry => `<article class="report-item"><div class="report-meta"><span>${escapeText(entry.market)}</span>${stamp(entry)}</div><h3>${link(entry)}</h3>${entry.summary ? `<p>${escapeText(entry.summary)}</p>` : ""}<span class="workflow">${escapeText(entry.workflow)}</span></article>`).join("") || '<p class="empty">No workflow reports match these filters.</p>';
  let dossiers = entries.filter(entry => entry.kind === "dossier" && (byId("sector").value === "all" || entry.sector === byId("sector").value) && (byId("verdict").value === "all" || entry.verdict === byId("verdict").value));
  if (byId("sort").value !== "updated") {
    const key = byId("sort").value === "symbol" ? "symbol" : "title";
    dossiers = dossiers.toSorted ? dossiers.toSorted((first, second) => first[key].localeCompare(second[key])) : [...dossiers].sort((first, second) => first[key].localeCompare(second[key]));
  }
  byId("library-count").textContent = `${dossiers.length} dossiers`;
  byId("dossier-list").innerHTML = dossiers.map(entry => `<tr><td><span class="symbol">${escapeText(entry.symbol)}</span>${link(entry)}</td><td>${escapeText(entry.market)}</td><td>${escapeText(entry.sector)}</td><td><span class="verdict">${escapeText(entry.verdict)}</span></td><td>${stamp(entry)}</td></tr>`).join("") || '<tr><td colspan="5" class="empty">No dossiers match these filters.</td></tr>';
}
async function load() {
  const button = byId("refresh");
  button.disabled = true;
  byId("error").hidden = true;
  try {
    const response = await fetch(`portal-data.json?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Catalog request failed (${response.status})`);
    const catalog = await response.json();
    if (catalog.schemaVersion !== 1 || !Array.isArray(catalog.entries)) throw new Error("Unsupported catalog format");
    if (catalog.entries.some(entry => !safeUrl(entry.url))) throw new Error("Catalog contains an invalid destination");
    state.entries = catalog.entries.sort((first, second) => (second.updatedAt || "").localeCompare(first.updatedAt || ""));
    for (const [id, key, label] of [["sector", "sector", "All sectors"], ["verdict", "verdict", "All verdicts"]]) {
      const control = byId(id);
      const previous = control.value;
      control.innerHTML = `<option value="all">${label}</option>` + [...new Set(state.entries.filter(entry => entry.kind === "dossier").map(entry => entry[key]))].sort().map(value => `<option value="${escapeText(value)}">${escapeText(value)}</option>`).join("");
      if ([...control.options].some(option => option.value === previous)) control.value = previous;
    }
    byId("catalog-time").textContent = `Catalog refreshed ${dateText(catalog.generatedAt)}`;
    byId("footer-status").textContent = `${state.entries.length} published pages`;
    render();
  } catch (error) {
    byId("error").textContent = `Research catalog unavailable. ${error.message}. Try refreshing. ${location.protocol === "file:" ? "Open this page through the local server or GitHub Pages." : ""}`;
    byId("error").hidden = false;
    byId("catalog-time").textContent = state.entries.length ? "Refresh failed; showing previous catalog" : "Catalog unavailable";
  } finally { button.disabled = false; }
}
document.querySelectorAll("[data-market]").forEach(button => button.addEventListener("click", () => {
  state.market = button.dataset.market;
  state.limit = 12;
  document.querySelectorAll("[data-market]").forEach(control => control.setAttribute("aria-pressed", String(control === button)));
  render();
}));
for (const id of ["search", "unread-only", "period", "sector", "verdict", "sort"]) byId(id).addEventListener(id === "search" ? "input" : "change", () => { state.limit = 12; render(); });
byId("more").addEventListener("click", () => { state.limit += 12; render(); });
byId("mark-read").addEventListener("click", () => { saveRead(activity().slice(0, state.limit)); render(); });
byId("refresh").addEventListener("click", load);
document.addEventListener("click", event => {
  const anchor = event.target.closest("a[data-entry]");
  if (anchor) {
    const entry = state.entries.find(item => item.id === anchor.dataset.entry);
    if (entry) saveRead([entry]);
  }
});
window.addEventListener("pageshow", () => { if (state.entries.length) render(); });
load();
