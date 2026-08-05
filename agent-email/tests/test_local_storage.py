from pathlib import Path

import pytest

from local_storage import get_service, upload_attachments
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


def test_upload_attachments_skips_mail_without_attachments(tmp_path):
    uploaded = upload_attachments(tmp_path, _message(attachments=[]), "Newsletter")

    assert uploaded == []
    assert list(tmp_path.iterdir()) == []


def test_upload_attachments_writes_single_attachment(tmp_path):
    message = _message(
        subject="Stromrechnung Juli",
        attachments=[Attachment(filename="rechnung.pdf", content_type="application/pdf", content=b"...")],
    )

    uploaded = upload_attachments(tmp_path, message, "Rechnungen/Zahlungen")

    expected_path = tmp_path / "Email-Ablage" / "Rechnungen-Zahlungen" / "2026-07-17_Stromrechnung Juli_rechnung.pdf"
    assert uploaded == [str(expected_path)]
    assert expected_path.read_bytes() == b"..."


def test_upload_attachments_keeps_original_filenames_distinct(tmp_path):
    message = _message(
        attachments=[
            Attachment(filename="rechnung.pdf", content_type="application/pdf", content=b"a"),
            Attachment(filename="anlage.pdf", content_type="application/pdf", content=b"b"),
        ]
    )

    uploaded = upload_attachments(tmp_path, message, "Rechnungen/Zahlungen")

    assert len(uploaded) == 2
    assert uploaded[0] != uploaded[1]
    assert Path(uploaded[0]).read_bytes() == b"a"
    assert Path(uploaded[1]).read_bytes() == b"b"


def test_get_service_creates_configured_directory(tmp_path, monkeypatch):
    target = tmp_path / "email-ablage-root"
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(target))

    root = get_service()

    assert root == target
    assert target.is_dir()


def test_get_service_raises_clear_error_when_path_not_configured(monkeypatch):
    monkeypatch.delenv("LOCAL_STORAGE_PATH", raising=False)

    with pytest.raises(RuntimeError, match="LOCAL_STORAGE_PATH"):
        get_service()
