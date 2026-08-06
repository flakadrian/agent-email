"""Ablage klassifizierter Mail-Anhänge auf einem lokalen Dateisystempfad.

Pfadschema (siehe CLAUDE.md-Anhang), identisch zu drive_client.py/onedrive_client.py:
    <LOCAL_STORAGE_PATH>/Email-Ablage/<Kategorie>/<Datum>_<Betreff>_<Original-Dateiname>

Kein OAuth nötig; run_auth_flow() legt lediglich den konfigurierten Pfad an,
falls er noch nicht existiert.
"""

import logging
import os
from pathlib import Path

from config import load_local_storage_config
from file_naming import message_date, sanitize_filename
from message_loader import LoadedMessage

logger = logging.getLogger(__name__)

ROOT_FOLDER_NAME = "Email-Ablage"


def run_auth_flow() -> None:
    """Kein Login nötig; stellt nur sicher, dass der konfigurierte Pfad existiert."""
    get_service()


def get_service() -> Path:
    """Liefert den validierten, konfigurierten lokalen Basis-Pfad."""
    config = load_local_storage_config()
    root = Path(config.path)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Lokaler Ablagepfad '{config.path}' ist nicht beschreibbar: {exc}"
        ) from exc

    # Unterscheidet einen echten Bind-Mount (Schreibzugriffe landen auf dem
    # NAS-Host) von einem normalen Ordner innerhalb der Container-eigenen,
    # nicht persistenten Dateisystemebene (z.B. bei fehlerhaft konfiguriertem
    # Docker-Volume) - beides sieht für das Programm selbst identisch aus.
    logger.info(
        f"Basis-Pfad: {root} (ist Mountpoint: {os.path.ismount(root)}), "
        f"vorhandener Inhalt: {[p.name for p in root.iterdir()]}"
    )
    return root


def upload_attachments(root: Path, message: LoadedMessage, category: str) -> list[str]:
    """Speichert alle Anhänge einer Mail im passenden Kategorie-Ordner.

    Gibt die geschriebenen Dateipfade zurück. Mails ohne Anhang werden
    bewusst nicht abgelegt (siehe CLAUDE.md-Anhang).
    """
    if not message.attachments:
        return []

    category_folder_name = category.replace("/", "-")
    target_dir = root / ROOT_FOLDER_NAME / category_folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    date_prefix = message_date(message)
    subject_slug = sanitize_filename(message.subject)

    written_paths = []
    for attachment in message.attachments:
        filename = f"{date_prefix}_{subject_slug}_{attachment.filename}"
        file_path = target_dir / filename
        file_path.write_bytes(attachment.content)

        written_size = file_path.stat().st_size
        logger.info(f"geschrieben: {file_path} ({written_size} Bytes, erwartet {len(attachment.content)} Bytes)")
        written_paths.append(str(file_path))

    return written_paths
