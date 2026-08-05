import json
from unittest.mock import MagicMock, patch

from config import LocalModelConfig
from local_classifier import FALLBACK_CATEGORY, classify
from message_loader import LoadedMessage

CONFIG = LocalModelConfig(host="http://ollama:11434", model="qwen2.5:1.5b")


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


def _chat_response(category: str) -> MagicMock:
    response = MagicMock()
    response.json.return_value = {"message": {"content": json.dumps({"category": category})}}
    return response


@patch("local_classifier.requests.post")
def test_classify_returns_category_from_chat_response(mock_post):
    mock_post.return_value = _chat_response("Rechnungen/Zahlungen")

    category = classify(_message(), CONFIG)

    assert category == "Rechnungen/Zahlungen"
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["model"] == "qwen2.5:1.5b"
    assert mock_post.call_args[0][0] == "http://ollama:11434/api/chat"


@patch("local_classifier.requests.post")
def test_classify_falls_back_on_request_error(mock_post):
    mock_post.side_effect = RuntimeError("Ollama nicht erreichbar")

    category = classify(_message(), CONFIG)

    assert category == FALLBACK_CATEGORY


@patch("local_classifier.requests.post")
def test_classify_falls_back_on_unexpected_category(mock_post):
    mock_post.return_value = _chat_response("Nicht-existente-Kategorie")

    category = classify(_message(), CONFIG)

    assert category == FALLBACK_CATEGORY


@patch("local_classifier.requests.post")
def test_classify_falls_back_on_malformed_json(mock_post):
    response = MagicMock()
    response.json.return_value = {"message": {"content": "kein json"}}
    mock_post.return_value = response

    category = classify(_message(), CONFIG)

    assert category == FALLBACK_CATEGORY
