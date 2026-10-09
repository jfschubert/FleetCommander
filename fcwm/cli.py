"""Command line: fcwm <command> [options]"""
from __future__ import annotations

import argparse
import json
import logging
import signal
import sys

from . import i18n
from . import __version__
from .app import App
from .config import slot_text
from .i18n import FcwmError, t
from .layout import eve_windows


def _print_plan(plan, dry_run: bool) -> None:
    print(f"{t('profile')}: {plan.profile}" + (f"  {t('dry_run')}" if dry_run else ""))
    for alias, lay in plan.layouts.items():
        a = lay.area
        print(f"  [{alias}] {lay.monitor.name}: "
              + t("grid_area", cols=lay.grid.cols, rows=lay.grid.rows, area=f"{a.w}x{a.h}+{a.x}+{a.y}"))
    for p in plan.placements:
        r = p.rect
        slot = f"{p.monitor}:{slot_text(p.slot, p.sub)}" + ("*" if p.auto else "")
        print(f"  {p.char:<28} -> {slot:<10} {r.w}x{r.h}+{r.x}+{r.y}")
    for p in plan.extra:
        r = p.rect
        print(f"  {'[' + p.char + ']':<28} -> {p.monitor + ':' + slot_text(p.slot, p.sub):<10} {r.w}x{r.h}+{r.x}+{r.y}")
    for c in plan.missing:
        print(f"  {t('not_open')}  {c}")
    for c in plan.unplaced:
        print(f"  {t('no_slot')} {c}")
    for w in plan.warnings:
        print(f"  {t('warning')}: {w}")
    if plan.focus:
        print(f"  {t('focus')}: {plan.focus.caption}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fcwm", description="EVE Online window manager for KDE Plasma")
    ap.add_argument("-c", "--config", help="path to config.yaml/.json")
    ap.add_argument("-b", "--backend", choices=["auto", "kwin", "x11"], help="force backend")
    ap.add_argument("-l", "--lang", help=f"language: {', '.join(i18n.LANGUAGES)} "
                                          "(default: settings.language or $LANG)")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("monitors", help="show detected monitors")
    w = sub.add_parser("windows", help="show EVE clients")
    w.add_argument("--all", action="store_true", help="all windows, not just EVE")
    sub.add_parser("profiles", help="list profiles")
    a = sub.add_parser("apply", help="apply a profile")
    a.add_argument("profile", nargs="?", help="profile name (default: default_profile)")
    a.add_argument("-n", "--dry-run", action="store_true", help="only compute and print")
    wa = sub.add_parser("watch", help="listen for new clients and place them automatically")
    wa.add_argument("profile", nargs="?")
    wa.add_argument("--initial", action="store_true", help="also place already open clients at start")
    we = sub.add_parser("web", help="start the web UI (includes the listener)")
    we.add_argument("--host", help="listen address (default: settings.web.host or 127.0.0.1)")
    we.add_argument("--port", type=int, help="port (default: settings.web.port or 8765)")
    sub.add_parser("state", help="dump full state as JSON")
    op = sub.add_parser("open", help="open the web UI in the browser (starts fcwm if needed)")
    op.add_argument("--port", type=int, help="port of the running instance (default: from config)")
    apw = sub.add_parser("app", help="open the web UI in its own window (starts fcwm if needed; "
                                     "needs PyQt6-WebEngine, otherwise opens the browser)")
    apw.add_argument("--port", type=int, help="port of the running instance (default: from config)")
    apw.add_argument("--native-frame", action="store_true",
                     help="keep the KDE title bar instead of FleetCommander's own window frame")
    rl = sub.add_parser("reload", help="make the running instance re-read its config (moves no windows)")
    rl.add_argument("--port", type=int, help="port of the running instance (default: from config)")
    rs = sub.add_parser("restart", help="restart the running instance (service or `fcwm web`)")
    rs.add_argument("--port", type=int, help="port of the running instance (default: from config)")
    ini = sub.add_parser("init", help="create a starter config from the detected monitors")
    ini.add_argument("--force", action="store_true", help="overwrite an existing config")
    sub.add_parser("cleanup", help="remove KWin scripts, shortcuts, window rules and color schemes "
                                   "created by fcwm (run before uninstalling)")
    ap.add_argument("-V", "--version", action="version", version=f"fcwm {__version__}")

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    i18n.set_default(args.lang)

    def _terminate(*_):  # treat SIGTERM (logout, systemd) like Ctrl+C -> unload KWin listener
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _terminate)
    if args.cmd in ("init", "cleanup", "open", "app", "reload", "restart"):   # do not need their own configuration
        from . import maintenance
        if getattr(args, "port", None) is None and args.cmd != "init":
            args.port = maintenance.configured_port(args.config)
        try:
            if args.cmd == "init":
                path = maintenance.init(args.config, args.force, i18n.lang())
                print(t("init_done", path=path))
            elif args.cmd == "open":
                print(maintenance.open_ui(args.port, args.config))
            elif args.cmd == "app":
                url = maintenance.ensure_running(args.port, args.config)
                try:
                    from . import appwindow
                    return appwindow.run(url, native_frame=args.native_frame)
                except ImportError:
                    print(t("app_missing"), file=sys.stderr)
                    print(maintenance.open_ui(args.port, args.config))
            elif args.cmd == "reload":
                print(t("reloaded", path=maintenance.reload_config(args.port)))
            elif args.cmd == "restart":
                print(t("restarted_" + maintenance.restart(args.port)))
            else:
                if maintenance.service_active():
                    print(t("cleanup_service"))
                    return 1
                print(t("cleanup_done", **maintenance.cleanup()))
            return 0
        except FileExistsError as e:
            print(f"{t('error')}: {t('init_exists', path=e)}", file=sys.stderr)
            return 1
        except (FcwmError, OSError, RuntimeError) as e:
            msg = t("not_running") if str(e) == "not_running" else e
            print(f"{t('error')}: {msg}", file=sys.stderr)
            return 1
    try:
        app = App(args.config, args.backend)
        if not args.lang:
            i18n.set_default(app.cfg.language)
        if args.cmd == "monitors":
            for m in app.snapshot()[1]:
                g, wa_ = m.geometry, m.workarea
                print(f"{m.name:<10} {g.w}x{g.h}+{g.x}+{g.y}  scale={m.scale:g}"
                      + (f"  {t('workarea')} {wa_.w}x{wa_.h}+{wa_.x}+{wa_.y}" if wa_ else ""))
        elif args.cmd == "windows":
            wins = app.backend.list_windows()
            if args.all:
                for win in wins:
                    print(f"{win.resource_class:<24} {win.caption}")
            else:
                for char, win in eve_windows(app.cfg, wins).items():
                    g = win.geometry
                    print(f"{char:<28} {g.w}x{g.h}+{g.x}+{g.y}  ({win.output or '?'})")
        elif args.cmd == "profiles":
            for name, p in app.cfg.profiles.items():
                mark = "*" if name == app.cfg.default_profile else " "
                print(f"{mark} {name:<20} {p.description}")
        elif args.cmd == "apply":
            _print_plan(app.apply(args.profile, dry_run=args.dry_run), args.dry_run)
        elif args.cmd == "watch":
            from .autoplace import run_forever
            run_forever(app, args.profile, args.initial)
        elif args.cmd == "web":
            from .web import serve
            serve(app, args.host or app.cfg.web["host"], args.port or app.cfg.web["port"])
        elif args.cmd == "state":
            json.dump(app.state(), sys.stdout, indent=2, ensure_ascii=False)
            print()
    except KeyboardInterrupt:
        return 130
    except (FcwmError, RuntimeError, KeyError, ValueError, OSError) as e:
        print(f"{t('error')}: {e}", file=sys.stderr)
        return 1
    return 0
