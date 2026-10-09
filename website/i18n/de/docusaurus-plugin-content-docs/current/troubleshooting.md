---
sidebar_position: 21
title: Fehlersuche & Grenzen
---

# Fehlersuche & Grenzen

## Häufige Prüfungen {#common-checks}

- **Debug-Infos:** *Einstellungen → Debug-Infos* in der Web-UI zeigt Backend, Listener, Versionen, Pfade sowie
  alle erkannten EVE-Clients und Monitore. Der Kopieren-Knopf (⧉) legt alles als Text in die Zwischenablage –
  bitte an Fehlerberichte anhängen.
- **Keine Clients gefunden:** `fcwm windows --all` listet alle Fenster mit Klasse und Titel. Passe
  `settings.match.caption_regex` / `resource_class` an, wenn dein Launcher Fenster anders benennt.
- **Falscher Monitor:** `fcwm monitors` zeigt die Anschlussnamen; nutze sie als `output:` unter `monitors`.
- **Plan sieht falsch aus:** `fcwm apply -n` zeigt die berechneten Platzierungen, ohne etwas zu verschieben;
  `-v` liefert Debug-Ausgaben.
- **`config.yaml` von Hand geändert:** `fcwm reload` ausführen (verschiebt nichts).
- **Web-UI nicht erreichbar:** [eingestellte Adresse/Port](configuration.md#web-ui-address) prüfen und ob der
  Dienst läuft: `systemctl --user status fcwm`.
- **Popups landen im Auffangfeld:** über `exclude` ausnehmen (siehe [Fensterzonen](window-zones.md#catch-all-zone)).
  Transiente Dialoge werden nie verschoben.
- **Übrig gebliebene Fensterregeln / Kurzbefehle:** `fcwm cleanup` entfernt alles, was fcwm in KWin angelegt hat
  (vorher den Dienst stoppen).

## Grenzen {#limitations}

- Kurzbefehle, Fixieren, Trennlinien und Vorschauen benötigen **KWin** (Plasma) und ein laufendes
  `fcwm web` / `fcwm watch`. Das X11-Backend (`wmctrl`/`xdotool`) ordnet nur an.
- Das KWin-Backend schreibt pro Abfrage bzw. Fenster-Ereignis ein paar Zeilen ins User-Journal (Rückkanal des
  KWin-Skripts).
- Die Web-UI hat keine Anmeldung. Sie lauscht standardmässig nur auf `127.0.0.1`; sie kann Fenster verschieben
  und die Konfiguration überschreiben – nicht ins Netz stellen.
- Ohne ruamel.yaml gehen beim Speichern aus der Web-UI die Kommentare in der `config.yaml` verloren.
- fcwm sendet nie Eingaben an EVE-Clients; es ordnet Fenster nur an, schaltet und zeigt Vorschauen.
