#!/usr/bin/env bash
# Generic, pip-less install of fcwm for distributions without a native package.
# Copies the pure-Python package next to a small launcher; uses the system python3 and
# PyYAML (install python3 + PyYAML + KWin/kconfig/kscreen tools with your package manager).
#
#   packaging/install.sh                         # per user: ~/.local/{bin,share}, ~/.config/systemd/user
#   packaging/install.sh --uninstall
#   sudo packaging/install.sh --prefix /usr/local            # system-wide (run as root yourself)
#   sudo packaging/install.sh --prefix /usr/local --uninstall
set -euo pipefail

top=$(cd "$(dirname "$0")/.." && pwd)
prefix="" uninstall=0
while (($#)); do
    case $1 in
        --prefix) prefix=${2:?--prefix needs a directory}; shift 2 ;;
        --prefix=*) prefix=${1#*=}; shift ;;
        --uninstall) uninstall=1; shift ;;
        -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
done

if [[ -n $prefix ]]; then
    prefix=$(realpath -m "$prefix")
    bindir=$prefix/bin libdir=$prefix/lib/fcwm docdir=$prefix/share/doc/fcwm
    unitdir=$prefix/lib/systemd/user appdir=$prefix/share/applications
    [[ -w $prefix || ( ! -e $prefix && -w $(dirname "$prefix") ) ]] || {
        echo "error: $prefix is not writable – run: sudo $0 --prefix $prefix$( ((uninstall)) && echo ' --uninstall')" >&2
        exit 1; }
else
    [[ $EUID -ne 0 ]] || { echo "error: per-user install as root – use --prefix for a system-wide install" >&2; exit 1; }
    data=${XDG_DATA_HOME:-$HOME/.local/share}
    bindir=$HOME/.local/bin libdir=$data/fcwm/lib docdir=$data/doc/fcwm
    unitdir=${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user appdir=$data/applications
fi

icondir=$(dirname "$appdir")/icons/hicolor/scalable/apps

if ((uninstall)); then
    rm -rf -- "$libdir/fcwm" "$docdir"
    rmdir -- "$libdir" 2>/dev/null || true
    [[ -z $prefix ]] && rmdir -- "$(dirname "$libdir")" 2>/dev/null || true
    rm -f -- "$bindir/fcwm" "$unitdir/fcwm.service" "$appdir/fcwm.desktop" "$icondir/fcwm.svg"
    echo "==> fcwm removed. Your config in ~/.config/fcwm/ is left untouched."
    echo "    (Run 'systemctl --user disable --now fcwm' and 'fcwm cleanup' as your user BEFORE uninstalling.)"
    exit 0
fi

command -v python3 >/dev/null || { echo "error: python3 not found" >&2; exit 1; }
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || { echo "error: Python >= 3.10 required" >&2; exit 1; }
python3 -c 'import yaml' 2>/dev/null || echo "warning: PyYAML missing – install it with your package manager (python3-yaml / python3-pyyaml / python3-PyYAML)" >&2

mkdir -p "$bindir" "$libdir" "$docdir" "$unitdir" "$appdir" "$icondir"
rm -rf -- "$libdir/fcwm"
cp -r "$top/fcwm" "$libdir/"
find "$libdir/fcwm" -name __pycache__ -type d -prune -exec rm -rf {} +

cat > "$bindir/fcwm" <<LAUNCHER
#!/bin/sh
PYTHONPATH="$libdir\${PYTHONPATH:+:\$PYTHONPATH}" exec python3 -m fcwm "\$@"
LAUNCHER
chmod 755 "$bindir/fcwm"

sed -e "s|^ExecStart=/usr/bin/fcwm|ExecStart=$bindir/fcwm|" \
    -e "s|^Documentation=.*|Documentation=file://$docdir/README.md|" \
    "$top/packaging/fcwm.service" > "$unitdir/fcwm.service"
sed -e "s|^Exec=fcwm|Exec=$bindir/fcwm|" "$top/packaging/fcwm.desktop" > "$appdir/fcwm.desktop"
chmod 644 "$unitdir/fcwm.service" "$appdir/fcwm.desktop"
cp "$top"/{README.md,README.de.md,config.example.yaml,LICENSE,NOTICE} "$docdir/"
install -m644 "$top/fcwm/static/fcwm.svg" "$icondir/fcwm.svg"

cat <<MSG
==> FleetCommander (fcwm) installed to $bindir/fcwm
    1. Create a starter config:    fcwm init
    2. Start it with your session: systemctl --user daemon-reload; systemctl --user enable --now fcwm
    3. Open the web UI:            http://127.0.0.1:8765/  (or "FleetCommander" in the menu)
MSG
[[ :$PATH: == *":$bindir:"* ]] || echo "    note: $bindir is not in your PATH – use $bindir/fcwm"
