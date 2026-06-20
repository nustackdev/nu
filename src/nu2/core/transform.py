"""Transform atoms: Python's stream-to-stream builtins.

Maps Python's builtins that take an iterable and yield another iterable onto Nu
StreamQueries (lazy lenses - pulled per item, no materialization). Pure shape
over their source; effects only ride in through Ref children.

Builtins to cover (Python -> Nu):
- ``map`` -> ``Map``, ``filter`` -> ``Filter``, ``sorted`` -> ``Sorted``

Plus two transforms v1 keeps as core: ``Flatten`` (one-level concat) and
``Unique`` (drop already-seen, order preserved).

``Map`` and ``Filter`` bind each item into the attrs side-channel under a name
and evaluate a Nu child against it. The name is a **child** (a Query yielding
the name), so it can be a ``Literal`` or a Ref computed elsewhere - never an
opaque payload. The body reads the item with ``AttrRef(<name>)``. The per-item
binding writes ``ctx.attrs`` directly - the model's side-channel for loop
variables, not a tracked fabric write.

Sorts: all StreamQuery (Q). ``Sorted`` / ``Flatten`` / ``Unique`` stay
structural stubs (no ``compile``) until they are filled.

v1 reference: ``src/nu/queries/stream_transform.py`` (Filter, Map),
``transform.py`` (Sorted, Flatten, Unique).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine import Term
from nu2.lang import StreamQuery
from nu2.lang.sentinels import EMPTY, INVALID

from ._stream import aiter_any, sync_iter
from .literal import Literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["Filter", "Flatten", "Map", "Sorted", "Unique"]


class Map(StreamQuery):
    """Applies a query child to every item of its stream child (lazy).

    Children: ``[source, transform, key]``. Each item of ``source`` is bound
    under the name ``key`` yields, then ``transform`` is evaluated and its
    value yielded. The transform reads the item with ``AttrRef(<name>)``.
    """

    def __init__(self, source: Term, transform: Term, key: object = "item") -> None:
        key_node = key if isinstance(key, Term) else Literal(key)
        super().__init__(source, transform, key_node)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        source, transform, key_t = children

        def thunk(rt: Runtime) -> object:
            name = key_t(rt)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    rt.ctx.attrs[name] = elem
                    yield transform(rt)

            return gen()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        source, transform, key_t = children

        async def athunk(rt: Runtime) -> object:
            name = await key_t(rt)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    rt.ctx.attrs[name] = elem
                    yield await transform(rt)

            return agen()

        return athunk


class Filter(StreamQuery):
    """Keeps the items of its stream child for which a predicate holds (lazy).

    Children: ``[source, predicate, key]``. Each item is bound under the name
    ``key`` yields, then ``predicate`` is evaluated; the item is yielded only
    when truthy. A sentinel predicate drops the item.
    """

    def __init__(self, source: Term, predicate: Term, key: object = "item") -> None:
        key_node = key if isinstance(key, Term) else Literal(key)
        super().__init__(source, predicate, key_node)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        source, predicate, key_t = children

        def thunk(rt: Runtime) -> object:
            name = key_t(rt)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    rt.ctx.attrs[name] = elem
                    keep = predicate(rt)
                    if keep is EMPTY or keep is INVALID:
                        continue
                    if keep:
                        yield elem

            return gen()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        source, predicate, key_t = children

        async def athunk(rt: Runtime) -> object:
            name = await key_t(rt)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    rt.ctx.attrs[name] = elem
                    keep = await predicate(rt)
                    if keep is EMPTY or keep is INVALID:
                        continue
                    if keep:
                        yield elem

            return agen()

        return athunk


class Sorted(StreamQuery):
    """Its source child, ordered. Eager: drains the source, then yields.

    Children: ``[source]``. The one barrier among these lenses - a pull on its
    output blocks until the whole source is drained and sorted.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        def thunk(rt: Runtime) -> object:
            return iter(sorted(sync_iter(source(rt))))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            items = sorted([x async for x in aiter_any(await source(rt))])

            async def agen() -> object:
                for x in items:
                    yield x

            return agen()

        return athunk


class Flatten(StreamQuery):
    """Concatenates a source of iterables one level into a flat stream (lazy).

    Children: ``[source]`` where each item of ``source`` is itself iterable.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        def thunk(rt: Runtime) -> object:
            def gen() -> object:
                for sub in sync_iter(source(rt)):
                    yield from sub

            return gen()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            async def agen() -> object:
                async for sub in aiter_any(await source(rt)):
                    for x in sub:
                        yield x

            return agen()

        return athunk


class Unique(StreamQuery):
    """Yields each item of its source child once, first-seen order (lazy).

    Children: ``[source]``. Items must be hashable.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        def thunk(rt: Runtime) -> object:
            def gen() -> object:
                seen: set = set()
                for x in sync_iter(source(rt)):
                    if x not in seen:
                        seen.add(x)
                        yield x

            return gen()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            async def agen() -> object:
                seen: set = set()
                async for x in aiter_any(await source(rt)):
                    if x not in seen:
                        seen.add(x)
                        yield x

            return agen()

        return athunk
