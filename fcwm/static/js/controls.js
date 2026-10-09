// ============================================================ Controls
$("cpSave").onclick = saveCellPop;
function syncCellPop() {
  const pv = !!$("cpPreview").value;
  $("cpWinOpts").style.display = pv ? "none" : "grid";
  $("cpShowWrap").style.display = pv ? "" : "none";
  $("cpExcludeWrap").style.display = $("cpCatch").checked ? "" : "none";
}
$("cpPreview").onchange = syncCellPop;
$("cpCatch").onchange = syncCellPop;
document.querySelectorAll("[data-sp]").forEach(b => b.onclick = () => {
  const [mon, slot] = [$("subpop").dataset.mon, +$("subpop").dataset.slot], sg = subgridOf(mon, slot), g = b.dataset.sp;
  if (!sg) return;
  setSubgrid(mon, slot, sg.grid[0] + (g === "c+") - (g === "c-"), sg.grid[1] + (g === "r+") - (g === "r-"));
  setTimeout(() => openSubPop(mon, slot), 300);
});
$("spEven").onclick = () => {
  const mon = $("subpop").dataset.mon, slot = +$("subpop").dataset.slot;
  setWeights(mon, 0, null, slot); setWeights(mon, 1, null, slot); changed();
  setTimeout(() => openSubPop(mon, slot), 300);
};
$("spMerge").onclick = () => mergeCell($("subpop").dataset.mon, +$("subpop").dataset.slot);
$("spClose").onclick = () => { $("subpop").style.display = "none"; };
$("cpCancel").onclick = () => { $("cellpop").style.display = "none"; };
$("subpop").onkeydown = (ev) => { if (ev.key === "Escape") $("spClose").click(); };
$("cellpop").onkeydown = (ev) => { if (ev.key === "Enter") saveCellPop(); if (ev.key === "Escape") $("cpCancel").click(); };
$("pname").oninput = () => { draft().name = $("pname").value.trim(); draft().dirty = true; renderHeader(); };
$("pdesc").oninput = () => { model().description = $("pdesc").value; draft().dirty = true; renderHeader(); };
$("pfocus").onchange = () => { model().focus = $("pfocus").value || null; changed(); };
$("save").onclick = save;
$("discard").onclick = () => {
  const d = draft();
  delete drafts[cur];
  if (!d.oldName) cur = state.default_profile || Object.keys(state.models)[0];
  if (!cur) newProfile();
  renderHeader(); preview();
};
$("profmenu").onclick = (ev) => {
  ev.stopPropagation();
  const d = draft();
  openMenu($("profmenu"), d.name, [
    {g: ic("copy"), l: t("duplicate"), run: () => { newProfile(draft()); renderHeader(); preview(); }},
    {g: ic("star"), l: t("makeDefault"), disabled: !d.oldName || d.oldName === state.default_profile, run: makeDefault},
    "-",
    {g: ic("trash"), l: t("delete"), danger: true, run: deleteProfile},
  ]);
};
async function makeDefault() {
  try { await api("/api/default", {name: draft().oldName}); flash(t("defaultSet")); await load(); }
  catch (e) { flash(e.message, "err"); }
}
async function deleteProfile() {
  const d = draft();
  if (!confirm(t("confirmDelete", {name: d.name}))) return;
  try {
    if (d.oldName) await api("/api/profile/delete", {name: d.oldName});
    delete drafts[cur]; cur = null;
    flash(t("profileDeleted", {name: d.name}));
    await load(false);
  } catch (e) { flash(e.message, "err"); }
}
$("apply").onclick = async () => {
  $("apply").disabled = true;
  try {
    const d = draft();
    const p = await api("/api/apply", {name: d.name, model: d.model});
    flash(t("placedN", {n: p.placements.length, name: d.name + (d.dirty ? `, ${t("unsaved")}` : "")}));
    await load();
  } catch (e) { flash(e.message, "err"); }
  finally { $("apply").disabled = false; }
};
$("refresh").onclick = () => load();
$("addchar").onclick = () => {
  const c = $("newchar").value.trim();
  if (!c) return;
  if (!extraChars.includes(c)) extraChars.push(c);
  try { localStorage.setItem("fcwm.extraChars", JSON.stringify(extraChars)); } catch {}
  $("newchar").value = "";
  renderEditor();
};
$("newchar").onkeydown = (ev) => { if (ev.key === "Enter") $("addchar").click(); };
$("lang").onchange = async () => {
  try { localStorage.setItem("fcwm.lang", $("lang").value); } catch {}
  await loadLang($("lang").value);
  applyStatic();
  if (auto) setAuto(auto);
  $("log").innerHTML = "";
  state.events.forEach(e => logEvent(e, false));
  load();   // fetch server messages (warnings) in the new language
};

$("cfgdetails").addEventListener("toggle", async (ev) => {
  if (ev.target.open) $("cfg").value = await api("/api/config");
});
$("reloadCfg").onclick = async () => {
  try {
    await api("/api/reload", {});
    for (const k of Object.keys(drafts)) if (!drafts[k].dirty) delete drafts[k];
    flash(t("cfgReloaded")); await load();
  } catch (e) { flash(e.message, "err"); }
};
$("webSave").onclick = async () => {
  const st = state.settings, port = +$("webPort").value, active = st.web_active || st.web;
  if (!(port >= 1 && port <= 65535)) return webMsg(t("invalidPort"), "err");
  if (port === active.port && port === st.web.port) return webMsg(t("webSameRestart"), "warn");
  if (Object.values(drafts).some(d => d.dirty) && !confirm(t("restartDirty"))) return;
  try {
    await api("/api/settings", {web: {...st.web, port}});
    await api("/api/restart", {});
    const url = `${location.protocol}//${location.hostname}:${port}/`;
    webMsg(t("webMoving", {port}), "warn");
    for (let i = 0; i < 40; i++) {    // wait for the new instance (different port -> only "no-cors" possible)
      await new Promise(r => setTimeout(r, 500));
      try { await fetch(url, {mode: "no-cors", cache: "no-store"}); location.href = url; return; } catch {}
    }
    webMsg(t("restartFailed"), "err");
  } catch (e) { webMsg(e.message, "err"); }
};
function webMsg(text, cls) { $("webMsg").innerHTML = `<div class="msg ${cls}">${esc(text)}</div>`; }
$("restartWm").onclick = async () => {
  if (Object.values(drafts).some(d => d.dirty) && !confirm(t("restartDirty"))) return;
  try {
    await api("/api/restart", {});
    flash(t("restartingUi"), "warn");
    for (let i = 0; i < 40; i++) {            // wait until the new instance responds
      await new Promise(r => setTimeout(r, 500));
      try { await api("/api/state"); for (const k of Object.keys(drafts)) delete drafts[k]; await load(); flash(t("restartedUi")); return; } catch {}
    }
    flash(t("restartFailed"), "err");
  } catch (e) { flash(e.message, "err"); }
};
$("savecfg").onclick = async () => {
  try {
    await api("/api/config", {text: $("cfg").value});
    for (const k of Object.keys(drafts)) delete drafts[k];
    $("cfgmsg").innerHTML = `<span style="color:var(--ok)">${esc(t("saved"))}</span>`;
    load();
  } catch (e) { $("cfgmsg").innerHTML = `<span style="color:var(--err)">${esc(e.message)}</span>`; }
};
window.addEventListener("resize", () => plan && renderEditor());
window.addEventListener("beforeunload", (ev) => { if (Object.values(drafts).some(d => d.dirty)) ev.preventDefault(); });

// Collapse windows (remember state per window)
let collapsed = {};
try { collapsed = JSON.parse(localStorage.getItem("fcwm.collapsed") || "{}"); } catch {}
document.querySelectorAll(".win[data-win]").forEach(w => {
  if (w.dataset.win in collapsed) w.classList.toggle("collapsed", collapsed[w.dataset.win]);
  const toggle = () => {
    collapsed[w.dataset.win] = w.classList.toggle("collapsed");
    try { localStorage.setItem("fcwm.collapsed", JSON.stringify(collapsed)); } catch {}
    if (!collapsed[w.dataset.win] && plan) renderEditor();
  };
  const btn = w.querySelector("[data-collapse]");   // windows without "—" (e.g. on the About page) stay open
  if (!btn) return;
  btn.onclick = toggle;
  w.querySelector(".bar").ondblclick = (ev) => { if (!ev.target.closest("button")) toggle(); };
});

// Pages: Layout / Settings / About (remembered, also linkable via #settings or #about)
function showPage(pg) {
  if (!document.querySelector(`main[data-page="${pg}"]`)) pg = "layout";
  document.querySelectorAll("main[data-page]").forEach(m => { m.hidden = m.dataset.page !== pg; });
  document.querySelectorAll(".page").forEach(b => b.classList.toggle("active", b.dataset.page === pg));
  try { localStorage.setItem("fcwm.page", pg); } catch {}
  if (location.hash.slice(1) !== pg) history.replaceState(null, "", pg === "layout" ? location.pathname : "#" + pg);
  closeMenu();
  $("tip").style.display = "none";
  if (pg === "layout" && plan) renderEditor();
}
document.querySelectorAll(".page").forEach(b => b.onclick = () => showPage(b.dataset.page));
let startPage = location.hash.slice(1);
try { startPage = startPage || localStorage.getItem("fcwm.page"); } catch {}
showPage(startPage || "layout");

// Help texts: hover or focus the "i"
function showTip(el) {
  const tip = $("tip");
  tip.textContent = t(el.dataset.tip);
  tip.style.display = "block";
  const r = el.getBoundingClientRect();
  tip.style.left = Math.max(8, Math.min(innerWidth - tip.offsetWidth - 8, r.left - 12)) + "px";
  tip.style.top = (r.bottom + tip.offsetHeight + 10 > innerHeight ? r.top - tip.offsetHeight - 6 : r.bottom + 6) + "px";
}
document.querySelectorAll(".info[data-tip]").forEach(el => { el.tabIndex = 0; el.setAttribute("role", "button"); });
document.addEventListener("mouseover", (ev) => { const el = ev.target.closest(".info[data-tip]"); if (el) showTip(el); });
document.addEventListener("mouseout", (ev) => { if (ev.target.closest(".info[data-tip]")) $("tip").style.display = "none"; });
document.addEventListener("focusin", (ev) => { if (ev.target.matches?.(".info[data-tip]")) showTip(ev.target); });
document.addEventListener("focusout", (ev) => { if (ev.target.matches?.(".info[data-tip]")) $("tip").style.display = "none"; });
// "i" inside a <label>/<summary> must not toggle the checkbox or expand it
document.addEventListener("click", (ev) => { if (ev.target.closest(".info[data-tip]")) ev.preventDefault(); }, true);

loadLang(lang).catch(e => console.error("i18n", e)).finally(() => {
  applyStatic();
  load();
  connectEvents();
});
