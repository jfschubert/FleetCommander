// ---- Subgrids (smaller clients in one cell)
function splitCell(mon, slot) {
  const m = model();
  m.subgrids = m.subgrids || [];
  if (subgridOf(mon, slot)) return openSubPop(mon, slot);
  // characters previously pinned exactly there stay as a stack in the first subcell
  for (const a of m.assign.filter(a => a.monitor === mon && subOf(a) === null && a.slot === slot)) { a.sub = 0; a.span = [1, 1]; }
  m.subgrids.push({monitor: mon, slot, grid: [2, 2], weights: null});
  changed();
  setTimeout(() => openSubPop(mon, slot), 250);
}
function setSubgrid(mon, slot, cols, rows) {
  const sg = subgridOf(mon, slot);
  if (!sg) return;
  cols = Math.max(1, Math.min(8, cols)); rows = Math.max(1, Math.min(8, rows));
  const [oc, or] = sg.grid, m = model(), dropped = [];
  for (const a of [...m.assign].filter(a => a.monitor === mon && a.slot === slot && subOf(a) !== null)) {
    const n = remap(subOf(a), oc, cols, rows);
    if (n === null) { m.assign.splice(m.assign.indexOf(a), 1); dropped.push(a.char); } else a.sub = n;
  }
  m.blocked = (m.blocked || []).filter(b => !(b.monitor === mon && b.slot === slot && subOf(b) !== null) ||
                                            (b.sub = remap(subOf(b), oc, cols, rows)) !== null);
  m.overflow = (m.overflow || []).filter(o => !(o.monitor === mon && o.slot === slot && subOf(o) !== null) ||
                                              (o.sub = remap(subOf(o), oc, cols, rows)) !== null);
  remapHotkeys((mo, sl_, sub) => mo !== mon || sl_ !== slot || sub === null ? [mo, sl_, sub]
                                 : (n => n === null ? null : [mo, sl_, n])(remap(sub, oc, cols, rows)));
  sg.grid = [cols, rows];
  if (cols !== oc) setWeights(mon, 0, null, slot);
  if (rows !== or) { setWeights(mon, 1, null, slot); dropRowOverrides(mon, slot, rows); }
  if (dropped.length) flash(t("droppedGrid", {list: dropped.join(", ")}), "warn");
  changed();
}
function mergeCell(mon, slot) {
  // Dissolve subgrid: pinned characters end up as a stack in the whole cell
  const m = model();
  m.subgrids = (m.subgrids || []).filter(g => !(g.monitor === mon && g.slot === slot));
  m.blocked = (m.blocked || []).filter(b => !(b.monitor === mon && b.slot === slot && subOf(b) !== null));
  m.overflow = (m.overflow || []).filter(o => !(o.monitor === mon && o.slot === slot && subOf(o) !== null));
  remapHotkeys((mo, sl_, sub) => mo === mon && sl_ === slot && sub !== null ? null : [mo, sl_, sub]);
  for (const a of m.assign.filter(a => a.monitor === mon && a.slot === slot)) { a.sub = null; a.span = [1, 1]; }
  $("subpop").style.display = "none";
  changed();
}
function openSubPop(mon, slot) {
  const sg = subgridOf(mon, slot), el = document.querySelector(`.subframe[data-mon="${mon}"][data-slot="${slot}"]`);
  if (!sg || !el) return;
  const pop = $("subpop"), r = el.getBoundingClientRect();
  $("spTitle").textContent = t("subgridOf", {slot: `${mon}:${slot}`});
  $("spCols").textContent = sg.grid[0]; $("spRows").textContent = sg.grid[1];
  $("spEven").style.display = sg.weights ? "" : "none";
  pop.dataset.mon = mon; pop.dataset.slot = slot;
  pop.style.display = "grid";
  pop.style.left = Math.min(innerWidth - pop.offsetWidth - 10, Math.max(10, r.left)) + "px";
  pop.style.top = Math.min(innerHeight - pop.offsetHeight - 10, r.top + 26) + "px";
}

// ---- Reserved cells: model().blocked = [{monitor, slot, sub, label, match}]
const blockedAt = (mon, slot, sub) => (model().blocked || []).find(b => b.monitor === mon && b.slot === slot && subOf(b) === sub);
function blockCell(mon, slot, sub = null) {
  const m = model();
  m.blocked = m.blocked || [];
  if (blockedAt(mon, slot, sub)) return;
  // characters pinned exactly there move back to the palette
  const key = sl(slot, sub), gone = m.assign.filter(a => a.monitor === mon && covered(a).includes(key));
  m.assign = m.assign.filter(a => !gone.includes(a));
  if (gone.length) flash(t("unpinnedForBlock", {list: gone.map(a => a.char).join(", ")}), "warn");
  m.overflow = (m.overflow || []).filter(o => !(o.monitor === mon && o.slot === slot && subOf(o) === sub));
  m.blocked.push({monitor: mon, slot, sub, label: "", match: ""});
  changed();
  setTimeout(() => editCell(mon, slot, sub), 250);
}
function unblockCell(mon, slot, sub = null) {
  const m = model();
  m.blocked = (m.blocked || []).filter(b => !(b.monitor === mon && b.slot === slot && subOf(b) === sub));
  changed();
}
function editCell(mon, slot, sub = null) {
  const b = blockedAt(mon, slot, sub);
  const el = document.querySelector(`.cell.blocked[data-mon="${mon}"][data-slot="${slot}"][data-sub="${sub ?? ""}"]`);
  if (!b || !el) return;
  const pop = $("cellpop"), r = el.getBoundingClientRect();
  $("cpLabel").value = b.label || ""; $("cpMatch").value = b.match || "";
  $("cpPreview").value = b.preview || "";
  $("cpShow").value = b.preview_show || "always";
  $("cpStack").checked = !!b.stack; $("cpCatch").checked = !!b.catch_all;
  $("cpExclude").value = b.exclude || ""; $("cpKeepSize").checked = b.resize === false;
  syncCellPop();
  $("cpWins").innerHTML = (state.windows || []).flatMap(([cap, cls]) => [cap, cls]).filter(Boolean)
    .filter((v, i, a) => a.indexOf(v) === i).map(v => `<option value="${esc(v)}">`).join("");
  pop.style.display = "grid";
  pop.style.left = Math.min(innerWidth - pop.offsetWidth - 10, Math.max(10, r.left)) + "px";
  pop.style.top = Math.min(innerHeight - pop.offsetHeight - 10, r.top + 24) + "px";
  pop.dataset.mon = mon; pop.dataset.slot = slot; pop.dataset.sub = sub ?? "";
  $("cpLabel").focus();
}
function saveCellPop() {
  const pop = $("cellpop"), b = blockedAt(...placeOf(pop));
  if (b) {
    b.label = $("cpLabel").value.trim();
    // a pick from the list is a literal title -> escape regex special characters
    let m = $("cpMatch").value.trim();
    if ((state.windows || []).some(([cap, cls]) => m === cap || m === cls)) m = m.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    b.preview = $("cpPreview").value;
    b.preview_show = $("cpShow").value;
    const win = !b.preview;          // preview and window in the same cell are mutually exclusive
    b.match = win ? m : "";
    b.stack = win && $("cpStack").checked;
    b.catch_all = win && $("cpCatch").checked;
    b.exclude = b.catch_all ? $("cpExclude").value.trim() : "";
    b.resize = !(win && $("cpKeepSize").checked);
    changed();
  }
  pop.style.display = "none";
}
// ---- Overflow cells: model().overflow = [{monitor, slot, sub, max}] in order
const overflowIdx = (mon, slot, sub) => (model().overflow || []).findIndex(o => o.monitor === mon && o.slot === slot && subOf(o) === sub);
function addOverflow(mon, slot, sub) {
  const m = model();
  m.overflow = m.overflow || [];
  if (overflowIdx(mon, slot, sub) < 0) m.overflow.push({monitor: mon, slot, sub, max: null});
  changed();
  setTimeout(() => openOfPop(overflowIdx(mon, slot, sub)), 250);
}
function openOfPop(i) {
  const ofl = model().overflow || [], o = ofl[i];
  if (!o) return;
  const el = document.querySelector(`.badge.of[data-i="${i}"]`), pop = $("ofpop");
  const last = i === ofl.length - 1;
  $("ofTitle").textContent = `${t("overflowN", {n: i + 1})} · ${o.monitor}:${sl(o.slot, subOf(o))}`;
  $("ofMax").textContent = o.max ? o.max : "∞";
  $("ofMaxRow").style.display = last ? "none" : "";
  $("ofLastHint").style.display = last ? "" : "none";
  pop.querySelector('[data-of="up"]').disabled = i === 0;
  pop.querySelector('[data-of="down"]').disabled = last;
  pop.dataset.i = i;
  showPop(pop, el);
}
document.querySelectorAll("[data-of]").forEach(b => b.onclick = () => {
  const m = model(), i = +$("ofpop").dataset.i, o = m.overflow[i], a = b.dataset.of;
  if (!o) return;
  if (a === "m+") o.max = (o.max || 0) + 1;
  if (a === "m-") o.max = o.max > 1 ? o.max - 1 : null;
  let ni = i;
  if (a === "up" && i > 0) { m.overflow.splice(i, 1); m.overflow.splice(i - 1, 0, o); ni = i - 1; }
  if (a === "down" && i < m.overflow.length - 1) { m.overflow.splice(i, 1); m.overflow.splice(i + 1, 0, o); ni = i + 1; }
  if (a === "remove") { m.overflow.splice(i, 1); $("ofpop").style.display = "none"; changed(); return; }
  changed();
  setTimeout(() => openOfPop(ni), 300);
});
$("ofClose").onclick = () => { $("ofpop").style.display = "none"; };

// ---- Preview bar on a stack: model().stack_previews = {"center:1": {mode, edge, size, show}}
function openSpPop(mon, slot, sub) {
  const key = `${mon}:${sl(slot, sub)}`, pop = $("sppop"), cur = (model().stack_previews || {})[key] || {};
  const el = document.querySelector(`[data-mon="${mon}"][data-slot="${slot}"][data-sub="${sub ?? ""}"]`);
  $("spvTitle").textContent = t("spvTitle", {cell: key});
  $("spvMode").value = cur.mode || ""; $("spvEdge").value = cur.edge || "bottom";
  $("spvSize").textContent = `${cur.size || 18} %`; $("spvShow").value = cur.show || "always";
  pop.dataset.key = key;
  showPop(pop, el);
}
function saveSpPop(sizeDelta = 0) {
  const m = model(), key = $("sppop").dataset.key, mode = $("spvMode").value;
  m.stack_previews = m.stack_previews || {};
  const size = Math.max(5, Math.min(60, (parseInt($("spvSize").textContent) || 18) + sizeDelta));
  $("spvSize").textContent = `${size} %`;
  if (!mode) delete m.stack_previews[key];
  else m.stack_previews[key] = {mode, edge: $("spvEdge").value, size, show: $("spvShow").value};
  changed();
}
["spvMode", "spvEdge", "spvShow"].forEach(id => $(id).onchange = () => saveSpPop());
document.querySelectorAll("[data-spv]").forEach(b => b.onclick = () => saveSpPop(b.dataset.spv === "+" ? 2 : -2));
$("spvClose").onclick = () => { $("sppop").style.display = "none"; };

// ---- Stack hotkeys: model().stack_hotkeys = {"center:1": "Meta+1"}
function openHkPop(mon, slot, sub) {
  const key = `${mon}:${sl(slot, sub)}`, pop = $("hkpop");
  const el = document.querySelector(`[data-mon="${mon}"][data-slot="${slot}"][data-sub="${sub ?? ""}"]`);
  $("hkTitle").textContent = t("stackHotkey", {cell: key});
  $("hkInput").value = (model().stack_hotkeys || {})[key] || "";
  $("hkInput").placeholder = t("noKey");
  pop.dataset.key = key;
  showPop(pop, el);
  $("hkInput").focus();
}
bindKeyCapture($("hkInput"), (keys) => {
  const m = model(), key = $("hkpop").dataset.key;
  m.stack_hotkeys = m.stack_hotkeys || {};
  if (keys) m.stack_hotkeys[key] = keys; else delete m.stack_hotkeys[key];
  changed();
});
$("hkClose").onclick = () => { $("hkpop").style.display = "none"; };
function showPop(pop, anchor) {
  pop.style.display = "grid";
  const r = anchor ? anchor.getBoundingClientRect() : {left: innerWidth / 2, top: innerHeight / 3};
  pop.style.left = Math.min(innerWidth - pop.offsetWidth - 10, Math.max(10, r.left)) + "px";
  pop.style.top = Math.min(innerHeight - pop.offsetHeight - 10, r.top + 24) + "px";
}
// Rewrite/remove slot keys ("mon:slot[.sub]") in the hotkey table
function remapHotkeys(fn) {   // rewrite slot keys in stack_hotkeys and stack_previews
  const m = model();
  for (const field of ["stack_hotkeys", "stack_previews"]) {
    const out = {};
    for (const [k, v] of Object.entries(m[field] || {})) {
      const [mon, rest] = k.split(":"), [slot, sub] = rest.split(".");
      const r = fn(mon, +slot, sub === undefined ? null : +sub);
      if (r) out[`${r[0]}:${sl(r[1], r[2])}`] = v;
    }
    m[field] = out;
  }
}
