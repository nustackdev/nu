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
from nu.engine.structure import Declared
from nu.lang import Attr, Bracket, Cardinality, Command, ScalarQuery
from nu.lang.literal import Literal
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["AttrExists", "Delete", "Let", "SetCmd"]


class SetCmd(Command):
    """Writes a value into the slot its Ref names, through that Ref.

    The Command never touches ``ctx.attrs`` itself. It hands the Ref its own
    node id, the Ref resolves its address and performs the write, which is
    what lets ``SetCmd`` drive any fabric Ref and not just ``AttrRef``.

    Args:
        ref: the Ref naming the slot to write. This is the mutation slot, so
            effect synthesis binds it WRITE; every other slot is a read.
        value: evaluated once, and its result is what lands in the slot.

    Notes:
        - An EMPTY or INVALID ``value`` writes nothing at all, so a slot that
          was already bound keeps whatever it held.
        - The write is open-ended: it lives on the context the run returns.
          ``Let`` is the scoped dual, binding only for a body's duration.

    Yields:
        Nothing (VOID). The write is the point.

    Example:
        >>> nu.run(nu.SetCmd(nu.AttrRef("total"), 10))[1].attrs
        Attributes(total=10)

        >>> first = nu.SetCmd(nu.AttrRef("a"), 1)
        >>> nu.run(nu.Sequential(first, nu.SetCmd(nu.AttrRef("a"), nu.AttrRef("no"))))[1].attrs
        Attributes(a=1)
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


class Delete(Command):
    """Removes the slot its Ref names from the fabric, through that Ref.

    Same shape as :class:`SetCmd`: the Ref is the declared mutation slot and
    the erase is delegated to it, so this drives any fabric Ref rather than
    only ``AttrRef``.

    Args:
        ref: the Ref naming the slot to remove. This is the mutation slot.

    Notes:
        - Removing a slot that is not bound is a no-op, not an error.
        - Deleting is not the same as holding EMPTY: after a delete
          ``.exists()`` yields False, whereas a slot ``Let`` bound to EMPTY
          reads EMPTY and still exists.

    Yields:
        Nothing (VOID). The erase is the point.

    Example:
        >>> bind = nu.SetCmd(nu.AttrRef("a"), 1)
        >>> nu.run(nu.Sequential(bind, nu.Delete(nu.AttrRef("a"))))[1].attrs
        Attributes()
    """

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
    """Whether the address of its ``AttrRef`` is bound in ``ctx.attrs``.

    Args:
        ref: the ``AttrRef`` whose address is resolved and looked up.

    Notes:
        - Normally written as ``AttrRef(...).exists()`` rather than built by
          hand.
        - Exists because the dual-role read cannot answer the question: an
          unbound slot yields EMPTY, and so does a slot holding EMPTY.
        - Only the address is resolved; the slot's value is never read.

    Yields:
        True or False, never a sentinel. An address that resolves to EMPTY or
        INVALID is looked up as a key like any other, and is simply absent.

    Example:
        >>> nu.run(nu.AttrRef("x").exists())[0]
        False

        >>> nu.run(nu.Let("x", 1, nu.AttrRef("x").exists()))[0]
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
    """Binds a name to a value in ``ctx.attrs`` for the body's duration.

    Evaluates ``value`` once, pushes it into ``ctx.attrs`` under ``name``,
    runs ``body``, then restores the prior slot on the way out - on a clean
    exit and on an exception alike. The body reads the binding back through
    ``AttrRef(name)`` (or any typed variant), so the one value can be
    dereferenced any number of times without recomputing it.

    Args:
        name: evaluated at run time and required to be a ``str``. A Python
            ``str`` is wrapped in a ``Literal`` at construction, so the
            common case is written with a plain name.
        value: evaluated once, before the body runs.
        body: runs with the binding in place. Required despite the default.

    Notes:
        - Scoped where ``SetCmd`` is open-ended. ``SetCmd`` leaves a slot on
          the context the run returns; a ``Let`` binding never leaks past its
          body. Reach for ``SetCmd`` when the write is the point, ``Let``
          when the binding is a local.
        - Nesting shadows: an inner ``Let`` on the same name hides the outer
          one, and the outer value comes back when the inner body ends.
        - Unlike ``SetCmd``, an EMPTY or INVALID ``value`` is still bound, so
          the slot exists and reads back as that sentinel.
        - Over a stream body the binding spans the whole drain, and is popped
          when the stream is exhausted.
        - Children are ordered ``[body, value, name]``; the body sits in slot
          0 to satisfy the Span transparency law.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality. Transparent
        like any Span: a Command body makes ``Let`` a writer, a stream body
        makes it a stream.

    Example:
        >>> nu.run(nu.Let("n", 7, nu.Add(nu.AttrRef("n"), 1)))[0]
        8

        >>> nu.run(nu.Let("n", 2, nu.Let("n", 5, nu.Mul(nu.AttrRef("n"), 10))))[0]
        50

        >>> nu.run(nu.Let("n", 7, nu.AttrRef("n")))[1].attrs
        Attributes()
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
