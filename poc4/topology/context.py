"""Context and Substrate types for the topology language PoC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


# =============================================================================
# Context — handle with capabilities, scoped to a Group
# =============================================================================


class Context(ABC):
    """Handle with capabilities. Scoped to a Group."""

    @abstractmethod
    def release(self) -> None:
        """Release on scope exit."""
        ...


class KVContext(Context, ABC):
    """Key-value access context."""

    @abstractmethod
    def get(self, key: str) -> Any:
        """Read a value by key."""
        ...


class Snapshot(KVContext):
    """Read-only KV context backed by a dict snapshot."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = dict(data)  # copy for isolation
        self.opened = True

    def get(self, key: str) -> Any:
        """Read a value by key."""
        return self._data.get(key)

    def release(self) -> None:
        """Release snapshot."""
        self.opened = False


class Transaction(KVContext):
    """Read-write atomic KV context backed by a dict."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data  # shared reference — writes go here on commit
        self._snapshot = dict(data)  # read from snapshot
        self._writes: dict[str, Any] = {}
        self.opened = True
        self.committed = False

    def get(self, key: str) -> Any:
        """Read from snapshot (or pending writes)."""
        if key in self._writes:
            return self._writes[key]
        return self._snapshot.get(key)

    def put(self, key: str, value: Any) -> None:
        """Stage a write."""
        self._writes[key] = value

    def commit(self) -> None:
        """Apply staged writes to the backing store."""
        self._data.update(self._writes)
        self.committed = True

    def release(self) -> None:
        """Commit if not yet committed, then release."""
        if not self.committed and self._writes:
            self.commit()
        self.opened = False


# =============================================================================
# Substrate — factory that creates Contexts
# =============================================================================


class Substrate(ABC):
    """Factory that creates Contexts."""

    @abstractmethod
    def create(self, ctx_type: type[Context]) -> Context:
        """Create a context handle of the given type."""
        ...


class DictKVSubstrate(Substrate):
    """In-memory dict-backed KV substrate."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.data: dict[str, Any] = data if data is not None else {}

    def create(self, ctx_type: type[Context]) -> Context:
        """Create a Snapshot or Transaction from the backing dict."""
        if ctx_type is Snapshot or ctx_type is KVContext:
            return Snapshot(self.data)
        if ctx_type is Transaction:
            return Transaction(self.data)
        msg = f"Unsupported context type: {ctx_type}"
        raise TypeError(msg)


# =============================================================================
# ContextMap — the execution context passed through the tree
# =============================================================================

ContextMap = dict[type[Context], Context]
SubstrateMap = dict[type[Context], Substrate]
