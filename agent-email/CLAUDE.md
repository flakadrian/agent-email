# Projekt: Persönlicher Assistent mit Multi-Agent-Orchestrierung

Ein Orchestrator verteilt Anfragen/Ereignisse an spezialisierte Einzel-Agenten.
Jeder Agent ist eigenständig, hat eigene Werkzeuge/Rechte und eigenen Kontext.
Neue Fähigkeiten = neuer Agent mit eigener Konfiguration, nie ein Sonderfall
im Orchestrator-Code.

Vollständigen Fahrplan mit allen Phasen und Entscheidungen siehe
`fahrplan-persoenlicher-assistent.md`.

## Aktueller Stand

- Phase 0 abgeschlossen (Use Case, Tech-Stack, Interface-Vertrag definiert)
- Erster Agent in Arbeit: `email-agent/` – IMAP-Anbindung steht, Klassifizierung
  und Google-Drive-Ablage fehlen noch
- Orchestrator selbst existiert noch nicht (kommt in Phase 1)

## Tech-Stack email-agent

- Python, IMAP über `imapclient` (IDLE bevorzugt, Polling als Fallback)
- Klassifizierung über die Claude API
- Ablage über die Google Drive API
- Läuft als eigenständiger Dienst, nicht als Teil einer Chat-Session

## Befehle

```bash
cd email-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # dann echte Werte eintragen, NIE committen
python main.py test    # IMAP-Verbindung prüfen
python main.py listen  # auf neue Mails warten (IDLE)
```

## Architektur-Dateien

- `email-agent/config.py` – lädt/validiert Umgebungsvariablen
- `email-agent/imap_client.py` – IMAP-Verbindung, Polling, IDLE
- `email-agent/main.py` – Einstiegspunkt/CLI

## Regeln

- Zugangsdaten/Secrets ausschließlich über `.env`, nie im Code oder Chat
- Kategorienliste ist fest vorgegeben (siehe Fahrplan-Anhang), nicht ohne
  Rücksprache ändern
- Jeder neue Agent bekommt: Name, Zuständigkeits-Beschreibung, erlaubte
  Werkzeuge, definiertes Ein-/Ausgabeformat – analog zum Interface-Vertrag
  des email-agent
- Kritische/irreversible Aktionen (z. B. Mail senden, Termin anlegen) nie ohne
  expliziten Freigabe-Schritt

## Nächster Schritt

Nachrichteninhalt + Anhänge aus der UID laden, über die Claude API anhand der
festen Kategorienliste klassifizieren, strukturiert in Google Drive ablegen
(Pfadschema siehe Fahrplan-Anhang).
