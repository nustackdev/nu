"""Policy spans: execution policy around a body - TryCatch.

Nu's Policy sub-shape of Span governs how a body runs on failure: re-run it,
fall back, give up. A Span is transparent (TRANSPARENT cardinality): it forwards
the body's yield in the same shape - scalar, stream, or nothing - and the
``span_cardinality_matches_body`` law holds the wrapper to the body's resolved
cardinality.

The structure lives in the tree, not in ``payload``. The slots are fixed:
``[body, catch, finally_, error_key]``. The body is slot 0; an absent ``catch``
/ ``finally_`` is a ``Noop`` leaf, so presence is read off the tree, not a
recorded index; ``error_key`` is a string-yielding Nu (a ``StrArg``, default the
literal ``"error"``) naming where the caught exception lands. Inter-Nu
communication is always through the Context attrs fabric - that is the one
mechanism - so the handler reads the error back at the same key. The only
pure-Python config is ``errors`` (the typed-exception filter): exception
*classes* are not meaningfully a Nu, so they stay in ``payload``.

``TryCatch(body, catch=None, finally_=None, errors=None, error_key="error")``
runs ``body``. On an exception matched by ``errors`` (any ``Exception`` when
``None``) it writes the exception string to ``attrs[error_key]`` and runs
``catch`` in the body's place; with no ``catch``, or an unmatched exception, the
error propagates. ``finally_`` runs on success or failure either way.

Two context disciplines, faithful to v1:

- **catch is isolated.** It runs against a *copy* of the context (``ctx._copy``)
  with the exception string written to ``attrs[error_key]``, so a handler can
  read it and compute a fallback value - but the catch's own writes are
  discarded; only its returned value forwards.
- **finally_ persists.** It runs against the live context; its writes land.

Transparency is resolved per cardinality, read off ``Attr.CHILD_CARDINALITY`` at
the node: a void/scalar body is a direct call; a stream body is wrapped in a
guarding generator so a failure *during iteration* swaps in the fallback stream.
A stream that fails mid-drain has already emitted its prefix - the fallback's
items follow it; we cannot un-yield.

Note: catch/finally isolation swaps ``rt.ctx`` for the duration of the branch.
That is safe within a sequential subtree (the swap is restored before the thunk
returns); a catch firing concurrently with a parallel sibling that shares the
runtime would observe the swap. Bodies under a Policy are sequential in
practice, so this is a documented edge, not a hot path.

v1 reference: ``src/nu/spans/policy.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.core import Noop
from nu2.core._stream import aiter_any, sync_iter
from nu2.lang import Attr, Cardinality, Policy


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu2.lang import Command, Flow, Nu, Span, StrArg
    from nu2.lang.runtime import Runtime

__all__ = ["TryCatch"]


def _run_catch(rt: Runtime, catch: Callable, error_key: Callable, exc: Exception) -> object:
    """Run the catch against a copy of the context carrying the error; return its value.

    The error string lands at ``attrs[error_key]`` (the attrs fabric is the one
    inter-Nu channel); the copy isolates the handler so its own writes do not
    leak back to the live context.
    """
    saved = rt.ctx
    rt.ctx = saved._copy()
    try:
        rt.ctx.attrs[error_key(rt)] = str(exc)
        return catch(rt)
    finally:
        rt.ctx = saved


async def _arun_catch(rt: Runtime, catch: Callable, error_key: Callable, exc: Exception) -> object:
    """Async sibling of :func:`_run_catch`."""
    saved = rt.ctx
    rt.ctx = saved._copy()
    try:
        rt.ctx.attrs[await error_key(rt)] = str(exc)
        return await catch(rt)
    finally:
        rt.ctx = saved


def _guard(
    rt: Runtime,
    body: Callable,
    catch: Callable | None,
    finally_: Callable | None,
    error_key: Callable,
    errors: tuple[type[Exception], ...] | None,
) -> Iterator:
    """Drive the stream body; catch swaps in a fallback stream, finally always runs."""
    try:
        try:
            yield from sync_iter(body(rt))
        except Exception as exc:
            if catch is None or (errors is not None and not isinstance(exc, errors)):
                raise
            yield from sync_iter(_run_catch(rt, catch, error_key, exc))
    finally:
        if finally_ is not None:
            finally_(rt)


async def _aguard(
    rt: Runtime,
    body: Callable,
    catch: Callable | None,
    finally_: Callable | None,
    error_key: Callable,
    errors: tuple[type[Exception], ...] | None,
) -> AsyncIterator:
    """Async sibling of :func:`_guard`."""
    try:
        try:
            async for v in aiter_any(await body(rt)):
                yield v
        except Exception as exc:
            if catch is None or (errors is not None and not isinstance(exc, errors)):
                raise
            async for v in aiter_any(await _arun_catch(rt, catch, error_key, exc)):
                yield v
    finally:
        if finally_ is not None:
            await finally_(rt)


class TryCatch(Policy):
    """``TryCatch(body, catch=None, finally_=None, errors=None, error_key="error")``.

    Children (fixed): ``[body, catch, finally_, error_key]``. The body is slot 0;
    an absent ``catch`` / ``finally_`` is a ``Noop``; ``error_key`` is a
    string-yielding Nu naming where the caught exception is written in the attrs
    fabric (default the literal ``"error"``). ``errors`` is the pure-Python typed
    filter (a tuple, or ``None`` for catch-all); unmatched exceptions propagate
    unretried. ``catch`` runs in an isolated context copy (writes discarded, only
    its value forwards); ``finally_`` runs on success or failure against the live
    context. Yields whatever the body yields (transparent).
    """

    def __init__(
        self,
        body: Nu,
        catch: Nu | None = None,
        finally_: Flow | Command | Span | None = None,
        errors: tuple[type[Exception], ...] | type[Exception] | None = None,
        error_key: StrArg = "error",
    ) -> None:
        if errors is not None and not isinstance(errors, tuple):
            errors = (errors,)
        super().__init__(
            body,
            catch if catch is not None else Noop(),
            finally_ if finally_ is not None else Noop(),
            error_key,
        )
        self.payload["errors"] = errors

    def _branches(self, children: tuple[Callable, ...]) -> tuple[Callable, Callable | None, Callable | None]:
        """Resolve ``(body, catch, finally_)`` thunks; ``Noop`` slots read None."""
        catch = None if isinstance(self.children[1], Noop) else children[1]
        finally_ = None if isinstance(self.children[2], Noop) else children[2]
        return children[0], catch, finally_

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body, catch, finally_ = self._branches(children)
        error_key = children[3]
        errors = self.payload["errors"]

        if catch is None and finally_ is None:
            return body  # nothing to wrap: the body is the whole behaviour

        if catch is not None and finally_ is not None:

            def thunk(rt: Runtime) -> object:
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _guard(rt, body, catch, finally_, error_key, errors)
                try:
                    try:
                        return body(rt)
                    except Exception as exc:
                        if errors is not None and not isinstance(exc, errors):
                            raise
                        return _run_catch(rt, catch, error_key, exc)
                finally:
                    finally_(rt)

            return thunk

        if catch is not None:

            def thunk(rt: Runtime) -> object:
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _guard(rt, body, catch, None, error_key, errors)
                try:
                    return body(rt)
                except Exception as exc:
                    if errors is not None and not isinstance(exc, errors):
                        raise
                    return _run_catch(rt, catch, error_key, exc)

            return thunk

        def thunk(rt: Runtime) -> object:  # finally_ only
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _guard(rt, body, None, finally_, error_key, errors)
            try:
                return body(rt)
            finally:
                finally_(rt)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body, catch, finally_ = self._branches(children)
        error_key = children[3]
        errors = self.payload["errors"]

        if catch is None and finally_ is None:
            return body

        if catch is not None and finally_ is not None:

            async def athunk(rt: Runtime) -> object:
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _aguard(rt, body, catch, finally_, error_key, errors)
                try:
                    try:
                        return await body(rt)
                    except Exception as exc:
                        if errors is not None and not isinstance(exc, errors):
                            raise
                        return await _arun_catch(rt, catch, error_key, exc)
                finally:
                    await finally_(rt)

            return athunk

        if catch is not None:

            async def athunk(rt: Runtime) -> object:
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _aguard(rt, body, catch, None, error_key, errors)
                try:
                    return await body(rt)
                except Exception as exc:
                    if errors is not None and not isinstance(exc, errors):
                        raise
                    return await _arun_catch(rt, catch, error_key, exc)

            return athunk

        async def athunk(rt: Runtime) -> object:  # finally_ only
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _aguard(rt, body, None, finally_, error_key, errors)
            try:
                return await body(rt)
            finally:
                await finally_(rt)

        return athunk
