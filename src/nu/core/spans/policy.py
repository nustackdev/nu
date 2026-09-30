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

Conventions (see ``AUTHORING.md``): structure lives in the tree, not ``payload``
(an absent optional branch is a ``Noop`` slot; names are ``StrArg`` children;
numeric knobs are returning children); ``ctx.attrs`` is the one inter-Nu channel
(the caught error and the attempt count are ``let``-bound there for the
handler that reads them, and only for as long as it runs); async-only atoms
declare ``requires_async`` and raise on the sync path as a backstop (the sync
entry refuses the subtree first).
"""

from __future__ import annotations

import asyncio
import random
from contextlib import ExitStack
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any, sync_iter
from nu.core.flows import Noop
from nu.engine.structure import Declared
from nu.lang import Attr, Cardinality, Policy


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Command, FloatArg, Flow, IntArg, Nu, Span, StrArg
    from nu.lang.runtime import Runtime

__all__ = ["CaughtError", "Retry", "Timeout", "TryCatch"]


class CaughtError(str):
    """The error a catch branch reads: a string that still carries the exception.

    ``attrs[error_key]`` has always held the exception string, and still
    does - this compares, formats and concatenates as ``str(exc)``, so
    ``ObjectRef("error")`` reads exactly as before. What it adds is
    ``.exception``, the live object, reachable from inside the tree with
    ``GetAttr(ObjectRef("error"), "exception")``.

    Args:
        exc: the caught exception, wrapped as ``str(exc)``.

    Notes:
        - A second attrs entry was the alternative, but that makes the
          channel two keys wide for one event and leaves a handler guessing
          which to read. A str subclass keeps one key.
        - Deliberately unslotted: ``Vars`` is ``vars()``, so walking into a
          structured error's fields (``ConstructionError.diagnostic.lineno``,
          say) needs a ``__dict__`` at every level.

    Yields:
        The string value on comparison/format/concat; ``.exception`` for the
        live object.

    Example:
        >>> from nu.core.spans.policy import CaughtError
        >>> c = CaughtError(ValueError("boom"))
        >>> c, c.exception
        ('boom', ValueError('boom'))
    """

    exception: BaseException

    def __new__(cls, exc: BaseException) -> CaughtError:
        """Wrap ``exc``, taking ``str(exc)`` as the string value."""
        self = super().__new__(cls, str(exc))
        self.exception = exc
        return self


def _async_backstop(name: str) -> Callable:
    """Sync-path backstop for an async-only span: the real path is ``acompile``."""

    def thunk(rt: Runtime) -> object:
        msg = f"{name} requires the async runtime; use arun / afirst / acollect"
        raise RuntimeError(msg)

    return thunk


# === TryCatch ==============================================================


def _run_catch(rt: Runtime, catch: Callable, error_key: Callable, exc: Exception) -> object:
    """Run catch with a :class:`CaughtError` bound at ``error_key``; return its value."""
    with rt.ctx.attrs.let(error_key(rt), CaughtError(exc)):
        return catch(rt)


async def _arun_catch(rt: Runtime, catch: Callable, error_key: Callable, exc: Exception) -> object:
    """Async sibling of :func:`_run_catch`."""
    with rt.ctx.attrs.let(await error_key(rt), CaughtError(exc)):
        return await catch(rt)


def _guard(
    rt: Runtime,
    body: Callable,
    catch: Callable | None,
    finally_: Callable | None,
    error_key: Callable,
    errors: tuple[type[Exception], ...] | None,
) -> Iterator:
    """Drive the stream body; catch swaps in a fallback stream, finally always runs.

    The caught error stays bound for as long as the fallback stream drains.
    """
    try:
        try:
            yield from sync_iter(body(rt))
        except Exception as exc:
            if catch is None or (errors is not None and not isinstance(exc, errors)):
                raise
            with rt.ctx.attrs.let(error_key(rt), CaughtError(exc)):
                yield from sync_iter(catch(rt))
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
            with rt.ctx.attrs.let(await error_key(rt), CaughtError(exc)):
                async for v in aiter_any(await catch(rt)):
                    yield v
    finally:
        if finally_ is not None:
            await finally_(rt)


class TryCatch(Policy):
    """Runs ``catch`` when the body raises a matching error; ``finally_`` always runs after.

    Children (fixed): ``[body, catch, finally_, error_key]``. An absent
    ``catch`` / ``finally_`` is a ``Noop`` slot. ``catch`` runs with the
    caught error bound at ``error_key`` for as long as it runs, a stream
    catch for its whole drain; ``finally_`` runs after, on success or failure
    alike.

    Args:
        body: the guarded Term.
        catch: runs on a matching failure, in place of the body. Optional.
        finally_: runs after, regardless of outcome. Optional.
        errors: the exception type(s) to catch. ``None`` catches everything;
            an unmatched exception propagates past this node untouched.
        error_key: where the caught exception (a :class:`CaughtError`) lands
            in the attrs fabric for ``catch`` to read.

    Yields:
        The body's value on success, or ``catch``'s value on a caught
        failure. Transparent otherwise: forwards the branch's shape as-is.

    Example:
        >>> nu.run(nu.TryCatch(nu.Div(1, 0), catch=nu.Str("failed")))[0]
        'failed'
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
        self._payload["errors"] = errors

    def _branches(
        self, children: tuple[Callable, ...]
    ) -> tuple[Callable, Callable | None, Callable | None]:
        """Resolve ``(body, catch, finally_)`` thunks; ``Noop`` slots read None."""
        catch = None if isinstance(self._children[1], Noop) else children[1]
        finally_ = None if isinstance(self._children[2], Noop) else children[2]
        return children[0], catch, finally_

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, catch, finally_ = self._branches(children)
        error_key = children[3]
        errors = self._payload["errors"]

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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, catch, finally_ = self._branches(children)
        error_key = children[3]
        errors = self._payload["errors"]

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


async def _arun_hook(rt: Runtime, hook: Callable, lets: dict) -> None:
    """Run a Retry hook with ``lets`` (attempt/error) bound for as long as it runs."""
    with ExitStack() as scope:
        for key, value in lets.items():
            scope.enter_context(rt.ctx.attrs.let(key, value))
        await hook(rt)


class Retry(Policy):
    """Re-runs the body on a matching failure, up to ``max_attempts`` times.

    Sync runs a bare retry: ``max_attempts`` and ``errors`` only, no delay,
    backoff, jitter or hooks. Async runs the full policy: ``delay`` grows by
    ``backoff`` each attempt, ``jitter`` decorrelates the wait, and
    ``on_attempt_fail`` / ``on_success`` / ``on_fail`` fire with the
    attempt count and error bound. A stream body is
    retried by atomic re-evaluation - drained fresh each attempt, emitted
    only on success, bounded streams only - and the stream path skips the
    per-attempt hooks.

    Args:
        body: the Term to re-run.
        max_attempts: the ceiling on attempts, including the first.
        delay: the wait before the first retry, in seconds (async only).
        backoff: the multiplier applied to ``delay`` after each attempt
            (async only).
        jitter: the fraction of ``delay`` to randomize by, ``0`` to ``1``
            (async only).
        errors: the exception type(s) that trigger a retry. ``None``
            matches any exception; an unmatched one propagates unretried.
        on_attempt_fail: runs after a failed attempt that still has retries
            left (async only). Optional.
        on_success: runs once the body succeeds (async only). Optional.
        on_fail: runs once attempts are exhausted, in place of re-raising
            (async only). Optional.
        error_key: where the failing attempt's error lands in the attrs
            fabric for a hook to read.
        attempt_key: where the attempt number lands in the attrs fabric for
            a hook to read.

    Yields:
        The body's value on the attempt that succeeds. On exhaustion:
        re-raises the last error, unless ``on_fail`` is set, in which case
        it yields ``None`` after running the hook.

    Example:
        >>> import asyncio
        >>> asyncio.run(nu.arun(nu.Retry(nu.Div(1, 1), max_attempts=1)))[0]
        1.0
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
        self._payload["errors"] = errors

    def _hooks(
        self, children: tuple[Callable, ...]
    ) -> tuple[Callable | None, Callable | None, Callable | None]:
        """Resolve ``(on_attempt_fail, on_success, on_fail)`` thunks; ``Noop`` slots read None."""
        oaf = None if isinstance(self._children[5], Noop) else children[5]
        osc = None if isinstance(self._children[6], Noop) else children[6]
        ofl = None if isinstance(self._children[7], Noop) else children[7]
        return oaf, osc, ofl

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[0]
        max_attempts_q = children[1]
        errors = self._payload["errors"]

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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[0]
        max_attempts_q, delay_q, backoff_q, jitter_q = (
            children[1],
            children[2],
            children[3],
            children[4],
        )
        oaf, osc, ofl = self._hooks(children)
        error_key, attempt_key = children[8], children[9]
        errors = self._payload["errors"]

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
    """Bounds the body by a wall-clock limit; runs ``on_timeout`` if it's hit.

    Async-only.

    Args:
        timeout: the wall-clock limit, in seconds.
        body: the bounded Term.
        on_timeout: runs against the live context if the limit is hit.
            Optional: without it, the timeout raises ``TimeoutError``.

    Notes:
        - ``asyncio.wait_for`` cancels the awaited body coroutine; a
          sync-only body offloaded to a thread can't be interrupted, so the
          limit stops the wait, not the thread itself.

    Yields:
        The body's value. ``None`` if ``on_timeout`` ran; otherwise
        ``TimeoutError`` propagates.

    Example:
        >>> import asyncio
        >>> asyncio.run(nu.arun(nu.Timeout(0.01, nu.Div(1, 1))))[0]
        1.0
    """

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(
        self, timeout: FloatArg, body: Nu, on_timeout: Flow | Command | Span | None = None
    ) -> None:
        super().__init__(body, timeout, on_timeout if on_timeout is not None else Noop())

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _async_backstop("Timeout")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, timeout_q = children[0], children[1]
        on_timeout = None if isinstance(self._children[2], Noop) else children[2]

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
