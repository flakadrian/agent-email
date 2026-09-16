"""Klassifiziert E-Mails über ein lokales Ollama-Modell statt der Claude API.

Nutzt dieselbe Kategorienliste und denselben Prompt wie classifier.py, damit
sich das Verhalten zwischen CLASSIFIER_PROVIDER=anthropic/local nur in der
Modell-Anbindung unterscheidet.
"""

import json
import logging

import requests

from classifier import _SYSTEM_PROMPT, CATEGORIES, FALLBACK_CATEGORY, _build_prompt
from config import LocalModelConfig
from message_loader import LoadedMessage

logger = logging.getLogger(__name__)

_RESPONSE_FORMAT = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
    },
    "required": ["category"],
}

# Kleinere Obergrenze als bei der Claude API (siehe classifier.DEFAULT_BODY_LIMIT):
# Auf schwacher NAS-Hardware wurden in der Praxis nur ~4,5 Tokens/s Prompt-
# Verarbeitung gemessen. Bei einem festen Overhead (System-Prompt + Kategorien
# + JSON-Schema) von grob 300-450 Tokens bleiben so bei einem 240s-Timeout
# noch ausreichend Tokens für den Mailtext übrig, ohne das Timeout zu
# riskieren. Betreff, Absender und Anhang-Dateinamen werden davon NICHT
# beschnitten (immer vollständig im Prompt), nur der Mailtext selbst.
_LOCAL_BODY_LIMIT = 1500


def classify(message: LoadedMessage, config: LocalModelConfig) -> str:
    try:
        response = requests.post(
            f"{config.host}/api/chat",
            json={
                "model": config.model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_prompt(message, body_limit=_LOCAL_BODY_LIMIT)},
                ],
                "format": _RESPONSE_FORMAT,
                "stream": False,
            },
            timeout=240,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        category = json.loads(content).get("category")
    except Exception as exc:
        logger.warning(f"Klassifizierung fehlgeschlagen, verwende Fallback '{FALLBACK_CATEGORY}': {exc}")
        return FALLBACK_CATEGORY

    return category if category in CATEGORIES else FALLBACK_CATEGORY
