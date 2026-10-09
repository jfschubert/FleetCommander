// ---- Global settings: hotkeys + title bars
async function saveSettings(patch, msg) {
  try { await api("/api/settings", patch); flash(msg); await load(); }
  catch (e) { flash(e.message, "err"); }
}
document.querySelectorAll("input.keycap[data-hk]").forEach(inp => bindKeyCapture(inp, () => {
  const hk = {...(state.settings.hotkeys || {})};
  document.querySelectorAll("input.keycap[data-hk]").forEach(i => { hk[i.dataset.hk] = i.value; });
  saveSettings({hotkeys: hk}, t("hkSaved"));
}));
bindKeyCapture($("photkey"), (keys) => { model().hotkey = keys; changed(); });
function colorInput(value, onChange) {
  const id = "c" + Math.random().toString(36).slice(2);
  setTimeout(() => {
    const el = document.getElementById(id);
    if (!el) return;
    el.querySelector("input").onchange = (ev) => onChange(ev.target.value);
    const clr = el.querySelector("button");
    if (clr) clr.onclick = () => onChange("");
  });
  return `<span class="clr" id="${id}"><input type="color" value="${esc(value || "#3a6f97")}" ${value ? "" : 'style="opacity:.35"'}>` +
    (value ? `<button title="${esc(t("clearColor"))}">${ic("close")}</button>` : `<span class="small">${esc(t("tbNone"))}</span>`) + `</span>`;
}
function renderSettings() {
  const st = state.settings || {}, feats = (state.auto && state.auto.features) || [];
  document.querySelectorAll("input.keycap[data-hk]").forEach(i => {
    if (document.activeElement !== i) { i.value = (st.hotkeys || {})[i.dataset.hk] || ""; i.placeholder = t("noKey"); }
    i.disabled = !feats.includes("hotkeys");
  });
  $("lockWrap").style.display = feats.includes("lock") ? "" : "none";
  $("lockWrap").title = t("lockHelp");
  const tb = st.titlebar || {};
  $("tbHide").checked = !!tb.hide;
  $("tbHide").disabled = !st.titlebar_available;
  $("tbDefault").innerHTML = colorInput(tb.color, (c) => saveSettings({titlebar: {...tb, color: c}}, t("tbSaved")));
  const sep = st.separator || {};
  $("sepWidth").textContent = sep.width ? `${sep.width} px` : t("off");
  $("sepShow").value = sep.show || "always";
  $("sepShow").disabled = !sep.width;
  $("sepColor").innerHTML = sep.width ? colorInput(sep.color || "#3c3c3c", (c) => saveSettings({separator: {...sep, color: c || "#3c3c3c"}}, t("sepSaved"))).replace(/<button[^>]*>.*?<\/button>/, "") : "";
  const web = st.web || {}, wa = st.web_active || web;
  $("webActive").textContent = `http://${wa.host}:${wa.port}/`;
  if (document.activeElement !== $("webPort")) $("webPort").value = web.port || 8765;
  const chars = st.characters || {};
  $("tbChars").innerHTML = allChars().map(c => `<li><span>${esc(c)}</span>${colorInput((chars[c] || {}).color, (col) => {
    const next = {...chars}; if (col) next[c] = {color: col}; else delete next[c];
    saveSettings({characters: next}, t("tbSaved"));
  })}</li>`).join("");
}
document.querySelectorAll("[data-sep]").forEach(b => b.onclick = () => {
  const sep = {...(state.settings.separator || {})};
  sep.width = Math.max(0, Math.min(20, (+sep.width || 0) + (b.dataset.sep === "+" ? 1 : -1)));
  saveSettings({separator: sep}, t("sepSaved"));
});
$("sepShow").onchange = (ev) => saveSettings({separator: {...(state.settings.separator || {}), show: ev.target.value}}, t("sepSaved"));
$("tbHide").onchange = (ev) => saveSettings({titlebar: {...(state.settings.titlebar || {}), hide: ev.target.checked}}, t("tbSaved"));
$("lockToggle").onchange = async (ev) => {
  try { setAuto(await api("/api/lock", {enabled: ev.target.checked})); } catch (e) { toast(t("tError"), e.message, "err"); }
};
