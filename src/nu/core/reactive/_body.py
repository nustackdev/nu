"""Running a reactive body.

Shared by every reactive flow, event and level alike: a body is run once and
whatever it yields is pulled through, so the side effects riding along a
stream body fire. Event flows hand the changed key to a lambda body, a
dynamic binding (``nu.lang.binding``) pushing a frame per run; level flows
never do, since their key is dropped at the edge.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang._stream import aiter_any


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["async_only", "drain_body"]


async def drain_body(rt: Runtime, body_thunk: Callable) -> None:
    """Run a reactive body once and pull any values it yields through to completion.

    Args:
        rt: the runtime to run the body under.
        body_thunk: the compiled body thunk to await.

    Notes:
        - A body may be a Command (returns ``None``) or a stream (returns an
          iterable / async-iterable). Commands carry their writes and stop
          here; a stream's values must be drained to fire the side effects
          riding along with them, since nothing else pulls on them.

    Yields:
        Nothing. Always returns ``None``.
    """
    result = await body_thunk(rt)
    if result is None:
        return
    async for _ in aiter_any(result):
        pass


def async_only(owner: str) -> Callable:
    """The sync thunk of a reactive flow: refuses to run."""

    def thunk(rt: Runtime) -> None:
        msg = f"{owner} requires an async runtime; use arun"
        raise RuntimeError(msg)

    return thunk
