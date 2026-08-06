# Persönlicher Assistent – Multi-Agent-Orchestrierung

Ein Orchestrator verteilt Anfragen/Ereignisse an spezialisierte Einzel-Agenten.
Jeder Agent ist eigenständig, hat eigene Werkzeuge/Rechte und eigenen Kontext.

## Status

- ✅ Phase 0 abgeschlossen (Use Case, Tech-Stack, Interface-Vertrag definiert)
- ✅ Erster Agent fertig: [`agent-email/`](agent-email/) – IMAP-Anbindung,
  Klassifizierung (Claude API oder lokal via Ollama) und Ablage der Anhänge
  (Google Drive, OneDrive oder lokaler Pfad)
- ⏳ Orchestrator selbst existiert noch nicht (Phase 1)

## Agenten

| Agent | Beschreibung | Doku |
|---|---|---|
| `agent-email` | Überwacht ein IMAP-Postfach, klassifiziert eingehende Mails und legt Anhänge strukturiert ab | [agent-email/README.md](agent-email/README.md) |

## Setup

Jeder Agent hat sein eigenes Setup, siehe die jeweilige README im Unterordner.
Für `agent-email`: [agent-email/README.md](agent-email/README.md#1-setup)

## Architektur

Details zum Gesamtkonzept und den Entscheidungen siehe [agent-email/CLAUDE.md](agent-email/CLAUDE.md).
