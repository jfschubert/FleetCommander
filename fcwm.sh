#!/usr/bin/env bash
# Startskript – funktioniert auch als Ziel für KDE-Kurzbefehle, z. B.:  fcwm.sh apply Fleet-Fight
cd "$(dirname "$(readlink -f "$0")")" && exec python3 -m fcwm "$@"
