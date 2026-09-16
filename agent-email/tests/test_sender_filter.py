import pytest

from sender_filter import is_automated_sender


@pytest.mark.parametrize(
    "sender",
    [
        "notifications@github.com",
        "GitHub <notifications@github.com>",
        "noreply@github.com",
        "Notifications <NOTIFICATIONS@GITHUB.COM>",
    ],
)
def test_is_automated_sender_matches_known_patterns(sender):
    assert is_automated_sender(sender) is True


@pytest.mark.parametrize(
    "sender",
    [
        "stadtwerke@beispiel.de",
        "Oma <oma@beispiel.de>",
        "shop@online-shop.de",
    ],
)
def test_is_automated_sender_does_not_match_regular_senders(sender):
    assert is_automated_sender(sender) is False
