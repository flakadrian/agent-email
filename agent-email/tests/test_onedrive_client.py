from unittest.mock import MagicMock, patch

import pytest

from message_loader import Attachment, LoadedMessage
from onedrive_client import get_service, upload_attachments


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


def test_upload_attachments_skips_mail_without_attachments():
    with patch("onedrive_client.requests.put") as mock_put:
        uploaded = upload_attachments("fake-token", _message(attachments=[]), "Newsletter")

    assert uploaded == []
    mock_put.assert_not_called()


@patch("onedrive_client.requests.put")
def test_upload_attachments_uploads_single_attachment(mock_put):
    mock_put.return_value.json.return_value = {"id": "item-1"}
    message = _message(
        subject="Stromrechnung Juli",
        attachments=[Attachment(filename="rechnung.pdf", content_type="application/pdf", content=b"...")],
    )

    uploaded = upload_attachments("fake-token", message, "Rechnungen/Zahlungen")

    assert uploaded == ["item-1"]
    args, kwargs = mock_put.call_args
    url = args[0]
    assert "Email-Ablage" in url
    assert "Rechnungen-Zahlungen" in url
    assert "2026-07-17_Stromrechnung%20Juli_rechnung.pdf" in url
    assert kwargs["headers"]["Authorization"] == "Bearer fake-token"
    assert kwargs["data"] == b"..."
    mock_put.return_value.raise_for_status.assert_called_once()


@patch("onedrive_client.requests.put")
def test_upload_attachments_keeps_original_filenames_distinct(mock_put):
    mock_put.return_value.json.side_effect = [{"id": "item-1"}, {"id": "item-2"}]
    message = _message(
        attachments=[
            Attachment(filename="rechnung.pdf", content_type="application/pdf", content=b"a"),
            Attachment(filename="anlage.pdf", content_type="application/pdf", content=b"b"),
        ]
    )

    uploaded = upload_attachments("fake-token", message, "Rechnungen/Zahlungen")

    assert uploaded == ["item-1", "item-2"]
    urls = [call.args[0] for call in mock_put.call_args_list]
    assert "rechnung.pdf" in urls[0]
    assert "anlage.pdf" in urls[1]
    assert urls[0] != urls[1]


def test_get_service_raises_clear_error_when_token_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="storage-auth"):
        get_service()
