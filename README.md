# EcoTracker Emulator for Home Assistant

Emuliert einen EcoTracker Energiemonitor über mDNS (`_everhome._tcp`) und einen HTTP-Endpunkt `/v1/json`.

## Installation

1. Füge dieses Repository als HACS Custom Repository hinzu (Kategorie: Integration).
2. Installiere die Integration "EcoTracker Emulator" über HACS.
3. Starte Home Assistant neu.
4. Gehe zu Einstellungen → Geräte & Dienste → Integration hinzufügen → "EcoTracker Emulator".
5. Konfiguriere den mDNS-Dienstnamen (Standard: `ecotracker-B43A452249C9`).

## Funktionsweise

- Die Integration veröffentlicht einen mDNS-Dienst (`_everhome._tcp`), der unter dem angegebenen Namen erreichbar ist.
- Auf `http://<HA-IP>:8123/v1/json` wird eine JSON-Payload zurückgegeben.
- Die Werte können später durch echte Sensor-Entitäten ersetzt werden (in Arbeit).

## Unterstützte Plattformen

- Home Assistant OS
- Home Assistant Container
- ...

## Entwicklung

Siehe [DEVELOPMENT.md](DEVELOPMENT.md)

## Lizenz

MIT