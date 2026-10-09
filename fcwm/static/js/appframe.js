// Custom window frame in the app window (`fcwm app`): the Qt window has no KDE title bar,
// the web UI header takes over its duties. KWin itself handles moving and resizing
// (startSystemMove/-Resize via QWebChannel) – so snapping to screen edges still works.
// In a normal browser tab nothing happens here.
(() => {
  const EDGE = 5;   // width of the invisible drag edge for resizing (px)
  // Qt.Edge: Top=1, Left=2, Right=4, Bottom=8
  const CURSORS = {1: "ns-resize", 8: "ns-resize", 2: "ew-resize", 4: "ew-resize",
                   3: "nwse-resize", 12: "nwse-resize", 5: "nesw-resize", 10: "nesw-resize"};
  let app = null, maximized = false;

  const interactive = (el) => el.closest("button, input, select, textarea, a, label, nav, .switch, .info, [draggable=true]");
  function edgesAt(ev) {
    if (maximized) return 0;
    let e = 0;
    if (ev.clientY <= EDGE) e |= 1;
    if (ev.clientX <= EDGE) e |= 2;
    if (ev.clientX >= innerWidth - EDGE) e |= 4;
    if (ev.clientY >= innerHeight - EDGE) e |= 8;
    return e;
  }
  function setMaximized(m) {
    maximized = !!m;
    document.documentElement.classList.toggle("maximized", maximized);
    $("winMax").innerHTML = ic(maximized ? "restore" : "max");
  }
  function init(bridge) {
    if (app || !bridge) return;
    app = bridge;
    document.documentElement.classList.add("in-app");
    $("winctl").hidden = false;
    app.maximizedChanged.connect(setMaximized);
    app.isMaximized(setMaximized);
    $("winMin").onclick = () => app.minimize();
    $("winMax").onclick = () => app.toggleMaximize();
    $("winClose").onclick = () => app.close();
    document.addEventListener("mousemove", (ev) => {
      document.documentElement.style.cursor = CURSORS[edgesAt(ev)] || "";
    }, true);
    document.addEventListener("mousedown", (ev) => {
      if (ev.button !== 0) return;
      const e = edgesAt(ev);
      if (e) { ev.preventDefault(); ev.stopPropagation(); app.startResize(e); return; }
      if (ev.target.closest("header") && !interactive(ev.target)) { ev.preventDefault(); app.startMove(); }
    }, true);
    document.querySelector("header").addEventListener("dblclick", (ev) => {
      if (!interactive(ev.target)) app.toggleMaximize();
    });
  }
  window.addEventListener("fcwm-app", () => init(window.fcwmApp));
  init(window.fcwmApp);
})();
