"""``MpWorkerRef``: fabric ref that resolves the ``MpWorker`` bound on ctx."""

from __future__ import annotations

from nu.context import FabricRef

from .resources import MpWorker


__all__ = ["MpWorkerRef"]


class MpWorkerRef(FabricRef):
    """The ``MpWorker`` bound on the Context.

    Notes:
        - Reading is a lookup and nothing else. No process is spawned, and
          the child of an already-provided worker is not contacted.
        - The lookup runs against whichever Context is in force where the
          ref sits, so inside a ``Teleport`` body it reads the worker
          process's own Context rather than the parent's.

    Yields:
        The bound ``MpWorker``. EMPTY when nothing is bound.

    Example:
        Provide(MpWorker, {"name": "solo"},
            MpWorkerRef().exists(),
        )
    """

    fabric = MpWorker
