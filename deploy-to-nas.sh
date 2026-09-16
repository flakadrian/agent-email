#!/usr/bin/env bash
# Überträgt den aktuellen committeten Stand von agent-email/ per SSH auf das
# NAS (git archive statt manuellem Kopieren, damit nie eine Datei vergessen
# oder ein veralteter Stand übertragen wird) und baut den Container neu.
#
# .env, credentials.json, token.json, onedrive_token_cache.json etc. sind
# nie Teil des Git-Repos und werden daher NICHT angefasst/überschrieben.
#
# Nur committete Änderungen (git archive liest aus dem letzten Commit, nicht
# aus dem Arbeitsverzeichnis) werden übertragen - erst committen, dann
# deployen.
#
# Aufruf:
#   NAS_HOST=192.168.1.100 NAS_USER=dein-nas-benutzer NAS_PATH=/volume1/docker/agent-email ./deploy-to-nas.sh
#
# Optional: NAS_PORT (Standard 22), NAS_REF (Standard: aktueller Branch/HEAD)

set -euo pipefail

: "${NAS_HOST:?Bitte NAS_HOST setzen (z.B. NAS_HOST=192.168.1.100)}"
: "${NAS_USER:?Bitte NAS_USER setzen (z.B. NAS_USER=dein-nas-benutzer)}"
: "${NAS_PATH:?Bitte NAS_PATH setzen (z.B. NAS_PATH=/volume1/docker/agent-email)}"
NAS_PORT="${NAS_PORT:-22}"
NAS_REF="${NAS_REF:-HEAD}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "==> Übertrage agent-email/ (Stand: $(git rev-parse --short "$NAS_REF")) nach ${NAS_USER}@${NAS_HOST}:${NAS_PATH}"

ssh -p "$NAS_PORT" "${NAS_USER}@${NAS_HOST}" "mkdir -p '${NAS_PATH}'"

git archive --format=tar "$NAS_REF" -- agent-email \
  | ssh -p "$NAS_PORT" "${NAS_USER}@${NAS_HOST}" "tar -x -C '${NAS_PATH}' --strip-components=1"

echo "==> Dateien übertragen."
echo "==> Versuche Rebuild über docker compose (kann fehlschlagen, falls ${NAS_USER} nicht in der Gruppe 'administrators' ist)..."

if ssh -p "$NAS_PORT" "${NAS_USER}@${NAS_HOST}" \
  "cd '${NAS_PATH}' && docker compose build agent-email && docker compose up -d agent-email"; then
  echo "==> Rebuild erfolgreich."
else
  echo "==> Rebuild fehlgeschlagen (vermutlich fehlende Docker-Berechtigung für ${NAS_USER})."
  echo "    Dateien sind trotzdem übertragen - Rebuild manuell über Container Manager -> Projekt -> agent-email -> Neu erstellen."
fi
