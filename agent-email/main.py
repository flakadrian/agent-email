"""Einstiegspunkt für den E-Mail-Agenten.

Lädt neue Mails, klassifiziert sie über die Claude API und legt Anhänge
strukturiert in Google Drive ab (siehe README).
"""

import sys
from functools import partial

from classifier import classify
from config import AnthropicConfig, load_anthropic_config
from drive_client import upload_attachments
from imap_client import test_connection
from message_loader import load_message

COMMANDS = {"test", "listen", "poll", "drive-auth"}

# Mail-Betreffzeilen können Emojis/Sonderzeichen enthalten, die die
# Windows-Konsole standardmäßig nicht darstellen kann (UnicodeEncodeError).
# UTF-8 mit Ersatzzeichen statt Absturz.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def handle_message(anthropic_config: AnthropicConfig, drive_service, client, uid: int) -> None:
    message = load_message(client, uid)
    category = classify(message, anthropic_config)
    print(f"UID {uid}: '{message.subject}' -> Kategorie: {category}")

    if message.attachments:
        uploaded_ids = upload_attachments(drive_service, message, category)
        print(f"  {len(uploaded_ids)} Anhang/Anhänge in Drive abgelegt ({category.replace('/', '-')})")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Verwendung:")
        print("  python main.py test        - Verbindung einmalig prüfen")
        print("  python main.py drive-auth  - Google-Drive-Zugriff einmalig autorisieren")
        print("  python main.py listen      - auf neue Mails warten (IMAP IDLE)")
        print("  python main.py poll        - auf neue Mails prüfen (Polling-Fallback)")
        sys.exit(1)

    command = sys.argv[1]

    if command == "test":
        success = test_connection()
        sys.exit(0 if success else 1)

    if command == "drive-auth":
        from drive_client import run_auth_flow
        run_auth_flow()
        print("Google-Drive-Autorisierung abgeschlossen, token.json gespeichert.")

    if command == "listen":
        from drive_client import get_service
        from imap_client import idle_listen
        idle_listen(partial(handle_message, load_anthropic_config(), get_service()))

    if command == "poll":
        from drive_client import get_service
        from imap_client import poll_new_messages
        poll_new_messages(partial(handle_message, load_anthropic_config(), get_service()))


if __name__ == "__main__":
    main()
