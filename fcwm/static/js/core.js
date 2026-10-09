// ============================================================ Basics
const $ = (id) => document.getElementById(id);
const DT = "application/x-fcwm-char";
let state = null, cur = null, plan = null, auto = null;
const drafts = {};
let previewSeq = 0, newCounter = 0, refreshTimer = null;
let extraChars = [];
try { extraChars = JSON.parse(localStorage.getItem("fcwm.extraChars") || "[]"); } catch {}

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const clone = (o) => JSON.parse(JSON.stringify(o));

async function api(path, body) {
  const opt = {headers: {"X-Lang": lang}};
  if (body !== undefined) Object.assign(opt, {method: "POST", body: JSON.stringify(body)}, {headers: {"X-Lang": lang, "Content-Type": "application/json"}});
  const r = await fetch(path, opt);
  const data = (r.headers.get("content-type") || "").includes("json") ? await r.json() : await r.text();
  if (!r.ok) throw new Error(data.error || data);
  return data;
}
function flash(text, cls = "ok") {
  $("msgs").innerHTML = `<div class="msg ${cls}">${esc(text)}</div>`;
  if (cls === "ok") setTimeout(() => { $("msgs").innerHTML = ""; }, 4000);
}
function toast(title, text, cls = "") {
  const el = document.createElement("div");
  el.className = `toast ${cls}`;
  el.innerHTML = `<div class="tt">${esc(title)}</div>${esc(text)}`;
  $("toasts").appendChild(el);
  setTimeout(() => el.remove(), 5000);
  while ($("toasts").children.length > 5) $("toasts").firstChild.remove();
}

// ============================================================ State
function draft() {
  if (!drafts[cur]) drafts[cur] = {name: cur, oldName: cur, model: clone(state.models[cur]), dirty: false};
  return drafts[cur];
}
const model = () => draft().model;
function changed() { draft().dirty = true; renderHeader(); preview(); }

async function load(keep = true) {
  $("refresh").disabled = true;
  try {
    const first = !state;
    state = await api("/api/state");
    const keys = [...Object.keys(state.models), ...Object.keys(drafts).filter(k => !state.models[k])];
    if (!keep || !cur || !keys.includes(cur)) cur = state.default_profile || keys[0] || null;
    if (!cur) newProfile();
    if (first) state.events.forEach(e => logEvent(e, false));
    setAuto(state.auto);
    renderHeader(); renderSidebar(); renderSettings();
    await preview();
  } catch (e) { flash(e.message, "err"); }
  finally { $("refresh").disabled = false; }
}
function scheduleRefresh() { clearTimeout(refreshTimer); refreshTimer = setTimeout(() => load(), 700); }

async function preview() {
  const seq = ++previewSeq, d = draft();
  try {
    const p = await api("/api/preview", {name: d.name, model: d.model});
    if (seq !== previewSeq) return;
    plan = p; renderEditor();
  } catch (e) {
    if (seq === previewSeq) $("planmsgs").innerHTML = `<div class="msg err">${esc(e.message)}</div>`;
  }
}

// ---- Capture key combination (Qt notation for KDE: "Meta+Ctrl+Alt+Shift+X")
function keyName(ev) {
  const c = ev.code, k = ev.key;
  if (/^Key[A-Z]$/.test(c)) return c.slice(3);
  if (/^Digit\d$/.test(c)) return c.slice(5);
  if (/^Numpad\d$/.test(c)) return "Num+" + c.slice(6);
  if (/^F\d{1,2}$/.test(k)) return k;
  const map = {ArrowLeft: "Left", ArrowRight: "Right", ArrowUp: "Up", ArrowDown: "Down", PageUp: "PgUp", PageDown: "PgDown",
               " ": "Space", Tab: "Tab", Home: "Home", End: "End", Insert: "Ins", Enter: "Return", Pause: "Pause",
               Backquote: "`", Minus: "-", Equal: "=", BracketLeft: "[", BracketRight: "]", Semicolon: ";", Quote: "'",
               Comma: ",", Period: ".", Slash: "/", Backslash: "\\"};
  return map[k] || map[c] || null;
}
function bindKeyCapture(input, onSet) {
  input.addEventListener("focus", () => { input.dataset.old = input.value; input.classList.add("rec"); input.value = ""; input.placeholder = t("pressKey"); });
  input.addEventListener("blur", () => { input.classList.remove("rec"); if (!input.value) input.value = input.dataset.old || ""; input.placeholder = t("noKey"); });
  input.addEventListener("keydown", (ev) => {
    ev.preventDefault(); ev.stopPropagation();
    if (ev.key === "Escape") { input.value = input.dataset.old || ""; input.blur(); return; }
    if ((ev.key === "Backspace" || ev.key === "Delete") && !ev.ctrlKey && !ev.altKey && !ev.metaKey) {
      input.dataset.old = ""; input.value = ""; input.blur(); onSet(""); return;
    }
    if (["Control", "Alt", "Shift", "Meta", "OS", "AltGraph"].includes(ev.key)) return;
    const name = keyName(ev);
    if (!name) return;
    const mods = [ev.metaKey && "Meta", ev.ctrlKey && "Ctrl", ev.altKey && "Alt", ev.shiftKey && "Shift"].filter(Boolean);
    const combo = [...mods, name].join("+");
    input.value = combo; input.dataset.old = combo; input.blur(); onSet(combo);
  });
}
