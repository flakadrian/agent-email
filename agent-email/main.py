"""Einstiegspunkt für den E-Mail-Agenten.

Lädt neue Mails, klassifiziert sie über die Claude API und legt Anhänge
strukturiert in Google Drive oder OneDrive ab (siehe README).
"""

import sys
from functools import partial

import drive_client
import onedrive_client
from classifier import classify
from config import AnthropicConfig, STORAGE_PROVIDERS, load_anthropic_config, load_storage_provider
from imap_client import test_connection
from message_loader import load_message

COMMANDS = {"test", "listen", "poll", "storage-auth"}

STORAGE_PROVIDER_MODULES = {
    "google_drive": drive_client,
    "onedrive": onedrive_client,
}

STORAGE_PROVIDER_LABELS = {
    "google_drive": "Google Drive",
    "onedrive": "OneDrive",
}

# Validate that all configured providers have corresponding modules
_missing_modules = set(STORAGE_PROVIDERS) - set(STORAGE_PROVIDER_MODULES.keys())
if _missing_modules:
    raise RuntimeError(
        f"Storage provider(s) {_missing_modules} configured in config.py "
        f"but missing module implementation in main.py"
    )

# Mail-Betreffzeilen können Emojis/Sonderzeichen enthalten, die die
# Windows-Konsole standardmäßig nicht darstellen kann (UnicodeEncodeError).
# UTF-8 mit Ersatzzeichen statt Absturz.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def handle_message(
    anthropic_config: AnthropicConfig,
    storage_module,
    storage_label: str,
    storage_service,
    client,
    uid: int,
) -> None:
    message = load_message(client, uid)
    category = classify(message, anthropic_config)
    print(f"UID {uid}: '{message.subject}' -> Kategorie: {category}")

    if message.attachments:
        uploaded_ids = storage_module.upload_attachments(storage_service, message, category)
        print(f"  {len(uploaded_ids)} Anhang/Anhänge in {storage_label} abgelegt ({category.replace('/', '-')})")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Verwendung:")
        print("  python main.py test         - Verbindung einmalig prüfen")
        print("  python main.py storage-auth - Cloud-Speicher-Zugriff einmalig autorisieren")
        print("  python main.py listen       - auf neue Mails warten (IMAP IDLE)")
        print("  python main.py poll         - auf neue Mails prüfen (Polling-Fallback)")
        sys.exit(1)

    command = sys.argv[1]

    if command == "test":
        success = test_connection()
        sys.exit(0 if success else 1)

    storage_provider = load_storage_provider()
    storage_module = STORAGE_PROVIDER_MODULES[storage_provider]
    storage_label = STORAGE_PROVIDER_LABELS[storage_provider]

    if command == "storage-auth":
        storage_module.run_auth_flow()
        print(f"{storage_label}-Autorisierung abgeschlossen.")

    if command == "listen":
        from imap_client import idle_listen
        idle_listen(
            partial(
                handle_message,
                load_anthropic_config(),
                storage_module,
                storage_label,
                storage_module.get_service(),
            )
        )

    if command == "poll":
        from imap_client import poll_new_messages
        poll_new_messages(
            partial(
                handle_message,
                load_anthropic_config(),
                storage_module,
                storage_label,
                storage_module.get_service(),
            )
        )


if __name__ == "__main__":
    main()
