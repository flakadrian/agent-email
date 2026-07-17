# E-Mail-Agent – IMAP-Anbindung + Klassifizierung + Cloud-Ablage

Dieser Teil kümmert sich um den IMAP-Zugriff (Verbinden, Login, auf neue Mails
reagieren), das Laden und Klassifizieren neuer Mails über die Claude API
sowie die Ablage der Anhänge wahlweise in Google Drive oder Microsoft
OneDrive (per `STORAGE_PROVIDER` konfigurierbar, siehe Abschnitt 5).

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
- **STORAGE_PROVIDER** – `google_drive` (Standard) oder `onedrive`, legt fest
  wohin Anhänge abgelegt werden (siehe Abschnitt 5).
- **ONEDRIVE_CLIENT_ID**/**ONEDRIVE_TENANT** – nur nötig, wenn
  `STORAGE_PROVIDER=onedrive` (siehe Abschnitt 5).

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

Mails **mit Anhang** werden zusätzlich in der konfigurierten Cloud-Ablage
abgelegt (Mails ohne Anhang bleiben nur klassifiziert, siehe Kategorienliste
in `CLAUDE.md`):

```
  2 Anhang/Anhänge in Google Drive abgelegt (Rechnungen-Zahlungen)
```

## 5. Cloud-Ablage einrichten (einmalig)

Welcher Dienst genutzt wird, legt `STORAGE_PROVIDER` in der `.env` fest
(`google_drive` oder `onedrive`). Jeweils einmalig einzurichten:

### Google Drive

Voraussetzung: ein Google-Cloud-Projekt mit aktivierter Drive API, OAuth-
Consent-Screen (External, deine eigene Adresse als Testnutzer) und einer
Desktop-OAuth-Client-ID. Die dabei heruntergeladene JSON-Datei legst du als
`agent-email/credentials.json` ab (per `.gitignore` von Git ausgeschlossen).

### OneDrive

1. [portal.azure.com](https://portal.azure.com) → **Microsoft Entra ID →
   App-Registrierungen → Neue Registrierung**
2. Name z. B. `agent-email`, "Unterstützte Kontotypen": je nach Konto
   persönliche + geschäftliche Konten (oder nur privat, falls du nur ein
   outlook.com/hotmail-Konto nutzt)
3. **Redirect-URI**: Plattform "Mobile- und Desktopanwendungen" auswählen,
   URI `http://localhost` eintragen
4. Nach dem Erstellen: **API-Berechtigungen → Berechtigung hinzufügen →
   Microsoft Graph → Delegierte Berechtigungen → Files.ReadWrite** hinzufügen
5. Die **Anwendungs-ID (Client)** von der Übersichtsseite kopieren und als
   `ONEDRIVE_CLIENT_ID` in die `.env` eintragen — kein Client-Secret nötig,
   da dies ein "Public Client" ist (Desktop-App-Flow)

### Autorisieren

Danach einmalig, unabhängig vom gewählten Anbieter:

```bash
python main.py storage-auth
```

Das öffnet den Browser zur Zustimmung und speichert den Zugriffstoken lokal
(`token.json` für Google Drive, `onedrive_token_cache.json` für OneDrive —
beide von Git ausgeschlossen, werden bei Ablauf automatisch erneuert). Ab
dann legen `listen`/`poll` Anhänge automatisch unter
`Email-Ablage/<Kategorie>/` im gewählten Dienst ab (Pfadschema siehe
`CLAUDE.md`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Die Tests laufen komplett gemockt (kein echter IMAP-Server, kein echter
API-Call, kein echter Drive-Zugriff).
