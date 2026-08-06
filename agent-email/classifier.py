"""Klassifiziert E-Mails über die Claude API anhand der festen Kategorienliste.

Die Kategorienliste ist bewusst fest vorgegeben (siehe CLAUDE.md-Anhang) und
wird per erzwungenem Tool-Call durchgesetzt, damit Claude niemals eine
Kategorie außerhalb der Liste zurückgibt.
"""

import logging

import anthropic

from config import AnthropicConfig
from message_loader import LoadedMessage

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Rechnungen/Zahlungen",
    "Verträge",
    "Bestellungen/Lieferungen",
    "Termine/Einladungen",
    "Newsletter",
    "Privat",
    "Sonstiges",
]

FALLBACK_CATEGORY = "Sonstiges"

_SYSTEM_PROMPT = """Du ordnest private E-Mails genau einer dieser Kategorien zu:

- Rechnungen/Zahlungen: Rechnungen, Zahlungsaufforderungen, Mahnungen, Kontoauszüge
- Verträge: Vertragsunterlagen, Kündigungsbestätigungen, Vertragsänderungen
- Bestellungen/Lieferungen: Bestellbestätigungen, Versand-/Lieferbenachrichtigungen, ohne eigentliche Zahlungsaufforderung
- Termine/Einladungen: Terminbestätigungen, Kalendereinladungen, Veranstaltungshinweise
- Newsletter: abonnierte Rundmails, Produktankündigungen, Marketing
- Privat: persönliche Nachrichten von Freunden/Familie
- Sonstiges: alles, was nicht eindeutig in eine der anderen Kategorien passt

Wähle im Zweifel Sonstiges statt zu raten."""

_CLASSIFY_TOOL = {
    "name": "classify_email",
    "description": "Ordnet eine E-Mail einer der festen Kategorien zu.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": CATEGORIES},
        },
        "required": ["category"],
    },
}


def _build_prompt(message: LoadedMessage) -> str:
    attachment_names = ", ".join(a.filename for a in message.attachments) or "keine"
    return (
        f"Betreff: {message.subject}\n"
        f"Absender: {message.sender}\n"
        f"Anhänge: {attachment_names}\n\n"
        f"Text:\n{message.body_text[:4000]}"
    )


def classify(message: LoadedMessage, config: AnthropicConfig) -> str:
    client = anthropic.Anthropic(api_key=config.api_key)

    try:
        response = client.messages.create(
            model=config.model,
            max_tokens=100,
            system=_SYSTEM_PROMPT,
            tools=[_CLASSIFY_TOOL],
            tool_choice={"type": "tool", "name": "classify_email"},
            messages=[{"role": "user", "content": _build_prompt(message)}],
        )
    except Exception as exc:
        logger.warning(f"Klassifizierung fehlgeschlagen, verwende Fallback '{FALLBACK_CATEGORY}': {exc}")
        return FALLBACK_CATEGORY

    for block in response.content:
        if block.type == "tool_use" and block.name == "classify_email":
            category = block.input.get("category")
            if category in CATEGORIES:
                return category

    return FALLBACK_CATEGORY
