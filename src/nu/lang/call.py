"""Calling a host callable over child thunks: the one mechanism behind factory values.

A node that runs its children and hands their values to a Python callable
builds its thunk here. Two consumers share it:

- the factory atoms (``nu.factory.InteractionFactory``, ``@nu.host``, and the
  constructors built with them: ``DictOf``, ``ListOf``, ``TupleOf``), where
  the callable is fixed per class;
- ``Literal(factory=f, **kwargs)``, where the callable is a field of the node.

Positional thunks land as positional args, keyword thunks as keyword args,
in child order. Each evaluation runs every child, then calls the callable
once, so a fresh result comes out of every run.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["call_athunk", "call_thunk"]


def call_thunk(
    fn: Callable[..., object],
    pos_ts: tuple[Callable[[Runtime], object], ...],
    kwkeys: tuple[str, ...],
    kw_ts: tuple[Callable[[Runtime], object], ...],
    *,
    void: bool = False,
) -> Callable[[Runtime], object]:
    """A sync thunk: run the child thunks, call ``fn`` on their values.

    ``void`` makes the thunk return ``None`` (a command runs for its effect).
    """

    def thunk(rt: Runtime) -> object:
        args = [ct(rt) for ct in pos_ts]
        kwargs = {k: kt(rt) for k, kt in zip(kwkeys, kw_ts, strict=True)}
        result = fn(*args, **kwargs)
        return None if void else result

    return thunk


def call_athunk(
    fn: Callable[..., object],
    pos_ts: tuple[Callable[[Runtime], object], ...],
    kwkeys: tuple[str, ...],
    kw_ts: tuple[Callable[[Runtime], object], ...],
    *,
    void: bool = False,
) -> Callable[[Runtime], object]:
    """The async sibling of :func:`call_thunk`; awaits ``fn`` when it returns an awaitable."""

    async def athunk(rt: Runtime) -> object:
        args = [await ct(rt) for ct in pos_ts]  # type: ignore[misc]
        kwargs = {k: await kt(rt) for k, kt in zip(kwkeys, kw_ts, strict=True)}  # type: ignore[misc]
        result = fn(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return None if void else result

    return athunk
