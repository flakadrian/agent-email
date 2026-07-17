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

import time
from collections.abc import Callable

from imapclient import IMAPClient

from config import ImapConfig, load_config

# Wird für jede neu erkannte Nachricht aufgerufen, bekommt die UID übergeben.
MessageCallback = Callable[[IMAPClient, int], None]


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
        print(f"Verbindung fehlgeschlagen: {exc}")
        return False

    try:
        folders = client.list_folders()
        message_count = client.folder_status(config.folder, ["MESSAGES"])[b"MESSAGES"]
        print(f"Verbindung erfolgreich zu {config.host} als {config.user}")
        print(f"Ordner '{config.folder}' enthält {message_count} Nachrichten")
        print(f"Verfügbare Ordner: {[f[2] for f in folders]}")
        return True
    finally:
        client.logout()


def poll_new_messages(on_message: MessageCallback, interval_seconds: int = 30) -> None:
    """Fallback ohne IDLE-Unterstützung: fragt regelmäßig nach ungelesenen Mails."""
    config = load_config()
    client = connect(config)
    seen_uids: set[int] = set(client.search("ALL"))

    print(f"Polling gestartet, prüfe alle {interval_seconds}s auf neue Mails...")
    try:
        while True:
            time.sleep(interval_seconds)
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

    print("IDLE-Modus gestartet, warte auf neue Mails...")
    try:
        while True:
            client.idle()
            try:
                client.idle_check(timeout=idle_timeout_seconds)
            finally:
                client.idle_done()

            current_uids = set(client.search("ALL"))
            new_uids = current_uids - known_uids
            for uid in sorted(new_uids):
                on_message(client, uid)
            known_uids = current_uids
    finally:
        client.logout()
