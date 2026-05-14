DOMAIN = "ecotracker_emulator"
DEFAULT_NAME = "EcoTracker Emulator"

# mDNS Konfiguration
MDNS_SERVICE_TYPE = "_everhome._tcp.local."
MDNS_SERVICE_NAME = "ecotracker-B43A452249C9"  # Kann später konfigurierbar sein
MDNS_PORT = 8123

# API Pfad
API_PATH = "/v1/json"

# Standard-Fallback-Werte (falls keine Sensoren gewählt)
DEFAULT_VALUES = {
    "power": 13,
    "powerAvg": 2,
    "agePower": 2635906,
    "powerPhase1": 83,
    "powerPhase2": -168,
    "powerPhase3": 98,
    "energyCounterOut": 5502204.6,
    "energyCounterIn": 1540610.7
}