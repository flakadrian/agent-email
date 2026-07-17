"""Ablage klassifizierter Mail-Anhänge in Google Drive.

Pfadschema (siehe CLAUDE.md-Anhang):
    /Email-Ablage/<Kategorie>/<Datum>_<Betreff>_<Original-Dateiname>

Der OAuth-Consent (run_auth_flow) ist ein einmaliger, ausschließlich vom
Nutzer selbst auszuführender Schritt (siehe main.py "drive-auth"-Befehl) -
get_service() liest nur den bereits erteilten, gespeicherten Token.
"""

import os
import re
from email.utils import parsedate_to_datetime
from datetime import date

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from message_loader import LoadedMessage

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"
ROOT_FOLDER_NAME = "Email-Ablage"

_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


def run_auth_flow() -> None:
    """Einmaliger interaktiver OAuth-Consent-Flow. Speichert token.json."""
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())


def get_service():
    """Baut den Drive-Service aus dem gespeicherten Token auf (kein Login-Flow)."""
    if not os.path.exists(TOKEN_PATH):
        raise RuntimeError(
            "Kein Google-Drive-Token gefunden. Bitte einmalig "
            "'python main.py drive-auth' ausführen."
        )

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def _escape_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _find_or_create_folder(service, name: str, parent_id: str | None = None) -> str:
    query = f"name = '{_escape_query_value(name)}' and mimeType = '{_FOLDER_MIME_TYPE}' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    existing = results.get("files", [])
    if existing:
        return existing[0]["id"]

    metadata = {"name": name, "mimeType": _FOLDER_MIME_TYPE}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def _sanitize_filename(text: str) -> str:
    sanitized = re.sub(r'[\\/:*?"<>|]', "_", text).strip()
    return sanitized[:80] or "ohne-betreff"


def _message_date(message: LoadedMessage) -> str:
    try:
        return parsedate_to_datetime(message.date).date().isoformat()
    except (TypeError, ValueError):
        return date.today().isoformat()


def upload_attachments(service, message: LoadedMessage, category: str) -> list[str]:
    """Lädt alle Anhänge einer Mail in den passenden Kategorie-Ordner hoch.

    Gibt die Drive-File-IDs der hochgeladenen Dateien zurück. Mails ohne
    Anhang werden bewusst nicht abgelegt (siehe CLAUDE.md-Anhang).
    """
    if not message.attachments:
        return []

    root_id = _find_or_create_folder(service, ROOT_FOLDER_NAME)
    category_folder_name = category.replace("/", "-")
    category_id = _find_or_create_folder(service, category_folder_name, root_id)

    date_prefix = _message_date(message)
    subject_slug = _sanitize_filename(message.subject)

    uploaded_ids = []
    for attachment in message.attachments:
        filename = f"{date_prefix}_{subject_slug}_{attachment.filename}"
        media = MediaInMemoryUpload(attachment.content, mimetype=attachment.content_type)
        file_metadata = {"name": filename, "parents": [category_id]}
        uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        uploaded_ids.append(uploaded["id"])

    return uploaded_ids
