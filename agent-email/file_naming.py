"""Gemeinsame Dateinamens-Hilfsfunktionen für die Cloud-Ablage (Google Drive, OneDrive).

Pfadschema (siehe CLAUDE.md-Anhang):
    Email-Ablage/<Kategorie>/<Datum>_<Betreff>_<Original-Dateiname>
"""

import re
from datetime import date
from email.utils import parsedate_to_datetime

from message_loader import LoadedMessage


def sanitize_filename(text: str) -> str:
    sanitized = re.sub(r'[\\/:*?"<>|]', "_", text).strip()
    return sanitized[:80] or "ohne-betreff"


def message_date(message: LoadedMessage) -> str:
    try:
        return parsedate_to_datetime(message.date).date().isoformat()
    except (TypeError, ValueError):
        return date.today().isoformat()
