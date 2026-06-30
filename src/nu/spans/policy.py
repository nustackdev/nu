"""Policy spans: execution policy around a body.

Nu's Policy sub-shape of Span governs how a body runs on failure or in time:
re-run it, fall back, give up, bound it, rate-limit it. A Span is transparent
(TRANSPARENT cardinality): it forwards the body's yield in the same shape -
scalar, stream, or nothing - and the ``span_cardinality_matches_body`` law holds
the wrapper to the body's resolved cardinality.

The atoms:

- ``TryCatch`` - try / catch / finally with a typed error filter.
- ``Retry`` - re-run the body on failure, with backoff, jitter, a typed filter,
  and per-attempt hooks (async path).
- ``Timeout`` - bound the body by a wall-clock limit (async-only).
- ``Throttle`` - drop body runs inside an interval of the prior run (async-only).
- ``Debounce`` - delay the body, cancelling a pending run on re-entry (async-only).

Conventions (see ``AUTHORING.md``): structure lives in the tree, not ``payload``
(an absent optional branch is a ``Noop`` slot; names are ``StrArg`` children;
numeric knobs are returning children); ``ctx.attrs`` is the one inter-Nu channel
(the error string, the attempt count, and the timing spans' cross-invocation
state all land there); a handler whose writes must not leak runs against a
``ctx._copy()``; async-only atoms declare ``requires_async`` and raise on the
sync path as a backstop (the sync entry refuses the subtree first).
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import TYPE_CHECKING

from nu.core import Noop
from nu.core._stream import aiter_any, sync_iter
from nu.engine.structure import Declared
from nu.lang import Attr, Cardinality, Policy


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Command, FloatArg, Flow, IntArg, Nu, Span, StrArg
    from nu.lang.runtime import Runtime

__all__ = ["Debounce", "Retry", "Throttle", "Timeout", "TryCatch"]


def _async_backstop(name: str) -> Callable:
    """Sync-path backstop for an async-only span: the real path is ``acompile``."""

    def thunk(rt: Runtime) -> object:
        msg = f"{name} requires the async runtime; use arun / afirst / acollect"
        raise RuntimeError(msg)

    return thunk


# === TryCatch ==============================================================


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


# === Retry =================================================================


async def _arun_hook(rt: Runtime, hook: Callable, sets: dict) -> None:
    """Run a Retry hook against an isolated ctx copy carrying ``sets`` (attempt/error)."""
    saved = rt.ctx
    rt.ctx = saved._copy()
    try:
        for key, value in sets.items():
            rt.ctx.attrs[key] = value
        await hook(rt)
    finally:
        rt.ctx = saved


class Retry(Policy):
    """``Retry(body, *, max_attempts=3, delay=0.0, backoff=1.0, jitter=0.0, ...)``.

    Re-runs ``body`` on a matching failure. Children (fixed):
    ``[body, max_attempts, delay, backoff, jitter, on_attempt_fail, on_success,
    on_fail, error_key, attempt_key]``. The numeric knobs are returning children
    (``IntArg`` / ``FloatArg``); the three hooks are non-returning, a ``Noop``
    when absent; ``error_key`` / ``attempt_key`` name where the error string and
    attempt number land in the attrs fabric. ``errors`` (pure-Python) scopes the
    retry to a typed exception; outside it propagates unretried.

    Sync runs a basic retry (``max_attempts`` + ``errors``, no delay or hooks).
    Async runs the full policy: ``delay`` grown by ``backoff`` each attempt,
    ``jitter`` decorrelating the wait, and the hooks fired on each failed attempt
    / on success / on final failure (each against an isolated ctx copy with the
    attempt count and error set). A stream body is retried by atomic
    re-evaluation - drained fresh per attempt, emitted only on success (bounded
    streams only); the stream path does not run the per-attempt hooks.
    """

    def __init__(
        self,
        body: Nu,
        *,
        max_attempts: IntArg = 3,
        delay: FloatArg = 0.0,
        backoff: FloatArg = 1.0,
        jitter: FloatArg = 0.0,
        errors: tuple[type[Exception], ...] | type[Exception] | None = None,
        on_attempt_fail: Flow | Command | Span | None = None,
        on_success: Flow | Command | Span | None = None,
        on_fail: Flow | Command | Span | None = None,
        error_key: StrArg = "error",
        attempt_key: StrArg = "attempt",
    ) -> None:
        if errors is not None and not isinstance(errors, tuple):
            errors = (errors,)
        super().__init__(
            body,
            max_attempts,
            delay,
            backoff,
            jitter,
            on_attempt_fail if on_attempt_fail is not None else Noop(),
            on_success if on_success is not None else Noop(),
            on_fail if on_fail is not None else Noop(),
            error_key,
            attempt_key,
        )
        self.payload["errors"] = errors

    def _hooks(self, children: tuple[Callable, ...]) -> tuple[Callable | None, Callable | None, Callable | None]:
        """Resolve ``(on_attempt_fail, on_success, on_fail)`` thunks; ``Noop`` slots read None."""
        oaf = None if isinstance(self.children[5], Noop) else children[5]
        osc = None if isinstance(self.children[6], Noop) else children[6]
        ofl = None if isinstance(self.children[7], Noop) else children[7]
        return oaf, osc, ofl

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body = children[0]
        max_attempts_q = children[1]
        errors = self.payload["errors"]

        def thunk(rt: Runtime) -> object:
            attempts = max(1, int(max_attempts_q(rt)))
            stream = rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM
            last: BaseException | None = None
            for _ in range(attempts):
                try:
                    if stream:
                        return iter(list(sync_iter(body(rt))))  # drain fresh per attempt
                    return body(rt)
                except Exception as exc:
                    if errors is not None and not isinstance(exc, errors):
                        raise
                    last = exc
            raise last  # type: ignore[misc]  # attempts >= 1, so last is set

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body = children[0]
        max_attempts_q, delay_q, backoff_q, jitter_q = children[1], children[2], children[3], children[4]
        oaf, osc, ofl = self._hooks(children)
        error_key, attempt_key = children[8], children[9]
        errors = self.payload["errors"]

        async def athunk(rt: Runtime) -> object:
            attempts = max(1, int(await max_attempts_q(rt)))

            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                last: BaseException | None = None
                for _ in range(attempts):
                    try:
                        return aiter_any([v async for v in aiter_any(await body(rt))])
                    except Exception as exc:
                        if errors is not None and not isinstance(exc, errors):
                            raise
                        last = exc
                raise last  # type: ignore[misc]

            delay = float(await delay_q(rt))
            backoff = float(await backoff_q(rt))
            jitter = float(await jitter_q(rt))
            ek, ak = await error_key(rt), await attempt_key(rt)

            for attempt in range(1, attempts + 1):
                try:
                    result = await body(rt)
                    if osc is not None:
                        await _arun_hook(rt, osc, {ak: attempt})
                    return result
                except Exception as exc:
                    if errors is not None and not isinstance(exc, errors):
                        raise
                    if attempt >= attempts:
                        if ofl is not None:
                            await _arun_hook(rt, ofl, {ak: attempt, ek: str(exc)})
                            return None
                        raise
                    if oaf is not None:
                        await _arun_hook(rt, oaf, {ak: attempt, ek: str(exc)})
                    wait = delay
                    if jitter > 0.0 and wait > 0.0:
                        spread = max(0.0, min(1.0, jitter))
                        wait *= 1.0 + random.uniform(-spread, spread)  # noqa: S311
                    await asyncio.sleep(wait)
                    delay *= backoff
            return None

        return athunk


# === timing: async-only ====================================================


class Timeout(Policy):
    """``Timeout(timeout, body, on_timeout=None)`` - bound the body by a wall-clock limit.

    Async-only. Children (fixed): ``[body, timeout, on_timeout]``. ``timeout`` is
    a returning child (seconds, ``FloatArg``); ``on_timeout`` is a non-returning
    branch run on the live context if the limit is hit (a ``Noop`` when absent -
    then the ``TimeoutError`` propagates). Forwards the body's value otherwise.

    Note: ``wait_for`` cancels the awaited body coroutine; a sync-only body
    offloaded to a thread cannot be interrupted - the limit stops the wait, not
    the thread.
    """

    requires_async = Declared(value=True)

    def __init__(self, timeout: FloatArg, body: Nu, on_timeout: Flow | Command | Span | None = None) -> None:
        super().__init__(body, timeout, on_timeout if on_timeout is not None else Noop())

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        return _async_backstop("Timeout")

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body, timeout_q = children[0], children[1]
        on_timeout = None if isinstance(self.children[2], Noop) else children[2]

        async def athunk(rt: Runtime) -> object:
            timeout = float(await timeout_q(rt))
            try:
                return await asyncio.wait_for(body(rt), timeout=timeout)
            except TimeoutError:
                if on_timeout is not None:
                    await on_timeout(rt)
                    return None
                raise

        return athunk


class Throttle(Policy):
    """``Throttle(interval, body)`` - drop body runs inside ``interval`` of the prior run.

    Async-only. Children (fixed): ``[body, interval]`` (seconds, ``FloatArg``).
    The last-run timestamp is cross-invocation state, so it lives in the attrs
    fabric keyed by this node (a Term is immutable and shared - no instance
    state). A dropped call yields ``None``; otherwise forwards the body's value.
    Meaningful only under repeated invocation (a loop / reactive).
    """

    requires_async = Declared(value=True)

    def __init__(self, interval: FloatArg, body: Nu) -> None:
        super().__init__(body, interval)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        return _async_backstop("Throttle")

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body, interval_q = children[0], children[1]
        state_key = f"__throttle_last_{nid}__"

        async def athunk(rt: Runtime) -> object:
            interval = float(await interval_q(rt))
            now = time.monotonic()
            if now - rt.ctx.attrs.get(state_key, 0.0) < interval:
                return None
            rt.ctx.attrs[state_key] = now
            return await body(rt)

        return athunk


class Debounce(Policy):
    """``Debounce(delay, body)`` - delay the body, cancelling a pending run on re-entry.

    Async-only. Children (fixed): ``[body, delay]`` (seconds, ``FloatArg``). Each
    invocation cancels the in-flight task and schedules a fresh one, so only the
    last call in a burst fires. The pending task is cross-invocation state, so it
    lives in the attrs fabric keyed by this node. Yields ``None`` immediately;
    the body runs later, detached. Meaningful only under repeated invocation.
    """

    requires_async = Declared(value=True)

    def __init__(self, delay: FloatArg, body: Nu) -> None:
        super().__init__(body, delay)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        return _async_backstop("Debounce")

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        body, delay_q = children[0], children[1]
        state_key = f"__debounce_pending_{nid}__"

        async def athunk(rt: Runtime) -> object:
            delay = float(await delay_q(rt))
            pending = rt.ctx.attrs.get(state_key)
            if pending is not None and not pending.done():
                pending.cancel()

            async def _later() -> object:
                await asyncio.sleep(delay)
                return await body(rt)

            rt.ctx.attrs[state_key] = asyncio.create_task(_later())
            return None

        return athunk
