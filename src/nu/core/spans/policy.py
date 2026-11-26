"""Policy spans: execution policy around a body.

Nu's Policy sub-shape of Span governs how a body runs on failure or in time:
re-run it, fall back, give up, bound it, rate-limit it. A Span is transparent
(TRANSPARENT cardinality): it forwards the body's yield in the same shape -
scalar, stream, or nothing - and the ``span_cardinality_matches_body`` law holds
the wrapper to the body's resolved cardinality.

The atoms:

- ``TryCatch`` - try / catch / finally with a typed error filter.
- ``Retry`` - re-run the body on failure, with backoff, jitter, a typed filter
  and an exclusion from it, and per-attempt hooks (async path).
- ``Timeout`` - bound the body by a wall-clock limit (async-only).

Conventions (see ``AUTHORING.md``): structure lives in the tree, not in fields
(an absent optional branch is a ``Noop`` slot, and the node records in a
field which branches were given, so a ``Noop`` passed on purpose still
runs; numeric knobs and the ``errors`` / ``except_errors`` filters are
returning children, evaluated on every run, so they can be computed); a
handler that reads what the span hands it (the caught error, the attempt
count) is a lambda over those values, a dynamic binding (``nu.lang.binding``)
that pushes a frame holding them for as long as the handler runs; async-only atoms
declare ``requires_async`` and raise on the sync path as a backstop (the sync
entry refuses the subtree first).
"""

from __future__ import annotations

import asyncio
import itertools
import random
from typing import TYPE_CHECKING, cast

from nu.core.flows import Noop
from nu.core.flows.parallel._scheduling import _settle
from nu.engine.structure import Declared
from nu.lang import Attr, Cardinality, Nu, Policy
from nu.lang._stream import aiter_any, sync_iter
from nu.lang.binding import Binding
from nu.lang.sentinels import UNSET, Unset


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Command, FloatArg, Flow, IntArg, Span
    from nu.lang.runtime import Runtime

__all__ = ["CaughtError", "Retry", "Timeout", "TryCatch"]


def _errors(errors: object) -> tuple[type[Exception], ...] | None:
    """The error filter as the thunks read it: a tuple, or None for any exception.

    Takes what an ``errors`` child yields (None, one exception class, or a
    tuple of them) and, at construction, the raw argument (UNSET too).

    Raises:
        TypeError: something other than exception classes.
    """
    if errors is UNSET or errors is None:
        return None
    out = errors if isinstance(errors, tuple) else (errors,)
    for cls in out:
        if not (isinstance(cls, type) and issubclass(cls, BaseException)):
            msg = f"errors must be exception classes, got {errors!r}"
            raise TypeError(msg)
    return cast("tuple[type[Exception], ...]", out)


def _errors_child(errors: object) -> object:
    """The ``errors`` argument as its child: a term as given, a plain filter checked first."""
    if isinstance(errors, Nu):
        return errors
    return _errors(errors)


def _slot(branch: object) -> object:
    """A branch as its child slot: itself when given, a ``Noop`` placeholder when UNSET."""
    return Noop() if branch is UNSET else branch


class CaughtError(str):
    """The error a catch branch reads: a string that still carries the exception.

    A catch has always been handed the exception string, and still is -
    this compares, formats and concatenates as ``str(exc)``. What it adds is
    ``.exception``, the live object, reachable from inside the tree with
    ``GetAttr(err, "exception")``.

    Args:
        exc: the caught exception, wrapped as ``str(exc)``.

    Notes:
        - A second value handed was the alternative, but that makes the
          handler two parameters wide for one event and leaves it guessing
          which to read. A str subclass keeps one value.
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


def _caught(rt: Runtime, binding: Binding, exc: Exception) -> Runtime:
    """``rt`` on a frame holding the :class:`CaughtError` of ``exc``, for the catch to read."""
    return rt.on(binding.push(rt.ctx, CaughtError(exc)))


def _guard(
    rt: Runtime,
    body: Callable,
    catch: Callable | None,
    finally_: Callable | None,
    binding: Binding,
    errors: tuple[type[Exception], ...] | None,
) -> Iterator:
    """Drive the stream body; catch swaps in a fallback stream, finally always runs.

    The caught error's frame stays for as long as the fallback stream drains.
    """
    try:
        try:
            yield from sync_iter(body(rt))
        except Exception as exc:
            if catch is None or (errors is not None and not isinstance(exc, errors)):
                raise
            yield from sync_iter(catch(_caught(rt, binding, exc)))
    finally:
        if finally_ is not None:
            finally_(rt)


async def _aguard(
    rt: Runtime,
    body: Callable,
    catch: Callable | None,
    finally_: Callable | None,
    binding: Binding,
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
            async for v in aiter_any(await catch(_caught(rt, binding, exc))):
                yield v
    finally:
        if finally_ is not None:
            await finally_(rt)


class TryCatch(Policy):
    """Runs ``catch`` when the body raises a matching error; ``finally_`` always runs after.

    Python's ``try`` one to one::

        try: b / except: h                 TryCatch(b, catch=h)
        try: b / except E: h               TryCatch(b, errors=E, catch=h)
        try: b / except: pass              TryCatch(b, catch=lambda err: nu.Noop())
        try: b / finally: f                TryCatch(b, finally_=f)
        try: b / except E: h / finally: f  TryCatch(b, errors=E, catch=h, finally_=f)

    Children (fixed): ``[body, catch, finally_, errors]``. A
    branch left out is a ``Noop`` slot, and the ``given`` field records which
    were given: a given branch runs whatever it is, ``Noop`` included. Which
    branches exist is structure, read at compile time to shape the thunk;
    ``errors`` is a value, evaluated on every run before the body. ``catch``
    runs on a frame holding the caught error, pushed when it is caught, for
    as long as it runs, a stream catch for its whole drain; ``finally_`` runs
    after, on success or failure alike.

    Args:
        body: the guarded Term.
        catch: runs on a matching failure, in place of the body: a lambda
            over the caught error (a :class:`CaughtError`), or a tree that
            reads none. Left out, nothing is caught, as a ``try`` with no
            ``except``.
        finally_: runs after, regardless of outcome. Optional.
        errors: the exception type(s) ``catch`` handles, or any Nu yielding
            them. Left out, any exception; an unmatched one propagates past
            this node untouched. Needs ``catch``: there is nothing to filter
            for without one.

    Notes:
        - The lambda runs once, at construction, and gets a ref to the error,
          not the error: it builds the handler and never inspects it in
          Python.

    Yields:
        The body's value on success, or ``catch``'s value on a caught
        failure. Transparent otherwise: forwards the branch's shape as-is.

    Example:
        >>> nu.run(nu.TryCatch(nu.Div(1, 0), catch=lambda err: "failed: " + nu.Str(err)))[0]
        'failed: division by zero'

        A tree catch, reading nothing:

        >>> nu.run(nu.TryCatch(nu.Div(1, 0), catch=nu.Literal("failed")))[0]
        'failed'
    """

    def __init__(
        self,
        body: Nu,
        catch: Nu | Callable | Unset = UNSET,
        finally_: Flow | Command | Span | Unset = UNSET,
        errors: tuple[type[Exception], ...] | type[Exception] | Nu | Unset = UNSET,
    ) -> None:
        if errors is not UNSET and catch is UNSET:
            msg = "TryCatch: errors= says what catch= handles; pass catch= too"
            raise TypeError(msg)
        given = frozenset(
            name
            for name, branch in (("catch", catch), ("finally_", finally_))
            if branch is not UNSET
        )
        if catch is UNSET:
            bound, self._binding = UNSET, Binding.none()
        else:
            bound, self._binding = Binding.of_lambda("TryCatch", catch, 1)
        super().__init__(body, _slot(bound), _slot(finally_), _errors_child(errors))
        self.given = given

    def _branches(
        self, children: tuple[Callable, ...]
    ) -> tuple[Callable, Callable | None, Callable | None]:
        """Resolve ``(body, catch, finally_)`` thunks; a branch not given reads None."""
        given = self.given
        catch = children[1] if "catch" in given else None
        finally_ = children[2] if "finally_" in given else None
        return children[0], catch, finally_

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, catch, finally_ = self._branches(children)
        binding = self._binding
        errors_t = children[3]

        if catch is None and finally_ is None:
            return body  # nothing to wrap: the body is the whole behaviour

        if catch is not None and finally_ is not None:

            def thunk(rt: Runtime) -> object:
                errors = _errors(errors_t(rt))
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _guard(rt, body, catch, finally_, binding, errors)
                try:
                    try:
                        return body(rt)
                    except Exception as exc:
                        if errors is not None and not isinstance(exc, errors):
                            raise
                        return catch(_caught(rt, binding, exc))
                finally:
                    finally_(rt)

            return thunk

        if catch is not None:

            def thunk(rt: Runtime) -> object:
                errors = _errors(errors_t(rt))
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _guard(rt, body, catch, None, binding, errors)
                try:
                    return body(rt)
                except Exception as exc:
                    if errors is not None and not isinstance(exc, errors):
                        raise
                    return catch(_caught(rt, binding, exc))

            return thunk

        def thunk(rt: Runtime) -> object:  # finally_ only
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _guard(rt, body, None, finally_, binding, None)
            try:
                return body(rt)
            finally:
                finally_(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, catch, finally_ = self._branches(children)
        binding = self._binding
        errors_t = children[3]

        if catch is None and finally_ is None:
            return body

        if catch is not None and finally_ is not None:

            async def athunk(rt: Runtime) -> object:
                errors = _errors(await errors_t(rt))
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _aguard(rt, body, catch, finally_, binding, errors)
                try:
                    try:
                        return await body(rt)
                    except Exception as exc:
                        if errors is not None and not isinstance(exc, errors):
                            raise
                        return await catch(_caught(rt, binding, exc))
                finally:
                    await finally_(rt)

            return athunk

        if catch is not None:

            async def athunk(rt: Runtime) -> object:
                errors = _errors(await errors_t(rt))
                if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                    return _aguard(rt, body, catch, None, binding, errors)
                try:
                    return await body(rt)
                except Exception as exc:
                    if errors is not None and not isinstance(exc, errors):
                        raise
                    return await catch(_caught(rt, binding, exc))

            return athunk

        async def athunk(rt: Runtime) -> object:  # finally_ only
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _aguard(rt, body, None, finally_, binding, None)
            try:
                return await body(rt)
            finally:
                await finally_(rt)

        return athunk


# === Retry =================================================================


async def _arun_hook(rt: Runtime, hook: Callable, binding: Binding, values: tuple) -> None:
    """Run a Retry hook on a frame holding ``values`` (error and attempt, or attempt)."""
    await hook(rt.on(binding.push(rt.ctx, *values)))


class Retry(Policy):
    """Re-runs the body on a matching failure, up to ``max_attempts`` times.

    Sync runs a bare retry: ``max_attempts``, ``errors`` and
    ``except_errors`` only, no delay, backoff, jitter or hooks. Async runs
    the full policy: ``delay`` grows by ``backoff`` each attempt up to
    ``max_delay``, ``jitter`` decorrelates the wait, and
    ``on_attempt_fail`` / ``on_success`` / ``on_fail`` fire with the
    error and the attempt count handed to them. A hook is a lambda over what
    it can see (``lambda err, attempt: ...`` for a failure, or just
    ``lambda err: ...``; ``lambda attempt: ...`` for success, where there is
    no error), or a tree that reads none. A stream body is retried by
    atomic re-evaluation - drained fresh each attempt, emitted only on
    success, bounded streams only - and the stream path skips the
    per-attempt hooks but waits the same delays.

    Args:
        body: the Term to re-run.
        max_attempts: the ceiling on attempts, including the first. ``None``
            retries without end, until the body succeeds, an error outside
            ``errors`` or inside ``except_errors`` is raised, or the caller
            cancels (async only).
        delay: the wait before the first retry, in seconds (async only).
        backoff: the multiplier applied to ``delay`` after each attempt
            (async only).
        jitter: the fraction of the wait to randomize by, ``0`` to ``1``
            (async only).
        max_delay: the ceiling on the grown wait, in seconds. ``None``, the
            default, leaves it uncapped (async only).
        errors: the exception type(s) that trigger a retry, or any Nu
            yielding them. Left out, any exception; an unmatched one
            propagates unretried.
        except_errors: the exception type(s) never retried, or any Nu
            yielding them. A match propagates at once, unretried and
            without hooks, even when ``errors`` matches it too or is left
            out: ``errors`` says what to retry, this carves out what not
            to. Left out, nothing is excluded.
        on_attempt_fail: runs after a failed attempt that still has retries
            left (async only): ``lambda err, attempt: ...`` or a tree.
            Optional.
        on_success: runs once the body succeeds (async only):
            ``lambda attempt: ...`` or a tree. Optional.
        on_fail: runs once attempts are exhausted, in place of re-raising
            (async only): ``lambda err, attempt: ...`` or a tree. Optional:
            left out, the last error is re-raised; given, even a ``Noop``,
            it is not.

    Notes:
        - The wait before retry ``n`` is ``delay * backoff ** (n - 1)``,
          capped at ``max_delay``; ``jitter`` applies after the cap, so a
          capped wait still spreads around ``max_delay``.
        - ``max_attempts=None`` is async only. The sync path has no delay, so
          an unbounded sync retry would spin a failing body without a pause:
          it raises ``ValueError`` when run instead. Unbounded with a
          ``max_delay`` is a supervisor: it backs off to the cap and keeps
          trying.
        - The error a hook gets is a :class:`CaughtError`, its message
          carrying the exception, as ``TryCatch``'s catch reads it; the
          attempt counts from 1.
        - Each hook is its own binding over its own lambda, so lambda hooks
          and tree hooks mix freely.
        - A lambda hook runs once, at construction, and gets refs, not
          values: it builds the hook and never inspects them in Python.

    Yields:
        The body's value on the attempt that succeeds. On exhaustion:
        re-raises the last error, unless ``on_fail`` is set, in which case
        it yields ``None`` after running the hook.

    Example:
        >>> import asyncio
        >>> asyncio.run(nu.arun(nu.Retry(nu.Div(1, 1), max_attempts=1)))[0]
        1.0

        A hook reading what it is handed:

        >>> gave_up = lambda err, attempt: nu.print("gave up after", attempt, "-", err)
        >>> _ = asyncio.run(nu.arun(nu.Retry(nu.Div(1, 0), max_attempts=2, on_fail=gave_up)))
        gave up after 2 - division by zero

        A supervisor that never gives up, backing off to at most a minute::

            nu.Retry(serve, max_attempts=None, delay=1.0, backoff=2.0, max_delay=60.0)

        One that retries anything but a refusal::

            nu.Retry(serve, max_attempts=None, delay=1.0, except_errors=Refused)
    """

    def __init__(
        self,
        body: Nu,
        *,
        max_attempts: IntArg | None = 3,
        delay: FloatArg = 0.0,
        backoff: FloatArg = 1.0,
        jitter: FloatArg = 0.0,
        max_delay: FloatArg | None = None,
        errors: tuple[type[Exception], ...] | type[Exception] | Nu | Unset = UNSET,
        on_attempt_fail: Flow | Command | Span | Unset = UNSET,
        on_success: Flow | Command | Span | Unset = UNSET,
        on_fail: Flow | Command | Span | Unset = UNSET,
        except_errors: tuple[type[Exception], ...] | type[Exception] | Nu | Unset = UNSET,
    ) -> None:
        # A plain cap is refused now; a term (computed or not) is checked when it runs.
        if not isinstance(max_delay, Nu):
            _max_delay(max_delay)
        hooks = (
            ("on_attempt_fail", on_attempt_fail),
            ("on_success", on_success),
            ("on_fail", on_fail),
        )
        given = frozenset(name for name, hook in hooks if hook is not UNSET)
        # Each hook is a binding of its own: error then attempt on a failure,
        # the attempt alone on success.
        bound = [
            Binding.of_lambda(f"Retry {name}", hook, handed)
            if hook is not UNSET
            else (Noop(), Binding.none())
            for (name, hook), handed in zip(hooks, (2, 1, 2), strict=True)
        ]
        (on_attempt_fail, oaf), (on_success, osc), (on_fail, ofl) = bound
        self.hook_bindings = (oaf, osc, ofl)
        super().__init__(
            body,
            max_attempts,
            delay,
            backoff,
            jitter,
            on_attempt_fail,
            on_success,
            on_fail,
            max_delay,
            _errors_child(errors),
            _errors_child(except_errors),
        )
        self.given = given

    def _hooks(
        self, children: tuple[Callable, ...]
    ) -> tuple[Callable | None, Callable | None, Callable | None]:
        """Resolve ``(on_attempt_fail, on_success, on_fail)`` thunks; a hook not given reads None."""
        given = self.given
        oaf = children[5] if "on_attempt_fail" in given else None
        osc = children[6] if "on_success" in given else None
        ofl = children[7] if "on_fail" in given else None
        return oaf, osc, ofl

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[0]
        max_attempts_q = children[1]
        errors_t, excluded_t = children[9], children[10]

        def thunk(rt: Runtime) -> object:
            attempts = _attempts(max_attempts_q(rt))
            errors = _errors(errors_t(rt))
            excluded = _errors(excluded_t(rt))
            if attempts is None:
                msg = (
                    "Retry: max_attempts=None needs the async runtime, where retries "
                    "wait between attempts; use arun, or give a ceiling"
                )
                raise ValueError(msg)
            stream = rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM
            last: BaseException | None = None
            for _ in range(attempts):
                try:
                    if stream:
                        return iter(list(sync_iter(body(rt))))  # drain fresh per attempt
                    return body(rt)
                except Exception as exc:
                    if not _retries(exc, errors, excluded):
                        raise
                    last = exc
            raise last  # type: ignore[misc]  # attempts >= 1, so last is set

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body = children[0]
        max_attempts_q, delay_q, backoff_q, jitter_q = children[1:5]
        max_delay_q = children[8]
        oaf, osc, ofl = self._hooks(children)
        oaf_b, osc_b, ofl_b = self.hook_bindings
        errors_t, excluded_t = children[9], children[10]

        async def athunk(rt: Runtime) -> object:
            attempts = _attempts(await max_attempts_q(rt))
            errors = _errors(await errors_t(rt))
            excluded = _errors(await excluded_t(rt))
            waits = _waits(
                float(await delay_q(rt)),
                float(await backoff_q(rt)),
                float(await jitter_q(rt)),
                _max_delay(await max_delay_q(rt)),
            )
            tries = itertools.count(1) if attempts is None else range(1, attempts + 1)

            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                for attempt in tries:
                    try:
                        return aiter_any([v async for v in aiter_any(await body(rt))])
                    except Exception as exc:
                        if not _retries(exc, errors, excluded):
                            raise
                        if attempt == attempts:
                            raise
                    await asyncio.sleep(next(waits))
                return None  # unreachable: the last attempt returns or raises

            for attempt in tries:
                try:
                    result = await body(rt)
                    if osc is not None:
                        await _arun_hook(rt, osc, osc_b, (attempt,))
                    return result
                except Exception as exc:
                    if not _retries(exc, errors, excluded):
                        raise
                    if attempt == attempts:
                        if ofl is not None:
                            await _arun_hook(rt, ofl, ofl_b, (CaughtError(exc), attempt))
                            return None
                        raise
                    if oaf is not None:
                        await _arun_hook(rt, oaf, oaf_b, (CaughtError(exc), attempt))
                await asyncio.sleep(next(waits))
            return None  # unreachable: the last attempt returns or raises

        return athunk


def _retries(
    exc: Exception,
    errors: tuple[type[Exception], ...] | None,
    excluded: tuple[type[Exception], ...] | None,
) -> bool:
    """Whether Retry takes another attempt at ``exc``: matched by ``errors``, not by ``except_errors``."""
    if excluded is not None and isinstance(exc, excluded):
        return False
    return errors is None or isinstance(exc, errors)


def _attempts(value: object) -> int | None:
    """The attempt ceiling as the thunks read it: at least 1, or None for no ceiling."""
    return None if value is None else max(1, int(value))


def _max_delay(value: object) -> float | None:
    """The ``max_delay`` cap as the thunks read it.

    Raises:
        ValueError: a negative cap.
    """
    if value is None:
        return None
    cap = float(value)
    if cap < 0:
        msg = f"Retry: max_delay must not be negative, got {cap}"
        raise ValueError(msg)
    return cap


def _waits(delay: float, backoff: float, jitter: float, cap: float | None) -> Iterator[float]:
    """The waits between attempts: grown by ``backoff``, capped, then jittered.

    Jitter comes after the cap, so a wait held at ``cap`` still spreads
    around it and contending retriers do not fall into step there.
    """
    spread = max(0.0, min(1.0, jitter))
    while True:
        if cap is not None:
            delay = min(delay, cap)
        wait = delay
        if spread > 0.0 and wait > 0.0:
            wait *= 1.0 + random.uniform(-spread, spread)  # noqa: S311
        yield wait
        delay *= backoff


# === timing: async-only ====================================================


class Timeout(Policy):
    """Bounds the body by a wall-clock limit; runs ``on_timeout`` if it's hit.

    Async-only.

    Args:
        timeout: the wall-clock limit, in seconds.
        body: the bounded Term.
        on_timeout: runs against the live context if the limit is hit.
            Optional: left out, the timeout raises ``TimeoutError``; given,
            even a ``Noop``, it does not.

    Notes:
        - Hitting the limit cancels the body; a sync-only body offloaded to
          a thread can't be interrupted, so the limit stops the wait, not
          the thread itself.
        - A cancel from outside always propagates, even when it lands as
          the body finishes.

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
        self, timeout: FloatArg, body: Nu, on_timeout: Flow | Command | Span | Unset = UNSET
    ) -> None:
        super().__init__(body, timeout, _slot(on_timeout))
        self.given = frozenset() if on_timeout is UNSET else frozenset({"on_timeout"})

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _async_backstop("Timeout")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, timeout_q = children[0], children[1]
        on_timeout = children[2] if "on_timeout" in self.given else None

        async def athunk(rt: Runtime) -> object:
            timeout = float(await timeout_q(rt))
            # The body runs as a task of its own, not under ``asyncio.wait_for``:
            # before 3.12 that returns the body's value and drops a cancel
            # landing in the same step, and before 3.11 it raises an error
            # that is not ``TimeoutError``. It stays on ``rt``: this span is
            # transparent and only waits while the body runs.
            task = asyncio.ensure_future(body(rt))
            try:
                await asyncio.wait((task,), timeout=timeout)
            finally:
                await _settle((task,))
            if not task.cancelled():
                return task.result()
            if on_timeout is None:
                raise TimeoutError
            await on_timeout(rt)
            return None

        return athunk
