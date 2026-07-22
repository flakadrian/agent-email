from datetime import date

from file_naming import message_date, sanitize_filename
from message_loader import LoadedMessage


def _message(**overrides) -> LoadedMessage:
    defaults = dict(
        uid=1,
        subject="Test",
        sender="test@beispiel.de",
        date="Wed, 22 Jul 2026 13:00:00 +0000",
        body_text="Test",
        attachments=[],
    )
    defaults.update(overrides)
    return LoadedMessage(**defaults)


def test_sanitize_filename_strips_filesystem_invalid_characters():
    assert sanitize_filename('a/b\\c:d*e?f"g<h>i|j') == "a_b_c_d_e_f_g_h_i_j"


def test_sanitize_filename_strips_graph_api_problematic_characters():
    # Live gegen OneDrive verifiziert: '#' und '%' im Dateinamen führen bei
    # pfadadressierten Graph-API-Uploads zu "400 Bad Request", auch wenn der
    # Wert URL-encodiert ist.
    assert sanitize_filename("Your receipt, PBC #2944-4936-4922") == "Your receipt, PBC _2944-4936-4922"
    assert sanitize_filename("100% fertig") == "100_ fertig"


def test_sanitize_filename_falls_back_when_empty():
    assert sanitize_filename("   ") == "ohne-betreff"


def test_message_date_parses_valid_date():
    msg = _message(date="Fri, 17 Jul 2026 10:00:00 +0000")
    assert message_date(msg) == "2026-07-17"


def test_message_date_uses_today_on_invalid_date():
    msg = _message(date="not a valid date")
    assert message_date(msg) == date.today().isoformat()


def test_message_date_uses_today_on_empty_date():
    msg = _message(date="")
    assert message_date(msg) == date.today().isoformat()
