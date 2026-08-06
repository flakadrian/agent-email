"""Einstiegspunkt für den E-Mail-Agenten.

Lädt neue Mails, klassifiziert sie (Claude API oder lokales Ollama-Modell,
per CLASSIFIER_PROVIDER) und legt Anhänge strukturiert ab (Google Drive,
OneDrive oder lokaler Pfad, per STORAGE_PROVIDER) - siehe README.
"""

import logging
import sys
from functools import partial

import classifier
import drive_client
import local_classifier
import local_storage
import onedrive_client
from config import (
    CLASSIFIER_PROVIDERS,
    STORAGE_PROVIDERS,
    load_anthropic_config,
    load_classifier_provider,
    load_local_model_config,
    load_storage_provider,
)
from imap_client import test_connection
from message_loader import load_message

COMMANDS = {"test", "listen", "poll", "storage-auth"}

STORAGE_PROVIDER_MODULES = {
    "google_drive": drive_client,
    "onedrive": onedrive_client,
    "local": local_storage,
}

STORAGE_PROVIDER_LABELS = {
    "google_drive": "Google Drive",
    "onedrive": "OneDrive",
    "local": "lokalem Pfad",
}

CLASSIFIER_PROVIDER_MODULES = {
    "anthropic": classifier,
    "local": local_classifier,
}

CLASSIFIER_CONFIG_LOADERS = {
    "anthropic": load_anthropic_config,
    "local": load_local_model_config,
}

_missing_modules = STORAGE_PROVIDERS - STORAGE_PROVIDER_MODULES.keys()
if _missing_modules:
    raise RuntimeError(
        f"Storage-Provider {sorted(_missing_modules)} sind in config.py als "
        f"gültig gelistet, aber main.py fehlt die zugehörige Modul-Implementierung."
    )

_missing_classifier_modules = CLASSIFIER_PROVIDERS - CLASSIFIER_PROVIDER_MODULES.keys()
if _missing_classifier_modules:
    raise RuntimeError(
        f"Classifier-Provider {sorted(_missing_classifier_modules)} sind in config.py "
        f"als gültig gelistet, aber main.py fehlt die zugehörige Modul-Implementierung."
    )

# Mail-Betreffzeilen können Emojis/Sonderzeichen enthalten, die die
# Windows-Konsole standardmäßig nicht darstellen kann (UnicodeEncodeError).
# UTF-8 mit Ersatzzeichen statt Absturz.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Auf stdout statt dem Logging-Standard stderr, damit Container Manager/
# Docker-Log-Viewer weiterhin alles im selben Protokoll-Stream zeigen wie
# bisher mit print().
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def handle_message(
    classifier_module,
    classifier_config,
    storage_module,
    storage_label: str,
    storage_service,
    client,
    uid: int,
) -> None:
    message = load_message(client, uid)
    category = classifier_module.classify(message, classifier_config)
    logger.info(f"UID {uid}: '{message.subject}' -> Kategorie: {category}")

    if message.attachments:
        uploaded_ids = storage_module.upload_attachments(storage_service, message, category)
        logger.info(
            f"{len(uploaded_ids)} Anhang/Anhänge in {storage_label} abgelegt "
            f"({category.replace('/', '-')}): {uploaded_ids}"
        )


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
        logger.info(f"{storage_label}-Autorisierung abgeschlossen.")

    if command in ("listen", "poll"):
        classifier_provider = load_classifier_provider()
        classifier_module = CLASSIFIER_PROVIDER_MODULES[classifier_provider]
        classifier_config = CLASSIFIER_CONFIG_LOADERS[classifier_provider]()

        storage_service = storage_module.get_service()
        logger.info(f"Speicherziel ({storage_label}): {storage_service}")

        handler = partial(
            handle_message,
            classifier_module,
            classifier_config,
            storage_module,
            storage_label,
            storage_service,
        )

        if command == "listen":
            from imap_client import idle_listen
            idle_listen(handler)

        if command == "poll":
            from imap_client import poll_new_messages
            poll_new_messages(handler)


if __name__ == "__main__":
    main()
