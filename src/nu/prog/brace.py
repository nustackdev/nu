"""``PyBrace``: a brace bound on ctx, so a tree can say where source is built.

:mod:`nu.prog.constructors` owns *how* a brace works. This module is the one
step that makes it addressable from inside a Nu program: a parent-side
resource, provisioned by ``Provide``, holding a live :class:`Constructor`
that :class:`~nu.prog.load.LoadNu` looks up on ctx.

    Provide(PyBrace, {"python": "/path/to/.venv/bin/python"}, body)
    Provide(PyBrace, {}, body)   # in-process, no child, no serialization

One mechanism, two framings, on purpose. A ``Provide`` at the top of an app
is "this whole app builds its programs in that venv". The same ``Provide``
sitting deeper in the tree is "this section builds its programs in that
venv, and nothing outside it does". Nothing distinguishes the two but where
the bracket sits, so there is no second class for the scoped case, and no
knob to keep in sync between them.

``setup`` starts the underlying constructor (for a venv brace that means
spawning the child and waiting for its handshake, so a bad interpreter fails
at the bracket rather than at the first ``LoadNu``); ``cleanup`` closes it.
Both lifecycles are implemented, sync and async, so either runtime can drive
the bracket - the async pair runs the blocking work off-thread, the same way
:class:`nu.mp.MpWorker` does.

A ``PyBrace`` is itself a :class:`~nu.prog.constructors.Constructor`: it
forwards ``construct`` to whatever it wraps. That is what lets ``LoadNu``
treat a bound brace and its unbound in-process fallback as the same thing.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .constructors import InProcess, Venv
from .source import DEFAULT_ENTRY, DEFAULT_FILENAME


if TYPE_CHECKING:
    import os
    from collections.abc import Mapping

    from nu.lang.nu import Nu
    from nu.lang.runtime import Context

    from .constructors import Constructor
    from .diagnostics import Diagnostic


__all__ = ["PyBrace"]


class PyBrace:
    """The environment a ``LoadNu`` in this subtree constructs source in.

    With no ``python``, the brace is :class:`~nu.prog.constructors.InProcess`
    and there is nothing to start or stop. With one, it is a
    :class:`~nu.prog.constructors.Venv` over a long-lived child process,
    reused across every ``LoadNu`` under the bracket.

    Args:
        python: interpreter path, or a venv root containing ``bin/python``.
            ``None`` selects the in-process brace.
        start_timeout: seconds to wait for a venv child's ready frame.
        cwd: working directory for a venv child. Defaults to inheriting ours.
        env: full environment for a venv child. Defaults to inheriting ours.
    """

    def __init__(
        self,
        python: str | os.PathLike[str] | None = None,
        *,
        start_timeout: float = 30.0,
        cwd: str | os.PathLike[str] | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.python = python
        self.start_timeout = start_timeout
        self.cwd = cwd
        self.env = dict(env) if env is not None else None
        self._constructor: Constructor | None = None

    # -- lifecycle -----------------------------------------------------------

    @property
    def constructor(self) -> Constructor:
        """The brace this wraps, built on first use.

        Building is separate from starting: a ``Venv`` resolves its
        interpreter path in ``__init__``, so a typo raises here rather than
        at the far end of a construct call.
        """
        if self._constructor is None:
            self._constructor = (
                InProcess()
                if self.python is None
                else Venv(
                    self.python,
                    start_timeout=self.start_timeout,
                    cwd=self.cwd,
                    env=self.env,
                )
            )
        return self._constructor

    @property
    def started(self) -> bool:
        """Whether a venv brace currently holds a live child."""
        return bool(getattr(self._constructor, "started", False))

    def setup(self, ctx: Context) -> None:
        """Build the brace and, for a venv, spawn the child and handshake."""
        start = getattr(self.constructor, "start", None)
        if start is not None:
            start()

    def cleanup(self) -> None:
        """Close the brace. Idempotent, and a closed brace can be built again."""
        brace, self._constructor = self._constructor, None
        if brace is not None:
            brace.close()  # type: ignore[attr-defined]

    async def asetup(self, ctx: Context) -> None:
        """Async lifecycle: spawn + handshake off-thread."""
        await asyncio.to_thread(self.setup, ctx)

    async def acleanup(self) -> None:
        """Async lifecycle: run the blocking ``cleanup`` off-thread."""
        await asyncio.to_thread(self.cleanup)

    # -- construction --------------------------------------------------------

    def construct(
        self,
        source: str,
        *,
        entry: str = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> Nu | Diagnostic:
        """Construct a Nu term from ``source`` in this brace.

        Args:
            source: python source for a whole module.
            entry: name of the entry point function in that module.
            scope: plain values bound to the entry point by parameter name.
            filename: name frames and diagnostics attribute the source to.

        Returns:
            The Nu term the entry point returned, or a Diagnostic.
        """
        return self.constructor.construct(source, entry=entry, scope=scope, filename=filename)

    async def aconstruct(
        self,
        source: str,
        *,
        entry: str = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> Nu | Diagnostic:
        """Construct off-thread, so pipe I/O never stalls the event loop.

        A venv brace blocks on a pipe read for the whole construction, and an
        in-process one runs arbitrary snippet code; neither is something to do
        on the loop.
        """
        return await asyncio.to_thread(
            self.construct, source, entry=entry, scope=scope, filename=filename
        )

    def __repr__(self) -> str:
        where = "in-process" if self.python is None else str(self.python)
        return f"PyBrace({where})"
