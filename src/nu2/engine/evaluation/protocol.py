"""Runtime: the dispatch contract a compiled Program is driven through.

The engine evaluation layer is a *contract*, not an implementation. A
concrete runtime that satisfies this Protocol carries whatever per-drive
state it needs (context, budget, scheduler, ...) and provides the two
dispatch entry points the thunk columns of a :class:`Program` close over.

The engine does not instantiate Runtimes. A language layer (Nu, in
``nu2.lang.runtime``) supplies the concrete implementation.

Contract:

- ``eval(nid)``  -- dispatch the sync thunk at ``nid``; returns the value.
- ``aeval(nid)`` -- dispatch the async thunk at ``nid``; returns an awaitable.

Thread-safety: implementations must be safe under concurrent sync dispatch
through ``eval``. Task-safety: implementations must be safe under concurrent
async dispatch through ``aeval``. Reentrant: the same Runtime is closed over
by every thunk in the program and is reused for sibling-nid dispatch (the
parallel and stream toolkits a concrete Runtime exposes both depend on
this).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


__all__ = ["Runtime"]


@runtime_checkable
class Runtime(Protocol):
    """The dispatch contract a compiled Program is driven through.

    A concrete Runtime is the per-drive handle every emitted thunk closes
    over and calls back into. The engine specifies only the dispatch shape;
    everything else (context, resource budget, sentinel rules, concurrency
    primitives, stream pumps, thread/loop boundaries) is the implementor's
    business.
    """

    def eval(self, nid: int = 0, /) -> object:
        """Synchronously dispatch the thunk at ``nid``; return its value."""
        ...

    async def aeval(self, nid: int = 0, /) -> object:
        """Asynchronously dispatch the thunk at ``nid``; return its value."""
        ...
