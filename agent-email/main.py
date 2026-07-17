"""Einstiegspunkt für den E-Mail-Agenten.

Aktuell nur der Verbindungstest - Klassifizierung und Ablage in Google Drive
kommen als nächste Ausbaustufe dazu (siehe README).
"""

import sys

from imap_client import test_connection


def print_message(_client, uid: int) -> None:
    print(f"Neue Nachricht erkannt, UID {uid} (Verarbeitung folgt in nächster Ausbaustufe)")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"test", "listen", "poll"}:
        print("Verwendung:")
        print("  python main.py test    - Verbindung einmalig prüfen")
        print("  python main.py listen  - auf neue Mails warten (IMAP IDLE)")
        print("  python main.py poll    - auf neue Mails prüfen (Polling-Fallback)")
        sys.exit(1)

    command = sys.argv[1]

    if command == "test":
        success = test_connection()
        sys.exit(0 if success else 1)

    if command == "listen":
        from imap_client import idle_listen
        idle_listen(print_message)

    if command == "poll":
        from imap_client import poll_new_messages
        poll_new_messages(print_message)


if __name__ == "__main__":
    main()
