"""functools interactions - the fold.

``reduce`` is the one ``functools`` member that is a runtime value operation, so
it is the only atom here. It is a ``Reduction`` (scalar-over-stream), hand-written
e2e like core's folds (``SumQuery`` ...) since folds are a hot path.

It is higher-order: the reducer is a Nu query child. Each step binds the
accumulator and the current item into the loop-var side-channel (the same
channel ``Map`` / ``Filter`` use), then evaluates the reducer, which reads them
via a typed AttrRef (e.g. ``IntAttrRef("acc") + IntAttrRef("item")``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import LiteralQuery
from nu.core._stream import aiter_any, sync_iter
from nu.engine import Term
from nu.lang import Reduction
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu, StrArg
    from nu.lang.runtime import Runtime


__all__ = ["NO_INITIAL", "ReduceQuery"]


NO_INITIAL = object()  # marks "no initializer" - distinct from any real value


class ReduceQuery(Reduction):
    """``functools.reduce(function, iterable[, initializer])``.

    Children: ``[source, function, acc_key, item_key, (initial)]``. Folds the
    source left-to-right. With an initializer the accumulator starts there;
    without one it starts at the first item. An empty source with no initializer
    raises ``TypeError`` (matching ``functools.reduce``).
    """

    def __init__(
        self,
        source: object,
        function: Nu,
        *,
        initial: object = NO_INITIAL,
        acc_key: StrArg = "acc",
        item_key: StrArg = "item",
    ) -> None:
        acc_node = acc_key if isinstance(acc_key, Term) else LiteralQuery(acc_key)
        item_node = item_key if isinstance(item_key, Term) else LiteralQuery(item_key)
        if initial is NO_INITIAL:
            super().__init__(source, function, acc_node, item_node)
            self.payload = {"has_initial": False}
        else:
            super().__init__(source, function, acc_node, item_node, initial)
            self.payload = {"has_initial": True}

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        has_initial = self.payload["has_initial"]
        source, function, acc_t, item_t = children[0], children[1], children[2], children[3]
        initial_t = children[4] if has_initial else None

        def thunk(rt: Runtime) -> object:
            acc_name = acc_t(rt)
            item_name = item_t(rt)
            started = False
            acc: object = None
            if initial_t is not None:
                acc = initial_t(rt)
                if acc is EMPTY or acc is INVALID:
                    return INVALID
                started = True
            for elem in sync_iter(source(rt)):
                if elem is EMPTY or elem is INVALID:
                    return INVALID
                if not started:
                    acc = elem
                    started = True
                    continue
                rt.ctx.attrs[acc_name] = acc
                rt.ctx.attrs[item_name] = elem
                acc = function(rt)
                if acc is EMPTY or acc is INVALID:
                    return INVALID
            if not started:
                msg = "reduce() of empty iterable with no initial value"
                raise TypeError(msg)
            return acc

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        has_initial = self.payload["has_initial"]
        source, function, acc_t, item_t = children[0], children[1], children[2], children[3]
        initial_t = children[4] if has_initial else None

        async def athunk(rt: Runtime) -> object:
            acc_name = await acc_t(rt)
            item_name = await item_t(rt)
            started = False
            acc: object = None
            if initial_t is not None:
                acc = await initial_t(rt)
                if acc is EMPTY or acc is INVALID:
                    return INVALID
                started = True
            async for elem in aiter_any(await source(rt)):
                if elem is EMPTY or elem is INVALID:
                    return INVALID
                if not started:
                    acc = elem
                    started = True
                    continue
                rt.ctx.attrs[acc_name] = acc
                rt.ctx.attrs[item_name] = elem
                acc = await function(rt)
                if acc is EMPTY or acc is INVALID:
                    return INVALID
            if not started:
                msg = "reduce() of empty iterable with no initial value"
                raise TypeError(msg)
            return acc

        return athunk
