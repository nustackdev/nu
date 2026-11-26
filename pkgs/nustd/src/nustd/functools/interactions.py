"""functools interactions - the fold.

``reduce`` is the one ``functools`` member that is a runtime value operation, so
it is the only atom here. It is a ``QueryReduction`` (scalar-over-stream), hand-written
e2e like core's folds (``Sum`` ...) since folds are a hot path.

It is higher-order: the reducer is a Nu query child and ``Reduce`` is a
dynamic binding (``nu.lang.binding``), like ``Map`` / ``Filter``. The reducer
is a lambda over the accumulator and the item (``lambda acc, x: acc + x``),
run once at construction with mem refs to both. Each step gets a frame of
its own holding the two values. A reducer given as a plain tree
reads neither.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import QueryReduction
from nu.lang._stream import aiter_any, sync_iter
from nu.lang.binding import Binding
from nu.lang.sentinels import UNSET


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["Reduce"]


class Reduce(QueryReduction):
    """``functools.reduce(function, iterable[, initializer])``.

    Children: ``[source, function, (initial)]``. Folds the source
    left-to-right. With an initializer the accumulator starts there; without
    one it starts at the first item. An empty source with no initializer
    raises ``TypeError`` (matching ``functools.reduce``).

    ``function`` is a lambda over the accumulator and the item (it may take
    only the accumulator), run once at construction with refs to them, or a
    tree that reads neither.
    """

    def __init__(
        self,
        source: object,
        function: Nu | Callable[..., Nu],
        *,
        initial: object = UNSET,
    ) -> None:
        step, self._binding = Binding.of_lambda("Reduce", function, 2)
        if initial is UNSET:
            super().__init__(source, step)
        else:
            super().__init__(source, step, initial)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, function = children[0], children[1]
        initial_t = children[2] if len(children) > 2 else None  # [source, function, initial?]
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            started = False
            acc: object = None
            if initial_t is not None:
                acc = initial_t(rt)
                started = True
            for elem in sync_iter(source(rt)):
                if not started:
                    acc = elem
                    started = True
                    continue
                acc = function(rt.on(binding.push(rt.ctx, acc, elem)))
            if not started:
                msg = "reduce() of empty iterable with no initial value"
                raise TypeError(msg)
            return acc

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, function = children[0], children[1]
        initial_t = children[2] if len(children) > 2 else None  # [source, function, initial?]
        binding = self._binding

        async def athunk(rt: Runtime) -> object:
            started = False
            acc: object = None
            if initial_t is not None:
                acc = await initial_t(rt)
                started = True
            async for elem in aiter_any(await source(rt)):
                if not started:
                    acc = elem
                    started = True
                    continue
                acc = await function(rt.on(binding.push(rt.ctx, acc, elem)))
            if not started:
                msg = "reduce() of empty iterable with no initial value"
                raise TypeError(msg)
            return acc

        return athunk
