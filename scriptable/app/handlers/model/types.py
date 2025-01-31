from __future__ import annotations

from dataclasses import dataclass

from sonny.state.async_state.protocols import StateProtocol, TransactionProtocol
from sonny.state.types import StateKey


# Transaction Context
@dataclass
class TransactionContext:
    """
    Holds transaction state for model operations.

    Attributes:
        transaction: Active transaction if any
    """

    transaction: TransactionProtocol | None = None

    @property
    def active(self) -> bool:
        """Check if there's an active transaction."""
        return self.transaction is not None


# Value Metadata
@dataclass
class StateContext:
    """
    Metadata for model.

    Attributes:
        state: State instance
        prefix: Key prefix for this value
        txn_context: Optional transaction context
    """

    state: StateProtocol
    prefix: StateKey
    txn_context: TransactionContext | None = None
