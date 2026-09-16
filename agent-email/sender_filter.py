r"""Erkennt automatisierte Absender (Entwickler-/Service-Benachrichtigungen),
die inhaltlich zu keiner der festen Kategorien passen.

Kleine lokale Modelle (z.B. qwen2.5:0.5b) klassifizieren solche Mails in der
Praxis unzuverlässig, statt wie im Prompt vorgegeben auf "Sonstiges"
auszuweichen (siehe CHANGELOG). Bekannte automatisierte Absender werden
daher schon vor dem KI-Aufruf erkannt und direkt auf Sonstiges geroutet -
spart nebenbei auch unnötige Klassifizierungs-Aufrufe.

Liste bei Bedarf um weitere bekannte automatisierte Absender ergänzen.

Konfiguration: Jede Zeile ist ein regulärer Ausdruck, der gegen die
Absenderadresse geprüft wird (Groß-/Kleinschreibung egal). Für eine
einfache Absenderadresse reicht "r" vor dem String plus Escaping des
Punkts mit "\.", z.B. für "no-reply@amazon.de":
    r"no-reply@amazon\.de"
(ohne den Backslash würde der Punkt "irgendein Zeichen" statt eines
wörtlichen Punkts bedeuten und das Muster unnötig weit fassen).

WICHTIG: Ein Treffer bedeutet immer "Sonstiges", ohne Ausnahme oder
Rückfrage. Nur Muster ergänzen, bei denen wirklich JEDE Mail dieses
Absenders in "Sonstiges" gehört - ein zu allgemeines Muster (z.B. nur
"amazon\.de" statt einer konkreten Absenderadresse) würde auch legitime
Mails erfassen, die eigentlich in eine andere Kategorie gehören.

Nach einer Änderung ist wie bei jeder Code-Änderung ein Neustart/Rebuild
nötig, damit sie wirksam wird (siehe README, Abschnitt "Updates einspielen").
"""

import re

AUTOMATED_SENDER_PATTERNS = [
    r"notifications@github\.com",
    r"noreply@github\.com",
]

_COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in AUTOMATED_SENDER_PATTERNS]


def is_automated_sender(sender: str) -> bool:
    return any(pattern.search(sender) for pattern in _COMPILED_PATTERNS)
