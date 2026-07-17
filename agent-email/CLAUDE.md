# Projekt: Persönlicher Assistent mit Multi-Agent-Orchestrierung

Ein Orchestrator verteilt Anfragen/Ereignisse an spezialisierte Einzel-Agenten.
Jeder Agent ist eigenständig, hat eigene Werkzeuge/Rechte und eigenen Kontext.
Neue Fähigkeiten = neuer Agent mit eigener Konfiguration, nie ein Sonderfall
im Orchestrator-Code.

Vollständigen Fahrplan mit allen Phasen und Entscheidungen siehe
`fahrplan-persoenlicher-assistent.md`.

## Aktueller Stand

- Phase 0 abgeschlossen (Use Case, Tech-Stack, Interface-Vertrag definiert)
- Erster Agent fertig: `agent-email/` – IMAP-Anbindung, Klassifizierung und
  Cloud-Ablage (Google Drive oder OneDrive, konfigurierbar) stehen
- Orchestrator selbst existiert noch nicht (kommt in Phase 1)

## Tech-Stack agent-email

- Python, IMAP über `imapclient` (IDLE bevorzugt, Polling als Fallback)
- Klassifizierung über die Claude API
- Ablage wahlweise über Google Drive API oder Microsoft Graph API
  (OneDrive), Auswahl per `STORAGE_PROVIDER`
- Läuft als eigenständiger Dienst, nicht als Teil einer Chat-Session

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
- `agent-email/imap_client.py` – IMAP-Verbindung, Polling, IDLE
- `agent-email/message_loader.py` – lädt Nachrichteninhalt + Anhänge per UID
- `agent-email/classifier.py` – Klassifizierung über die Claude API
- `agent-email/file_naming.py` – gemeinsame Dateinamens-/Datums-Hilfsfunktionen
  für die Cloud-Ablage
- `agent-email/drive_client.py` – OAuth-Flow + Ablage der Anhänge in Google Drive
- `agent-email/onedrive_client.py` – OAuth-Flow + Ablage der Anhänge in OneDrive
- `agent-email/main.py` – Einstiegspunkt/CLI, wählt Storage-Provider per
  `STORAGE_PROVIDER`

## Regeln

- Zugangsdaten/Secrets ausschließlich über `.env`, nie im Code oder Chat
- Kategorienliste ist fest vorgegeben (siehe Anhang unten), nicht ohne
  Rücksprache ändern
- Jeder neue Agent bekommt: Name, Zuständigkeits-Beschreibung, erlaubte
  Werkzeuge, definiertes Ein-/Ausgabeformat – analog zum Interface-Vertrag
  des agent-email
- Kritische/irreversible Aktionen (z. B. Mail senden, Termin anlegen) nie ohne
  expliziten Freigabe-Schritt

## Nächster Schritt

`agent-email` ist damit abgeschlossen (IMAP, Klassifizierung, Drive-Ablage).
Nächster Baustein laut Fahrplan: der Orchestrator selbst (Phase 1) sowie
weitere Einzel-Agenten – jeweils mit eigenem Namen, Zuständigkeits-
Beschreibung, erlaubten Werkzeugen und definiertem Ein-/Ausgabeformat (siehe
Regeln oben).

## Anhang: Kategorienliste (Stand 2026-07-17)

1. Rechnungen/Zahlungen
2. Verträge
3. Bestellungen/Lieferungen
4. Termine/Einladungen
5. Newsletter
6. Privat
7. Sonstiges (Fallback für alles Unklare)

## Anhang: Pfadschema Cloud-Ablage (Stand 2026-07-17, erweitert 2026-07-17)

Flach nach Kategorie, kein Jahresordner, identisch für Google Drive und
OneDrive. Nur Mails **mit Anhang** werden abgelegt; der Original-Dateiname
bleibt Teil des Dateinamens (wichtig bei mehreren Anhängen pro Mail):

```
Email-Ablage/<Kategorie>/<Datum>_<Betreff>_<Original-Dateiname>
```

Beispiel: `Email-Ablage/Rechnungen-Zahlungen/2026-07-17_Stromrechnung Juli_rechnung.pdf`

Welcher Dienst genutzt wird, legt `STORAGE_PROVIDER` (`google_drive` oder
`onedrive`) in der `.env` fest — nicht beide gleichzeitig.
