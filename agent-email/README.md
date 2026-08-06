# E-Mail-Agent – IMAP-Anbindung + Klassifizierung + Ablage

Dieser Teil kümmert sich um den IMAP-Zugriff (Verbinden, Login, auf neue Mails
reagieren), das Laden und Klassifizieren neuer Mails sowie die Ablage der
Anhänge. Sowohl Klassifizierung als auch Ablage sind austauschbar:

- **Klassifizierung** – über die Claude API oder über ein lokales Modell via
  [Ollama](https://ollama.com) (per `CLASSIFIER_PROVIDER` konfigurierbar,
  siehe Abschnitt 6).
- **Ablage** – wahlweise in Google Drive, Microsoft OneDrive oder einem
  lokalen Dateisystempfad (per `STORAGE_PROVIDER` konfigurierbar, siehe
  Abschnitt 5).

Läuft entweder direkt mit Python (lokale Entwicklung/Tests, siehe unten) oder
als Docker-Container, z. B. dauerhaft auf einem NAS (siehe Abschnitt 7).

## 1. Setup

```bash
cd agent-email
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Auf Firmenrechnern mit SSL-Inspektionsproxy (z. B. Zscaler/Netskope) können
HTTPS-Calls zur Claude-/Google-API sonst mit `CERTIFICATE_VERIFY_FAILED`
fehlschlagen. `requirements.txt` enthält dafür bereits `pip-system-certs`,
das die Betriebssystem-Zertifikatsablage statt des Python-eigenen
`certifi`-Bundles nutzt.

## 2. Zugangsdaten eintragen

```bash
cp .env.example .env
```

Dann `.env` mit einem Editor öffnen und ausfüllen (vollständige Liste inkl.
Kommentaren siehe `.env.example`):

- **IMAP_HOST** – Adresse des Mailservers. Steht meist in den Hilfeseiten
  deines Anbieters unter "IMAP-Einstellungen" oder "E-Mail-Client einrichten".
- **IMAP_PORT** – in der Regel `993` (IMAP über SSL). Nur ändern, wenn dein
  Anbieter explizit etwas anderes vorgibt.
- **IMAP_USER** – deine volle E-Mail-Adresse.
- **IMAP_PASSWORD** – Achtung: viele Anbieter (z. B. wenn 2FA aktiv ist)
  verlangen ein separates **App-Passwort** statt deines normalen Passworts.
  Das legst du in den Sicherheitseinstellungen deines E-Mail-Kontos an.
- **IMAP_FOLDER** – meist `INBOX`.
- **CLASSIFIER_PROVIDER** – `anthropic` (Standard) oder `local`, legt fest,
  wer die Klassifizierung übernimmt (siehe Abschnitt 6).
- **ANTHROPIC_API_KEY**/**ANTHROPIC_MODEL** – nur nötig, wenn
  `CLASSIFIER_PROVIDER=anthropic`. Key zu erstellen unter
  https://console.anthropic.com/settings/keys.
- **OLLAMA_HOST**/**OLLAMA_MODEL** – nur nötig, wenn
  `CLASSIFIER_PROVIDER=local` (siehe Abschnitt 6).
- **STORAGE_PROVIDER** – `google_drive` (Standard), `onedrive` oder `local`,
  legt fest wohin Anhänge abgelegt werden (siehe Abschnitt 5).
- **ONEDRIVE_CLIENT_ID**/**ONEDRIVE_TENANT** – nur nötig, wenn
  `STORAGE_PROVIDER=onedrive` (siehe Abschnitt 5).
- **LOCAL_STORAGE_PATH** – nur nötig, wenn `STORAGE_PROVIDER=local` (siehe
  Abschnitt 5). **Wichtig im Docker-Betrieb:** siehe die ausführliche Warnung
  dazu in `.env.example` – hier gehört der Pfad *innerhalb* des Containers
  hin, nicht der echte NAS-Pfad.

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

Beim Start wird das konfigurierte Ablageziel einmal ausgegeben (z. B.
`Speicherziel (lokalem Pfad): /data`). Bei neuen Mails wird der
Nachrichteninhalt inkl. Anhänge geladen (siehe `message_loader.py`) und über
den konfigurierten `CLASSIFIER_PROVIDER` einer der festen Kategorien
zugeordnet (siehe `classifier.py`/`local_classifier.py`, Kategorienliste in
`CLAUDE.md`). Beispiel:

```
UID 123: 'Stromrechnung Juli' -> Kategorie: Rechnungen/Zahlungen
```

Bei Fehlern (z. B. API/Ollama nicht erreichbar, Timeout, unerwartete
Antwort) fällt die Klassifizierung auf `Sonstiges` zurück statt abzustürzen.

Mails **mit Anhang** werden zusätzlich in der konfigurierten Ablage
abgelegt (Mails ohne Anhang bleiben nur klassifiziert, siehe Kategorienliste
in `CLAUDE.md`), inkl. der geschriebenen Pfade/IDs:

```
  2 Anhang/Anhänge in Google Drive abgelegt (Rechnungen-Zahlungen):
    <file-id-1>
    <file-id-2>
```

## 5. Ablage einrichten (einmalig)

Welches Ziel genutzt wird, legt `STORAGE_PROVIDER` in der `.env` fest
(`google_drive`, `onedrive` oder `local`).

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

Danach einmalig, für Google Drive oder OneDrive:

```bash
python main.py storage-auth
```

Das öffnet den Browser zur Zustimmung und speichert den Zugriffstoken lokal
(`token.json` für Google Drive, `onedrive_token_cache.json` für OneDrive —
beide von Git ausgeschlossen, werden bei Ablauf automatisch erneuert).

### Lokaler Pfad

Kein OAuth nötig. `LOCAL_STORAGE_PATH` in der `.env` auf den gewünschten
Basis-Pfad setzen (lokal z. B. einen absoluten Pfad auf deinem Rechner; im
Docker-Betrieb den Container-internen Pfad, siehe Warnung in
`.env.example` und Abschnitt 7). Der Ordner wird beim Start automatisch
angelegt, falls er noch nicht existiert.

Ab dann legen `listen`/`poll` Anhänge automatisch unter
`Email-Ablage/<Kategorie>/` im gewählten Ziel ab (Pfadschema siehe
`CLAUDE.md`).

## 6. Lokale Klassifizierung mit Ollama einrichten (optional)

Alternative zur Claude API, z. B. um ganz ohne externe API-Abhängigkeit
auszukommen. Voraussetzung: [Ollama](https://ollama.com) läuft erreichbar
unter `OLLAMA_HOST` (lokal per nativer Installation, im Docker-Betrieb als
eigener Service, siehe Abschnitt 7).

```bash
ollama pull qwen2.5:1.5b   # Modellname muss zu OLLAMA_MODEL in .env passen
```

In `.env`:

```
CLASSIFIER_PROVIDER=local
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

**Hardware-Hinweis:** Auf schwacher Hardware (z. B. Einsteiger-NAS ohne GPU,
wenig RAM) kann das Laden/Antworten je nach Modellgröße mehrere zehn Sekunden
bis wenige Minuten dauern. `local_classifier.py` wartet aktuell bis zu 240
Sekunden auf eine Antwort, bevor es auf `Sonstiges` zurückfällt. Bei
knappem RAM (deutlich unter ~2 GB frei) empfiehlt sich ein kleineres Modell,
z. B. `qwen2.5:0.5b` statt `qwen2.5:1.5b`.

## 7. Betrieb über Docker (z. B. auf einem NAS)

Für dauerhaften Betrieb ohne offene SSH-Sitzung, z. B. auf einem Synology-NAS
über Container Manager. Im Ordner liegen bereits `Dockerfile` und
`docker-compose.yml`.

### Einmaliges Setup

1. Projektordner (inkl. ausgefüllter `.env` und ggf. `credentials.json` /
   `token.json` / `onedrive_token_cache.json`) auf den Zielrechner
   übertragen.
2. Falls `STORAGE_PROVIDER=local`: In `docker-compose.yml` den Bind-Mount
   der `agent-email`-Volumes anpassen (linke Seite = echter Pfad auf dem
   Host, rechte Seite muss zu `LOCAL_STORAGE_PATH` in `.env` passen – siehe
   ausführliche Warnung dazu in `.env.example`, das war in der Praxis die
   häufigste Fehlerquelle).
3. Falls `CLASSIFIER_PROVIDER=local`: Der optionale `ollama`-Service in
   `docker-compose.yml` startet mit; Modell einmalig im laufenden Container
   laden:
   ```bash
   docker exec -it ollama ollama pull qwen2.5:1.5b
   ```
4. Bauen und starten:
   ```bash
   docker compose up -d --build
   ```

### Updates einspielen

Nach Code- oder `.env`-Änderungen reicht **kein** einfacher Container-Neustart
– Docker liest `env_file` und Volumes nur beim tatsächlichen Neu-Erstellen
des Containers neu ein:

```bash
docker compose build agent-email
docker compose up -d agent-email
```

(Auf Synology entspricht das: Container Manager → Projekt →
`agent-email` → Neu erstellen. Der `ollama`-Container und das bereits
geladene Modell bleiben davon unberührt, da das Modell in einem separaten,
persistenten Volume liegt.)

### Fehlersuche ohne SSH

- **Logs**: Container Manager → Container → `agent-email`/`ollama` →
  Protokoll. Zeigt u. a. das beim Start ausgegebene Speicherziel und bei
  `STORAGE_PROVIDER=local` zusätzlich pro Datei den Zielpfad sowie ob der
  konfigurierte Pfad tatsächlich ein Mountpoint ist (`local_storage.py`).
- **Umgebungsvariablen/Volumes prüfen**: Container Manager → Container →
  `agent-email` → Detail → Reiter "Umgebung"/"Volumen" – zeigt die
  tatsächlich aktiven Werte, ohne dass ein Terminal nötig ist.
- **Terminal**: `tty: true`/`stdin_open: true` sind für den
  `agent-email`-Service gesetzt, damit Container Manager ein Terminal
  anhängen kann (Container → Detail → Terminal).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Die Tests laufen komplett gemockt (kein echter IMAP-Server, kein echter
API-/Ollama-Call, kein echter Drive-/OneDrive-/Dateisystem-Zugriff außerhalb
von `tmp_path`).
