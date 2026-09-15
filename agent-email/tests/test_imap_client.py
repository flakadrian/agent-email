import imaplib
from unittest.mock import MagicMock, patch

import pytest
from imapclient.exceptions import IMAPClientError

import imap_client
from config import ImapConfig
from imap_client import connect, idle_listen, poll_new_messages
from imap_client import test_connection as check_connection


class _StopLoop(Exception):
    """Bricht die Endlosschleife von poll_new_messages/idle_listen kontrolliert ab."""


def _config() -> ImapConfig:
    return ImapConfig(
        host="imap.beispiel.de", port=993, user="me@beispiel.de", password="pw", use_ssl=True, folder="INBOX"
    )


@patch("imap_client.IMAPClient")
def test_connect_logs_in_and_selects_folder(mock_imap_cls):
    mock_client = mock_imap_cls.return_value

    client = connect(_config())

    mock_imap_cls.assert_called_once_with("imap.beispiel.de", port=993, ssl=True)
    mock_client.login.assert_called_once_with("me@beispiel.de", "pw")
    mock_client.select_folder.assert_called_once_with("INBOX")
    assert client is mock_client


@patch("imap_client.connect")
@patch("imap_client.load_config")
def test_connection_reports_success(mock_load_config, mock_connect, caplog):
    mock_load_config.return_value = _config()
    mock_client = MagicMock()
    mock_client.list_folders.return_value = [(None, b"/", "INBOX"), (None, b"/", "Archive")]
    mock_client.folder_status.return_value = {b"MESSAGES": 42}
    mock_connect.return_value = mock_client

    with caplog.at_level("INFO"):
        result = check_connection()

    assert result is True
    mock_client.logout.assert_called_once()
    assert "Verbindung erfolgreich zu imap.beispiel.de als me@beispiel.de" in caplog.text
    assert "42 Nachrichten" in caplog.text


@patch("imap_client.connect")
@patch("imap_client.load_config")
def test_connection_reports_failure_on_connect_error(mock_load_config, mock_connect, caplog):
    mock_load_config.return_value = _config()
    mock_connect.side_effect = RuntimeError("Login fehlgeschlagen")

    with caplog.at_level("INFO"):
        result = check_connection()

    assert result is False
    assert "Verbindung fehlgeschlagen" in caplog.text


@patch("imap_client._touch_heartbeat")
@patch("imap_client.time.sleep")
@patch("imap_client.connect")
@patch("imap_client.load_config")
def test_poll_new_messages_calls_callback_for_new_uids(mock_load_config, mock_connect, mock_sleep, mock_heartbeat):
    mock_load_config.return_value = _config()
    client = MagicMock()
    client.search.side_effect = [{1, 2}, {1, 2, 3}]
    mock_connect.return_value = client
    mock_sleep.side_effect = [None, _StopLoop()]

    on_message = MagicMock()

    with pytest.raises(_StopLoop):
        poll_new_messages(on_message, interval_seconds=0)

    on_message.assert_called_once_with(client, 3)
    client.logout.assert_called_once()
    # Einmal vor der Schleife, einmal im ersten (einzigen abgeschlossenen) Durchlauf.
    assert mock_heartbeat.call_count == 2


@patch("imap_client._touch_heartbeat")
@patch("imap_client.connect")
@patch("imap_client.load_config")
def test_idle_listen_calls_callback_for_new_uids(mock_load_config, mock_connect, mock_heartbeat):
    mock_load_config.return_value = _config()
    client = MagicMock()
    client.search.side_effect = [{1, 2}, {1, 2, 3}]
    client.idle_check.side_effect = [None, _StopLoop()]
    mock_connect.return_value = client

    on_message = MagicMock()

    with pytest.raises(_StopLoop):
        idle_listen(on_message, idle_timeout_seconds=1)

    on_message.assert_called_once_with(client, 3)
    assert client.idle.call_count == 2
    assert client.idle_done.call_count == 2
    client.logout.assert_called_once()
    assert mock_heartbeat.call_count == 2


@patch("imap_client._touch_heartbeat")
@patch("imap_client.time.sleep")
@patch("imap_client.connect")
@patch("imap_client.load_config")
def test_idle_listen_reconnects_after_connection_error(mock_load_config, mock_connect, mock_sleep, mock_heartbeat):
    mock_load_config.return_value = _config()

    broken_client = MagicMock()
    broken_client.search.return_value = {1, 2}
    broken_client.idle_check.side_effect = imaplib.IMAP4.abort("timeout")

    new_client = MagicMock()
    new_client.search.side_effect = [{1, 2}, _StopLoop()]

    mock_connect.side_effect = [broken_client, new_client]

    on_message = MagicMock()

    with pytest.raises(_StopLoop):
        idle_listen(on_message, idle_timeout_seconds=1)

    assert mock_connect.call_count == 2
    broken_client.logout.assert_called_once()
    new_client.logout.assert_called_once()


@patch("imap_client._touch_heartbeat")
@patch("imap_client.time.sleep")
@patch("imap_client.connect")
@patch("imap_client.load_config")
def test_idle_listen_reconnects_after_server_bye(mock_load_config, mock_connect, mock_sleep, mock_heartbeat):
    """Reproduziert den in der Praxis beobachteten Absturz: der Server beendet
    die IDLE-Verbindung serverseitig (z.B. nach ein paar Stunden Laufzeit)."""
    mock_load_config.return_value = _config()

    broken_client = MagicMock()
    broken_client.search.return_value = {1}
    broken_client.idle_check.side_effect = IMAPClientError("Unexpected IDLE response: b'* BYE timeout'")

    new_client = MagicMock()
    new_client.search.side_effect = [{1}, _StopLoop()]

    mock_connect.side_effect = [broken_client, new_client]

    with pytest.raises(_StopLoop):
        idle_listen(MagicMock(), idle_timeout_seconds=1)

    assert mock_connect.call_count == 2


@patch("imap_client._touch_heartbeat")
@patch("imap_client.time.sleep")
@patch("imap_client.connect")
@patch("imap_client.load_config")
def test_poll_new_messages_reconnects_after_connection_error(
    mock_load_config, mock_connect, mock_sleep, mock_heartbeat
):
    mock_load_config.return_value = _config()

    broken_client = MagicMock()
    broken_client.search.side_effect = [{1}, imaplib.IMAP4.abort("timeout")]

    new_client = MagicMock()
    new_client.search.side_effect = [{1}, _StopLoop()]

    mock_connect.side_effect = [broken_client, new_client]

    with pytest.raises(_StopLoop):
        poll_new_messages(MagicMock(), interval_seconds=0)

    assert mock_connect.call_count == 2
    broken_client.logout.assert_called_once()


def test_touch_heartbeat_creates_file(tmp_path, monkeypatch):
    heartbeat_path = tmp_path / "heartbeat"
    monkeypatch.setattr(imap_client, "HEARTBEAT_PATH", heartbeat_path)

    imap_client._touch_heartbeat()

    assert heartbeat_path.exists()


def test_touch_heartbeat_logs_warning_instead_of_raising(monkeypatch, caplog):
    unwritable_path = MagicMock()
    unwritable_path.touch.side_effect = OSError("Festplatte voll")
    monkeypatch.setattr(imap_client, "HEARTBEAT_PATH", unwritable_path)

    with caplog.at_level("WARNING"):
        imap_client._touch_heartbeat()

    assert "konnte nicht geschrieben werden" in caplog.text
