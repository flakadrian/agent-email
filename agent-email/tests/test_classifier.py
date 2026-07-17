from unittest.mock import MagicMock, patch

from classifier import FALLBACK_CATEGORY, classify
from config import AnthropicConfig
from message_loader import LoadedMessage

CONFIG = AnthropicConfig(api_key="test-key", model="claude-haiku-4-5-20251001")


def _message(**overrides) -> LoadedMessage:
    defaults = dict(
        uid=1,
        subject="Stromrechnung Juli",
        sender="stadtwerke@beispiel.de",
        date="Fri, 17 Jul 2026 10:00:00 +0000",
        body_text="Anbei deine Rechnung über 42 EUR.",
        attachments=[],
    )
    defaults.update(overrides)
    return LoadedMessage(**defaults)


def _tool_use_response(category: str) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.name = "classify_email"
    block.input = {"category": category}
    response = MagicMock()
    response.content = [block]
    return response


@patch("classifier.anthropic.Anthropic")
def test_classify_returns_category_from_tool_response(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    mock_client.messages.create.return_value = _tool_use_response("Rechnungen/Zahlungen")

    category = classify(_message(), CONFIG)

    assert category == "Rechnungen/Zahlungen"
    mock_anthropic_cls.assert_called_once_with(api_key="test-key")
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["model"] == "claude-haiku-4-5-20251001"
    assert kwargs["tool_choice"] == {"type": "tool", "name": "classify_email"}


@patch("classifier.anthropic.Anthropic")
def test_classify_falls_back_on_api_error(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    mock_client.messages.create.side_effect = RuntimeError("API down")

    category = classify(_message(), CONFIG)

    assert category == FALLBACK_CATEGORY


@patch("classifier.anthropic.Anthropic")
def test_classify_falls_back_on_unexpected_category(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    mock_client.messages.create.return_value = _tool_use_response("Nicht-existente-Kategorie")

    category = classify(_message(), CONFIG)

    assert category == FALLBACK_CATEGORY


@patch("classifier.anthropic.Anthropic")
def test_classify_falls_back_on_empty_response(mock_anthropic_cls):
    mock_client = mock_anthropic_cls.return_value
    response = MagicMock()
    response.content = []
    mock_client.messages.create.return_value = response

    category = classify(_message(), CONFIG)

    assert category == FALLBACK_CATEGORY
