"use strict";

// Backend origin: same-origin when the API serves this page (port 8005),
// or the canonical Mac-facing backend port when served by nginx on 5174.
const API = (() => {
  const fromQuery = new URLSearchParams(location.search).get("api");
  if (fromQuery) return fromQuery;
  return location.port === "5174" ? "http://localhost:8005" : "";
})();

const grid = document.getElementById("grid");
const countEl = document.getElementById("count");
const updatedEl = document.getElementById("updated");
const msgEl = document.getElementById("msg");
const sponsorsWrap = document.getElementById("sponsors-wrap");
const sponsorsEl = document.getElementById("sponsors");
document.getElementById("api-origin").textContent = API || location.origin;

function chip(href, label) {
  const isRoute = href != null && href.startsWith("/");
  const target = isRoute ? API + href : null;
  const a = document.createElement("a");
  a.className = "chip";
  a.textContent = label;
  if (target) { a.href = target; } else { a.href = "#"; a.title = href ?? ""; }
  return a;
}

function card(agent) {
  const el = document.createElement("article");
  el.className = "card";
  el.dataset.search = (agent.name + " " + agent.role + " " + agent.channel + " " + agent.description).toLowerCase();

  const name = document.createElement("h2");
  name.className = "name";
  name.textContent = agent.name;

  const role = document.createElement("p");
  role.className = "role";
  role.textContent = agent.role;

  const desc = document.createElement("p");
  desc.className = "desc";
  desc.textContent = agent.description;

  const row = document.createElement("p");
  row.className = "row";
  row.textContent = "Channel: " + agent.channel;

  const chips = document.createElement("div");
  chips.className = "chips";
  agent.demo_routes.forEach((r) => chips.appendChild(chip(r, r)));
  agent.jira_refs.forEach((j) => chips.appendChild(chip(null, j)));
  agent.evidence_links.forEach((e) => chips.appendChild(chip(null, e)));
  (agent.sponsors ?? []).forEach((sp) => {
    const c = chip(null, sp);
    c.className = "chip chip-sponsor";
    c.title = "Sponsor integration: " + sp;
    chips.appendChild(c);
  });

  el.append(name, role, desc, row, chips);
  return el;
}

async function render() {
  try {
    const res = await fetch(API + "/api/agents");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    countEl.textContent = String(data.count);
    updatedEl.textContent = data.updated;
    data.agents.forEach((a) => grid.appendChild(card(a)));
  } catch (err) {
    msgEl.hidden = false;
    msgEl.textContent = "Failed to load catalog from " + (API || location.origin) + " — " + err.message;
  }
}

// PP-80: sponsor registry strip. Isolated on purpose — a sponsor-render
// failure must never take the agent grid down with it.
async function renderSponsors() {
  try {
    const res = await fetch(API + "/api/sponsors");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    (data.sponsors ?? []).forEach((sp) => {
      const a = document.createElement("a");
      a.className = "sponsor" + (sp.example ? " sponsor-example" : "");
      a.textContent = sp.name + " · " + sp.integration.type;
      a.title = (sp.challenge_title ?? "") + " — integration: " + sp.integration.type;
      a.href = "#";
      sponsorsEl.appendChild(a);
    });
    if (sponsorsEl.children.length > 0) sponsorsWrap.hidden = false;
  } catch (err) {
    // sponsors are additive metadata; degrade silently (grid stays up)
    if (typeof console !== "undefined" && console.warn) console.warn("sponsors strip skipped:", err.message);
  }
}

document.getElementById("q").addEventListener("input", (ev) => {
  const q = ev.target.value.trim().toLowerCase();
  for (const el of grid.children) {
    el.style.display = !q || el.dataset.search.includes(q) ? "" : "none";
  }
});

render();
renderSponsors();
