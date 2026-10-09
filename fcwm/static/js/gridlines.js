// ---- Dragging grid lines (pointer events, live preview)
let canvasMap = null, lineDrag = null, lastLinePreview = 0;
function startLineDrag(ev) {
  ev.preventDefault();
  const d = ev.currentTarget.dataset, lay = plan.layouts[d.mon], slot = d.gslot === "" ? null : +d.gslot;
  lineDrag = {alias: d.mon, slot, axis: +d.axis, k: +d.k, row: d.row === undefined ? null : +d.row,
              area: slot === null ? lay.area : lay.cells[slot]};
  document.body.classList.add(+d.axis ? "drag-h" : "drag-v");
  $("gltip").style.display = "block";
  moveLineDrag(ev);
}
function moveLineDrag(ev) {
  if (!lineDrag) return;
  const {alias, slot, axis, k, area} = lineDrag, rect = $("canvas").getBoundingClientRect(), {minX, minY, s} = canvasMap;
  // vertical line: only this row; with Ctrl the whole line across all rows
  const row = axis === 0 && !ev.ctrlKey ? lineDrag.row : null;
  const pos = axis === 0 ? (ev.clientX - rect.left) / s + minX : (ev.clientY - rect.top) / s + minY;
  let p = (pos - area[axis]) / area[axis + 2];
  const w = weightsOf(alias, axis, slot, row), total = w.reduce((x, y) => x + y, 0);
  const f = w.map(x => x / total), lo = f.slice(0, k).reduce((x, y) => x + y, 0), hi = lo + f[k] + f[k + 1];
  const MIN = 0.05;
  p = Math.min(hi - MIN, Math.max(lo + MIN, p));
  p = ev.shiftKey ? Math.round(p * 12) / 12 : Math.round(p * 200) / 200;   // Shift: snap to 1/12
  p = Math.min(hi - MIN, Math.max(lo + MIN, p));
  f[k] = p - lo; f[k + 1] = hi - p;
  const nw = f.map(x => Math.round(x * 1000) / 10);
  if (axis === 0 && row === null) {   // Ctrl: whole line -> clear row overrides
    const e = weightEntry(alias, slot);
    if (e && e[2]) e[2] = null;
  }
  setWeights(alias, axis, nw, slot, row);
  const px = Math.round(area[axis + 2] * f[k]), px2 = Math.round(area[axis + 2] * f[k + 1]);
  const tip = $("gltip");
  const scope = axis === 0 ? (row === null ? t("allRows") : t("rowN", {n: row + 1})) + "  " : "";
  tip.textContent = `${scope}${(f[k] * 100).toFixed(1)}% | ${(f[k + 1] * 100).toFixed(1)}%   ${px} | ${px2} px`;
  tip.style.left = ev.clientX + 14 + "px"; tip.style.top = ev.clientY + 14 + "px";
  draft().dirty = true;
  const now = Date.now();
  if (now - lastLinePreview > 60) { lastLinePreview = now; preview(); }
}
function endLineDrag() {
  if (!lineDrag) return;
  lineDrag = null;
  document.body.classList.remove("drag-h", "drag-v");
  $("gltip").style.display = "none";
  changed();
}
window.addEventListener("pointermove", moveLineDrag);
window.addEventListener("pointerup", endLineDrag);

// Reset refers to the default profile (unless you are editing it yourself);
// otherwise to the monitor's base grid from the configuration.
function defaultGridOf(alias) {
  const name = state.default_profile, base = state.monitor_config[alias];
  const dm = name && name !== draft().oldName ? state.models[name] : null;
  if (dm && dm.grids[alias]) return {grid: dm.grids[alias], weights: (dm.weights || {})[alias] || null, fromProfile: name};
  return {grid: base.grid, weights: base.weights, fromProfile: null};
}

// Rename monitor: input directly in the card; empty = automatic name (model)
function renameMonitor(card, alias) {
  const holder = card.querySelector(".mname");
  holder.innerHTML = `<input class="rename" value="${esc((state.monitor_config[alias] || {}).label || "")}"
    placeholder="${esc(monitorDefaultName(monitorOf(alias)) || alias)}" title="${esc(t("renameHint"))}">`;
  const inp = holder.querySelector("input");
  inp.focus(); inp.select();
  let done = false;
  const finish = async (save) => {
    if (done) return; done = true;
    if (save) {
      try { await api("/api/settings", {monitor_labels: {[alias]: inp.value.trim()}}); await load(); return; }
      catch (e) { flash(e.message, "err"); }
    }
    renderEditor();
  };
  inp.onkeydown = (ev) => { if (ev.key === "Enter") finish(true); if (ev.key === "Escape") finish(false); };
  inp.onblur = () => finish(true);
}

function drawMonitorCards() {
  const m = model(), connected = new Set(Object.keys(plan.layouts));
  $("moncards").innerHTML = Object.entries(state.monitor_config).map(([alias, mc]) => {
    const [c, r] = gridOf(alias), def = defaultGridOf(alias), isDef = c === def.grid[0] && r === def.grid[1];
    const mon = monitorOf(alias);
    const moved = !!(m.weights || {})[alias];
    const used = !(m.disabled || []).includes(alias), there = connected.has(alias) || !used;
    return `<div class="mcard ${there && used ? "" : "off"}" data-mon="${esc(alias)}">
      <div class="t"><span class="mname"><b>${esc(monitorLabel(alias))}${primaryStar(mon)}</b>
        <button class="wbtn ren" data-rename title="${esc(t("renameMon"))}">${ic("pencil")}</button></span>
        <span class="small">${esc(mc.output ?? "index " + mc.index)} · ${esc(alias)}${there ? "" : " · " + esc(t("notConnected"))}</span></div>
      <label class="switch"><input type="checkbox" data-use ${used ? "checked" : ""}><span class="track"></span><span class="lbl">${esc(t("useMonitor"))}</span></label>
      <div class="row">
        <span class="k">${esc(t("cols"))}</span><span class="stepper"><button data-g="c-">−</button><span>${c}</span><button data-g="c+">+</button></span>
        <span class="k">${esc(t("rows"))}</span><span class="stepper"><button data-g="r-">−</button><span>${r}</span><button data-g="r+">+</button></span>
      </div>
      <div class="row">
        <label class="small"><input type="checkbox" data-fill ${m.fill.includes(alias) ? "checked" : ""} ${used ? "" : "disabled"}> ${esc(t("fillFree"))}</label>
        <span class="small" style="margin-left:auto">${moved ? `<a href="#" data-g="even">${esc(t("evenLines"))}</a> · ` : ""}${isDef ? esc(t(def.fromProfile ? "defaultGridProfile" : "defaultGrid")) : `<a href="#" data-g="reset" title="${esc(def.fromProfile ? t("resetHintProfile", {name: def.fromProfile}) : "")}">${esc(t("resetTo", {g: `${def.grid[0]}×${def.grid[1]}`}))}</a>`}</span>
      </div>
    </div>`;
  }).join("");
  document.querySelectorAll(".mcard").forEach(card => {
    const alias = card.dataset.mon;
    card.querySelectorAll("[data-g]").forEach(b => b.onclick = (ev) => {
      ev.preventDefault();
      const [c, r] = gridOf(alias), g = b.dataset.g;
      if (g === "reset") {
        const def = defaultGridOf(alias), dw = def.weights;
        setGrid(alias, ...def.grid);
        model().weights = model().weights || {};
        if (dw) model().weights[alias] = clone(dw); else delete model().weights[alias];
        return changed();
      }
      if (g === "even") { setWeights(alias, 0, null); setWeights(alias, 1, null); return changed(); }
      setGrid(alias, c + (g === "c+") - (g === "c-"), r + (g === "r+") - (g === "r-"));
    });
    card.querySelector("[data-fill]").onchange = (ev) => toggleFill(alias, ev.target.checked);
    card.querySelector("[data-rename]").onclick = () => renameMonitor(card, alias);
    card.querySelector("[data-use]").onchange = (ev) => toggleUse(alias, ev.target.checked);
  });
}

function acceptDrop(el, onDrop, onCell = null) {
  const ok = (ev) => ev.dataTransfer.types.includes(DT) || (onCell && ev.dataTransfer.types.includes(DTC));
  el.addEventListener("dragover", ev => { if (ok(ev)) { ev.preventDefault(); ev.stopPropagation(); el.classList.add("over"); } });
  el.addEventListener("dragleave", () => el.classList.remove("over"));
  el.addEventListener("drop", ev => {
    ev.preventDefault(); ev.stopPropagation(); el.classList.remove("over");
    const cell = ev.dataTransfer.getData(DTC);
    if (cell && onCell) return onCell(JSON.parse(cell));
    onDrop(ev.dataTransfer.getData(DT), ev.shiftKey);
  });
}
function bindDnD() {
  document.querySelectorAll("[draggable=true]").forEach(el =>
    el.addEventListener("dragstart", ev => {
      ev.stopPropagation();
      if (el.dataset.dnd) ev.dataTransfer.setData(DTC, el.dataset.dnd);
      else ev.dataTransfer.setData(DT, el.dataset.char);
      ev.dataTransfer.effectAllowed = "move";
    }));
  const onCell = (el) => (d) => moveCellThing(d, placeOf(el));
  document.querySelectorAll(".cell.blocked").forEach(el => {
    el.ondblclick = () => editCell(...placeOf(el));
    acceptDrop(el, () => flash(t("dropOnBlocked"), "warn"), onCell(el));
  });
  document.querySelectorAll(".cell.drop").forEach(el => acceptDrop(el, (char, shift) => {
    if (char) assignTo(char, ...placeOf(el), shift);
  }, onCell(el)));
  document.querySelectorAll(".srow button, .subframe .sgtag").forEach(b => b.onclick = (ev) => {
    ev.stopPropagation();
    const cell = b.closest(".cell, .subframe");
    runAction(b.dataset.act, cell, (b.closest(".srow") || cell).dataset.char);
  });
  document.querySelectorAll(".cell .gear").forEach(b => {
    b.onclick = (ev) => { ev.stopPropagation(); openActMenu(b); };
    b.ondragstart = (ev) => ev.preventDefault();
  });
}
acceptDrop($("palette"), unassign);   // palette = drop target for removing
