# E-Mail-Agent – IMAP-Anbindung + Klassifizierung

Dieser Teil kümmert sich um den IMAP-Zugriff (Verbinden, Login, auf neue Mails
reagieren) sowie das Laden und Klassifizieren neuer Mails über die Claude API.
Die Ablage in Google Drive kommt als nächster Baustein dazu, sobald die
dafür nötigen OAuth-Credentials eingerichtet sind.

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

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Die Tests laufen komplett gemockt (kein echter IMAP-Server, kein echter
API-Call).

## Nächste Schritte (noch nicht Teil dieses Bausteins)

- Strukturierte Ablage in Google Drive gemäß dem in `CLAUDE.md` festgelegten
  Pfadschema (erfordert OAuth-Setup im Google-Konto)
