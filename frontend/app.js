// FixFlow demo UI. Plain ES module, no build step. Talks to the same FastAPI
// process that serves it (/health, /v1/scenarios, /v1/troubleshoot?debug=true).

const $ = (sel) => document.querySelector(sel);
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const DUMMY = "bixby://dummy_positive";

const CATEGORY_LABEL = {
  auto: "One tap in Settings",
  manual: "Do by hand",
  critical: "Disruptive, done last",
};

const FALLBACK_NOTICE = {
  no_match: "The article has no usable steps for this problem, so no plan was made.",
  no_siis_context: "This question hasn't been answered before. Add its knowledge-base article and build again.",
  low_confidence: "Low confidence. Check these steps against the article before using them.",
};

let scenarios = [];
let lastPlan = null;
let toastTimer = null;

// ---------- toast notifications (Un-Vibe Rules 2 & 4) ----------
function showToast(message, type = "success") {
  const t = $("#toast");
  if (!t) return;
  t.textContent = message;
  t.className = `toast ${type}`;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.hidden = true;
  }, 4000);
}

// ---------- small DOM helpers (text only, never innerHTML with API data) ----------
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "dataset") Object.assign(node.dataset, v);
    else if (v !== undefined && v !== null) node.setAttribute(k, v);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}
const sleep = (ms) => new Promise((r) => setTimeout(r, reduceMotion ? Math.min(ms, 150) : ms));

// ---------- status + scenarios ----------
async function loadStatus() {
  const status = $("#status");
  try {
    const res = await fetch("/health");
    await res.json();
    status.textContent = "System Ready";
    status.className = "status ok";
  } catch {
    status.textContent = "API not reachable. Start the server and reload.";
    status.className = "status down";
    showToast("API server not reachable. Ensure uvicorn is running.", "error");
  }
}

async function loadScenarios() {
  try {
    const res = await fetch("/v1/scenarios");
    scenarios = (await res.json()).scenarios;
  } catch {
    return;
  }
  const select = $("#scenario");
  scenarios.forEach((s, i) => {
    const text = s.query.replace(/^\s*\d+\.\s*"?/, "").replace(/"$/, "");
    select.append(el("option", { value: String(i) }, `${i + 1}. ${text.slice(0, 70)}${text.length > 70 ? "…" : ""}`));
  });
}

$("#scenario").addEventListener("change", (e) => {
  const s = scenarios[Number(e.target.value)];
  if (!s) return;
  $("#query").value = s.query;
  $("#siis-title").value = s.siis_response.title;
  $("#siis-content").value = s.siis_response.content;
  $("#source-hint").textContent = `"${s.siis_response.title}" loaded`;
  showToast(`Loaded Scenario: ${s.siis_response.title || "Selected scenario"}`);
});

// ---------- build plan ----------
async function buildPlan() {
  const query = $("#query").value.trim();
  if (!query) {
    $("#query").focus();
    $("#hint").textContent = "Describe the problem first.";
    showToast("Please describe the device issue or select a kit scenario.", "error");
    return;
  }
  const payload = { query };
  const content = $("#siis-content").value.trim();
  if (content) payload.siis_response = { title: $("#siis-title").value.trim() || "Article", content };

  const btn = $("#build");
  btn.setAttribute("aria-busy", "true");
  btn.textContent = "Building plan…";
  try {
    const res = await fetch("/v1/troubleshoot?debug=true", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`The API answered ${res.status}.`);
    const data = await res.json();
    renderPlan(data);
    $("#hint").textContent = "Ask the same thing again to see it answered from cache.";
    const count = (data.response && data.response.contexts[0] && data.response.contexts[0].actions)
      ? data.response.contexts[0].actions.length : 0;
    if (data.meta && data.meta.cache_hit) {
      showToast(`Instant Cache Hit: Served in ${Math.round(data.meta.latency_ms)}ms`, "success");
    } else if (data.meta && data.meta.retrieved_article) {
      showToast(`Auto-matched: ${data.meta.retrieved_article} (${count} actions)`, "success");
    } else {
      showToast(`Generated ${count}-action guided troubleshooting plan`, "success");
    }
  } catch (err) {
    const msg = err.message || "The request failed.";
    $("#hint").textContent = `${msg} Check the server is running.`;
    showToast(msg, "error");
  } finally {
    btn.removeAttribute("aria-busy");
    btn.textContent = "Build plan";
  }
}
$("#build").addEventListener("click", buildPlan);
$("#query").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) buildPlan();
});

function sourceLabel(meta) {
  if (meta.cache_hit) {
    return "FixFlow Cache";
  }
  return "AI Extraction";
}

function renderPlan(data) {
  lastPlan = data;
  const goal = data.response.contexts[0];
  $("#empty").hidden = true;
  $("#result").hidden = false;

  const notice = $("#notice");
  const fb = data.meta && data.meta.fallback;
  notice.hidden = !fb;
  notice.textContent = fb ? FALLBACK_NOTICE[fb] || fb : "";

  $("#goal").textContent = goal ? goal.goal : "No plan for this one";

  const facts = $("#facts");
  facts.replaceChildren();
  const fact = (label, value) => facts.append(el("div", {}, el("dt", {}, label), el("dd", {}, value)));
  if (goal) fact("Confidence", `${Math.round(goal.score * 100)}%`);
  fact("Answered in", `${Math.round(data.meta.latency_ms)} ms`);
  fact("Source", sourceLabel(data.meta));
  if (data.meta && data.meta.retrieved_article) {
    fact("Knowledge Base", `${data.meta.retrieved_article} (Auto-retrieved)`);
  }
  fact("Cost", `$${data.meta.cost_usd.toFixed(4)}`);

  const list = $("#actions");
  list.replaceChildren();
  for (const action of goal ? goal.actions : []) list.append(renderAction(action));

  renderTrace(data.trace || {});
  const vlist = $("#variations");
  vlist.replaceChildren(...(data.query_variations || []).map((v) => el("li", {}, v)));

  prepareDevice(goal);
}

function renderAction(action) {
  const cat = action.category || "manual";
  const li = el("li", { class: "action", dataset: { cat } },
    el("div", { class: "action-head" },
      el("h3", { class: "action-name" }, action.actionName),
      el("span", { class: "cat" }, CATEGORY_LABEL[cat] || cat)),
    el("p", { class: "action-desc" }, action.description));

  for (const sg of action.stepGroups) {
    li.append(el("ol", { class: "steps" }, sg.steps.map((s) => el("li", {}, s))));
    const links = el("div", { class: "links" });
    const ad = sg.actionableDeeplink;
    if (ad) {
      links.append(ad.deeplink === DUMMY
        ? el("span", { class: "chip" }, el("b", {}, "Opens "), `${ad.message} (not in catalog)`)
        : el("span", { class: "chip", title: ad.deeplink }, el("b", {}, "Opens "), ad.message));
    }
    const vd = sg.validationDeeplink;
    if (vd) {
      const expect = vd.resultType ? ` should be ${vd.value}` : "";
      links.append(el("span", { class: "chip check", title: vd.deeplink }, el("b", {}, "Checks "), `${vd.key}${expect}`));
    }
    if (links.childElementCount) li.append(links);
  }
  return li;
}

// ---------- trace ----------
function renderTrace(t) {
  const body = $("#trace-body");
  body.replaceChildren();

  const pathText = {
    cache: `Answered from cache (${(t.cache_hit_type || "").replace(/_/g, " ")}), zero latency overhead.`,
    cold: t.siis_retrieval && t.siis_retrieval.auto_retrieved
      ? `Auto-retrieved Samsung troubleshooting article: "${t.siis_retrieval.title}" (Relevance: ${(t.siis_retrieval.score * 100).toFixed(0)}%).`
      : "Extracted from the reference article.",
    no_siis: "Not in cache and no relevant article found in Samsung troubleshooting corpus.",
  };
  body.append(el("p", {}, pathText[t.path] || ""));
  if (t.siis_retrieval && t.siis_retrieval.auto_retrieved) {
    body.append(el("p", {}, `🔍 Auto-matched Knowledge Base: "${t.siis_retrieval.title}" (Hybrid score: ${t.siis_retrieval.score}, BM25: ${t.siis_retrieval.bm25_score}, Cosine: ${t.siis_retrieval.cosine_score})`));
  }
  if (t.extraction && t.extraction.replaced_ungrounded_llm_output) {
    body.append(el("p", {}, "Unverified steps filtered to guarantee strict SIIS grounding."));
  }

  if (t.clauses && t.clauses.length) {
    body.append(el("h3", {}, "How the complaint was read"));
    const rows = t.clauses.map((c) => el("tr", {},
      el("td", {}, c.text),
      el("td", {}, [c.signature.component, c.signature.symptom].filter((x) => x && x !== "unknown").join(", ") || "general"),
      el("td", {}, c.signature.polarity === "negated" ? "not working" : "happening")));
    body.append(el("table", {},
      el("thead", {}, el("tr", {}, el("th", {}, "Part of the complaint"), el("th", {}, "About"), el("th", {}, "Reads as"))),
      el("tbody", {}, rows)));
  }

  if (t.resolution && t.resolution.length) {
    body.append(el("h3", {}, "Which Settings screen each step opens"));
    const status = {
      matched: "Matched in catalog",
      dummy_positive: "No catalog match, opened by name",
      manual_no_deeplink: "Physical step, no screen",
      critical_no_screen: "No Settings screen involved",
    };
    const rows = t.resolution.map((r) => el("tr", {},
      el("td", {}, r.action),
      el("td", {}, r.deeplink),
      el("td", {}, status[r.status] || r.status)));
    body.append(el("table", {},
      el("thead", {}, el("tr", {}, el("th", {}, "Action"), el("th", {}, "Deeplink"), el("th", {}, "Status"))),
      el("tbody", {}, rows)));
  }
}

// ---------- device simulation ----------
function validations(goal) {
  const seen = new Map();
  for (const a of goal ? goal.actions : []) {
    for (const sg of a.stepGroups) {
      const vd = sg.validationDeeplink;
      if (vd && vd.resultType === "boolean" && !seen.has(vd.key)) seen.set(vd.key, vd);
    }
  }
  return [...seen.values()];
}

function prepareDevice(goal) {
  const checks = validations(goal);
  const box = $("#start-state");
  const toggles = $("#start-toggles");
  toggles.replaceChildren();
  box.hidden = checks.length === 0;
  checks.forEach((vd, i) => {
    const id = `start-${i}`;
    toggles.append(el("label", { for: id }, el("input", { type: "checkbox", id, "data-key": vd.key }), vd.key));
  });
  $("#run").disabled = !goal || goal.actions.length === 0;
  $("#screen").replaceChildren(el("p", { class: "screen-idle" },
    checks.length ? "Tick any setting that's already on, then run the plan." : "Run the plan to walk through it."));
}

function screenFor(action) {
  const screen = $("#screen");
  screen.replaceChildren();
  const sg = action.stepGroups[0];
  const ad = sg.actionableDeeplink;
  const cat = action.category;
  screen.append(el("p", { class: "screen-crumb" }, cat === "auto" ? "Settings" : CATEGORY_LABEL[cat]));
  screen.append(el("p", { class: "screen-title" }, ad ? ad.message.replace(/^(View|Open)\s+/i, "") : action.actionName));
  return { screen, sg };
}

async function runPlan() {
  const goal = lastPlan && lastPlan.response.contexts[0];
  if (!goal) return;
  const run = $("#run");
  run.disabled = true;
  const state = {};
  document.querySelectorAll("#start-toggles input").forEach((cb) => { state[cb.dataset.key] = cb.checked; });

  const logItems = goal.actions.map((a) => el("li", {}, a.actionName));
  for (let i = 0; i < goal.actions.length; i++) {
    const action = goal.actions[i];
    const { screen, sg } = screenFor(action);
    const vd = sg.validationDeeplink;

    if (action.category === "auto") {
      if (vd && vd.resultType === "boolean") {
        const want = String(vd.value).toLowerCase() === "true";
        const sw = el("span", { class: `switch${state[vd.key] ? " on" : ""}`, role: "img", "aria-label": state[vd.key] ? "On" : "Off" });
        screen.append(el("div", { class: "row" }, el("span", {}, vd.key, el("small", {}, want ? "Needs to be on" : "Needs to be off")), sw));
        await sleep(700);
        if (Boolean(state[vd.key]) === want) {
          screen.append(el("p", { class: "verdict skip" }, "Already set, so this step is skipped."));
        } else {
          sw.classList.toggle("on", want);
          sw.setAttribute("aria-label", want ? "On" : "Off");
          state[vd.key] = want;
          await sleep(500);
          screen.append(el("p", { class: "verdict pass" }, "Changed, then checked. It worked."));
        }
      } else {
        screen.append(el("ol", {}, sg.steps.slice(0, 4).map((s) => el("li", {}, s))));
        screen.append(el("p", { class: "verdict pass" }, "Screen opened in one tap."));
      }
    } else if (action.category === "manual") {
      screen.append(el("ol", {}, sg.steps.slice(0, 4).map((s) => el("li", {}, s))));
      screen.append(el("p", { class: "verdict hand" }, "Do this by hand, then continue."));
    } else {
      screen.append(el("ol", {}, sg.steps.slice(0, 4).map((s) => el("li", {}, s))));
      screen.append(el("p", { class: "verdict warn" }, "Disruptive. Only if the steps above didn't fix it."));
    }

    logItems[i].classList.add("done");
    screen.append(el("ol", { class: "run-log" }, logItems));
    await sleep(1600);
  }
  run.disabled = false;
  run.textContent = "Run plan again";
  showToast("Interactive One UI simulation completed!", "success");
}
$("#run").addEventListener("click", runPlan);

// ---------- mobile segment switcher (Un-Vibe Rule 5) ----------
document.querySelectorAll(".m-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".m-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const targetId = `section-${tab.dataset.target}`;
    const targetEl = document.getElementById(targetId);
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
    }
  });
});

// ---------- dynamic copyright year (Un-Vibe Rule 16) ----------
const yearEl = $("#copy-year");
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}

// ---------- clock + boot ----------
function tick() {
  const d = new Date();
  $("#clock").textContent = `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
}
tick();
setInterval(tick, 30_000);
loadStatus();
loadScenarios();
