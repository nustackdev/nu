"""Interaction - the non-Ref Nu.

Nu                          - the primitive
├── Ref                     - addressable location in a fabric
├── Interaction             - compute or mutate Γ (this module)
├── Form                    - typed descriptor (interface.py)
└── ContextManager          - bracket (context_manager.py)

Interactions split by role:
    Query   - functional construction. No WRITE. Yields value(s).
    Command - imperative mutation. WRITE in subtree. Yields nothing.
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar

from .nu import RValue
from .types import T_co


__all__ = [
    "Interaction",
]


class Interaction(RValue[T_co], ABC):
    """Non-Ref Nu. Structural anchor for Query and Command.

    Effect declarations (class-level):
        writes: int | tuple[int, ...] = ()   Ref-target child positions for WRITE
        reads:  int | tuple[int, ...] = ()   Ref-target child positions for READ

    Un-listed Ref children default to READ in effect analysis.
    """

    writes: ClassVar[int | tuple[int, ...]] = ()
    reads: ClassVar[int | tuple[int, ...]] = ()

    def __init__(self, *children: object) -> None:
        """Wrap raw Python values as Literals."""
        from nu.utils import ensure_nu

        super().__init__(*[ensure_nu(c) for c in children])
