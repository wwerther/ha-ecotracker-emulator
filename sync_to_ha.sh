#!/bin/bash

# ====================================================
# Sync lokal entwickelte EcoTracker Integration nach HAOS
# ====================================================

# ---------- Konfiguration ----------
# SSH-Ziel: Benutzer@Host 
SSH_TARGET="root@homeassistant.lan"
SSH_PORT="22"                     # 22 für Add-on, 22222 für Host-Zugang

# Zielverzeichnis auf HAOS (absoluter Pfad)
HA_TARGET_DIR="/root/homeassistant/custom_components/ecotracker_emulator"

# Lokales Quellverzeichnis (relativ zu diesem Skript)
LOCAL_SOURCE_DIR="./custom_components/ecotracker_emulator/"

# Backup des Zielverzeichnisses vor dem Sync? (true/false)
DO_BACKUP=false

# Home Assistant nach Sync neu starten? (true/false)
RESTART_HA=false
# -----------------------------------

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Prüfen, ob rsync existiert
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}❌ rsync nicht gefunden. Bitte installiere rsync (z.B. 'apt install rsync' oder 'brew install rsync').${NC}"
    exit 1
fi

# Prüfen, ob Quellverzeichnis existiert
if [ ! -d "$LOCAL_SOURCE_DIR" ]; then
    echo -e "${RED}❌ Lokales Quellverzeichnis nicht gefunden: $LOCAL_SOURCE_DIR${NC}"
    echo "   Stelle sicher, dass du das Skript aus dem Repository-Root ausführst."
    exit 1
fi

echo -e "${GREEN}🔁 Synchronisiere $LOCAL_SOURCE_DIR → $SSH_TARGET:$HA_TARGET_DIR${NC}"

# Optional: Backup auf dem Ziel erstellen
if [ "$DO_BACKUP" = true ]; then
    BACKUP_CMD="if [ -d $HA_TARGET_DIR ]; then cp -r $HA_TARGET_DIR ${HA_TARGET_DIR}_backup_$(date +%Y%m%d_%H%M%S); fi"
    echo -e "${YELLOW}📦 Erstelle Backup des Ziels...${NC}"
    ssh -p "$SSH_PORT" "$SSH_TARGET" "$BACKUP_CMD"
fi

# Rsync-Kommando
# -a : Archivmodus (behält Rechte, Symlinks, etc.)
# -v : verbose
# -z : komprimieren
# --delete : Dateien löschen, die lokal nicht mehr existieren
# --exclude : ignoriere __pycache__ etc.
RSYNC_CMD="rsync -avz --delete --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' -e 'ssh -p $SSH_PORT' \"$LOCAL_SOURCE_DIR/\" \"$SSH_TARGET:$HA_TARGET_DIR/\""

echo -e "${GREEN}📤 Führe rsync aus...${NC}"
eval $RSYNC_CMD

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Sync erfolgreich abgeschlossen.${NC}"
else
    echo -e "${RED}❌ Fehler während des Syncs.${NC}"
    exit 1
fi

# Optional: Home Assistant neustarten (Core)
if [ "$RESTART_HA" = true ]; then
    echo -e "${YELLOW}🔄 Starte Home Assistant Core neu...${NC}"
    ssh -p "$SSH_PORT" "$SSH_TARGET" "ha core restart"
    echo -e "${GREEN}✅ Neustart-Befehl gesendet.${NC}"
else
    echo -e "${YELLOW}💡 Tipp: Starte Home Assistant manuell neu (Einstellungen → System → Neustart), damit die Änderungen geladen werden.${NC}"
fi

echo -e "${GREEN}✨ Fertig!${NC}"
