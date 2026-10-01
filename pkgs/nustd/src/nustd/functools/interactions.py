"""functools interactions - the fold.

``reduce`` is the one ``functools`` member that is a runtime value operation, so
it is the only atom here. It is a ``Reduction`` (scalar-over-stream), hand-written
e2e like core's folds (``Sum`` ...) since folds are a hot path.

It is higher-order: the reducer is a Nu query child. Each step binds the
accumulator and the current item for that one evaluation of the reducer (the
same scoped binding ``Map`` / ``Filter`` use). The reducer is usually a lambda
over the two (``lambda acc, x: acc + x``), which mints their names; a plain
tree reads them with ``Attr`` under explicit names
(``Attr("acc") + Attr("item")``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.core._stream import aiter_any, sync_iter
from nu.lang import Reduction
from nu.lang.sentinels import EMPTY, UNSET


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.context import Attr
    from nu.lang import Nu, StrArg
    from nu.lang.runtime import Runtime


__all__ = ["Reduce"]


class Reduce(Reduction):
    """``functools.reduce(function, iterable[, initializer])``.

    Children: ``[source, function, acc_key, item_key, (initial)]``. Folds the
    source left-to-right. With an initializer the accumulator starts there;
    without one it starts at the first item. An empty source with no initializer
    raises ``TypeError`` (matching ``functools.reduce``).

    ``function`` is a lambda over the accumulator and the item, run once at
    construction with refs to both, or a tree reading them under ``acc_key``
    (default ``"acc"``) and ``item_key`` (default ``"item"``).
    """

    def __init__(
        self,
        source: object,
        function: Nu | Callable[[Attr, Attr], Nu],
        *,
        initial: object = UNSET,
        acc_key: StrArg | None = None,
        item_key: StrArg | None = None,
    ) -> None:
        function, (acc_key, item_key) = bind("Reduce", function, acc_key=acc_key, item_key=item_key)
        names = ("acc" if acc_key is None else acc_key, "item" if item_key is None else item_key)
        if initial is UNSET:
            super().__init__(source, function, *names)
            self._payload = {"has_initial": False}
        else:
            super().__init__(source, function, *names, initial)
            self._payload = {"has_initial": True}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_initial = self._payload["has_initial"]
        source, function, acc_t, item_t = children[0], children[1], children[2], children[3]
        initial_t = children[4] if has_initial else None

        def thunk(rt: Runtime) -> object:
            acc_name = acc_t(rt)
            item_name = item_t(rt)
            started = False
            acc: object = None
            if initial_t is not None:
                acc = initial_t(rt)
                if acc is EMPTY:
                    return EMPTY
                started = True
            for elem in sync_iter(source(rt)):
                if elem is EMPTY:
                    return EMPTY
                if not started:
                    acc = elem
                    started = True
                    continue
                with rt.ctx.attrs.let(acc_name, acc), rt.ctx.attrs.let(item_name, elem):
                    acc = function(rt)
                if acc is EMPTY:
                    return EMPTY
            if not started:
                msg = "reduce() of empty iterable with no initial value"
                raise TypeError(msg)
            return acc

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_initial = self._payload["has_initial"]
        source, function, acc_t, item_t = children[0], children[1], children[2], children[3]
        initial_t = children[4] if has_initial else None

        async def athunk(rt: Runtime) -> object:
            acc_name = await acc_t(rt)
            item_name = await item_t(rt)
            started = False
            acc: object = None
            if initial_t is not None:
                acc = await initial_t(rt)
                if acc is EMPTY:
                    return EMPTY
                started = True
            async for elem in aiter_any(await source(rt)):
                if elem is EMPTY:
                    return EMPTY
                if not started:
                    acc = elem
                    started = True
                    continue
                with rt.ctx.attrs.let(acc_name, acc), rt.ctx.attrs.let(item_name, elem):
                    acc = await function(rt)
                if acc is EMPTY:
                    return EMPTY
            if not started:
                msg = "reduce() of empty iterable with no initial value"
                raise TypeError(msg)
            return acc

        return athunk
