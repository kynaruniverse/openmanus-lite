// OpenManus-Lite — minimal vanilla JS frontend.
const $ = sel => document.querySelector(sel);
const messages = $("#messages");
const composer = $("#composer");
const taskInput = $("#task");
const sendBtn = $("#send");
const stopBtn = $("#stop");
const statusDot = $("#status-dot");
const statusText = $("#status-text");
const providerSel = $("#provider");
const modelInput = $("#model");
const modeSel = $("#mode");
const budgetInput = $("#budget");
const pathInput = $("#path");
const useCacheCb = $("#use-cache");
const sidebar = $("#sidebar");
const settingsBtn = $("#settings-btn");
const providerHelp = $("#provider-help");

let abortController = null;
let info = null;

settingsBtn.addEventListener("click", () => sidebar.classList.toggle("open"));

// Suggestions on the empty state.
document.querySelectorAll(".chip").forEach(b => {
  b.addEventListener("click", () => { taskInput.value = b.textContent; taskInput.focus(); });
});

// Pretty status helper.
function setStatus(state, text) {
  statusDot.className = "dot" + (state ? " " + state : "");
  statusText.textContent = text;
}

// Server info → provider list.
async function loadInfo() {
  try {
    const res = await fetch("/api/info");
    info = await res.json();
  } catch {
    info = { providers: [], defaults: {}, current_provider: "gemini" };
  }
  providerSel.innerHTML = "";
  for (const p of info.providers) {
    const opt = document.createElement("option");
    opt.value = p.name;
    const label = p.name === "ollama"
      ? `${p.name}  (local)`
      : `${p.name}  ${p.ready ? "" : "(no key)"}`;
    opt.textContent = label;
    if (p.name === info.current_provider) opt.selected = true;
    providerSel.appendChild(opt);
  }
  updateProviderHelp();
}
providerSel.addEventListener("change", updateProviderHelp);

function updateProviderHelp() {
  const name = providerSel.value;
  const meta = info.providers.find(p => p.name === name);
  const def = info.defaults[name] || {};
  let help = `Default model: ${def.model || "(none)"}\n`;
  if (meta && meta.key_var) {
    help += meta.ready
      ? `✓ ${meta.key_var} is set.`
      : `⚠ ${meta.key_var} is not set. Add it to your environment / Replit Secrets.`;
  } else if (name === "ollama") {
    help += "ℹ Runs locally via the Ollama server (http://localhost:11434).\n" +
            "First time: install Ollama (ollama.com) and run\n  ollama pull llama3.2";
  }
  providerHelp.textContent = help;
}

// ---------- chat rendering ----------
function clearEmpty() {
  const empty = messages.querySelector(".empty");
  if (empty) empty.remove();
}

function userMessage(text) {
  clearEmpty();
  const div = document.createElement("div");
  div.className = "msg user";
  div.textContent = text;
  messages.appendChild(div);
  scrollDown();
}

function stepCard(action) {
  const card = document.createElement("div");
  card.className = "step";
  const head = document.createElement("div");
  head.className = "head";
  const badge = document.createElement("span");
  badge.className = "badge " + action;
  badge.textContent = action;
  head.appendChild(badge);
  const title = document.createElement("span");
  title.className = "thought";
  head.appendChild(title);
  card.appendChild(head);
  messages.appendChild(card);
  return { card, head, title };
}

function attachObservation(card, content, ok) {
  const obs = document.createElement("pre");
  obs.className = "obs";
  obs.textContent = content;
  card.appendChild(obs);
  if (!ok) card.classList.add("fail");
}

function finalMessage(text) {
  const div = document.createElement("div");
  div.className = "final";
  div.textContent = text;
  messages.appendChild(div);
  scrollDown();
}

function errorMessage(text) {
  const div = document.createElement("div");
  div.className = "error-msg";
  div.textContent = "❌ " + text;
  messages.appendChild(div);
  scrollDown();
}

function scrollDown() {
  messages.scrollTop = messages.scrollHeight;
}

// ---------- streaming via fetch+SSE ----------
function setBusy(on) {
  sendBtn.disabled = on;
  stopBtn.hidden = !on;
  if (on) setStatus("busy", "Thinking…");
}

async function runTask(task) {
  setBusy(true);
  abortController = new AbortController();
  const body = {
    task,
    provider: providerSel.value || null,
    model: modelInput.value.trim() || null,
    mode: modeSel.value,
    budget: parseInt(budgetInput.value || "0", 10),
    path: pathInput.value.trim() || null,
    use_cache: useCacheCb.checked,
  };

  let res;
  try {
    res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: abortController.signal,
    });
  } catch (e) {
    errorMessage("Request failed: " + e.message);
    setBusy(false);
    setStatus("error", "Error");
    return;
  }

  if (!res.ok || !res.body) {
    errorMessage("Server returned " + res.status);
    setBusy(false);
    setStatus("error", "Error");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentStep = null;
  let sawError = false;

  while (true) {
    let chunk;
    try {
      chunk = await reader.read();
    } catch (e) {
      break;
    }
    if (chunk.done) break;
    buffer += decoder.decode(chunk.value, { stream: true });

    // SSE frames are separated by blank lines.
    let idx;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const dataLine = frame.split("\n").find(l => l.startsWith("data:"));
      if (!dataLine) continue;
      const json = dataLine.slice(5).trim();
      if (!json) continue;
      let ev;
      try { ev = JSON.parse(json); } catch { continue; }
      const handled = handleEvent(ev, currentStep);
      currentStep = handled.currentStep;
      if (handled.error) sawError = true;
    }
  }

  setBusy(false);
  setStatus(sawError ? "error" : "ok", sawError ? "Error" : "Done");
}

function handleEvent(ev, currentStep) {
  let error = false;
  switch (ev.type) {
    case "start":
      setStatus("busy", `Working with ${ev.provider} · ${ev.model}`);
      break;
    case "iter":
      // optional: show iteration counter
      break;
    case "thought":
      currentStep = stepCard(ev.action || "step");
      currentStep.title.textContent = ev.text || "(thinking…)";
      // Show params as a tiny code block under the head.
      if (ev.params && Object.keys(ev.params).length) {
        const params = document.createElement("pre");
        params.className = "obs";
        params.style.opacity = "0.85";
        params.textContent = formatParams(ev.action, ev.params);
        currentStep.card.appendChild(params);
      }
      scrollDown();
      break;
    case "observation":
      if (currentStep) {
        attachObservation(currentStep.card, ev.content || "", ev.ok !== false);
      }
      scrollDown();
      break;
    case "parse_error":
      currentStep = stepCard("error");
      currentStep.title.textContent = "Bad JSON from model — retrying";
      attachObservation(currentStep.card, ev.raw || "", false);
      scrollDown();
      break;
    case "cache_hit":
      finalMessage("🚀 (from cache)\n\n" + (ev.answer || ""));
      break;
    case "finish":
      finalMessage(ev.answer || "(no answer)");
      break;
    case "done":
      // Last event before stream closes — already rendered finish.
      break;
    case "error":
      errorMessage(ev.message || "Unknown error");
      error = true;
      break;
  }
  return { currentStep, error };
}

function formatParams(action, params) {
  if (action === "shell") return "$ " + (params.command || "");
  if (action === "file_read") return "open " + (params.file || "");
  if (action === "file_write") {
    const c = params.content || "";
    const preview = c.length > 200 ? c.slice(0, 200) + "…" : c;
    return "write " + (params.file || "") + "\n---\n" + preview;
  }
  if (action === "git") return "git " + ((params.args || []).join(" "));
  if (action === "python") return params.code || "";
  if (action === "search") return "search: " + (params.query || "");
  return JSON.stringify(params, null, 2);
}

// ---------- form handlers ----------
composer.addEventListener("submit", (e) => {
  e.preventDefault();
  const task = taskInput.value.trim();
  if (!task) return;
  userMessage(task);
  taskInput.value = "";
  runTask(task);
});

taskInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    composer.requestSubmit();
  }
});

stopBtn.addEventListener("click", () => {
  if (abortController) {
    abortController.abort();
    setStatus("error", "Stopped");
    setBusy(false);
  }
});

loadInfo();
