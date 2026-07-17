from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock

from message_loader import load_message


def _build_raw_email(*, subject: str, body: str, attachment_name: str, attachment_bytes: bytes) -> bytes:
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = "absender@beispiel.de"
    message["Date"] = "Fri, 17 Jul 2026 10:00:00 +0000"
    message.attach(MIMEText(body, "plain", "utf-8"))

    attachment = MIMEApplication(attachment_bytes)
    attachment.add_header("Content-Disposition", "attachment", filename=attachment_name)
    message.attach(attachment)

    return message.as_bytes()


def _client_returning(uid: int, raw: bytes) -> MagicMock:
    client = MagicMock()
    client.fetch.return_value = {uid: {b"RFC822": raw}}
    return client


def test_load_message_extracts_subject_body_and_attachment():
    raw = _build_raw_email(
        subject="Stromrechnung Juli",
        body="Anbei deine Rechnung.",
        attachment_name="rechnung.pdf",
        attachment_bytes=b"%PDF-1.4 fake content",
    )
    client = _client_returning(42, raw)

    result = load_message(client, 42)

    assert result.uid == 42
    assert result.subject == "Stromrechnung Juli"
    assert result.sender == "absender@beispiel.de"
    assert "Anbei deine Rechnung." in result.body_text
    assert len(result.attachments) == 1
    assert result.attachments[0].filename == "rechnung.pdf"
    assert result.attachments[0].content == b"%PDF-1.4 fake content"
    client.fetch.assert_called_once_with([42], ["RFC822"])


def test_load_message_falls_back_to_html_when_no_plain_text():
    message = MIMEMultipart()
    message["Subject"] = "Newsletter"
    message["From"] = "newsletter@beispiel.de"
    message["Date"] = "Fri, 17 Jul 2026 10:00:00 +0000"
    message.attach(MIMEText("<p>Hallo <b>Welt</b></p>", "html", "utf-8"))
    client = _client_returning(7, message.as_bytes())

    result = load_message(client, 7)

    assert "Hallo" in result.body_text
    assert "Welt" in result.body_text
    assert "<p>" not in result.body_text
    assert result.attachments == []


def test_load_message_decodes_encoded_subject():
    message = MIMEMultipart()
    message["Subject"] = Header("Termin mörgen", "utf-8").encode()
    message["From"] = "kalender@beispiel.de"
    message["Date"] = "Fri, 17 Jul 2026 10:00:00 +0000"
    message.attach(MIMEText("Text", "plain", "utf-8"))
    client = _client_returning(3, message.as_bytes())

    result = load_message(client, 3)

    assert result.subject == "Termin mörgen"
