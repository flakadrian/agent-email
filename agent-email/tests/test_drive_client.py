from unittest.mock import MagicMock, patch

import pytest

from drive_client import _find_or_create_folder, get_service, upload_attachments
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


def _service_with_list_result(files: list[dict]) -> MagicMock:
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {"files": files}
    return service


def test_find_or_create_folder_returns_existing_id_without_creating():
    service = _service_with_list_result([{"id": "existing-123", "name": "Rechnungen-Zahlungen"}])

    folder_id = _find_or_create_folder(service, "Rechnungen-Zahlungen")

    assert folder_id == "existing-123"
    service.files.return_value.create.assert_not_called()


def test_find_or_create_folder_creates_when_missing():
    service = _service_with_list_result([])
    service.files.return_value.create.return_value.execute.return_value = {"id": "new-456"}

    folder_id = _find_or_create_folder(service, "Newsletter", parent_id="root-1")

    assert folder_id == "new-456"
    _, kwargs = service.files.return_value.create.call_args
    assert kwargs["body"]["name"] == "Newsletter"
    assert kwargs["body"]["parents"] == ["root-1"]


def test_upload_attachments_skips_mail_without_attachments():
    service = MagicMock()

    uploaded = upload_attachments(service, _message(attachments=[]), "Newsletter")

    assert uploaded == []
    service.files.assert_not_called()


@patch("drive_client._find_or_create_folder")
def test_upload_attachments_uploads_single_attachment(mock_find_or_create_folder):
    mock_find_or_create_folder.side_effect = ["root-id", "category-id"]
    service = MagicMock()
    service.files.return_value.create.return_value.execute.return_value = {"id": "file-1"}

    message = _message(
        subject="Stromrechnung Juli",
        attachments=[Attachment(filename="rechnung.pdf", content_type="application/pdf", content=b"...")],
    )

    uploaded = upload_attachments(service, message, "Rechnungen/Zahlungen")

    assert uploaded == ["file-1"]
    _, kwargs = service.files.return_value.create.call_args
    assert kwargs["body"]["name"] == "2026-07-17_Stromrechnung Juli_rechnung.pdf"
    assert kwargs["body"]["parents"] == ["category-id"]
    mock_find_or_create_folder.assert_any_call(service, "Email-Ablage")
    mock_find_or_create_folder.assert_any_call(service, "Rechnungen-Zahlungen", "root-id")


@patch("drive_client._find_or_create_folder")
def test_upload_attachments_keeps_original_filenames_distinct(mock_find_or_create_folder):
    mock_find_or_create_folder.side_effect = ["root-id", "category-id"]
    service = MagicMock()
    service.files.return_value.create.return_value.execute.side_effect = [{"id": "file-1"}, {"id": "file-2"}]

    message = _message(
        attachments=[
            Attachment(filename="rechnung.pdf", content_type="application/pdf", content=b"a"),
            Attachment(filename="anlage.pdf", content_type="application/pdf", content=b"b"),
        ]
    )

    uploaded = upload_attachments(service, message, "Rechnungen/Zahlungen")

    assert uploaded == ["file-1", "file-2"]
    names = [call.kwargs["body"]["name"] for call in service.files.return_value.create.call_args_list]
    assert names[0].endswith("rechnung.pdf")
    assert names[1].endswith("anlage.pdf")
    assert names[0] != names[1]


def test_get_service_raises_clear_error_when_token_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="drive-auth"):
        get_service()
