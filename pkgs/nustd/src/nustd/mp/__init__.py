"""nustd.mp - the multiprocessing compute fabric.

Same shape as ``nustd.cluster``, backed by stdlib ``multiprocessing`` process
workers instead of ray actors. Zero-dependency, single-host: teleport a Nu
tree into a child process, run it there, get the result back.

- ``MpWorker`` - one long-lived child process hosting a Nu ``Context``
  + tree executor. Provisioned per-instance by ``Provide`` / ``ProvideList``
  / ``ProvideDict``. ``init`` (a lifecycle bracket, typically ``With(...)``)
  or ``ctx_builder`` (a callable) builds the worker's Context inside the
  child.
- ``MpWorkerRef`` - fabric ref. Reads the ``MpWorker`` bound on the
  Context.
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
interpreter. Everything handed to it (``init``, ``ctx_builder``, each body)
goes through cloudpickle (``nu.lang.wire``), so closures and classes defined
inside a function travel too.
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
