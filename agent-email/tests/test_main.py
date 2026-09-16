from unittest.mock import MagicMock, patch

from main import handle_message
from message_loader import Attachment, LoadedMessage


def _message(**overrides) -> LoadedMessage:
    defaults = dict(
        uid=1,
        subject="Stromrechnung Juli",
        sender="stadtwerke@beispiel.de",
        date="Fri, 17 Jul 2026 10:00:00 +0000",
        body_text="Anbei deine Rechnung.",
        attachments=[],
    )
    defaults.update(overrides)
    return LoadedMessage(**defaults)


@patch("main.load_message")
def test_handle_message_classifies_and_uploads_attachments(mock_load_message, caplog):
    message = _message(
        attachments=[Attachment(filename="rechnung.pdf", content_type="application/pdf", content=b"...")]
    )
    mock_load_message.return_value = message

    classifier_module = MagicMock()
    classifier_module.classify.return_value = "Rechnungen/Zahlungen"
    storage_module = MagicMock()
    storage_module.upload_attachments.return_value = ["/data/Email-Ablage/Rechnungen-Zahlungen/rechnung.pdf"]

    client = MagicMock()
    with caplog.at_level("INFO"):
        handle_message(
            classifier_module,
            "classifier-config",
            storage_module,
            "lokalem Pfad",
            "storage-service",
            client,
            42,
        )

    mock_load_message.assert_called_once_with(client, 42)
    classifier_module.classify.assert_called_once_with(message, "classifier-config")
    storage_module.upload_attachments.assert_called_once_with("storage-service", message, "Rechnungen/Zahlungen")

    assert "UID 42: 'Stromrechnung Juli' -> Kategorie: Rechnungen/Zahlungen" in caplog.text
    assert "1 Anhang/Anhänge in lokalem Pfad abgelegt (Rechnungen-Zahlungen):" in caplog.text
    assert "/data/Email-Ablage/Rechnungen-Zahlungen/rechnung.pdf" in caplog.text


@patch("main.load_message")
def test_handle_message_skips_upload_when_no_attachments(mock_load_message, caplog):
    message = _message(attachments=[])
    mock_load_message.return_value = message

    classifier_module = MagicMock()
    classifier_module.classify.return_value = "Newsletter"
    storage_module = MagicMock()

    with caplog.at_level("INFO"):
        handle_message(
            classifier_module,
            "classifier-config",
            storage_module,
            "lokalem Pfad",
            "storage-service",
            MagicMock(),
            7,
        )

    storage_module.upload_attachments.assert_not_called()
    assert "UID 7: 'Stromrechnung Juli' -> Kategorie: Newsletter" in caplog.text
    assert "abgelegt" not in caplog.text


@patch("main.load_message")
def test_handle_message_skips_classification_for_automated_sender(mock_load_message, caplog):
    message = _message(
        sender="GitHub <notifications@github.com>",
        subject="[flakadrian/agent-email] Neuer Commit",
        attachments=[],
    )
    mock_load_message.return_value = message

    classifier_module = MagicMock()
    storage_module = MagicMock()

    with caplog.at_level("INFO"):
        handle_message(
            classifier_module,
            "classifier-config",
            storage_module,
            "lokalem Pfad",
            "storage-service",
            MagicMock(),
            99,
        )

    classifier_module.classify.assert_not_called()
    assert "Kategorie: Sonstiges" in caplog.text
    assert "Klassifizierung übersprungen" in caplog.text
