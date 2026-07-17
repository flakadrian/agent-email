"""Lädt Nachrichteninhalt und Anhänge einer Mail per UID aus dem IMAP-Postfach.

Baut auf der bestehenden IMAP-Verbindung auf (siehe imap_client.py) und
liefert eine strukturierte Repräsentation für die Klassifizierung
(siehe classifier.py). Die Ablage der Anhangsbytes in Google Drive kommt
als nächster Baustein.
"""

import re
from dataclasses import dataclass, field
from email import message_from_bytes
from email.header import decode_header
from email.message import Message as EmailMessage

from imapclient import IMAPClient


@dataclass
class Attachment:
    filename: str
    content_type: str
    content: bytes


@dataclass
class LoadedMessage:
    uid: int
    subject: str
    sender: str
    date: str
    body_text: str
    attachments: list[Attachment] = field(default_factory=list)


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _decode_header_value(value: str) -> str:
    parts = decode_header(value)
    decoded = (
        part.decode(charset or "utf-8", errors="replace") if isinstance(part, bytes) else part
        for part, charset in parts
    )
    return "".join(decoded)


def load_message(client: IMAPClient, uid: int) -> LoadedMessage:
    raw = client.fetch([uid], ["RFC822"])[uid][b"RFC822"]
    email_message: EmailMessage = message_from_bytes(raw)

    body_text = ""
    html_fallback = ""
    attachments: list[Attachment] = []

    for part in email_message.walk():
        if part.is_multipart():
            continue

        content_type = part.get_content_type()
        is_attachment = part.get_content_disposition() == "attachment"

        if is_attachment:
            attachments.append(
                Attachment(
                    filename=part.get_filename() or "unbenannt",
                    content_type=content_type,
                    content=part.get_payload(decode=True) or b"",
                )
            )
            continue

        if content_type == "text/plain" and not body_text:
            charset = part.get_content_charset() or "utf-8"
            payload = part.get_payload(decode=True) or b""
            body_text = payload.decode(charset, errors="replace")
        elif content_type == "text/html" and not html_fallback:
            charset = part.get_content_charset() or "utf-8"
            payload = part.get_payload(decode=True) or b""
            html_fallback = payload.decode(charset, errors="replace")

    return LoadedMessage(
        uid=uid,
        subject=_decode_header_value(email_message.get("Subject", "")),
        sender=_decode_header_value(email_message.get("From", "")),
        date=email_message.get("Date", ""),
        body_text=(body_text or _strip_html(html_fallback)).strip(),
        attachments=attachments,
    )
