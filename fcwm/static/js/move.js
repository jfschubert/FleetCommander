// ---- Moving cell types: reserved cells (incl. preview), overflow, hotkeys, subgrids
const DTC = "application/x-fcwm-cell";
const samePlace = (x, mon, slot, sub) => x.monitor === mon && x.slot === slot && subOf(x) === sub;
function movePinnedChars(from, to) {   // move characters pinned exactly to `from` over to `to`
  for (const a of model().assign.filter(a => samePlace(a, ...from))) { a.monitor = to[0]; a.slot = to[1]; a.sub = to[2]; a.span = [1, 1]; }
}
function moveCellThing(d, to) {
  const m = model(), [mon, slot, sub] = to;
  if (d.kind === "blocked") {
    const from = [d.mon, d.slot, d.sub], b = blockedAt(...from), other = blockedAt(mon, slot, sub);
    if (!b || (mon === d.mon && slot === d.slot && sub === d.sub)) return;
    if (other) { other.monitor = d.mon; other.slot = d.slot; other.sub = d.sub; }
    const tmp = [d.mon, d.slot, d.sub];
    // characters at the target swap with the previous place (it was reserved there)
    const there = m.assign.filter(a => samePlace(a, mon, slot, sub));
    there.forEach(a => { a.monitor = tmp[0]; a.slot = tmp[1]; a.sub = tmp[2]; a.span = [1, 1]; });
    const oi = overflowIdx(mon, slot, sub);
    if (oi >= 0) { const o = m.overflow[oi]; o.monitor = tmp[0]; o.slot = tmp[1]; o.sub = tmp[2]; }
    b.monitor = mon; b.slot = slot; b.sub = sub;
  } else if (d.kind === "overflow") {
    const o = (m.overflow || [])[d.i];
    if (!o) return;
    if (blockedAt(mon, slot, sub)) return flash(t("dropOnBlocked"), "warn");
    const oi = overflowIdx(mon, slot, sub);
    if (oi >= 0 && oi !== d.i) { const x = m.overflow[oi]; x.monitor = o.monitor; x.slot = o.slot; x.sub = subOf(o); }
    o.monitor = mon; o.slot = slot; o.sub = sub;
  } else if (d.kind === "hotkey") {
    const hk = m.stack_hotkeys || {}, key = `${mon}:${sl(slot, sub)}`;
    if (!hk[d.key] || key === d.key) return;
    const mine = hk[d.key], theirs = hk[key];
    delete hk[d.key];
    if (theirs) hk[d.key] = theirs;
    hk[key] = mine;
  } else if (d.kind === "stackpreview") {
    const sp = m.stack_previews || {}, key = `${mon}:${sl(slot, sub)}`;
    if (!sp[d.key] || key === d.key) return;
    const mine = sp[d.key], theirs = sp[key];
    delete sp[d.key];
    if (theirs) sp[d.key] = theirs;
    sp[key] = mine;
  } else if (d.kind === "subgrid") {
    if (sub !== null) return flash(t("subgridTarget"), "warn");
    const sg = subgridOf(d.mon, d.slot);
    if (!sg || (mon === d.mon && slot === d.slot)) return;
    if (subgridOf(mon, slot) || blockedAt(mon, slot, null)) return flash(t("subgridTarget"), "warn");
    // main-cell content at the target moves to the old place, subcell content moves along
    movePinnedChars([mon, slot, null], [d.mon, d.slot, null]);
    const inSub = (x) => x.monitor === d.mon && x.slot === d.slot && subOf(x) !== null;
    [...m.assign, ...(m.blocked || []), ...(m.overflow || [])].filter(inSub).forEach(x => { x.monitor = mon; x.slot = slot; });
    remapHotkeys((mo, s_, su) => mo === d.mon && s_ === d.slot && su !== null ? [mon, slot, su] : [mo, s_, su]);
    if (sg.weights === undefined) sg.weights = null;
    sg.monitor = mon; sg.slot = slot;
  } else return;
  changed();
}

function toggleUse(alias, on) {
  // assignments are kept (non-destructive) – the server fills them elsewhere in the meantime
  const m = model(), set = new Set(m.disabled || []);
  on ? set.delete(alias) : set.add(alias);
  m.disabled = Object.keys(state.monitor_config).filter(a => set.has(a));
  changed();
}
function toggleFill(alias, on) {
  const m = model(), order = Object.keys(state.monitor_config), set = new Set(m.fill);
  on ? set.add(alias) : set.delete(alias);
  m.fill = order.filter(a => set.has(a));
  changed();
}
