# Projekt: Persönlicher Assistent mit Multi-Agent-Orchestrierung

Ein Orchestrator verteilt Anfragen/Ereignisse an spezialisierte Einzel-Agenten.
Jeder Agent ist eigenständig, hat eigene Werkzeuge/Rechte und eigenen Kontext.
Neue Fähigkeiten = neuer Agent mit eigener Konfiguration, nie ein Sonderfall
im Orchestrator-Code.

Vollständigen Fahrplan mit allen Phasen und Entscheidungen siehe
`fahrplan-persoenlicher-assistent.md`.

## Aktueller Stand

- Phase 0 abgeschlossen (Use Case, Tech-Stack, Interface-Vertrag definiert)
- Erster Agent in Arbeit: `agent-email/` – IMAP-Anbindung und Klassifizierung
  stehen, Google-Drive-Ablage fehlt noch (wartet auf OAuth-Setup im
  Google-Konto des Nutzers)
- Orchestrator selbst existiert noch nicht (kommt in Phase 1)

## Tech-Stack agent-email

- Python, IMAP über `imapclient` (IDLE bevorzugt, Polling als Fallback)
- Klassifizierung über die Claude API
- Ablage über die Google Drive API
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
- `agent-email/main.py` – Einstiegspunkt/CLI

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

Strukturierte Ablage in Google Drive gemäß dem Pfadschema (siehe Anhang
unten). Voraussetzung: Google-Cloud-Projekt mit OAuth-Credentials im
Google-Konto des Nutzers einrichten (Drive API aktivieren, Consent Screen,
Credentials-Download) – erfordert manuelle Schritte, die nicht automatisiert
durchführbar sind.

## Anhang: Kategorienliste (Stand 2026-07-17)

1. Rechnungen/Zahlungen
2. Verträge
3. Bestellungen/Lieferungen
4. Termine/Einladungen
5. Newsletter
6. Privat
7. Sonstiges (Fallback für alles Unklare)

## Anhang: Pfadschema Google Drive (Stand 2026-07-17)

Flach nach Kategorie, kein Jahresordner:

```
/Email-Ablage/<Kategorie>/<Datum>_<Betreff>.<ext>
```

Beispiel: `/Email-Ablage/Rechnungen-Zahlungen/2026-07-17_Stromrechnung-Juli.pdf`
