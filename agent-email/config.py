"""Lädt die Konfiguration (IMAP, Klassifizierung, Ablage) aus der .env-Datei und validiert sie."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class ImapConfig:
    host: str
    port: int
    user: str
    password: str
    use_ssl: bool
    folder: str


@dataclass
class AnthropicConfig:
    api_key: str
    model: str


@dataclass
class OneDriveConfig:
    client_id: str
    tenant: str


@dataclass
class LocalModelConfig:
    host: str
    model: str


@dataclass
class LocalStorageConfig:
    path: str


STORAGE_PROVIDERS = {"google_drive", "onedrive", "local"}
CLASSIFIER_PROVIDERS = {"anthropic", "local"}


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Umgebungsvariable {name} fehlt. Hast du .env.example nach .env "
            f"kopiert und die Werte eingetragen?"
        )
    return value


def load_config() -> ImapConfig:
    return ImapConfig(
        host=_require("IMAP_HOST"),
        port=int(os.getenv("IMAP_PORT", "993")),
        user=_require("IMAP_USER"),
        password=_require("IMAP_PASSWORD"),
        use_ssl=os.getenv("IMAP_USE_SSL", "true").lower() == "true",
        folder=os.getenv("IMAP_FOLDER", "INBOX"),
    )


def load_anthropic_config() -> AnthropicConfig:
    return AnthropicConfig(
        api_key=_require("ANTHROPIC_API_KEY"),
        model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
    )


def load_onedrive_config() -> OneDriveConfig:
    return OneDriveConfig(
        client_id=_require("ONEDRIVE_CLIENT_ID"),
        tenant=os.getenv("ONEDRIVE_TENANT", "common"),
    )


def load_storage_provider() -> str:
    provider = os.getenv("STORAGE_PROVIDER", "google_drive").strip().lower()
    if provider not in STORAGE_PROVIDERS:
        raise RuntimeError(
            f"Unbekannter STORAGE_PROVIDER '{provider}'. Erlaubt: "
            f"{', '.join(sorted(STORAGE_PROVIDERS))}."
        )
    return provider


def load_classifier_provider() -> str:
    provider = os.getenv("CLASSIFIER_PROVIDER", "anthropic").strip().lower()
    if provider not in CLASSIFIER_PROVIDERS:
        raise RuntimeError(
            f"Unbekannter CLASSIFIER_PROVIDER '{provider}'. Erlaubt: "
            f"{', '.join(sorted(CLASSIFIER_PROVIDERS))}."
        )
    return provider


def load_local_model_config() -> LocalModelConfig:
    return LocalModelConfig(
        host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        model=_require("OLLAMA_MODEL"),
    )


def load_local_storage_config() -> LocalStorageConfig:
    return LocalStorageConfig(path=_require("LOCAL_STORAGE_PATH"))
