"""Subscription types."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.loc import key


__all__ = [
    "SubscriptionCallback",
    "SubscriptionReceiver",
]

type SubscriptionReceiver = SubscriptionCallback
"""Receiver function type for subscription notifications."""

type SubscriptionCallback = "Callable[[key.Key], None]"
"""Callback function type for subscription notifications."""
