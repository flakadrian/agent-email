"""Lädt die IMAP-Konfiguration aus der .env-Datei und validiert sie."""

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
