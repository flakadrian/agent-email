"""IMAP-Anbindung für den E-Mail-Agenten.

Bietet drei Bausteine:
- connect(): stellt eine Verbindung her und meldet sich an
- test_connection(): prüft, ob Zugangsdaten und Ordner passen
- poll_new_messages(): einfacher Fallback, fragt in Intervallen nach neuen Mails
- idle_listen(): reagiert nahezu sofort auf neue Mails (IMAP IDLE)

Die eigentliche Kategorisierung/Ablage ist bewusst NICHT hier drin - dieses
Modul kümmert sich nur um den IMAP-Zugriff. Die Verarbeitung einzelner
Nachrichten kommt als nächster Baustein (Klassifizierung über Claude API).
"""

import logging
import time
from collections.abc import Callable
from pathlib import Path

from imapclient import IMAPClient

from config import ImapConfig, load_config

logger = logging.getLogger(__name__)

# Wird für jede neu erkannte Nachricht aufgerufen, bekommt die UID übergeben.
MessageCallback = Callable[[IMAPClient, int], None]

# Wird bei jedem Schleifendurchlauf von poll_new_messages/idle_listen berührt.
# Grundlage für den HEALTHCHECK im Dockerfile - erkennt einen hängenden
# Prozess (läuft noch, reagiert aber nicht mehr), nicht nur einen Absturz
# (den erkennt bereits Dockers "restart: unless-stopped" von selbst).
HEARTBEAT_PATH = Path("/tmp/agent-email-heartbeat")


def _touch_heartbeat() -> None:
    try:
        HEARTBEAT_PATH.touch()
    except OSError as exc:
        logger.warning(f"Heartbeat-Datei '{HEARTBEAT_PATH}' konnte nicht geschrieben werden: {exc}")


def connect(config: ImapConfig) -> IMAPClient:
    client = IMAPClient(config.host, port=config.port, ssl=config.use_ssl)
    client.login(config.user, config.password)
    client.select_folder(config.folder)
    return client


def test_connection() -> bool:
    """Prüft Verbindung, Login und Ordnerzugriff. Gibt True/False zurück."""
    config = load_config()
    try:
        client = connect(config)
    except Exception as exc:
        logger.error(f"Verbindung fehlgeschlagen: {exc}")
        return False

    try:
        folders = client.list_folders()
        message_count = client.folder_status(config.folder, ["MESSAGES"])[b"MESSAGES"]
        logger.info(f"Verbindung erfolgreich zu {config.host} als {config.user}")
        logger.info(f"Ordner '{config.folder}' enthält {message_count} Nachrichten")
        logger.info(f"Verfügbare Ordner: {[f[2] for f in folders]}")
        return True
    finally:
        client.logout()


def poll_new_messages(on_message: MessageCallback, interval_seconds: int = 30) -> None:
    """Fallback ohne IDLE-Unterstützung: fragt regelmäßig nach ungelesenen Mails."""
    config = load_config()
    client = connect(config)
    seen_uids: set[int] = set(client.search("ALL"))

    logger.info(f"Polling gestartet, prüfe alle {interval_seconds}s auf neue Mails...")
    _touch_heartbeat()
    try:
        while True:
            time.sleep(interval_seconds)
            _touch_heartbeat()
            current_uids = set(client.search("ALL"))
            new_uids = current_uids - seen_uids
            for uid in sorted(new_uids):
                on_message(client, uid)
            seen_uids = current_uids
    finally:
        client.logout()


def idle_listen(on_message: MessageCallback, idle_timeout_seconds: int = 60) -> None:
    """Wartet per IMAP IDLE auf neue Mails. Bevorzugter Modus, sofern der
    Anbieter IDLE unterstützt (die meisten aktuellen IMAP-Server tun das)."""
    config = load_config()
    client = connect(config)
    known_uids: set[int] = set(client.search("ALL"))

    logger.info("IDLE-Modus gestartet, warte auf neue Mails...")
    _touch_heartbeat()
    try:
        while True:
            client.idle()
            try:
                client.idle_check(timeout=idle_timeout_seconds)
            finally:
                client.idle_done()
            _touch_heartbeat()

            current_uids = set(client.search("ALL"))
            new_uids = current_uids - known_uids
            for uid in sorted(new_uids):
                on_message(client, uid)
            known_uids = current_uids
    finally:
        client.logout()
