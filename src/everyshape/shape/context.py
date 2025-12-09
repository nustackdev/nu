"""Terms execution context defintion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


__all__ = [
    "ContextProtocol",
]


@dataclass(frozen=True)
class ContextProtocol(Protocol):
    """Execution context for operations and commands.

    Bundles together the tree instance and storage context needed for executing operations.

    TODO: Implement interface.
    """

    pass
