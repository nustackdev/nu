"""Addressing contract: Ref.

Ref is the concrete, addressable LValue that points to a Slot instance
inside some Shape. It does not itself perform work; it identifies *where*
work would happen. Behavior (Ops/Cmds) lives in higher layers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import Context, PathSegment, TuplePath
from .shape import Shape, Slot
from .term import LValue


class Ref(LValue, ABC):
    """Addressable reference to a Slot instance."""

    def __init__(self, slot: Slot, owner_shape: type[Shape]) -> None:
        super().__init__()
        ...

    # ----- LValue obligations -----

    @abstractmethod
    def resolve(self, context: Context) -> TuplePath:
        """Return the concrete path (segments) for this reference.

        May evaluate dynamic components using the context.
        """
        ...

    @abstractmethod
    def parent(self) -> Ref | None:
        """Return the parent reference (if any) in the navigation chain."""
        ...

    @abstractmethod
    def last_segment(self) -> PathSegment:
        """Return the final key/index segment for this reference."""
        ...

    # ----- convenience -----

    def __repr__(self) -> str:
        return "<Ref>"
