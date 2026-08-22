"""Host-namespace escape hatches: ``globals()`` and ``locals()``.

Reach the live Python interpreter namespace, bypassing the Context. Host
glue, not Context reads. Kept explicit so their use is obvious.

Python's meta-evaluation builtins that *interpret Nu-authored source*
(``eval`` / ``compile`` / ``exec``) are deliberately absent: dynamic
evaluation of programs happens through :class:`nu.Eval` (the ``nu.prog``
fabric), not by running Python source strings inside a Nu term.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Globals", "Locals"]


class Globals(ScalarQuery):
    """ESCAPE HATCH: the host module namespace dict (Python ``globals``).

    Returns the live interpreter globals at evaluation. Bypasses the Context
    entirely - host glue, not a Context read.
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
    """ESCAPE HATCH: the host local namespace dict (Python ``locals``).

    Returns the live interpreter locals at evaluation. Bypasses the Context
    entirely - host glue, not a Context read.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return locals()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return locals()

        return athunk
