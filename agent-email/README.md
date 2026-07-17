# E-Mail-Agent – IMAP-Anbindung + Klassifizierung + Google-Drive-Ablage

Dieser Teil kümmert sich um den IMAP-Zugriff (Verbinden, Login, auf neue Mails
reagieren), das Laden und Klassifizieren neuer Mails über die Claude API
sowie die Ablage der Anhänge in Google Drive.

## 1. Setup

```bash
cd agent-email
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Zugangsdaten eintragen

```bash
cp .env.example .env
```

Dann `.env` mit einem Editor öffnen und ausfüllen:

- **IMAP_HOST** – Adresse des Mailservers. Steht meist in den Hilfeseiten
  deines Anbieters unter "IMAP-Einstellungen" oder "E-Mail-Client einrichten".
- **IMAP_PORT** – in der Regel `993` (IMAP über SSL). Nur ändern, wenn dein
  Anbieter explizit etwas anderes vorgibt.
- **IMAP_USER** – deine volle E-Mail-Adresse.
- **IMAP_PASSWORD** – Achtung: viele Anbieter (z. B. wenn 2FA aktiv ist)
  verlangen ein separates **App-Passwort** statt deines normalen Passworts.
  Das legst du in den Sicherheitseinstellungen deines E-Mail-Kontos an.
- **IMAP_FOLDER** – meist `INBOX`.
- **ANTHROPIC_API_KEY** – für die Klassifizierung über die Claude API. Zu
  erstellen unter https://console.anthropic.com/settings/keys.
- **ANTHROPIC_MODEL** – optional, Standard ist ein schnelles/günstiges Modell.
  Reicht für die Klassifizierung anhand der festen Kategorienliste völlig aus.

Die `.env` bleibt lokal bei dir, sie wird über `.gitignore` von Git
ausgeschlossen und landet nie in einem Repository.

## 3. Verbindung testen

```bash
python main.py test
```

Erwartete Ausgabe bei Erfolg:

```
Verbindung erfolgreich zu imap.deinanbieter.de als deine-adresse@beispiel.de
Ordner 'INBOX' enthält 42 Nachrichten
Verfügbare Ordner: [...]
```

Typische Fehlerquellen, falls es nicht klappt:

- Falscher Host/Port → in den Hilfeseiten deines Anbieters nachsehen
- Login schlägt fehl, obwohl Passwort stimmt → vermutlich App-Passwort nötig
- "IMAP nicht aktiviert" → manche Anbieter verlangen, IMAP-Zugriff im
  Webmail-Interface erst manuell freizuschalten

## 4. Auf neue Mails reagieren

```bash
python main.py listen   # bevorzugt: IMAP IDLE, reagiert nahezu sofort
python main.py poll     # Fallback, falls der Anbieter kein IDLE unterstützt
```

Bei neuen Mails wird der Nachrichteninhalt inkl. Anhänge geladen (siehe
`message_loader.py`) und über die Claude API einer der festen Kategorien
zugeordnet (siehe `classifier.py`, Kategorienliste in `CLAUDE.md`). Beispiel:

```
UID 123: 'Stromrechnung Juli' -> Kategorie: Rechnungen/Zahlungen
```

Bei Fehlern (z. B. API nicht erreichbar, unerwartete Antwort) fällt die
Klassifizierung auf `Sonstiges` zurück statt abzustürzen.

Mails **mit Anhang** werden zusätzlich in Google Drive abgelegt (Mails ohne
Anhang bleiben nur klassifiziert, siehe Kategorienliste in `CLAUDE.md`):

```
  2 Anhang/Anhänge in Drive abgelegt (Rechnungen-Zahlungen)
```

## 5. Google-Drive-Ablage einrichten (einmalig)

Voraussetzung: ein Google-Cloud-Projekt mit aktivierter Drive API, OAuth-
Consent-Screen (External, deine eigene Adresse als Testnutzer) und einer
Desktop-OAuth-Client-ID. Die dabei heruntergeladene JSON-Datei legst du als
`agent-email/credentials.json` ab (per `.gitignore` von Git ausgeschlossen).

Danach einmalig:

```bash
python main.py drive-auth
```

Das öffnet den Browser zur Google-Zustimmung und speichert den Zugriffstoken
in `token.json` (ebenfalls von Git ausgeschlossen, wird bei Ablauf automatisch
erneuert). Ab dann legen `listen`/`poll` Anhänge automatisch unter
`Email-Ablage/<Kategorie>/` in deinem Drive ab (Pfadschema siehe `CLAUDE.md`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Die Tests laufen komplett gemockt (kein echter IMAP-Server, kein echter
API-Call, kein echter Drive-Zugriff).
