"""Klassifiziert E-Mails über ein lokales Ollama-Modell statt der Claude API.

Nutzt dieselbe Kategorienliste und denselben Prompt wie classifier.py, damit
sich das Verhalten zwischen CLASSIFIER_PROVIDER=anthropic/local nur in der
Modell-Anbindung unterscheidet.
"""

import json

import requests

from classifier import CATEGORIES, FALLBACK_CATEGORY, _SYSTEM_PROMPT, _build_prompt
from config import LocalModelConfig
from message_loader import LoadedMessage

_RESPONSE_FORMAT = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
    },
    "required": ["category"],
}


def classify(message: LoadedMessage, config: LocalModelConfig) -> str:
    try:
        response = requests.post(
            f"{config.host}/api/chat",
            json={
                "model": config.model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_prompt(message)},
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
        print(f"Klassifizierung fehlgeschlagen, verwende Fallback '{FALLBACK_CATEGORY}': {exc}")
        return FALLBACK_CATEGORY

    return category if category in CATEGORIES else FALLBACK_CATEGORY
