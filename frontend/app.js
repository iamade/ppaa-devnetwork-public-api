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

document.getElementById("q").addEventListener("input", (ev) => {
  const q = ev.target.value.trim().toLowerCase();
  for (const el of grid.children) {
    el.style.display = !q || el.dataset.search.includes(q) ? "" : "none";
  }
});

render();
