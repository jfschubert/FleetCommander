// ============================================================ Model operations
// A place is (monitor, slot, sub): sub is null for a normal cell, otherwise the cell in the
// subgrid of that slot ("center:1.3").
const subOf = (x) => (x.sub === undefined || x.sub === null || x.sub === "") ? null : +x.sub;
const sl = (slot, sub) => sub === null || sub === undefined ? `${slot}` : `${slot}.${sub}`;
const placeOf = (el) => [el.dataset.mon, +el.dataset.slot, el.dataset.sub === "" || el.dataset.sub === undefined ? null : +el.dataset.sub];
const placeAttrs = (mon, slot, sub) => `data-mon="${esc(mon)}" data-slot="${slot}" data-sub="${sub ?? ""}"`;

const gridOf = (alias) => model().grids[alias] || state.monitor_config[alias].grid;
// Subgrids: model().subgrids = [{monitor, slot, grid: [c, r], weights: [cw|null, rw|null] | null}]
const subgridOf = (mon, slot) => (model().subgrids || []).find(g => g.monitor === mon && g.slot === slot);

// Grid line weights. Stored as [columns|null, rows|null, {row: columns}|null] –
// on the monitor (model().weights[alias]) or on the subgrid (sg.weights). Target: slot = null -> monitor grid.
function weightEntry(alias, slot, create = false) {
  const m = model();
  if (slot !== null) {
    const sg = subgridOf(alias, slot);
    if (!sg) return null;
    if (create && !sg.weights) sg.weights = [null, null, null];
    return sg.weights;
  }
  m.weights = m.weights || {};
  if (create && !m.weights[alias]) m.weights[alias] = [null, null, null];
  return m.weights[alias] || null;
}
function cleanEntry(alias, slot) {
  const e = weightEntry(alias, slot);
  if (!e) return;
  while (e.length < 3) e.push(null);
  if (e[2] && !Object.keys(e[2]).length) e[2] = null;
  if (!e[0] && !e[1] && !e[2]) {
    if (slot !== null) subgridOf(alias, slot).weights = null; else delete model().weights[alias];
  }
}
const gridFor = (alias, slot) => slot === null ? gridOf(alias) : subgridOf(alias, slot).grid;
function weightsOf(alias, axis, slot = null, row = null) {
  const n = gridFor(alias, slot)[axis], e = weightEntry(alias, slot) || [];
  const ok = (w) => w && w.length === n;
  if (axis === 0 && row !== null && e[2] && ok(e[2][row])) return e[2][row];
  return ok(e[axis]) ? e[axis] : Array(n).fill(1);
}
const sameRatio = (a, b) => {
  const sa = a.reduce((x, y) => x + y, 0), sb = b.reduce((x, y) => x + y, 0);
  return a.length === b.length && a.every((x, i) => Math.abs(x / sa - b[i] / sb) < 1e-4);
};
// w = null resets the axis (for columns incl. all row overrides)
function setWeights(alias, axis, w, slot = null, row = null) {
  const e = weightEntry(alias, slot, true);
  if (!e) return;
  while (e.length < 3) e.push(null);
  if (axis === 0 && row !== null) {           // this row only
    const rc = e[2] || {};
    if (!w || sameRatio(w, weightsOf(alias, 0, slot))) delete rc[row]; else rc[row] = w;
    e[2] = rc;
  } else {
    const uniform = !w || w.every(x => Math.abs(x - w[0]) < 1e-6);
    e[axis] = uniform ? null : w;
    if (axis === 0 && !w) e[2] = null;
  }
  cleanEntry(alias, slot);
}
function dropRowOverrides(alias, slot, rows) {   // remove row overrides beyond the new row count
  const e = weightEntry(alias, slot);
  if (e && e[2]) { for (const r of Object.keys(e[2])) if (+r >= rows) delete e[2][r]; cleanEntry(alias, slot); }
}
// Occupied places of an assignment as keys: "3" (main cell) or "1.2" (subgrid cell)
function covered(a) {
  if (subOf(a) !== null) return [sl(a.slot, subOf(a))];
  const [cols] = gridOf(a.monitor), c0 = a.slot % cols, r0 = Math.floor(a.slot / cols), out = [];
  for (let r = 0; r < a.span[1]; r++) for (let c = 0; c < a.span[0]; c++) out.push(`${(r0 + r) * cols + c0 + c}`);
  return out;
}
// Stack = several assignments on exactly the same place; the first entry in model().assign is on top.
const sameStack = (a, o) => o !== a && o.monitor === a.monitor && o.slot === a.slot && subOf(o) === subOf(a);
const stackOf = (a) => model().assign.filter(o => o === a || sameStack(a, o));
function fits(a) {
  if (subOf(a) !== null) return true;
  const [cols, rows] = gridOf(a.monitor), c0 = a.slot % cols, r0 = Math.floor(a.slot / cols);
  if (c0 + a.span[0] > cols || r0 + a.span[1] > rows) return false;
  const mine = covered(a);
  if (a.span[0] * a.span[1] > 1 && mine.some(k => subgridOf(a.monitor, +k))) return false;  // do not span across subgrids
  const set = new Set(mine);
  return !model().assign.some(o => o !== a && !sameStack(a, o) && o.monitor === a.monitor && covered(o).some(k => set.has(k)));
}
function toTop(a) {   // move a in the array before the first stack member
  const m = model(), first = m.assign.findIndex(o => o === a || sameStack(a, o));
  m.assign.splice(m.assign.indexOf(a), 1);
  m.assign.splice(first, 0, a);
}
function assignTo(char, monitor, slot, sub = null, swap = false, pinAuto = true) {
  const m = model(), prev = m.assign.find(a => a.char === char), key = sl(slot, sub);
  if (prev && prev.monitor === monitor && covered(prev).includes(key)) return;
  let occupants = m.assign.filter(o => o !== prev && o.monitor === monitor && covered(o).includes(key));
  if (!occupants.length && !swap && pinAuto) {
    // place is only auto-occupied: pin these clients here so they get stacked
    const autos = plan.placements.filter(p => p.auto && p.char !== char && p.monitor === monitor && p.slot === slot && subOf(p) === sub);
    occupants = autos.map(p => ({char: p.char, monitor, slot, sub, span: [1, 1]}));
    m.assign.push(...occupants);
  }
  const a = prev || {char, monitor, slot, sub, span: [1, 1]};
  if (!prev) m.assign.push(a);
  if (occupants.length && swap) {         // Shift: swap
    for (const o of occupants) {
      if (prev) { o.monitor = prev.monitor; o.slot = prev.slot; o.sub = subOf(prev); o.span = [1, 1]; }
      else m.assign.splice(m.assign.indexOf(o), 1);
    }
    a.monitor = monitor; a.slot = slot; a.sub = sub;
    if (!fits(a)) a.span = [1, 1];
    for (const o of occupants) if (m.assign.includes(o) && !fits(o)) m.assign.splice(m.assign.indexOf(o), 1);
  } else if (occupants.length) {          // default: put on the existing stack (on top)
    const base = occupants[0];
    a.monitor = base.monitor; a.slot = base.slot; a.sub = subOf(base);
    a.span = subOf(base) === null ? [...base.span] : [1, 1];
    toTop(a);
  } else {
    a.monitor = monitor; a.slot = slot; a.sub = sub;
    if (sub !== null || !fits(a)) a.span = [1, 1];
  }
  changed();
}
function unassign(char) {
  const m = model(), i = m.assign.findIndex(a => a.char === char);
  if (i >= 0) { m.assign.splice(i, 1); changed(); }
}
function raiseInStack(char) {
  const a = model().assign.find(x => x.char === char);
  if (a) { toTop(a); changed(); }
}
function growSpan(char, axis) {   // applies to the whole stack; not in subgrids
  const a = model().assign.find(x => x.char === char);
  if (!a || subOf(a) !== null) return;
  const stack = stackOf(a);
  a.span[axis]++;
  if (!fits(a)) a.span[axis] = 1;
  stack.forEach(o => { o.span = [...a.span]; });
  changed();
}
// Preserve position (column/row) when changing a grid; null = drops out
function remap(idx, oc, cols, rows) {
  const c = idx % oc, r = Math.floor(idx / oc);
  return c >= cols || r >= rows ? null : r * cols + c;
}
function setGrid(alias, cols, rows) {
  cols = Math.max(1, Math.min(12, cols)); rows = Math.max(1, Math.min(12, rows));
  const [oc, or] = gridOf(alias), m = model(), dropped = [];
  m.blocked = (m.blocked || []).filter(b => b.monitor !== alias || (b.slot = remap(b.slot, oc, cols, rows)) !== null);
  m.subgrids = (m.subgrids || []).filter(g => g.monitor !== alias || (g.slot = remap(g.slot, oc, cols, rows)) !== null);
  m.overflow = (m.overflow || []).filter(o => o.monitor !== alias || (o.slot = remap(o.slot, oc, cols, rows)) !== null);
  remapHotkeys((mon, slot, sub) => mon !== alias ? [mon, slot, sub] : (n => n === null ? null : [mon, n, sub])(remap(slot, oc, cols, rows)));
  if (cols !== oc) setWeights(alias, 0, null);   // column count changed -> lines evenly spaced
  if (rows !== or) { setWeights(alias, 1, null); dropRowOverrides(alias, null, rows); }
  for (const a of [...m.assign].filter(a => a.monitor === alias)) {
    const n = remap(a.slot, oc, cols, rows);
    if (n === null) { m.assign.splice(m.assign.indexOf(a), 1); dropped.push(a.char); continue; }
    const c = n % cols, r = Math.floor(n / cols);
    a.slot = n;
    a.span = [Math.min(a.span[0], cols - c), Math.min(a.span[1], rows - r)];
  }
  m.grids[alias] = [cols, rows];
  for (const a of m.assign.filter(a => a.monitor === alias)) if (!fits(a)) stackOf(a).forEach(o => { o.span = [1, 1]; });
  if (dropped.length) flash(t("droppedGrid", {list: dropped.join(", ")}), "warn");
  changed();
}
