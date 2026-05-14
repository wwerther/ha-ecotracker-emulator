# EcoTracker Emulator for Home Assistant

> 🌐 **Sprache / Language:** [English](README.md) · **Deutsch**

Emuliert einen [everHome EcoTracker](https://everhome.cloud/en/developer/ecotracker)
Energiemonitor: veröffentlicht den passenden mDNS-Dienst (`_everhome._tcp`) und liefert
auf `/v1/json` die erwartete Payload mit Energiedaten.

## Wozu?

Aktuelle **EcoFlow-Wechselrichter** (PowerStream u. ä.) können in der EcoFlow-App als
externen Stromzähler nur noch **EcoTracker-Geräte über die lokale API** einbinden – ohne
Umweg über einen verknüpften Cloud-Account. Außerdem lässt die App die **IP-Adresse des
Zählers nicht mehr manuell eintragen**; das Pairing erfolgt ausschließlich über
**mDNS-Discovery** im selben Netz.

Wer den Verbrauch / die Einspeisung schon in Home Assistant misst (Shelly 3EM, Tibber Pulse,
Smart-Meter, etc.), hat damit ein Problem: Ohne ein echtes EcoTracker-Gerät bekommt der
EcoFlow-Wechselrichter keine Messwerte. Hier setzt diese Integration an:

- Sie **gibt sich gegenüber der EcoFlow-App als EcoTracker aus** (mDNS-Service, JSON-API,
  TXT-Records, Service-Name `ecotracker-<MAC>` mit der EcoTracker-OUI `B4:3A:45`).
- Die **Werte stammen aus beliebigen Home-Assistant-Sensoren**, die über den Options-Flow
  pro JSON-Feld zugewiesen werden – mit numerischem Fallback, falls ein Sensor noch keinen
  gültigen Wert liefert.
- Damit kann der EcoFlow-Wechselrichter den in HA gemessenen Bezug/Einspeisung als
  Steuergröße nutzen, **ohne dass ein zusätzliches Hardware-Gerät** angeschafft oder ein
  Cloud-Account verknüpft werden muss.

## Installation

1. Füge dieses Repository als HACS Custom Repository hinzu (Kategorie: Integration).
2. Installiere die Integration "EcoTracker Emulator" über HACS.
3. Starte Home Assistant neu.
4. Gehe zu Einstellungen → Geräte & Dienste → Integration hinzufügen → "EcoTracker Emulator".
5. MAC-Suffix, Seriennummer und Produkt-ID bestätigen oder anpassen (sinnvolle Defaults
   sind vorbelegt – das MAC-Suffix beginnt bewusst mit der EcoTracker-OUI `B43A45`).
6. Anschließend in den **Optionen** der Integration jedem JSON-Feld einen Sensor oder
   einen festen Fallback-Wert zuweisen.

## Funktionsweise

- Die Integration veröffentlicht einen mDNS-Dienst (`_everhome._tcp`) unter dem
  konfigurierten Namen (`ecotracker-<MAC>`), inklusive der TXT-Records `serial`,
  `productid` und `ip`.
- Auf `http://<HA-IP>:8123/v1/json` wird die EcoTracker-kompatible JSON-Payload
  zurückgegeben (Felder: `power`, `powerAvg`, `agePower`, `powerPhase1..3`,
  `energyCounterIn`, `energyCounterOut`).
- Energiezähler werden in **Wattstunden (Wh)** erwartet – passend zur offiziellen Spec
  (siehe [`docs/api-spec.md`](docs/api-spec.md)).

## Bekannte Einschränkungen

- Die HTTP-API läuft auf dem **Home-Assistant-Port (Standard 8123)**, nicht auf Port 80.
  Aktuelle EcoFlow-Clients akzeptieren das, weil der Port via mDNS-TXT bekanntgegeben
  wird – Clients, die strikt Port 80 erwarten, brauchen einen Reverse-Proxy.
- Es kann nur **eine Instanz** pro Home Assistant eingerichtet werden (globaler `/v1/json`
  Pfad).
- Authentifizierung ist deaktiviert (so wie beim echten Gerät) – der Endpunkt ist im
  lokalen Netz frei lesbar.

## Unterstützte Plattformen

- Home Assistant OS
- Home Assistant Container
- Home Assistant Supervised / Core (überall, wo `zeroconf` und der HA-eigene
  HTTP-Server laufen)

## Entwicklung

Siehe [`AGENTS.md`](AGENTS.md) für Setup, Sync nach HAOS und Coding-Konventionen,
[`docs/api-spec.md`](docs/api-spec.md) für die emulierte Spec inkl. Real-Device-Capture,
und [`TODO.md`](TODO.md) für den aktuellen Arbeitsstand.

## Lizenz

MIT