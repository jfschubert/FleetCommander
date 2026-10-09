---
sidebar_position: 2
title: Installation
---

# Installation

## Fertige Pakete {#prebuilt-packages}

Jedes [Release auf GitHub](https://github.com/jfschubert/FleetCommander/releases) enthält Pakete für
Arch Linux (`.pkg.tar.zst`), Debian 13 / Ubuntu 25.04+ (`.deb`) und Fedora (`.rpm`) sowie ein Python-Wheel.
In den Release-Notes steht jeweils der passende Installationsbefehl, z. B.:

```bash
sudo pacman -U fcwm-<version>-1-any.pkg.tar.zst   # Arch
sudo apt install ./fcwm_<version>_all.deb          # Debian / Ubuntu
sudo dnf install fcwm-<version>-1.fc*.noarch.rpm   # Fedora
```

Danach weiter mit `fcwm init` wie [unten](#arch-linux) beschrieben. Wer das Paket lieber selbst baut, liest
einfach weiter.

## Abhängigkeiten

| Was | Wofür | Arch | Debian/Ubuntu |
|---|---|---|---|
| Python ≥ 3.10 | Laufzeit | `python` | `python3` |
| PyYAML | YAML-Konfiguration (für JSON nicht nötig) | `python-yaml` | `python3-yaml` |
| `kscreen-doctor` | Monitore erkennen (Fallback, wenn KWin nicht antwortet) | `kscreen` | `libkscreen-bin` |
| `busctl`, `journalctl` | D-Bus-Aufrufe an KWin und Rückgabewerte lesen (systemd, normalerweise vorhanden) | `systemd` | `systemd` |
| *optional* ruamel.yaml | Kommentare in der `config.yaml` beim Speichern aus der Web-UI erhalten | `python-ruamel-yaml` | `python3-ruamel.yaml` |
| PyQt6-WebEngine | [Programmfenster](web-ui.md#app-window) statt Browser-Tab (wird mit den fcwm-Paketen installiert; ohne öffnet `fcwm app` den Browser) | `python-pyqt6-webengine` | `python3-pyqt6.qtwebengine` |
| *optional* `wmctrl` / `xdotool` / `xrandr` | X11-Backend ohne KWin | `wmctrl xdotool xorg-xrandr` | `wmctrl xdotool x11-xserver-utils` |

Unter Plasma brauchst du nur Python und PyYAML. Die Web-UI nutzt nur die Python-Standardbibliothek.

## Arch Linux

fcwm wird als ein Arch-Paket verteilt (PKGBUILD in `packaging/arch/`):

```bash
git clone https://github.com/jfschubert/FleetCommander.git
cd FleetCommander/packaging/arch
makepkg -si                          # baut, führt die Tests aus, installiert
fcwm init                            # Startkonfiguration aus deinen Monitoren -> ~/.config/fcwm/config.yaml
systemctl --user enable --now fcwm   # läuft mit der Plasma-Sitzung
```

Die Web-UI ist unter <http://127.0.0.1:8765/> erreichbar (bzw. dem [eingestellten Port](configuration.md#web-ui-address))
oder über „FleetCommander“ im Anwendungsmenü, das sie in einem eigenen [Programmfenster](web-ui.md#app-window) öffnet (`fcwm app`).

Das Paket installiert `/usr/bin/fcwm`, den systemd-Benutzerdienst `fcwm.service`, den Menüeintrag und die
Dokumentation (`/usr/share/doc/fcwm/`, inkl. `config.example.yaml` mit allen Funktionen).

### Aktualisieren

```bash
git pull && cd packaging/arch && makepkg -sif
fcwm restart
```

### Deinstallieren

**Vor dem Deinstallieren** als normaler Benutzer:

```bash
systemctl --user disable --now fcwm
fcwm cleanup        # entfernt fcwms KWin-Fensterregeln, Farbschemata und globale Kurzbefehle
sudo pacman -R fcwm
```

Die Konfiguration in `~/.config/fcwm/` bleibt erhalten.

## Andere Distributionen

Pakete für **Debian/Ubuntu** und **Fedora/openSUSE** kommen gerade unter `packaging/` im Repository dazu.
Siehe dort [`packaging/README`](https://github.com/jfschubert/FleetCommander/blob/master/packaging/README.md) für den aktuellen Stand und die Bauanleitung.

Bis dahin lässt sich fcwm direkt aus dem Quellordner starten: Abhängigkeiten aus der Tabelle oben installieren
und im Repository `./fcwm.sh` (oder `python3 -m fcwm`) verwenden.

## Umstieg von `evewm`

`evewm` ist der frühere Name; das Paket ersetzt es. Beim ersten Start wird `~/.config/evewm` nach
`~/.config/fcwm` kopiert (der alte Ordner bleibt als Sicherung) und alte `evewm-*`-Fensterregeln und
Kurzbefehle werden aufgeräumt. Dienst umstellen:

```bash
systemctl --user disable --now evewm
systemctl --user enable --now fcwm
```
