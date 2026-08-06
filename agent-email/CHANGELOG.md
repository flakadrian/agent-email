# Changelog

Nennenswerte Änderungen an `agent-email`, chronologisch geordnet (neueste
zuerst). Hält fest, *was* sich geändert hat und *warum* – für Details siehe
die verlinkten PRs bzw. `git log`.

Es gibt keine Versionsnummern/Releases, daher Gliederung nach Datum. Bei
jeder nennenswerten Änderung (neues Feature, Verhaltensänderung, wichtiger
Fix) einen Eintrag hier ergänzen, idealerweise im selben PR.

## 2026-08-06 – Entwicklungsprozess gehärtet

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
