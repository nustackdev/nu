"""Chat: ScalarAction that runs one chat/completions call."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction

from .core import acompile_call, compile_call


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["Chat"]


class Chat(ScalarAction):
    """One chat/completions call; yields dict with text + message + usage + finish_reason."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)
