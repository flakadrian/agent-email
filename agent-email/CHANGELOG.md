# Changelog

Nennenswerte Änderungen an `agent-email`, chronologisch geordnet (neueste
zuerst). Hält fest, *was* sich geändert hat und *warum* – für Details siehe
die verlinkten PRs bzw. `git log`.

Es gibt keine Versionsnummern/Releases, daher Gliederung nach Datum. Bei
jeder nennenswerten Änderung (neues Feature, Verhaltensänderung, wichtiger
Fix) einen Eintrag hier ergänzen, idealerweise im selben PR.

## 2026-09-17 – Unterstützung für mehrere Postfächer

- **Feature:** Mehrere IMAP-Accounts können jetzt parallel vom selben Agenten
  überwacht werden - ein eigener Docker-Container pro Account, alle gegen
  denselben `ollama`-Service (kein mehrfaches Vorhalten des lokalen Modells
  auf schwacher NAS-Hardware). Jeder Account wählt unabhängig
  `CLASSIFIER_PROVIDER`/`STORAGE_PROVIDER`.
- Reine Deployment-/Doku-Erweiterung, **keine `*.py`-Datei geändert**: die
  Isolation zwischen Accounts ergibt sich vollständig aus Container-/
  Volume-Grenzen (Heartbeat-Datei ist bereits containerlokal, Token-/
  Ablage-Pfade sind bereits über Volume-Mounts konfigurierbar).
- Neue Konvention `agent-email/accounts/<name>/` für Config/Secrets
  zusätzlicher Accounts (`.env` + ggf. `credentials.json`/`token.json`/
  `onedrive_token_cache.json`), per `.gitignore` ausgeschlossen. Bestehender
  Root-Account (`.env`, `token.json` etc.) bleibt unverändert, um kein
  ungewolltes Redeploy des bereits laufenden Containers auszulösen.
- `docker-compose.yml` enthält einen auskommentierten Beispiel-Service als
  Vorlage zum Kopieren für weitere Accounts.
- `deploy-to-nas.sh` baut/startet jetzt alle Compose-Services statt nur
  `agent-email`, damit aktivierte Zusatz-Accounts automatisch mit
  ausgerollt werden.

## 2026-09-16 – Prompt-Länge für lokale Klassifizierung begrenzt

- **Bugfix:** Eine Mail mit längerem Text führte zu einem 1748-Token-Prompt,
  der auf der schwachen NAS-CPU (gemessen ~4,5 Tokens/s Prompt-Verarbeitung)
  nicht innerhalb des 240s-Timeouts verarbeitet werden konnte – Fallback auf
  `Sonstiges` statt korrekter Klassifizierung.
- `_build_prompt()` (`classifier.py`) nimmt jetzt ein `body_limit`-Argument;
  Claude API nutzt weiterhin 4000 Zeichen (`DEFAULT_BODY_LIMIT`, keine
  Geschwindigkeitsprobleme dort), der lokale Pfad (`local_classifier.py`)
  nutzt bewusst nur 1500 Zeichen (`_LOCAL_BODY_LIMIT`) - rechnerisch
  hergeleitet aus der gemessenen Geschwindigkeit, damit auch längere Mails
  sicher innerhalb des Timeouts verarbeitet werden. Betreff, Absender und
  Anhang-Dateinamen bleiben in beiden Fällen vollständig erhalten (nur der
  Mailtext wird gekürzt).

## 2026-09-16 – Projektumfang bewusst auf einen einzelnen Agenten festgelegt

- **Entscheidung:** Ursprünglich als erster Baustein eines geplanten
  Multi-Agent-Systems mit Orchestrator angelegt (siehe ältere Einträge unten).
  Bewusst dabei belassen, `agent-email` als eigenständiges, abgeschlossenes
  Projekt weiterzuentwickeln – kein Orchestrator, keine weiteren Agenten
  geplant.
- `CLAUDE.md` und das Root-`README.md` entsprechend umgeschrieben (keine
  "Phase 0/1"-Rahmung mehr, kein Verweis auf einen geplanten Orchestrator).
  Ordnerstruktur (Root + `agent-email/`) bewusst unverändert gelassen, um
  kein erneutes NAS-Redeployment auszulösen.
- GitHub-Repo von `agent-assistant` zurück zu `agent-email` umbenannt,
  passend zum jetzt fixierten Alleinstellungszweck.
- **Sicherheitsaudit vor Veröffentlichung:** Repo und komplette Git-Historie
  auf Secrets geprüft (keine gefunden, `.gitignore` greift korrekt). Echte
  interne NAS-IP und SSH-Benutzername aus den Beispiel-Kommentaren in
  `deploy-to-nas.sh` entfernt (unnötige Preisgabe von Heimnetzwerk-Infos in
  diesem öffentlichen Repo).
- **Klassifizierungs-Genauigkeit:** Bekannte automatisierte Absender (z. B.
  GitHub-Benachrichtigungen zu eigenen Commits/PRs) wurden vom lokalen
  `qwen2.5:0.5b`-Modell fälschlich als `Rechnungen/Zahlungen` eingeordnet,
  statt wie im Prompt vorgegeben auf `Sonstiges` auszuweichen – eine
  Grenze kleiner lokaler Modelle bei ungewöhnlichem Inhalt. Neues Modul
  `sender_filter.py` erkennt solche Absender jetzt vorab per Muster und
  routet sie ohne KI-Aufruf direkt auf `Sonstiges`.

## 2026-09-15 – Stabilität: automatischer Reconnect bei IMAP-Verbindungsabbrüchen

- **Bugfix:** `listen`/`poll` stürzten alle paar Stunden komplett ab, wenn der
  Mailserver die IMAP-Verbindung serverseitig beendete (Timeout, TLS-EOF,
  BYE-Antwort während IDLE) – in den Logs sichtbar als wiederkehrende
  `imaplib.IMAP4.abort`/`.error`- bzw. `ssl.SSLError`-Tracebacks im
  ~3-Stunden-Rhythmus. Die Exception war unbehandelt und beendete den
  gesamten Prozess; nur `restart: unless-stopped` brachte den Container
  danach wieder hoch, mit spürbarer Lücke bis zum Neustart.
- `idle_listen()`/`poll_new_messages()` fangen diese Verbindungsfehler jetzt
  ab (`imaplib.IMAP4.error`, `imapclient.exceptions.IMAPClientError`,
  `OSError`/`ssl.SSLError`), loggen eine `WARNING` und bauen die
  IMAP-Verbindung selbst neu auf, statt den Prozess zu beenden.

## 2026-08-06 – Entwicklungsprozess gehärtet

- **Sicherheitsfix:** Bind-Mount für `STORAGE_PROVIDER=local` band versehentlich
  eine bestehende, umfassende persönliche Freigabe (`/volume1/Daten`) statt
  eines dedizierten Ordners ein – der (als root laufende) Container hatte
  dadurch vollen Zugriff auf private Dateien statt nur auf die E-Mail-Ablage.
  Auf einen eigenen Freigabeordner (`/volume1/Agent`) umgestellt, Warnung
  dazu in `docker-compose.yml`/`.env.example`/README ergänzt. Entdeckt über
  die neue Diagnose-Logausgabe (Verzeichnisinhalt beim Start).
- CI-Pipeline (GitHub Actions): automatisierte Tests + Linting bei jedem
  Push/PR, inkl. Docker-Build-Check ([#12](https://github.com/flakadrian/agent-email/pull/12))
- Dependencies auf exakte Versionen gepinnt statt offener `>=`-Constraints,
  `ruff` als Linter eingerichtet ([#12](https://github.com/flakadrian/agent-email/pull/12))
- Test-Lücken geschlossen: `main.py` (Verdrahtung Klassifizierung/Ablage) und
  `imap_client.py` waren zuvor komplett ungetestet ([#13](https://github.com/flakadrian/agent-email/pull/13))
- `print()` durch strukturiertes Logging ersetzt (Zeitstempel, Level,
  Modulname) ([#14](https://github.com/flakadrian/agent-email/pull/14))
- Docker gehärtet: `ollama`-Image-Version gepinnt statt `:latest`,
  `HEALTHCHECK` via Heartbeat-Datei erkennt einen hängenden (nicht nur
  abgestürzten) Prozess ([#15](https://github.com/flakadrian/agent-email/pull/15))
- Automatisiertes Deployment-Skript (`deploy-to-nas.sh`, `git archive` über
  SSH) statt manuellem Datei-Kopieren per File Station – live gegen ein
  echtes NAS getestet ([#16](https://github.com/flakadrian/agent-email/pull/16))
- Diagnose-Logging für lokale Dateiablage ergänzt (erkennt u. a., ob ein
  konfigurierter Pfad wirklich ein Mountpoint ist); Pfad-Konfiguration in
  `.env.example`/`docker-compose.yml` deutlich klarer dokumentiert, nachdem
  eine Verwechslung von Host- und Container-Pfad zu stundenlanger
  Fehlersuche geführt hatte
- Klassifizierungs-Timeout erhöht (60s → 240s) für schwache NAS-Hardware;
  Terminal-Zugriff auf den `agent-email`-Container ermöglicht (`tty`)
- Gesamte Dokumentation (README, `CLAUDE.md`, Docstrings) auf aktuellen
  Stand gebracht

## 2026-08-05 – Lokale Alternativen zu Cloud-Diensten

- Lokale Klassifizierung über [Ollama](https://ollama.com) statt Claude API
  (`CLASSIFIER_PROVIDER=local`) – ermöglicht Betrieb ganz ohne externe
  API-Abhängigkeit
- Lokale Dateiablage statt Google Drive/OneDrive
  (`STORAGE_PROVIDER=local`)

## 2026-08-04 – Docker/NAS-Betrieb

- `Dockerfile` + `docker-compose.yml` für dauerhaften Betrieb ohne offene
  SSH-Sitzung, z. B. auf einem Synology-NAS über Container Manager

## 2026-07-22 – Robustheit

- OneDrive als Alternative zu Google Drive (`STORAGE_PROVIDER=onedrive`)
- Namenskonflikt bei `STORAGE_PROVIDERS` behoben, bessere
  Upload-Fehlermeldungen
- `pip-system-certs` ergänzt (behebt `CERTIFICATE_VERIFY_FAILED` auf
  Firmenrechnern mit SSL-Inspektionsproxy)

## 2026-07-17 – Erste Version

- IMAP-Anbindung (Verbinden, IDLE, Polling-Fallback)
- Klassifizierung neuer Mails über die Claude API anhand einer festen
  Kategorienliste
- Ablage der Anhänge klassifizierter Mails in Google Drive
- Absturz bei Emoji-Betreffzeilen auf der Windows-Konsole behoben
