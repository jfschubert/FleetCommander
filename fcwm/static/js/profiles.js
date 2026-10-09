// ============================================================ Profiles
function newProfile(base) {
  const key = `*new*${++newCounter}`;
  const m = base ? clone(base.model) : {description: "", fill: [], focus: null, assign: [], disabled: [],
    grids: Object.fromEntries(Object.entries(state.monitor_config).map(([a, mc]) => [a, mc.grid])),
    weights: Object.fromEntries(Object.entries(state.monitor_config).filter(([, mc]) => mc.weights).map(([a, mc]) => [a, mc.weights]))};
  const stem = base ? `${base.name} ${t("copy")}` : t("newProfile");
  const taken = (n) => state.models[n] || Object.values(drafts).some(d => d.name === n);
  let name = stem;
  for (let i = 2; taken(name); i++) name = `${stem} ${i}`;
  drafts[key] = {name, oldName: null, model: m, dirty: true};
  cur = key;
}
async function save() {
  const d = draft();
  try {
    await api("/api/profile", {name: d.name, old_name: d.oldName, model: d.model});
    delete drafts[cur]; cur = d.name;
    flash(t("profileSaved", {name: d.name}));
    await load();
  } catch (e) { flash(e.message, "err"); }
}

// ============================================================ Auto-placement + events
function setAuto(a) {
  auto = a;
  $("autoToggle").checked = $("autoToggle2").checked = a.enabled;
  $("lockToggle").checked = !!a.lock;
  $("autoState").textContent = t("autoShort");
  $("autoBanner").className = "banner" + (a.enabled ? "" : " off");
  $("autoBannerText").textContent = a.enabled ? t("bannerOn", {profile: a.effective_profile || "–"}) : t("bannerOff");
  $("listenerKind").textContent = a.listener + (a.running ? "" : " (stopped)");
  const names = Object.keys(state?.models || {});
  $("autoProfile").innerHTML = `<option value="">${esc(t("defaultProfile"))} (${esc(state?.default_profile || "–")})</option>` +
    names.map(n => `<option ${n === a.profile ? "selected" : ""}>${esc(n)}</option>`).join("");
}
async function updateAuto(patch) {
  try { setAuto(await api("/api/auto", patch)); } catch (e) { toast(t("tError"), e.message, "err"); }
}
$("autoToggle").onchange = (ev) => updateAuto({enabled: ev.target.checked});
$("autoToggle2").onchange = (ev) => updateAuto({enabled: ev.target.checked});
$("autoProfile").onchange = (ev) => updateAuto({profile: ev.target.value || null});

function eventText(e) {
  switch (e.type) {
    case "login": return t(e.auto ? "evLoginAuto" : "evLogin", {char: e.char});
    case "closed": return t("evClosed", {char: e.char});
    case "placed": return [e.items.map(i => t("evPlaced", i)).join(", "),
                           e.unplaced.length ? t("evUnplaced", {list: e.unplaced.join(", ")}) : ""].filter(Boolean).join(" · ");
    case "profile": return t("evProfile", {name: e.name, n: e.placed});
    case "windows": return t("evWindows", {list: e.items.map(i => t("evPlaced", {char: i.char || "?", slot: i.slot})).join(", ")});
    case "error": return e.message;
    case "auto": return e.enabled ? t("evAutoOn", {profile: e.effective_profile}) : t("evAutoOff");
  }
  return JSON.stringify(e);
}
function logEvent(e, live = true) {
  if (e.type === "placed" && !e.items.length && !e.unplaced.length) return;
  const li = document.createElement("li");
  const time = new Date(e.ts * 1000).toLocaleTimeString(bcp47(), {hour: "2-digit", minute: "2-digit", second: "2-digit"});
  li.innerHTML = `<time>${time}</time><span class="${e.type}">${esc(eventText(e))}</span>`;
  $("log").prepend(li);
  while ($("log").children.length > 100) $("log").lastChild.remove();
  if (!live) return;
  if (e.type === "login") toast(t("tNew"), eventText(e));
  if (e.type === "placed") toast(t("tPlaced"), eventText(e), e.unplaced.length ? "warn" : "ok");
  if (e.type === "error") toast(t("tError"), e.message, "err");
  if (e.type === "profile") toast(t("tProfile"), eventText(e), "ok");
}
function connectEvents() {
  const es = new EventSource("/api/events");
  // Status indicator "Service": connection to the running fcwm (event stream)
  const status = (on) => { $("live").classList.toggle("on", on); $("live").title = t(on ? "serviceOn" : "serviceOff"); };
  es.onopen = () => status(true);
  es.onerror = () => status(false);
  es.onmessage = (m) => {
    const e = JSON.parse(m.data);
    if (e.type === "auto") { setAuto(e); logEvent(e); return; }
    logEvent(e);
    if (["login", "closed", "placed", "profile", "windows"].includes(e.type)) scheduleRefresh();
  };
}
$("clearlog").onclick = () => { $("log").innerHTML = ""; };
