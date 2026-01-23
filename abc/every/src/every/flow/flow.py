"""Base Flow class - core execution infrastructure."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TypeVar

import attrs

from .runtime import Runtime


__all__ = [
    "Flow",
]

T = TypeVar("T")

logger = logging.getLogger(__name__)


@attrs.define
class Flow[RuntimeT: Runtime](ABC):
    """Base class for all flows - handles core execution infrastructure.

    Flows orchestrate execution. They can contain:
    - Other Flows (composition)
    - EveryShape Terms (data operations)

    Subclasses implement `run()` for business logic.
    Base `execute()` handles infrastructure (cancellation, errors).
    """

    @abstractmethod
    def exectue(self) -> None:
        """Exec."""
        ...

    # Flow
    pass
