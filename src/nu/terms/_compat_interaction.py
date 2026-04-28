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

import inspect
from abc import ABC
from typing import Any, ClassVar

from ._compat_nu import RValue
from ._compat_types import Mode, T_co


__all__ = [
    "Interaction",
]


# The four valid (own_mode, func_mode) pairs. Any other combination is
# incoherent (e.g. own_mode=SYNC + func_mode=ASYNC is a contradiction:
# async core work cannot run via a sync-only path).
_VALID_MODE_PAIRS: frozenset[tuple[Mode, Mode]] = frozenset(
    {
        (Mode.SYNC, Mode.SYNC),
        (Mode.BOTH, Mode.SYNC),
        (Mode.BOTH, Mode.BOTH),
        (Mode.ASYNC, Mode.ASYNC),
    }
)


class Interaction(RValue[T_co], ABC):
    """Non-Ref Nu. Structural anchor for Query and Command.

    Effect declarations (class-level):
        writes: int | tuple[int, ...] = ()   Ref-target child positions for WRITE
        reads:  int | tuple[int, ...] = ()   Ref-target child positions for READ

    Un-listed Ref children default to READ in effect analysis.

    Mode enforcement: every concrete (non-abstract) Interaction subclass must
    declare `own_mode` and `func_mode` in its own __dict__. The pair must be
    one of (SYNC,SYNC), (BOTH,SYNC), (BOTH,BOTH), (ASYNC,ASYNC). Other pairs
    are incoherent. See projects/nu/model/programming/modes.md.
    """

    writes: ClassVar[int | tuple[int, ...]] = ()
    reads: ClassVar[int | tuple[int, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Exempt role markers: ABC in direct bases or @abstractmethod present.
        if ABC in cls.__bases__ or inspect.isabstract(cls):
            return
        # Phase E migration: accept the new `support` declaration in lieu of the
        # legacy `(own_mode, func_mode)` pair. If `support` is declared, derive
        # legacy modes from it for the rest of the runtime; otherwise, enforce
        # the legacy pair as before.
        if "support" in cls.__dict__:
            support = cls.__dict__["support"]
            # Derive legacy modes for runtime dispatch compatibility.
            sync_in = any(getattr(m, "name", None) == "SYNC" for m in support)
            async_in = any(getattr(m, "name", None) == "ASYNC" for m in support)
            if sync_in and async_in:
                cls.own_mode = Mode.BOTH
                cls.func_mode = Mode.BOTH
            elif async_in:
                cls.own_mode = Mode.ASYNC
                cls.func_mode = Mode.ASYNC
            elif sync_in:
                cls.own_mode = Mode.SYNC
                cls.func_mode = Mode.SYNC
            else:
                msg = f"{cls.__module__}.{cls.__qualname__}: empty `support` set."
                raise TypeError(msg)
            return
        for name in ("own_mode", "func_mode"):
            if name not in cls.__dict__:
                msg = (
                    f"{cls.__module__}.{cls.__qualname__} must declare "
                    f"`{name}` explicitly (Mode.SYNC, Mode.ASYNC, or Mode.BOTH), "
                    "or declare `support` (frozenset[Mode])."
                )
                raise TypeError(msg)
        pair = (cls.own_mode, cls.func_mode)
        if pair not in _VALID_MODE_PAIRS:
            msg = (
                f"{cls.__module__}.{cls.__qualname__} declares "
                f"own_mode={cls.own_mode.name}, func_mode={cls.func_mode.name}. "
                "Valid pairs: (SYNC,SYNC), (BOTH,SYNC), (BOTH,BOTH), "
                "(ASYNC,ASYNC). See projects/nu/model/programming/modes.md."
            )
            raise TypeError(msg)
