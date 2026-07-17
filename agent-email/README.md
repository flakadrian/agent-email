# E-Mail-Agent – IMAP-Anbindung (Phase 1, Schritt 1)

Dieser Teil kümmert sich nur um den IMAP-Zugriff: Verbinden, Login, auf neue
Mails reagieren. Klassifizierung (Claude API) und Ablage (Google Drive) kommen
als nächste Bausteine dazu, sobald die Verbindung steht.

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

Aktuell wird bei neuen Mails nur die UID ausgegeben (`print_message` in
`main.py`). Das ist der Anschlusspunkt für den nächsten Schritt.

## Nächste Schritte (noch nicht Teil dieses Bausteins)

- Nachrichteninhalt + Anhänge aus der UID laden
- Klassifizierung über die Claude API anhand der festgelegten Kategorienliste
- Strukturierte Ablage in Google Drive gemäß dem im Fahrplan festgelegten
  Pfadschema
