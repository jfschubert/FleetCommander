#!/usr/bin/env bash
# Launcher script – also works as a target for KDE shortcuts, e.g.:  fcwm.sh apply Fleet-Fight
cd "$(dirname "$(readlink -f "$0")")" && exec python3 -m fcwm "$@"
