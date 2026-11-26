"""BlobFabric: one backend, opened when a tree enters its binding and closed when it leaves."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.context import Fabric


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.lang.runtime import Context

    from .protocol import BlobBackend


__all__ = ["BlobFabric"]


class BlobFabric(Fabric):
    """A blob backend held open for the span of a ``Provide``.

    The tree carries the backend class and its options, not an instance: the
    backend is built when the bracket is entered, so two runs of one tree
    each open and close their own, and a tree sent to another process opens
    the store there.

    Args:
        backend: a ``BlobBackend`` class, such as ``LMDBBackend``.
        options: its constructor kwargs, plain Python values.

    Notes:
        - A sync run opens and closes it in place; an async run does both in
          a thread, so neither blocks the event loop.
        - An async run reaches the backend through its async twins, a sync
          run through the sync calls.
    """

    def __init__(
        self,
        *,
        backend: type[BlobBackend],
        options: Mapping[str, object] | None = None,
    ) -> None:
        self._backend = backend(**dict(options or {}))
        self._open = False

    @property
    def backend(self) -> BlobBackend:
        """The open backend.

        Raises ``RuntimeError`` outside the bracket that bound it.
        """
        if not self._open:
            raise RuntimeError("the blob backend is not open: use it inside the With that binds it")
        return self._backend

    def setup(self, ctx: Context) -> None:
        """Open the backend."""
        self._backend.open()
        self._open = True

    def cleanup(self) -> None:
        """Close the backend."""
        self._open = False
        self._backend.close()

    async def asetup(self, ctx: Context) -> None:
        """Open the backend off the event loop."""
        await asyncio.to_thread(self._backend.open)
        self._open = True

    async def acleanup(self) -> None:
        """Close the backend off the event loop."""
        self._open = False
        await asyncio.to_thread(self._backend.close)
