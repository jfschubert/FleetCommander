// Settings → Debug info: backend, versions, paths, detected clients and monitors.
// "Copy" delivers the same as plain text for bug reports.
const rectText = (r) => r ? `${r[2]}×${r[3]} @ ${r[0]},${r[1]}` : "–";

function debugRows(tr = t) {
  const d = state.debug || {};
  const modules = [d.pyqt_webengine && "PyQt6-WebEngine", d.ruamel && "ruamel.yaml"].filter(Boolean).join(", ") || tr("dbgNone");
  return [
    ["dbgVersion", d.fcwm],
    ["dbgBackend", d.backend || state.backend],
    ["dbgListener", d.listener ? `${d.listener} (${tr(d.listener_running ? "dbgRunning" : "dbgStopped")})` : ""],
    ["dbgFeatures", (d.features || []).join(", ") || tr("dbgNone")],
    ["dbgSession", [d.session, d.desktop].filter(Boolean).join(" / ")],
    ["dbgKde", [d.kwin, d.plasma].filter(Boolean).join(" / ") || "–"],
    ["dbgPython", d.python],
    ["dbgModules", modules],
    ["dbgProfile", d.active_profile || "–"],
    ["dbgConfig", d.config || state.config_path],
    ["dbgState", d.state_file],
    ["dbgWeb", d.web],
  ];
}

function renderDebug() {
  refreshDebugConfig();
  $("dbgInfo").innerHTML = debugRows().map(([k, v]) =>
    `<span class="k">${esc(t(k))}</span><span class="v">${esc(v ?? "–")}</span>`).join("");
  const clients = Object.entries(state.clients).sort((a, b) => a[0].localeCompare(b[0]));
  $("dbgClientsTitle").textContent = t("dbgClients", {n: clients.length});
  $("dbgClients").innerHTML = clients.length
    ? `<tr><th>${esc(t("dbgChar"))}</th><th>${esc(t("dbgClass"))}</th><th>${esc(t("dbgOutput"))}</th><th>${esc(t("dbgGeometry"))}</th></tr>` +
      clients.map(([c, w]) => `<tr><td>${esc(c)}</td><td>${esc(w.class || "")}</td><td>${esc(w.output || "")}</td><td>${esc(rectText(w.geometry))}</td></tr>`).join("")
    : `<tr><td class="small">${esc(t("noClients"))}</td></tr>`;
  $("dbgMonsTitle").textContent = t("dbgMonitors", {n: state.monitors.length});
  $("dbgMons").innerHTML =
    `<tr><th>${esc(t("dbgOutput"))}</th><th>${esc(t("dbgModel"))}</th><th>${esc(t("dbgGeometry"))}</th><th>${esc(t("dbgWorkarea"))}</th><th>${esc(t("dbgScale"))}</th></tr>` +
    state.monitors.map(m => `<tr><td>${esc(m.name)}${m.primary ? " ★" : ""}</td><td class="wrap">${esc([m.manufacturer, m.model, m.serial].filter(Boolean).join(" · ") || "–")}</td>` +
      `<td>${esc(rectText(m.geometry))}</td><td>${esc(rectText(m.workarea))}</td><td>${esc(m.scale ?? 1)}</td></tr>`).join("");
}

function debugText() {
  const lines = ["FleetCommander debug info", ...debugRows().map(([k, v]) => `${t(k)}: ${v ?? "–"}`), ""];
  const clients = Object.entries(state.clients).sort((a, b) => a[0].localeCompare(b[0]));
  lines.push(t("dbgClients", {n: clients.length}) + ":");
  clients.forEach(([c, w]) => lines.push(`  ${c} | ${w.class || ""} | ${w.output || ""} | ${rectText(w.geometry)}`));
  lines.push("", t("dbgMonitors", {n: state.monitors.length}) + ":");
  state.monitors.forEach(m => lines.push(`  ${m.name}${m.primary ? " (primary)" : ""} | ${[m.manufacturer, m.model, m.serial].filter(Boolean).join(" ") || "-"} | ${rectText(m.geometry)} | ` +
    `${t("dbgWorkarea")} ${rectText(m.workarea)} | ${t("dbgScale")} ${m.scale ?? 1}`));
  return lines.join("\n");
}

// Clipboard: the app window copies via Qt (QWebChannel); browsers use the Clipboard API, falling back to
// execCommand. Returns false if nothing worked – the caller then shows the text for manual copying.
async function copyText(text) {
  if (window.fcwmBridge?.copyText) { window.fcwmBridge.copyText(text); return true; }
  try { await navigator.clipboard.writeText(text); return true; } catch {}
  const ta = Object.assign(document.createElement("textarea"), {value: text});
  ta.style.cssText = "position:fixed;opacity:0";
  document.body.appendChild(ta); ta.select();
  let ok = false;
  try { ok = document.execCommand("copy"); } catch {}
  ta.remove();
  return ok;
}
function showCopyFallback(text) {
  const out = $("dbgOut");
  out.value = text; out.hidden = false; out.focus(); out.select();
  flash(t("copyManual"), "warn");
}
$("dbgCopy").onclick = async () => {
  const text = debugText();
  if (await copyText(text)) flash(t("dbgCopied")); else showCopyFallback(text);
};

// For GitHub issues: Markdown tables, always in English, character names and serial numbers anonymized
// (issues are public).
// English texts are loaded up front so the click handler can copy right away (browsers only allow
// clipboard access shortly after the click).
let MSG_EN = null, CFG_TEXT = "";
fetch("/api/i18n?lang=en", {headers: {"X-Lang": "en"}}).then(r => r.json()).then(d => { MSG_EN = d.messages; }).catch(() => {});
function refreshDebugConfig() {   // called on every state update, so the copy contains the current file
  fetch("/api/config", {cache: "no-store"}).then(r => r.ok ? r.text() : "").then(txt => { CFG_TEXT = txt; }).catch(() => {});
}

// Character names -> "<race> Citizen <n>": the race is random, the number counts up; the mapping stays
// fixed for this page so repeated copies match.
const RACES = ["Amarr", "Caldari", "Gallente", "Minmatar"];
const aliases = new Map();
function charAlias(name) {
  if (!aliases.has(name)) aliases.set(name, `${RACES[Math.floor(Math.random() * RACES.length)]} Citizen ${aliases.size + 1}`);
  return aliases.get(name);
}
function knownCharNames() {
  const set = new Set(allChars());
  Object.keys((state.settings || {}).characters || {}).forEach(c => set.add(c));
  for (const m of Object.values(state.models || {})) if (m.focus) set.add(m.focus);
  return [...set].filter(Boolean).sort((a, b) => a.localeCompare(b));
}
function anonymize(text) {
  const names = knownCharNames();
  names.forEach(charAlias);   // fixed order -> stable numbers
  const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  // longest names first, so "Mister Forever" wins over "Forever"; only whole names
  for (const n of [...names].sort((a, b) => b.length - a.length))
    text = text.replace(new RegExp(`(?<![\\p{L}\\p{N}_])${reEsc(n)}(?![\\p{L}\\p{N}_])`, "gu"), charAlias(n));
  return text.replace(/\/home\/[^/\s]+/g, "~");
}
function debugMarkdown() {
  const msgs = MSG_EN || MSG;
  const te = (k, p = {}) => (msgs[k] ?? MSG[k] ?? k).replace(/\{(\w+)\}/g, (_, n) => p[n] ?? "");
  const cell = (v) => String(v ?? "–").replace(/\|/g, "\\|").replace(/\n/g, " ");
  const row = (cells) => `| ${cells.map(cell).join(" | ")} |`;
  const table = (head, rows) => [row(head), row(head.map(() => "---")), ...rows.map(row)];
  const d = state.debug || {};
  const rows = debugRows(te).map(([k, v]) => [te(k), typeof v === "string" ? anonymize(v) : v]);
  const clients = Object.entries(state.clients).sort((a, b) => a[0].localeCompare(b[0]));
  const out = ["<details><summary>FleetCommander debug info</summary>", "", ...table(["Item", "Value"], rows), "",
    `**${te("dbgClients", {n: clients.length})}**`, ""];
  if (clients.length) out.push(...table([te("dbgChar"), te("dbgClass"), te("dbgOutput"), te("dbgGeometry")],
    clients.map(([c, w]) => [anonymize(c), w.class || "", w.output || "", rectText(w.geometry)])));
  else out.push("–");
  out.push("", `**${te("dbgMonitors", {n: state.monitors.length})}**`, "",
    ...table([te("dbgOutput"), te("dbgModel"), te("dbgGeometry"), te("dbgWorkarea"), te("dbgScale")],
      state.monitors.map(m => [m.name + (m.primary ? " (primary)" : ""), [m.manufacturer, m.model].filter(Boolean).join(" ") || "–",
        rectText(m.geometry), rectText(m.workarea), m.scale ?? 1])));
  if (CFG_TEXT) out.push("", "**config.yaml**", "", "````yaml", anonymize(CFG_TEXT).trimEnd(), "````");
  out.push("", "</details>");
  return out.join("\n");
}
$("dbgIssueCopy").onclick = async () => {
  const text = debugMarkdown();
  if (await copyText(text)) flash(t("dbgIssueCopied")); else showCopyFallback(text);
};

// About page: show version, copy character name for the ISK donation
function renderAbout() {
  const d = state.debug || {};
  $("aboutVersion").textContent = `fcwm ${d.fcwm || ""} · GPL-3.0 · © 2026 Jan-Frederic Schubert`;
}
$("donateCopy").onclick = async () => {
  if (await copyText("Mister Forever")) flash(t("donateCopied")); else flash(t("copyFailed"), "err");
};
