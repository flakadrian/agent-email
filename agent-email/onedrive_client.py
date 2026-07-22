"""Ablage klassifizierter Mail-Anhänge in Microsoft OneDrive (Microsoft Graph API).

Pfadschema (siehe CLAUDE.md-Anhang), identisch zu drive_client.py:
    Email-Ablage/<Kategorie>/<Datum>_<Betreff>_<Original-Dateiname>

Der OAuth-Consent (run_auth_flow) ist ein einmaliger, ausschließlich vom
Nutzer selbst auszuführender Schritt (siehe main.py "storage-auth"-Befehl) -
get_service() liest nur den bereits erteilten, gespeicherten Token-Cache.

Vereinfachung gegenüber Google Drive: Microsoft Graph erlaubt Pfad-
Adressierung beim Upload und legt fehlende Zwischenordner automatisch an,
ein manuelles "find-or-create-folder" ist daher nicht nötig.
"""

import os
import urllib.parse

import msal
import requests

from config import OneDriveConfig, load_onedrive_config
from file_naming import message_date, sanitize_filename
from message_loader import LoadedMessage

SCOPES = ["Files.ReadWrite"]
TOKEN_CACHE_PATH = "onedrive_token_cache.json"
ROOT_FOLDER_NAME = "Email-Ablage"
GRAPH_ROOT = "https://graph.microsoft.com/v1.0"


def _authority(config: OneDriveConfig) -> str:
    return f"https://login.microsoftonline.com/{config.tenant}"


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_PATH):
        with open(TOKEN_CACHE_PATH, "r") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        with open(TOKEN_CACHE_PATH, "w") as f:
            f.write(cache.serialize())


def run_auth_flow() -> None:
    """Einmaliger interaktiver OAuth-Consent-Flow. Speichert onedrive_token_cache.json."""
    config = load_onedrive_config()
    cache = msal.SerializableTokenCache()
    app = msal.PublicClientApplication(
        client_id=config.client_id, authority=_authority(config), token_cache=cache
    )
    result = app.acquire_token_interactive(scopes=SCOPES)
    if "access_token" not in result:
        raise RuntimeError(
            f"OneDrive-Autorisierung fehlgeschlagen: {result.get('error_description', result)}"
        )
    _save_cache(cache)


def get_service() -> str:
    """Liefert ein gültiges Access-Token aus dem gespeicherten Cache (kein Login-Flow)."""
    if not os.path.exists(TOKEN_CACHE_PATH):
        raise RuntimeError(
            "Kein OneDrive-Token gefunden. Bitte einmalig "
            "'python main.py storage-auth' ausführen."
        )

    config = load_onedrive_config()
    cache = _load_cache()
    app = msal.PublicClientApplication(
        client_id=config.client_id, authority=_authority(config), token_cache=cache
    )

    accounts = app.get_accounts()
    if not accounts:
        raise RuntimeError(
            "Kein OneDrive-Konto im Token-Cache gefunden. Bitte "
            "'python main.py storage-auth' erneut ausführen."
        )

    result = app.acquire_token_silent(SCOPES, account=accounts[0])
    _save_cache(cache)

    if not result or "access_token" not in result:
        raise RuntimeError(
            "OneDrive-Token abgelaufen oder ungültig. Bitte "
            "'python main.py storage-auth' erneut ausführen."
        )

    return result["access_token"]


def upload_attachments(access_token: str, message: LoadedMessage, category: str) -> list[str]:
    """Lädt alle Anhänge einer Mail in den passenden Kategorie-Ordner in OneDrive hoch.

    Gibt die OneDrive-Item-IDs der hochgeladenen Dateien zurück. Mails ohne
    Anhang werden bewusst nicht abgelegt (siehe CLAUDE.md-Anhang).
    """
    if not message.attachments:
        return []

    category_folder_name = category.replace("/", "-")
    date_prefix = message_date(message)
    subject_slug = sanitize_filename(message.subject)

    uploaded_ids = []
    for attachment in message.attachments:
        filename = f"{date_prefix}_{subject_slug}_{attachment.filename}"
        path = f"{ROOT_FOLDER_NAME}/{category_folder_name}/{filename}"
        url = f"{GRAPH_ROOT}/me/drive/root:/{urllib.parse.quote(path)}:/content"

        response = requests.put(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": attachment.content_type,
            },
            data=attachment.content,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"OneDrive-Upload fehlgeschlagen für '{attachment.filename}' "
                f"(Kategorie: {category}): {response.text}"
            ) from exc

        try:
            uploaded_ids.append(response.json()["id"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"Ungültige Antwort von Microsoft Graph für '{attachment.filename}': "
                f"{response.text}"
            ) from exc

    return uploaded_ids
