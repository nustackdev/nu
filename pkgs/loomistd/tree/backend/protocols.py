from __future__ import annotations

from typing import Protocol

from loomi.state.interface.kv import (
    SyncObservableStorageProtocol,
    SyncTransactionContextManagerProtocol,
    SyncTransactionProtocol,
)
from loomi.state.interface.observer import SyncSubscriptionProtocol

from ..types import Value

__all__ = [
    "BackendProtocol",
    "TransactionProtocol",
    "TransactionContextManagerProtocol",
    "SubscriptionProtocol",
]


class BackendProtocol(SyncObservableStorageProtocol[Value], Protocol):
    """
    Backend protocol for observable key-value storage.
    """


class TransactionProtocol(SyncTransactionProtocol[Value], Protocol):
    """
    Transaction protocol for observable key-value storage.
    """


class TransactionContextManagerProtocol(SyncTransactionContextManagerProtocol[Value], Protocol):
    """
    Transaction context manager protocol for observable key-value storage.
    """


class SubscriptionProtocol(SyncSubscriptionProtocol, Protocol):
    """
    Subscription protocol for observable key-value storage.
    """
