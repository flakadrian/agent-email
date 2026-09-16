# agent-email

E-Mail-Agent: überwacht ein IMAP-Postfach, klassifiziert eingehende Mails
anhand einer festen Kategorienliste (Claude API oder lokal via Ollama) und
legt Anhänge strukturiert ab (Google Drive, OneDrive oder ein lokaler
Dateisystempfad). Läuft lokal mit Python oder dauerhaft als Docker-Container,
z. B. auf einem NAS.

Der eigentliche Code liegt im Unterordner [`agent-email/`](agent-email/) -
Setup, Konfiguration und Betrieb siehe [agent-email/README.md](agent-email/README.md).
Änderungshistorie siehe [agent-email/CHANGELOG.md](agent-email/CHANGELOG.md),
Architektur-/Entwicklungshinweise siehe [agent-email/CLAUDE.md](agent-email/CLAUDE.md).
