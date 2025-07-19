from __future__ import annotations

from typing import Protocol, runtime_checkable

from loomi.state.interface.kv import (
    SyncObservableStorageProtocol,
    SyncSnapshotContextManagerProtocol,
    SyncSnapshotProtocol,
    SyncTransactionContextManagerProtocol,
    SyncTransactionProtocol,
)
from loomi.state.interface.observer import SyncSubscriptionProtocol

from ..types import Value

__all__ = [
    "BackendProtocol",
    "TransactionProtocol",
    "TransactionContextManagerProtocol",
    "SnapshotProtocol",
    "SnapshotContextManagerProtocol",
    "SubscriptionProtocol",
]


@runtime_checkable
class BackendProtocol(SyncObservableStorageProtocol[Value], Protocol):
    """
    Backend protocol for observable key-value storage.
    """


@runtime_checkable
class TransactionProtocol(SyncTransactionProtocol[Value], Protocol):
    """
    Transaction protocol for observable key-value storage.
    Implements both the KV transaction protocol and the unified context protocol.
    """


@runtime_checkable
class TransactionContextManagerProtocol(SyncTransactionContextManagerProtocol[Value], Protocol):
    """
    Transaction context manager protocol for observable key-value storage.
    """


@runtime_checkable
class SnapshotProtocol(SyncSnapshotProtocol[Value], Protocol):
    """
    Snapshot protocol for observable key-value storage.
    Implements both the KV snapshot protocol and the unified context protocol.
    """


@runtime_checkable
class SnapshotContextManagerProtocol(SyncSnapshotContextManagerProtocol[Value], Protocol):
    """
    Snapshot context manager protocol for observable key-value storage.
    """


@runtime_checkable
class SubscriptionProtocol(SyncSubscriptionProtocol, Protocol):
    """
    Subscription protocol for observable key-value storage.
    """
