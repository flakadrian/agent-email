# Projekt: E-Mail-Agent (agent-email)

Eigenständiger Dienst, der ein IMAP-Postfach überwacht, neu eingehende Mails
anhand einer festen Kategorienliste klassifiziert und Anhänge strukturiert
ablegt. Bewusst als einzelnes, in sich abgeschlossenes Projekt geführt -
kein Teil eines größeren Multi-Agent- oder Orchestrator-Systems.

## Aktueller Stand

- Funktional vollständig: IMAP-Anbindung (IDLE bevorzugt, Polling als
  Fallback, automatischer Reconnect bei Verbindungsabbrüchen), Klassifizierung
  (Claude API oder lokal via Ollama), Ablage (Google Drive, OneDrive oder
  lokaler Dateisystempfad), Betrieb lokal mit Python oder als Docker-Container
  (z. B. dauerhaft auf einem NAS)
- Entwicklungsprozess etabliert: CI (Tests + Linting bei jedem PR), gepinnte
  Dependencies, strukturiertes Logging, gehärtetes Docker-Setup
  (Healthcheck, gepinnte Image-Version, dedizierter Bind-Mount statt
  Zugriff auf umfassendere Freigaben), automatisiertes Deployment-Skript
- Läuft produktiv

## Tech-Stack

- Python, IMAP über `imapclient` (IDLE bevorzugt, Polling als Fallback)
- Klassifizierung über die Claude API oder ein lokales Modell via Ollama,
  Auswahl per `CLASSIFIER_PROVIDER`
- Ablage wahlweise über Google Drive API, Microsoft Graph API (OneDrive)
  oder einen lokalen Dateisystempfad, Auswahl per `STORAGE_PROVIDER`
- Läuft als eigenständiger Dienst (lokal oder als Docker-Container), nicht
  als Teil einer Chat-Session

## Befehle

```bash
cd agent-email
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # dann echte Werte eintragen, NIE committen
python main.py test    # IMAP-Verbindung prüfen
python main.py listen  # auf neue Mails warten (IDLE)
```

## Architektur-Dateien

- `agent-email/config.py` – lädt/validiert Umgebungsvariablen
- `agent-email/imap_client.py` – IMAP-Verbindung, Polling, IDLE, Reconnect
- `agent-email/message_loader.py` – lädt Nachrichteninhalt + Anhänge per UID
- `agent-email/classifier.py` – Klassifizierung über die Claude API
- `agent-email/local_classifier.py` – Klassifizierung über ein lokales
  Ollama-Modell (gleiche Kategorienliste/Prompt wie classifier.py)
- `agent-email/file_naming.py` – gemeinsame Dateinamens-/Datums-Hilfsfunktionen
  für die Ablage
- `agent-email/drive_client.py` – OAuth-Flow + Ablage der Anhänge in Google Drive
- `agent-email/onedrive_client.py` – OAuth-Flow + Ablage der Anhänge in OneDrive
- `agent-email/local_storage.py` – Ablage der Anhänge auf einem lokalen
  Dateisystempfad, kein OAuth nötig
- `agent-email/main.py` – Einstiegspunkt/CLI, wählt Classifier-/Storage-
  Provider per `CLASSIFIER_PROVIDER`/`STORAGE_PROVIDER`
- `agent-email/Dockerfile`/`agent-email/docker-compose.yml` – Container-Image
  und Compose-Setup für dauerhaften Betrieb (z. B. auf einem NAS), optional
  inkl. `ollama`-Service für die lokale Klassifizierung
- `deploy-to-nas.sh` – überträgt den committeten Stand per SSH (`git
  archive`) auf ein Zielsystem, statt Dateien manuell zu kopieren

## Regeln

- Zugangsdaten/Secrets ausschließlich über `.env`, nie im Code oder Chat
- Kategorienliste ist fest vorgegeben (siehe Anhang unten), nicht ohne
  Rücksprache ändern
- Kritische/irreversible Aktionen (z. B. Mail senden, Termin anlegen) nie ohne
  expliziten Freigabe-Schritt
- Bind-Mounts für `STORAGE_PROVIDER=local` immer auf einen dedizierten
  Ordner beschränken, nie auf eine umfassendere Freigabe mit anderen/privaten
  Dateien (der Container läuft als root - siehe Kommentar in
  `docker-compose.yml`)
- Nennenswerte Änderungen im selben PR in `CHANGELOG.md` festhalten

## Weiterentwicklung

Keine Erweiterung um weitere Agenten oder einen Orchestrator geplant -
Fokus bleibt auf `agent-email` selbst (Robustheit, neue Ablageziele,
bessere Diagnose/Beobachtbarkeit etc.), siehe `CHANGELOG.md` für den
bisherigen Verlauf.

## Anhang: Kategorienliste (Stand 2026-07-17)

1. Rechnungen/Zahlungen
2. Verträge
3. Bestellungen/Lieferungen
4. Termine/Einladungen
5. Newsletter
6. Privat
7. Sonstiges (Fallback für alles Unklare)

## Anhang: Pfadschema Ablage (Stand 2026-07-17, erweitert 2026-08-06)

Flach nach Kategorie, kein Jahresordner, identisch für Google Drive,
OneDrive und lokalen Pfad. Nur Mails **mit Anhang** werden abgelegt; der
Original-Dateiname bleibt Teil des Dateinamens (wichtig bei mehreren
Anhängen pro Mail):

```
Email-Ablage/<Kategorie>/<Datum>_<Betreff>_<Original-Dateiname>
```

Beispiel: `Email-Ablage/Rechnungen-Zahlungen/2026-07-17_Stromrechnung Juli_rechnung.pdf`

Welches Ziel genutzt wird, legt `STORAGE_PROVIDER` (`google_drive`,
`onedrive` oder `local`) in der `.env` fest — immer nur eins gleichzeitig.
