"""Attr-fabric interactions: ``SetCmd``, ``Delete``, ``AttrExists``, ``Let``.

The write ops (``SetCmd`` / ``Delete``) delegate to the Ref
(``ref._write`` / ``ref._erase``) so the write mechanism lives with the fabric,
not hardcoded here. ``AttrExists`` complements the dual-role read: an
unbound read yields EMPTY, which a bound EMPTY would alias, so existence needs
an explicit query.

``Let`` is a scoped attr binding: a Bracket that pushes ``name -> value`` into
``ctx.attrs`` for the body's duration and restores the prior slot on exit
(also on exception). It lives here (not with the fabric-lifecycle brackets in
``context/fabric/lifecycle.py``) because the binding it governs is a scratch
attr, not a fabric instance - same axis as ``SetCmd`` / ``AttrRef``, just
scoped rather than open-ended.

Each interaction holds its Ref in a mutation or read slot; effect synthesis
binds it to the right effect on the attrs fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core._stream import aiter_any, sync_iter
from nu.core.literal import Literal
from nu.engine.structure import Declared
from nu.lang import Attr, Bracket, Cardinality, Command, ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["AttrExists", "Delete", "Let", "SetCmd"]


class SetCmd(Command):
    """Writes the value of slot 1 to the Ref in slot 0, through that Ref."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return
            ref._write(rt, v, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return
            await ref._awrite(rt, v, rt.program.children[nid][0])

        return athunk


class Delete(Command):
    """Removes the Ref in slot 0 from its fabric, through that Ref."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            ref._erase(rt, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            await ref._aerase(rt, rt.program.children[nid][0])

        return athunk


class AttrExists(ScalarQuery):
    """Yields whether the slot-0 ``AttrRef``'s address is bound in ``ctx.attrs``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            address = ref._address(rt, rt.program.children[nid][0])
            return address in rt.ctx.attrs

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            address = await ref._aaddress(rt, rt.program.children[nid][0])
            return address in rt.ctx.attrs

        return athunk


# --- Let: scoped attr binding ------------------------------------------------


class Let(Bracket):
    """``Let(name, value, body)`` - bind ``name -> value`` for the body's duration.

    Evaluates ``value`` once, pushes ``ctx.attrs[name] = <that value>``, runs
    ``body``, then restores the prior slot on exit (LIFO on nesting, also on
    exception). ``body`` reads the binding through ``AttrRef(name)`` (or any
    typed variant), so the same value is dereferenceable an arbitrary number
    of times inside the body without recomputing ``value``.

    Semantics vs ``SetCmd``: ``SetCmd`` writes an open-ended slot that persists
    on the returned context; ``Let`` is scoped, so the binding never leaks
    past ``body``. The two are duals - use ``SetCmd`` when the write is the
    point, ``Let`` when the binding is a local for the body.

    Nesting: inner ``Let(name, ...)`` shadows outer ``Let(name, ...)`` for the
    duration of the inner body; the outer value is restored on the inner's pop.

    Transparent like any Span: yields whatever ``body`` yields (scalar or
    stream) in the body's cardinality. If ``body`` is a Command (writes),
    ``Let`` writes; if it is a Query yielding a Str, ``Let`` yields Str.

    Children (fixed): ``[body, value, name]``. Body is slot 0 for the Span
    transparency law; ``value`` and ``name`` are any Nu expressions. ``name``
    is evaluated at eval time and coerced to ``str`` - callers passing a
    Python ``str`` get it auto-wrapped in ``Literal`` at construction, so the
    common case reads ``Let("k", ..., body=...)`` unchanged.
    """

    def __init__(self, name: object, value: object, body: Nu | None = None) -> None:
        if body is None:
            msg = "Let requires a body"
            raise TypeError(msg)
        if isinstance(name, str):
            name = Literal(name)
        super().__init__(body, value, name)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body_thunk, value_thunk, name_thunk = children[0], children[1], children[2]

        def thunk(rt: Runtime) -> object:
            name = name_thunk(rt)
            if not isinstance(name, str):
                msg = f"Let name must be a str, got {type(name).__name__}"
                raise TypeError(msg)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _stream_let(rt, name, value_thunk, body_thunk)
            v = value_thunk(rt)
            attrs = rt.ctx.attrs
            had_prev = name in attrs
            prev = attrs[name] if had_prev else None
            attrs[name] = v
            try:
                return body_thunk(rt)
            finally:
                # If a nested bracket swapped rt.ctx underneath, it has been
                # restored by now, so the current rt.ctx.attrs is the same
                # instance we wrote into - pop against it.
                _restore(rt.ctx.attrs, name, had_prev, prev)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body_thunk, value_thunk, name_thunk = children[0], children[1], children[2]

        async def athunk(rt: Runtime) -> object:
            name = await name_thunk(rt)
            if not isinstance(name, str):
                msg = f"Let name must be a str, got {type(name).__name__}"
                raise TypeError(msg)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _astream_let(rt, name, value_thunk, body_thunk)
            v = await value_thunk(rt)
            attrs = rt.ctx.attrs
            had_prev = name in attrs
            prev = attrs[name] if had_prev else None
            attrs[name] = v
            try:
                return await body_thunk(rt)
            finally:
                _restore(rt.ctx.attrs, name, had_prev, prev)

        return athunk

    def __repr__(self) -> str:
        return f"Let({self._children[2]!r}, {self._children[1]!r}, body={self._children[0]!r})"


def _restore(attrs: object, name: str, had_prev: bool, prev: object) -> None:
    """Pop the scoped binding: restore prior value or delete the slot."""
    if had_prev:
        attrs[name] = prev  # type: ignore[index]
    elif name in attrs:  # type: ignore[operator]
        del attrs[name]  # type: ignore[attr-defined]


def _stream_let(
    rt: Runtime,
    name: str,
    value_thunk: Callable,
    body_thunk: Callable,
) -> Iterator:
    """Sync stream body: the binding lives for the whole drain."""
    v = value_thunk(rt)
    attrs = rt.ctx.attrs
    had_prev = name in attrs
    prev = attrs[name] if had_prev else None
    attrs[name] = v
    try:
        yield from sync_iter(body_thunk(rt))
    finally:
        _restore(rt.ctx.attrs, name, had_prev, prev)


async def _astream_let(
    rt: Runtime,
    name: str,
    value_thunk: Callable,
    body_thunk: Callable,
) -> AsyncIterator:
    """Async sibling of :func:`_stream_let`."""
    v = await value_thunk(rt)
    attrs = rt.ctx.attrs
    had_prev = name in attrs
    prev = attrs[name] if had_prev else None
    attrs[name] = v
    try:
        async for item in aiter_any(await body_thunk(rt)):
            yield item
    finally:
        _restore(rt.ctx.attrs, name, had_prev, prev)
