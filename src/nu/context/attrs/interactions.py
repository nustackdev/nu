"""Attrs interactions: ``Let``, ``Set``, ``Exists``.

``Let`` declares a name in ``ctx.attrs`` for a body's duration and restores the
prior slot on exit (also on exception). It is the only way a name comes into
scope, and leaving the scope is the only way it goes. It lives here (not with
the fabric-lifecycle brackets in ``context/fabric/lifecycle.py``) because the
binding it governs is a plain attr, not a fabric instance.

``Set`` reassigns a declared name. It delegates to the Ref (``ref._write``) so
the write mechanism lives with the fabric, and is reached through
``ref.set(value)`` rather than built by hand. ``Exists`` complements the
dual-role read: an unbound read yields EMPTY, which a name declared without a
value would alias, so existence needs an explicit query.

Each interaction holds its Ref in a mutation or read slot; effect synthesis
binds it to the right effect on the attrs fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core._stream import aiter_any, sync_iter
from nu.engine.structure import Declared
from nu.lang import Attr, Bracket, Cardinality, Command, ScalarQuery
from nu.lang.literal import Literal
from nu.lang.sentinels import EMPTY, INVALID

from .refs import AttrRef


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["Exists", "Let", "Set"]


class Set(Command):
    """Reassigns the name its attrs ref names, through that Ref.

    The Command never touches ``ctx.attrs`` itself. It hands the Ref its own
    node id, and the Ref resolves its address and performs the write. Built
    by ``ref.set(value)``.

    Args:
        ref: the attrs ref naming the slot to reassign. This is the mutation
            slot, so effect synthesis binds it WRITE; every other slot is a
            read.
        value: evaluated once, and its result is what lands in the slot.

    Notes:
        - The name must be declared by an enclosing ``Let``. Reassigning an
          undeclared name raises, so no write outlives its scope.
        - An EMPTY or INVALID ``value`` writes nothing at all, so the name
          keeps whatever it held.

    Yields:
        Nothing (VOID). The write is the point.

    Example:
        >>> total = nu.IntRef("total")
        >>> _ = nu.run(nu.Let(total, 1, total.set(10) >> nu.print(total)))
        10

        >>> a = nu.IntRef("a")
        >>> _ = nu.run(nu.Let(a, 1, a.set(nu.ObjectRef("no")) >> nu.print(a)))
        1
    """

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


class Exists(ScalarQuery):
    """Whether the name its attrs ref names is declared in ``ctx.attrs``.

    Args:
        ref: the attrs ref whose address is resolved and looked up.

    Notes:
        - Normally written as ``ref.exists()`` rather than built by hand.
        - Exists because the dual-role read cannot answer the question: an
          unbound slot yields EMPTY, and so does a name declared without a
          value.
        - Only the address is resolved; the slot's value is never read.

    Yields:
        True or False, never a sentinel. An address that resolves to EMPTY or
        INVALID is looked up as a key like any other, and is simply absent.

    Example:
        >>> nu.run(nu.ObjectRef("x").exists())[0]
        False

        >>> nu.run(nu.Let("x", body=nu.ObjectRef("x").exists()))[0]
        True
    """

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
    """Declares a name in ``ctx.attrs`` for the body's duration.

    Evaluates ``value`` once, binds it to the name, runs ``body``, then
    restores the prior slot on the way out - on a clean exit and on an
    exception alike. The body reads the binding through an attrs ref
    (``nu.IntRef(name)``, ``nu.ObjectRef(name)``, ...) and may reassign it
    with ``ref.set(v)``; the reassignment ends with the scope too.

    Args:
        target: the name to declare. Either a name, evaluated at run time and
            required to be a ``str`` (a Python ``str`` is wrapped in a
            ``Literal`` at construction), or an attrs ref, whose address is
            resolved the same way the ref resolves it.
        value: evaluated once, before the body runs. Left out, the name is
            declared holding EMPTY.
        body: runs with the binding in place. Required despite the default.

    Notes:
        - Nesting shadows: an inner ``Let`` on the same name hides the outer
          one, a ``.set()`` in the inner body rebinds the inner one, and the
          outer value comes back when the inner body ends.
        - An EMPTY or INVALID ``value`` is still bound, so the name exists
          and reads back as that sentinel.
        - Over a stream body the binding spans the whole drain, and is popped
          when the stream is exhausted.
        - Children are ordered ``[body, value, target]``; the body sits in
          slot 0 to satisfy the Span transparency law.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality. Transparent
        like any Span: a Command body makes ``Let`` a writer, a stream body
        makes it a stream.

    Example:
        >>> n = nu.IntRef("n")
        >>> nu.run(nu.Let(n, 7, n + 1))[0]
        8

        >>> nu.run(nu.Let(n, 2, nu.Let(n, 5, n * 10)))[0]
        50

        >>> nu.run(nu.Let(n, body=n.exists()))[0]
        True

        >>> _ = nu.run(nu.Let(n, 2, nu.Let(n, 5, n.set(6)) >> nu.print(n)))
        2

        >>> nu.run(nu.Let("n", 7, n))[1].attrs
        Attributes()
    """

    def __init__(self, target: object, value: object = EMPTY, body: Nu | None = None) -> None:
        if body is None:
            msg = "Let requires a body"
            raise TypeError(msg)
        if isinstance(target, str):
            target = Literal(target)
        super().__init__(body, value, target)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body_thunk, value_thunk, name_thunk = children[0], children[1], children[2]
        target = self._children[2]

        def resolve(rt: Runtime) -> str:
            if isinstance(target, AttrRef):
                return _check_name(target._address(rt, rt.program.children[nid][2]))
            return _check_name(name_thunk(rt))

        def thunk(rt: Runtime) -> object:
            name = resolve(rt)
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
        target = self._children[2]

        async def resolve(rt: Runtime) -> str:
            if isinstance(target, AttrRef):
                return _check_name(await target._aaddress(rt, rt.program.children[nid][2]))
            return _check_name(await name_thunk(rt))

        async def athunk(rt: Runtime) -> object:
            name = await resolve(rt)
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


def _check_name(name: object) -> str:
    """The declared name, which must be a ``str``."""
    if not isinstance(name, str):
        msg = f"Let name must be a str, got {type(name).__name__}"
        raise TypeError(msg)
    return name


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
