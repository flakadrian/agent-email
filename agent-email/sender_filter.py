"""Erkennt automatisierte Absender (Entwickler-/Service-Benachrichtigungen),
die inhaltlich zu keiner der festen Kategorien passen.

Kleine lokale Modelle (z.B. qwen2.5:0.5b) klassifizieren solche Mails in der
Praxis unzuverlässig, statt wie im Prompt vorgegeben auf "Sonstiges"
auszuweichen (siehe CHANGELOG). Bekannte automatisierte Absender werden
daher schon vor dem KI-Aufruf erkannt und direkt auf Sonstiges geroutet -
spart nebenbei auch unnötige Klassifizierungs-Aufrufe.

Liste bei Bedarf um weitere bekannte automatisierte Absender ergänzen.
"""

import re

AUTOMATED_SENDER_PATTERNS = [
    r"notifications@github\.com",
    r"noreply@github\.com",
]

_COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in AUTOMATED_SENDER_PATTERNS]


def is_automated_sender(sender: str) -> bool:
    return any(pattern.search(sender) for pattern in _COMPILED_PATTERNS)
