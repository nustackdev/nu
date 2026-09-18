"""Dynamic dispatch atoms: reach into the live Python interpreter namespace.

Wraps ``globals()`` and ``locals()`` as ScalarQueries. Host glue, not Context
reads: both bypass the Context entirely and hand back the interpreter's own
namespace dict. Kept explicit and separate from the other core atoms so their
use is obvious wherever they show up in a tree.

Sorts: both ScalarQuery (Q), zero children.

Python's meta-evaluation builtins that *interpret Nu-authored source*
(``eval`` / ``compile`` / ``exec``) are deliberately absent here: dynamic
evaluation of programs happens through ``nu.Eval`` (the ``nu.prog`` fabric),
not by running Python source strings inside a Nu term.

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). Both return a thunk that calls the Python builtin fresh on every
evaluation and ignores the Runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Globals", "Locals"]


class Globals(ScalarQuery):
    """ESCAPE HATCH: the host module namespace dict.

    Notes:
        - Bypasses the Context entirely. This is host glue, not a Context
          read, and the result depends on where in the interpreter the
          evaluation happens to run.
        - No children, so there is nothing for a sentinel to propagate
          through.

    Yields:
        The live result of Python's ``globals()``, called fresh each time.

    Example:
        >>> type(nu.run(nu.Globals())[0])
        <class 'dict'>
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return globals()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return globals()

        return athunk


class Locals(ScalarQuery):
    """ESCAPE HATCH: the host local namespace dict.

    Notes:
        - Bypasses the Context entirely. This is host glue, not a Context
          read, and the result depends on the Python call frame the thunk
          happens to run in.
        - No children, so there is nothing for a sentinel to propagate
          through.

    Yields:
        The live result of Python's ``locals()``, called fresh each time.

    Example:
        >>> type(nu.run(nu.Locals())[0])
        <class 'dict'>
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return locals()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return locals()

        return athunk
