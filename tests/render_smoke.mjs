// Deterministic frontend render smoke harness for PP-79/PP-63 (no browser needed).
// Loads frontend/app.js into a minimal DOM shim, feeds it the real /api/agents
// payload (fixture file or --api base), executes the actual render() path, then
// asserts: #grid non-empty AND #msg error banner stays hidden.
// Exit 0 + JSON summary on success; exit 1 + reason on failure.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
let fixturePath = null;
let apiBase = null;
let frontendDirOverride = null;
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--api") apiBase = args[++i];
  else if (args[i] === "--frontend") frontendDirOverride = args[++i];
  else fixturePath = args[i];
}

const frontendDirRaw = frontendDirOverride ?? new URL("../frontend/", import.meta.url).pathname;
const frontendDir = frontendDirRaw.endsWith("/") ? frontendDirRaw : frontendDirRaw + "/";
const appSrc = readFileSync(frontendDir + "app.js", "utf8");

function makeElement(tagName) {
  return {
    tagName, className: "", children: [], dataset: {}, style: {},
    hidden: true, textContent: "", href: "", title: "", value: "",
    appendChild(c) { this.children.push(c); return c; },
    append(...cs) { cs.forEach((c) => this.appendChild(c)); },
    addEventListener() {},
  };
}

const elements = {};
function byId(id) {
  if (!elements[id]) elements[id] = makeElement("div#" + id);
  return elements[id];
}

const documentShim = {
  getElementById: byId,
  createElement: (t) => makeElement(t),
};

const locationShim = { origin: "http://localhost:5174", port: "5174", search: "" };

async function loadPayload() {
  if (apiBase) {
    const res = await fetch(apiBase + "/api/agents");
    if (!res.ok) throw new Error("live api " + res.status);
    return await res.json();
  }
  return JSON.parse(readFileSync(fixturePath, "utf8"));
}

const payload = await loadPayload();

const sandbox = {
  document: documentShim,
  location: locationShim,
  URLSearchParams,
  fetch: () =>
    Promise.resolve({ ok: true, status: 200, json: async () => payload }),
  console,
  setTimeout,
};

// Execute the real app.js (the exact file nginx serves from frontend/).
new Function(...Object.keys(sandbox), appSrc)(...Object.values(sandbox));

// render() is async — flush pending promise/microtask work before asserting.
await new Promise((r) => setTimeout(r, 50));

const grid = byId("grid");
const msg = byId("msg");
const out = {
  gridChildren: grid.children.length,
  bannerHidden: msg.hidden === true,
  bannerText: msg.textContent,
  count: payload.count !== undefined ? payload.count : payload.agents.length,
};

const problems = [];
if (out.gridChildren === 0) problems.push("#grid is empty — no agent cards rendered");
if (out.gridChildren !== out.count) problems.push(`#grid has ${out.gridChildren} cards but API count is ${out.count}`);
if (!out.bannerHidden) problems.push("#msg error banner visible: " + out.bannerText);

if (problems.length) {
  console.error(JSON.stringify({ ok: false, ...out, problems }));
  process.exit(1);
}
console.log(JSON.stringify({ ok: true, ...out }));
