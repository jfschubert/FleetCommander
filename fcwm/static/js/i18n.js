// ============================================================ i18n
// Texts live in fcwm/locales/web/<language>.json (editable with Weblate etc.); the server delivers
// the requested language, supplemented by the source language (en) for keys not yet translated.
let lang = "en", MSG = {};
try { lang = localStorage.getItem("fcwm.lang") || navigator.language || "en"; } catch {}
async function loadLang(code) {
  const r = await fetch(`/api/i18n?lang=${encodeURIComponent(code)}`, {headers: {"X-Lang": code}});
  if (!r.ok) {
    // index.html is read fresh on every request, the Python code only at startup: after an
    // update without a restart the page does not match the running server
    document.body.insertAdjacentHTML("afterbegin", `<div class="msg err" style="margin:6px">fcwm was updated but is still
      running the old version – run <b>fcwm restart</b> and reload this page.<br>fcwm wurde aktualisiert, läuft aber noch in
      der alten Version – <b>fcwm restart</b> ausführen und die Seite neu laden.</div>`);
    throw new Error(`/api/i18n: HTTP ${r.status}`);
  }
  const d = await r.json();
  lang = d.lang; MSG = d.messages;
  $("lang").innerHTML = d.languages.map(l => `<option value="${esc(l.code)}">${esc(l.name)}</option>`).join("");
}
const bcp47 = () => lang.replace("_", "-");
const ic = (n, cls = "ic") => `<svg class="${cls}"><use href="#i-${n}"/></svg>`;   // Lucide icon from index.html
const PIN = ic("pin", "pin");
const t = (k, p = {}) => (MSG[k] ?? k).replace(/\{(\w+)\}/g, (_, n) => p[n] ?? "");
function applyStatic() {
  document.documentElement.lang = bcp47();
  document.querySelectorAll("[data-i18n]").forEach(el => el.textContent = t(el.dataset.i18n));
  document.querySelectorAll("[data-i18n-title]").forEach(el => el.title = t(el.dataset.i18nTitle));
  $("newchar").placeholder = t("addPlaceholder");
  $("pname").placeholder = t("name");
  $("lang").value = lang;
  $("clearlog").title = t("clear");
  document.querySelectorAll("[data-collapse]").forEach(b => b.title = t("collapse"));
}
