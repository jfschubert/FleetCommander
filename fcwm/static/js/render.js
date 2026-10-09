// ============================================================ Rendering
function renderHeader() {
  const keys = [...Object.keys(state.models), ...Object.keys(drafts).filter(k => !state.models[k])];
  $("tabs").innerHTML = keys.map(k => {
    const d = drafts[k], name = d ? d.name : k;
    return `<button class="tab ${k === cur ? "active" : ""}" data-k="${esc(k)}">${esc(name)}` +
      (k === state.default_profile ? `<span class="def" title="${esc(t("defaultProfile"))}">★</span>` : "") +
      (auto && k === auto.effective_profile ? `<span class="act" title="${esc(t("activeProfile"))}">▸</span>` : "") +
      (d && d.dirty ? `<span class="dirty" title="${esc(t("unsaved"))}">◆</span>` : "") + `</button>`;
  }).join("") + `<button class="tab" id="newtab" title="${esc(t("newProfile"))}">＋</button>`;
  document.querySelectorAll(".tab[data-k]").forEach(b => b.onclick = () => { cur = b.dataset.k; renderHeader(); preview(); });
  $("newtab").onclick = () => { newProfile(); renderHeader(); preview(); };

  const d = draft();
  if (document.activeElement !== $("pname")) $("pname").value = d.name;
  if (document.activeElement !== $("pdesc")) $("pdesc").value = d.model.description || "";
  if (document.activeElement !== $("photkey")) { $("photkey").value = d.model.hotkey || ""; $("photkey").placeholder = t("noKey"); }
  $("save").disabled = !d.dirty;
  $("discard").disabled = !d.dirty;
}

// Display name of a monitor: custom name > model from the EDID data (with the connector for
// identical models, e.g. "DELL G3223Q · DP-1") > connector or alias. ★ marks the primary monitor.
function monitorDefaultName(mon) {
  if (!mon) return "";
  if (!mon.model) return mon.name;
  const same = state.monitors.filter(o => o.model === mon.model).length > 1;
  return same ? `${mon.model} · ${mon.name}` : mon.model;
}
const monitorOf = (alias) => state.monitors.find(m => m.name === (state.monitor_config[alias] || {}).output);
function monitorLabel(alias) {
  const mc = state.monitor_config[alias] || {};
  return mc.label || monitorDefaultName(monitorOf(alias)) || alias;
}
const primaryStar = (mon) => (mon && mon.primary ? " ★" : "");

function renderSidebar() {
  const n = Object.keys(state.clients).length;
  $("cfgpath").textContent = $("cfgpathTop").textContent = state.config_path;
  $("clientCount").textContent = n;
  const clients = Object.entries(state.clients).sort((a, b) => a[0].localeCompare(b[0]));
  $("clients").innerHTML = clients.length ? clients.map(([c, w]) =>
    `<li><span>${esc(c)}</span><span class="small">${esc(w.output || "")}</span></li>`).join("")
    : `<li class="small">${esc(t("noClients"))}</li>`;
  renderDebug();
  renderAbout();
}

function allChars() {
  const set = new Set([...Object.keys(state.clients), ...extraChars]);
  for (const m of Object.values(state.models)) m.assign.forEach(a => set.add(a.char));
  model().assign.forEach(a => set.add(a.char));
  return [...set].sort((a, b) => a.localeCompare(b));
}

function renderEditor() {
  const m = model(), chars = allChars();
  $("pfocus").innerHTML = `<option value="">${esc(t("none"))}</option>` +
    chars.map(c => `<option ${c === m.focus ? "selected" : ""}>${esc(c)}</option>`).join("");

  const placedBy = Object.fromEntries(plan.placements.map(p => [p.char, p]));
  const pinned = Object.fromEntries(m.assign.map(a => [a.char, a]));
  $("palette").innerHTML = chars.map(c => {
    const open = !!state.clients[c], a = pinned[c], p = placedBy[c];
    const cls = a ? "pinned" : p ? "auto" : open ? "unplaced" : "";
    const where = a ? `${a.monitor}:${sl(a.slot, subOf(a))}` : p ? `${t("auto")} ${p.monitor}:${sl(p.slot, subOf(p))}` : open ? t("noSpace") : "";
    return `<span class="chip ${cls} ${open ? "open" : ""}" draggable="true" data-char="${esc(c)}" title="${esc(open ? t("loggedIn") : t("notLoggedIn"))}">` +
      `<span class="dot"></span>${esc(c)}${where ? `<span class="where">${esc(where)}</span>` : ""}</span>`;
  }).join("") || `<span class="small">${esc(t("noChars"))}</span>`;

  drawCanvas();
  drawMonitorCards();

  const msgs = [];
  if (plan.unplaced.length) msgs.push(`<div class="msg warn">${esc(t("unplaced", {list: plan.unplaced.join(", ")}))}</div>`);
  plan.warnings.forEach(w => msgs.push(`<div class="msg warn">${esc(w)}</div>`));
  $("planmsgs").innerHTML = msgs.join("");
  bindDnD();
}

// ---- Actions of a cell (⚙ menu)
const ACTIONS = {
  pin: {g: PIN, l: "pinHere"}, w: {g: ic("wider"), l: "wider"}, h: {g: ic("taller"), l: "taller"},
  hk: {g: ic("key"), l: "setHotkey"}, spv: {g: ic("preview"), l: "setStackPreview"}, split: {g: ic("split"), l: "splitCell"},
  overflow: {g: ic("overflow"), l: "makeOverflow"}, block: {g: ic("ban"), l: "blockCell"}, edit: {g: ic("pencil"), l: "editCell"},
  x: {g: ic("close"), l: "remove", danger: true}, unblock: {g: ic("close"), l: "unblockCell", danger: true},
};
const gear = (acts) => `<button class="gear" draggable="false" data-acts="${acts.join(" ")}" aria-haspopup="menu" title="${esc(t("actionsFor", {cell: ""}).replace(/ · $/, ""))}"><svg><use href="#i-cog"/></svg></button>`;
function runAction(act, cell, char) {
  const [mon, slot, sub] = placeOf(cell);
  ({pin: () => assignTo(char, mon, slot, sub, false, false), w: () => growSpan(char, 0),
    h: () => growSpan(char, 1), x: () => unassign(char), up: () => raiseInStack(char),
    block: () => blockCell(mon, slot, sub), unblock: () => unblockCell(mon, slot, sub),
    edit: () => editCell(mon, slot, sub), split: () => splitCell(mon, slot),
    overflow: () => addOverflow(mon, slot, sub), hk: () => openHkPop(mon, slot, sub), spv: () => openSpPop(mon, slot, sub),
    subedit: () => openSubPop(mon, slot)})[act]?.();
}
// items: [{g, l (text), danger, disabled, run}] or "-" as a separator line
function openMenu(anchor, head, items) {
  const menu = $("actmenu");
  closeMenu();
  menu.innerHTML = (head ? `<div class="mh">${esc(head)}</div>` : "") + items.map((it, i) => it === "-" ? "<hr>" :
    `<button role="menuitem" data-i="${i}" class="${it.danger ? "danger" : ""}" ${it.disabled ? "disabled" : ""}><span class="g">${it.g || ""}</span>${esc(it.l)}</button>`).join("");
  menu.querySelectorAll("button[data-i]").forEach(b => b.onclick = (ev) => {
    ev.stopPropagation(); closeMenu(); items[+b.dataset.i].run();
  });
  menu.style.display = "block";
  const r = anchor.getBoundingClientRect();
  menu.style.left = Math.max(8, Math.min(innerWidth - menu.offsetWidth - 8, r.right - menu.offsetWidth)) + "px";
  menu.style.top = (r.bottom + menu.offsetHeight + 8 > innerHeight ? Math.max(8, r.top - menu.offsetHeight - 4) : r.bottom + 4) + "px";
  anchor.classList.add("open");
  menu._anchor = anchor;
  menu.querySelector("button:not(:disabled)")?.focus();
}
function closeMenu() {
  const menu = $("actmenu");
  if (menu.style.display !== "block") return;
  menu.style.display = "none";
  menu._anchor?.classList.remove("open");
}
function openActMenu(btn) {
  const cell = btn.closest(".cell"), [mon, slot, sub] = placeOf(cell), char = cell.dataset.char;
  openMenu(btn, t("actionsFor", {cell: `${mon}:${sl(slot, sub)}`}), btn.dataset.acts.split(" ").map(a =>
    ({g: ACTIONS[a].g, l: t(ACTIONS[a].l), danger: ACTIONS[a].danger, run: () => runAction(a, cell, char)})));
}
document.addEventListener("click", (ev) => { if (!ev.target.closest("#actmenu")) closeMenu(); });
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeMenu(); });
window.addEventListener("scroll", closeMenu, true);

function drawCanvas() {
  const cv = $("canvas"), mons = state.monitors;
  const minX = Math.min(...mons.map(m => m.geometry[0])), minY = Math.min(...mons.map(m => m.geometry[1]));
  const maxX = Math.max(...mons.map(m => m.geometry[0] + m.geometry[2])), maxY = Math.max(...mons.map(m => m.geometry[1] + m.geometry[3]));
  const s = cv.clientWidth / (maxX - minX);
  cv.style.height = Math.round((maxY - minY) * s) + "px";
  const box = (r, cls, inner = "", attrs = "") =>
    `<div class="${cls}" ${attrs} style="left:${(r[0]-minX)*s}px;top:${(r[1]-minY)*s}px;width:${r[2]*s}px;height:${r[3]*s}px">${inner}</div>`;
  const small = (r) => r[2] * s < 90 || r[3] * s < 60;   // label very small cells more compactly

  const aliasOf = Object.fromEntries(Object.entries(state.monitor_config).filter(([, mc]) => mc.output).map(([a, mc]) => [mc.output, a]));
  Object.entries(plan.layouts).forEach(([a, l]) => { aliasOf[l.output] = a; });
  const off = new Set(plan.disabled);
  let html = mons.map(m => {
    const alias = aliasOf[m.name], unused = alias && off.has(alias);
    return box(m.geometry, `mon ${unused ? "unused" : ""}`,
      `<span class="label">${esc(alias ? monitorLabel(alias) : monitorDefaultName(m))}${primaryStar(m)} · ` +
      `${esc(alias ? alias + (unused ? " · " + t("unused") : "") : t("notConfigured"))}</span>`);
  }).join("");

  // occupied places ("mon:3" or "mon:1.2")
  const taken = new Set();
  const mark = (x, span = [1, 1]) => {
    const sub = subOf(x);
    if (sub !== null) return taken.add(`${x.monitor}:${sl(x.slot, sub)}`);
    const [cols] = plan.layouts[x.monitor].grid;
    for (let r = 0; r < span[1]; r++) for (let c = 0; c < span[0]; c++) taken.add(`${x.monitor}:${x.slot + r * cols + c}`);
  };
  plan.placements.forEach(p => mark(p, p.span));
  plan.reserved.forEach(p => mark(p, p.span));
  plan.blocked.forEach(b => mark(b));

  const ofKeys = new Set((plan.overflow || []).map(o => `${o.monitor}:${sl(o.slot, subOf(o))}`));
  const emptyActs = (mon, slot, sub) => [...(ofKeys.has(`${mon}:${sl(slot, sub)}`) ? [] : ["overflow"]), "hk", "spv",
                                          ...(sub === null ? ["split"] : []), "block"];
  for (const [alias, lay] of Object.entries(plan.layouts)) {
    html += box(lay.area, "area");
    lay.cells.forEach((c, i) => {
      const sg = (lay.subgrids || {})[i];
      if (sg) {   // frame of the split cell + empty subcells
        html += box(c, "subframe", `<button class="sgtag" data-act="subedit" draggable="true" data-dnd="${esc(JSON.stringify({kind: "subgrid", mon: alias, slot: i}))}" title="${esc(t("editSubgrid") + " · " + t("dragCellType"))}">${ic("split")} ${sg.grid[0]}×${sg.grid[1]}</button>`,
                    `data-mon="${esc(alias)}" data-slot="${i}"`);
        sg.cells.forEach((sc, j) => {
          if (!taken.has(`${alias}:${i}.${j}`))
            html += box(sc, `cell drop subcell ${small(sc) ? "tiny" : ""} ${ofKeys.has(`${alias}:${i}.${j}`) ? "ofl" : ""}`, gear(emptyActs(alias, i, j)) +
                        `<span class="idx">${esc(alias)}:${i}.${j}</span><span class="sub">${sc[2]}×${sc[3]}</span>`, placeAttrs(alias, i, j));
        });
      } else if (!taken.has(`${alias}:${i}`)) {
        html += box(c, `cell drop ${ofKeys.has(`${alias}:${i}`) ? "ofl" : ""}`, gear(emptyActs(alias, i, null)) +
                    `<span class="idx">${esc(alias)}:${i}</span><span class="sub">${c[2]}×${c[3]}</span>`, placeAttrs(alias, i, null));
      }
    });
  }
  for (const b of plan.blocked) {
    const wins = b.windows || [];
    const sub = b.preview ? t(b.preview === "hidden" ? "pvHidden" : "pvAll")
              : wins.length > 1 ? t("windowsN", {n: wins.length}) : b.window ? `→ ${b.window}`
              : b.match ? `≈ ${b.match} · ${t("notOpen")}` : b.catch_all ? "" : t("keptFreeSub");
    const bdnd = esc(JSON.stringify({kind: "blocked", mon: b.monitor, slot: b.slot, sub: subOf(b)}));
    const tiny = small(b.rect);
    html += box(b.rect, `cell blocked ${b.preview ? "preview" : ""} ${tiny ? "tiny" : ""}`,
      gear(["edit", "hk", "unblock"]) +
      `<span class="bl">${b.preview ? ic("preview") + " " : ""}${esc(b.label || (b.preview ? t("preview") : b.catch_all ? t("catchAll") : t("keptFree")))}</span>` +
      (b.catch_all && b.label ? `<span class="catch">${esc(t("catchAll"))}</span>` : "") +
      `<span class="sub">${esc(sub)}</span>` +
      (wins.length > 1 && !tiny ? `<div class="wlist">${wins.map(w => `<div title="${esc(w)}">${esc(w)}</div>`).join("")}</div>` : "") +
      `<span class="idx">${esc(b.monitor)}:${sl(b.slot, subOf(b))}</span>`,
      placeAttrs(b.monitor, b.slot, subOf(b)) + ` draggable="true" data-dnd="${bdnd}" title="${esc(t("dragCellType"))}"`);
  }

  const tools = (auto, inSub) => gear(auto ? ["pin", "hk", "spv"] : ["hk", "spv", ...(inSub ? [] : ["w", "h"]), "x"]);

  // group placements + offline-reserved places by stack (monitor:slot[.sub])
  const order = Object.fromEntries(model().assign.map((a, i) => [a.char, i]));
  const items = [
    ...plan.placements.map(p => ({...p, kind: p.auto ? "auto" : "pinned"})),
    ...plan.reserved.map(p => ({...p, kind: "offline", auto: false})),
  ];
  const stacks = {};
  for (const it of items) (stacks[`${it.monitor}:${sl(it.slot, subOf(it))}`] ??= []).push(it);
  const rank = (it) => it.auto ? 1e6 : (order[it.char] ?? 1e5);

  for (const members of Object.values(stacks)) {
    members.sort((a, b) => rank(a) - rank(b));
    const top = members[0], sub = subOf(top), inSub = sub !== null, tiny = small(top.rect) ? "tiny" : "";
    const where = placeAttrs(top.monitor, top.slot, sub), idx = `${esc(top.monitor)}:${sl(top.slot, sub)}`;
    if (members.length === 1) {
      const info = top.kind === "offline" ? t("notLoggedIn") : `${top.rect[2]}×${top.rect[3]}${top.auto ? " · " + t("auto") : ""}`;
      html += box(top.rect, `cell p drop ${top.kind} ${inSub ? "subcell" : ""} ${tiny}`,
        `${tools(top.auto, inSub)}<span class="nm">${esc(top.char)}</span><span class="sub">${esc(info)}</span><span class="idx">${idx}</span>`,
        `draggable="true" data-char="${esc(top.char)}" ${where}`);
      continue;
    }
    const rows = members.map((it, i) => {
      const btns = it.auto
        ? `<button data-act="pin" title="${esc(t("pinHere"))}">${PIN}</button>`
        : (i > 0 ? `<button data-act="up" title="${esc(t("toTop"))}">${ic("up")}</button>` : "") +
          `<button data-act="x" title="${esc(t("remove"))}">${ic("close")}</button>`;
      return `<div class="srow ${it.kind} ${i === 0 ? "top" : ""}" draggable="true" data-char="${esc(it.char)}">` +
        `<span class="nm">${esc(it.char)}</span><span class="sbtn">${btns}</span></div>`;
    }).join("");
    const stackTools = gear(["hk", "spv", ...(top.auto || inSub ? [] : ["w", "h"])]);
    html += box(top.rect, `cell p drop stack ${top.kind} ${inSub ? "subcell" : ""} ${tiny}`,
      `${stackTools}<div class="shead">${esc(t("stack", {n: members.length}))}</div><div class="slist">${rows}</div>` +
      `<span class="idx">${idx} · ${top.rect[2]}×${top.rect[3]}</span>`,
      `data-char="${esc(top.char)}" ${where}`);
  }

  // Badges: overflow order/max and stack hotkeys
  const at = (r, dx, dy, cls, text, attrs) =>
    `<span class="badge ${cls}" ${attrs} style="left:${(r[0] - minX) * s + dx}px;top:${(r[1] - minY) * s + dy}px">${esc(text)}</span>`;
  (plan.overflow || []).forEach((o, i) => {
    html += at(o.rect, 4, 3, "of", `${ic("overflow")} ${o.order} · ${o.max ? "max " + o.max : "∞"}${o.count ? " · " + o.count : ""}`,
               `data-i="${i}" draggable="true" data-dnd="${esc(JSON.stringify({kind: "overflow", i}))}" title="${esc(t("dragCellType"))}"`);
  });
  for (const [k, keys] of Object.entries(model().stack_hotkeys || {})) {
    const [mon, rest] = k.split(":"), [slot, sub] = rest.split(".");
    const lay = plan.layouts[mon];
    if (!lay) continue;
    const rect = sub === undefined ? lay.cells[+slot] : ((lay.subgrids || {})[slot] || {cells: []}).cells[+sub];
    if (rect) html += at(rect, 4, Math.max(22, rect[3] * s - 40), "hk", `${ic("key")} ${keys}`, placeAttrs(mon, +slot, sub === undefined ? null : +sub) +
                         ` draggable="true" data-dnd="${esc(JSON.stringify({kind: "hotkey", key: k}))}" title="${esc(t("dragCellType"))}"`);
  }

  for (const sp of plan.stack_previews || []) {
    html += box(sp.rect, "spstrip", "");
    const label = `${ic("preview")} ${t(sp.mode === "all" ? "spvAllShort" : "spvStackShort")}`;
    html += at(sp.stack, Math.max(4, sp.stack[2] * s - 110), 3, "sp", label, placeAttrs(sp.monitor, sp.slot, sp.sub) +
               ` draggable="true" data-dnd="${esc(JSON.stringify({kind: "stackpreview", key: sp.key}))}" title="${esc(t("dragCellType"))}"`);
  }

  // Movable grid lines (monitor grid and subgrids)
  canvasMap = {minX, minY, s};
  const lines = (alias, slot, area, grid, c) => {
    const [cols, rows] = grid, attrs = `data-mon="${esc(alias)}" data-gslot="${slot ?? ""}"`, cls = slot === null ? "" : "sg";
    for (let r = 0; r < rows; r++) {
      for (let k = 0; k < cols - 1; k++) {
        const a = c[r * cols + k], b = c[r * cols + k + 1], x = (a[0] + a[2] + b[0]) / 2;
        const top = r === 0 ? area[1] : a[1], bottom = r === rows - 1 ? area[1] + area[3] : a[1] + a[3];
        html += `<div class="gl v ${cls}" ${attrs} data-axis="0" data-k="${k}" data-row="${r}" title="${esc(t(rows > 1 ? "dragLineRow" : "dragLine"))}"
          style="left:${(x - minX) * s}px;top:${(top - minY) * s}px;height:${(bottom - top) * s}px"></div>`;
      }
    }
    for (let k = 0; k < rows - 1; k++) {
      const i = k * cols, y = (c[i][1] + c[i][3] + c[i + cols][1]) / 2;
      html += `<div class="gl h ${cls}" ${attrs} data-axis="1" data-k="${k}" title="${esc(t("dragLine"))}"
        style="top:${(y - minY) * s}px;left:${(area[0] - minX) * s}px;width:${area[2] * s}px"></div>`;
    }
  };
  for (const [alias, lay] of Object.entries(plan.layouts)) {
    lines(alias, null, lay.area, lay.grid, lay.cells);
    for (const [slot, sg] of Object.entries(lay.subgrids || {})) lines(alias, +slot, lay.cells[+slot], sg.grid, sg.cells);
  }
  cv.innerHTML = html;
  cv.querySelectorAll(".gl").forEach(el => el.onpointerdown = startLineDrag);
  cv.querySelectorAll(".badge.of").forEach(el => el.onclick = () => openOfPop(+el.dataset.i));
  cv.querySelectorAll(".badge.hk").forEach(el => el.onclick = () => openHkPop(...placeOf(el)));
  cv.querySelectorAll(".badge.sp").forEach(el => el.onclick = () => openSpPop(...placeOf(el)));
}
