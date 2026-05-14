# EcoTracker Emulator

Emuliert einen EcoTracker Energiemonitor im Netzwerk, damit andere Geräte (z. B. ein Wechselrichter oder eine App) ihn als echten EcoTracker erkennen und die Messwerte abfragen können.

## Funktionsweise

- Die Integration veröffentlicht einen **mDNS‑Dienst** (`_everhome._tcp`) mit einem konfigurierbaren Namen (z. B. `ecotracker-B43A452249C9`).
- Sie stellt einen **HTTP‑Endpunkt** `/v1/json` bereit, der eine JSON‑Payload mit Energiedaten zurückgibt.
- Die zurückgegebenen Werte können **frei mit echten Home Assistant Sensoren verknüpft** werden (z. B. Leistung der Phasen, Gesamtenergie).
- Ideal, um einen fehlenden EcoTracker zu simulieren oder Testdaten bereitzustellen.

## Installation

1. **HACS Custom Repository hinzufügen**  
   - HACS → Einstellungen → Benutzerdefinierte Repositories  
   - URL: `https://github.com/dein-name/ha-ecotracker`  
   - Typ: `Integration`

2. **Integration installieren**  
   HACS → Integrationen → „EcoTracker Emulator“ → Installieren

3. **Home Assistant neustarten**

4. **Integration einrichten**  
   Einstellungen → Geräte & Dienste → Integration hinzufügen → „EcoTracker Emulator“  
   - Dienstname (mDNS): z. B. `ecotracker-B43A452249C9`  
   - Port: normalerweise `8123` (der Standard‑Port von Home Assistant)

## Konfiguration der Messwerte

Nach der Ersteinrichtung kannst du **für jeden JSON‑Wert** entweder:
- eine **Sensor‑Entität** auswählen (z. B. `sensor.leistung_phase_1`), oder
- einen **festen Fallback‑Zahlenwert** verwenden.

Die Integration aktualisiert die Antwort bei jedem Aufruf von `/v1/json` mit den aktuellen Sensorwerten.

### Verfügbare JSON‑Felder

| Feld | Beschreibung |
|------|--------------|
| `power` | Gesamtleistung (Watt) |
| `powerAvg` | Durchschnittsleistung (Watt) |
| `agePower` | Lebensenergie (Wattsekunden) |
| `powerPhase1` | Leistung Phase 1 (Watt) |
| `powerPhase2` | Leistung Phase 2 (Watt) |
| `powerPhase3` | Leistung Phase 3 (Watt) |
| `energyCounterOut` | Gelieferte Energie (kWh) |
| `energyCounterIn` | Bezogene Energie (kWh) |

## Testen

- **mDNS‑Dienst prüfen** (auf einem anderen Rechner im selben Netzwerk):  
  `avahi-browse -r _everhome._tcp`  
  → Der konfigurierte Dienstname sollte erscheinen.

- **HTTP‑Endpunkt abrufen:**  
  `http://<HA-IP>:8123/v1/json`  
  → Die JSON‑Antwort mit den aktuellen Werten wird angezeigt.

## Bekannte Einschränkungen

- Der Dienst wird **nur auf dem Standard‑HTTP‑Port von Home Assistant** (8123) angeboten. Falls dein Abfrager zwingend Port 80 erwartet, muss ein Reverse‑Proxy (z. B. Nginx) eingerichtet werden.
- Die Authentifizierung ist deaktiviert (`requires_auth=False`), da der echte EcoTracker keine Authentifizierung verlangt. Der Endpunkt ist daher im gesamten Netzwerk lesbar.

## Support & Fehler melden

- **Issues:** [GitHub Issues](https://github.com/dein-name/ha-ecotracker/issues)
- **Diskussionen:** [Home Assistant Community Forum](https://community.home-assistant.io/)

## Lizenz

MIT