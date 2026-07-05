"""Noop: the empty Flow - the identity of flow composition.

A childless Strategy that composes nothing. It yields nothing and mutates
nothing, so it is the identity element of the flow monoid:
``Sequential(a, Noop(), b)`` runs exactly like ``Sequential(a, b)``. Use it as
the placeholder for a work slot that must hold a Nu but where nothing should
run - an else-less branch, a bodyless ``DelayedDo``, an absent ``catch`` /
``finally_`` / hook.

Being a Flow, it slot-fits wherever work fits: a Strategy child, a Control
body, a Span body. It does *not* fit a value slot or a param slot - a no-op
belongs where a mutator would go, never where a value is read. Owners still
identity-check it (``isinstance(child, Noop)``) to read "this optional branch
is absent" and skip it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Strategy


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Noop"]


class Noop(Strategy[None]):
    """The empty Flow: composes nothing, the identity of flow composition."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        return lambda rt: None

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> None:
            return None

        return athunk
