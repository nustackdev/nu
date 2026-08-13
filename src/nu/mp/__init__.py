"""nu.mp - the multiprocessing compute fabric.

Same shape as ``nu.cluster``, backed by stdlib ``multiprocessing`` process
workers instead of ray actors. Zero-dependency, single-host: teleport a Nu
tree into a child process, run it there, get the result back.

- ``MpWorker`` - one long-lived child process hosting a Nu ``Context``
  + tree executor. Provisioned per-instance by ``Provide`` / ``ProvideList``
  / ``ProvideDict``. ``init`` (a lifecycle bracket, typically ``With(...)``)
  or ``ctx_builder`` (a callable) builds the worker's Context inside the
  child.
- ``MpWorkerRef`` - fabric ref. Takes an arbitrary hashable tag
  (``MpWorkerRef("indexer-main")``, ``MpWorkerRef(("shard", 0))``).
- ``Teleport`` - the interaction; ships the body term to a tagged
  ``MpWorker`` and waits for its result. Works on both sync and async
  runtimes (pipe I/O is blocking either way; async wraps it off-thread).

Typical shape::

    Provide(MpWorker, {"name": "solo"},
        Teleport(some_tree),
    )

    ProvideList(MpWorker, [
        {"name": "w-0"},
        {"name": "w-1"},
    ],
        Sequential(
            Teleport(some_tree, target=0),
            Teleport(some_tree, target=1),
        ),
    )

The default ``start_method`` is ``"spawn"`` - the child gets a clean
interpreter, so any callable / bracket you pass in ``init`` or
``ctx_builder`` must be pickleable (top-level in a module, no closures).
"""

from __future__ import annotations

from .interactions import Teleport
from .refs import MpWorkerRef
from .resources import MpWorker


__all__ = [
    "MpWorker",
    "MpWorkerRef",
    "Teleport",
]
