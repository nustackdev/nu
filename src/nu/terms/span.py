"""Span - transparent Interaction sub-kind.

Wraps a body and forwards the body's yield in the same shape and
protocol. The Span atom is always a Span; parents slot-fit it by
looking through to the body. Sub-shapes: Bracket (lifecycle hooks
`before` / `after` / `after_failure`), Policy (re-run / fall back on
failure).

`body_slot` is a single int (deliberately distinct from
`Flow.Control.body_slots`, a tuple - two different concepts).

Span exposes the four-method API by delegating to its body and layering
Bracket / Policy hooks around the body's call. The body's yield-shape
decides which method is non-trivial; the others delegate naively.
"""

from __future__ import annotations

from typing import Any, ClassVar

from .interaction import Interaction
from .nu import NuBase, register_subclass_validator
from .types import Realization


__all__ = [
    "Bracket",
    "Policy",
    "Retry",
    "Snapshot",
    "Span",
    "Transaction",
    "TryCatch",
]


class Span(Interaction):
    """Abstract Span base. Concrete subclasses declare `body_slot`.

    Span is transparent: it wraps any Nu (Ref, Query, Command, Flow, or
    another Span) and forwards the body's yield in the same shape and
    protocol. The four-method API delegates to the body and layers
    Bracket or Policy hooks around it. Concrete Bracket / Policy
    subclasses override the `before` / `after` / `after_failure` /
    `around` hooks.
    """

    @property
    def realization(self) -> Realization:
        """Yield-shape forwarded from the body."""
        body = self._children[type(self).body_slot]  # type: ignore[attr-defined]
        body_real = getattr(type(body), "realization", None)
        if isinstance(body_real, Realization):
            return body_real
        # Body is itself a Span: walk through.
        if isinstance(body, Span):
            return body.realization
        msg = f"{type(self).__name__}: body has no realization"
        raise TypeError(msg)

    # --- delegated four-method API ----------------------------------------

    def _body(self) -> NuBase:
        return self._children[type(self).body_slot]  # type: ignore[attr-defined]

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        return self._dispatch_sync(ctx, "eval")

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        return await self._dispatch_async(ctx, "aeval")

    def open(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        return self._open_sync(ctx)

    def aopen(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        return self._open_async(ctx)

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        self._dispatch_sync(ctx, "run")

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        await self._dispatch_async(ctx, "arun")

    # --- private dispatch helpers -----------------------------------------

    def _dispatch_sync(self, ctx: Any, method: str) -> Any:  # noqa: ANN401
        body = self._body()
        fn = getattr(body, method)
        # Default Span: just delegate. Bracket / Policy override below.
        return fn(ctx)

    async def _dispatch_async(self, ctx: Any, method: str) -> Any:  # noqa: ANN401
        body = self._body()
        fn = getattr(body, method)
        return await fn(ctx)

    def _open_sync(self, ctx: Any) -> Any:  # noqa: ANN401
        yield from self._body().open(ctx)

    async def _open_async(self, ctx: Any) -> Any:  # noqa: ANN401
        async for v in self._body().aopen(ctx):
            yield v


# --- Bracket -----------------------------------------------------------------


class Bracket(Span):
    """Lifecycle Span. Hooks: before / after / after_failure.

    Subclasses override `before` to set up scoped state, `after` to
    commit on success, `after_failure` to clean up on failure. The
    body's method is wrapped: hooks fire around it.
    """

    def before(self, ctx: Any) -> Any:  # noqa: ANN401
        """Set up the bracket. Return the (possibly scoped) context."""
        return ctx

    def after(self, ctx: Any) -> None:  # noqa: ANN401
        """Clean up after successful execution."""
        return None

    def after_failure(self, ctx: Any, error: BaseException) -> None:  # noqa: ANN401
        """Clean up after a failure."""
        return None

    def _dispatch_sync(self, ctx: Any, method: str) -> Any:  # noqa: ANN401
        scoped = self.before(ctx)
        try:
            result = getattr(self._body(), method)(scoped)
        except BaseException as e:
            self.after_failure(scoped, e)
            raise
        self.after(scoped)
        return result

    async def _dispatch_async(self, ctx: Any, method: str) -> Any:  # noqa: ANN401
        scoped = self.before(ctx)
        try:
            result = await getattr(self._body(), method)(scoped)
        except BaseException as e:
            self.after_failure(scoped, e)
            raise
        self.after(scoped)
        return result

    def _open_sync(self, ctx: Any) -> Any:  # noqa: ANN401
        scoped = self.before(ctx)
        try:
            for v in self._body().open(scoped):
                yield v
        except BaseException as e:
            self.after_failure(scoped, e)
            raise
        self.after(scoped)

    async def _open_async(self, ctx: Any) -> Any:  # noqa: ANN401
        scoped = self.before(ctx)
        try:
            async for v in self._body().aopen(scoped):
                yield v
        except BaseException as e:
            self.after_failure(scoped, e)
            raise
        self.after(scoped)


class Snapshot(Bracket):
    """Snapshot the body's reads. No commit on success.

    Lightweight Bracket - in this simple shape the hooks are no-ops at
    the term level; concrete fabric-aware Snapshots subclass and
    override.
    """

    body_slot: ClassVar[int] = 0


class Transaction(Bracket):
    """Atomic body execution: commit on success, rollback on failure.

    Simple shape: `before` opens a transaction, `after` commits,
    `after_failure` rolls back. Concrete fabric-aware Transactions
    subclass and override these to talk to the actual store.
    """

    body_slot: ClassVar[int] = 0


# --- Policy ------------------------------------------------------------------


class Policy(Span):
    """Execution Policy. Mechanism: re-run, fall back on failure.

    Subclasses implement `around(ctx, call)` which receives a thunk that
    runs the body once. Default just calls the thunk. Concrete subclasses
    (Retry, TryCatch) wrap the thunk with retry / fallback logic.
    """

    def around(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401
        """Default: run the body once."""
        return call()

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401
        """Async default: run the body once."""
        return await call()

    def _dispatch_sync(self, ctx: Any, method: str) -> Any:  # noqa: ANN401
        def _call() -> Any:
            return getattr(self._body(), method)(ctx)

        return self.around(ctx, _call)

    async def _dispatch_async(self, ctx: Any, method: str) -> Any:  # noqa: ANN401
        async def _call() -> Any:
            return await getattr(self._body(), method)(ctx)

        return await self.aaround(ctx, _call)

    def _open_sync(self, ctx: Any) -> Any:  # noqa: ANN401
        # Policy applies to scalar/command paths; for streams we fall back to
        # a single attempt. Concrete Policies that need stream wrapping
        # override `_open_sync`.
        def _drain() -> list[Any]:
            return list(self._body().open(ctx))

        for v in self.around(ctx, _drain):
            yield v

    async def _open_async(self, ctx: Any) -> Any:  # noqa: ANN401
        async def _drain() -> list[Any]:
            return [v async for v in self._body().aopen(ctx)]

        for v in await self.aaround(ctx, _drain):
            yield v


class Retry(Policy):
    """`Retry(body, attempts_q)` - re-run body on failure up to N times.

    Simple shape: catch any exception, re-run up to `attempts` times
    total. Feature-rich variants (per-attempt callbacks, exponential
    backoff, exception filters) subclass `Retry` and override hooks.

    `attempts` is read from the second child slot if present (a Query
    yielding an int), else defaults to 3.
    """

    body_slot: ClassVar[int] = 0

    def _attempts(self, ctx: Any) -> int:  # noqa: ANN401
        if len(self._children) > 1:
            attempts_node = self._children[1]
            n = attempts_node.eval(ctx)
            return int(n) if n is not None else 3
        return 3

    async def _aattempts(self, ctx: Any) -> int:  # noqa: ANN401
        if len(self._children) > 1:
            attempts_node = self._children[1]
            n = await attempts_node.aeval(ctx)
            return int(n) if n is not None else 3
        return 3

    def around(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        n = self._attempts(ctx)
        last_error: BaseException | None = None
        for _ in range(max(1, n)):
            try:
                return call()
            except Exception as e:
                last_error = e
        if last_error is not None:
            raise last_error
        msg = "Retry: attempts <= 0"
        raise RuntimeError(msg)

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        n = await self._aattempts(ctx)
        last_error: BaseException | None = None
        for _ in range(max(1, n)):
            try:
                return await call()
            except Exception as e:
                last_error = e
        if last_error is not None:
            raise last_error
        msg = "Retry: attempts <= 0"
        raise RuntimeError(msg)


class TryCatch(Policy):
    """`TryCatch(body, fallback_body)` - run body; on failure run fallback.

    Simple shape: catches any exception from the body and runs the
    fallback once. Feature-rich variants (typed exception filters,
    exception-bound rebinding) subclass.
    """

    body_slot: ClassVar[int] = 0

    def around(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        try:
            return call()
        except Exception:
            if len(self._children) > 1:
                fb = self._children[1]
                # Run fallback in scalar/command position - use eval if it
                # yields a value, run if it's a Command.
                fn = getattr(fb, "eval", None) or getattr(fb, "run", None)
                if fn is not None:
                    return fn(ctx)
            raise

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401, D102
        try:
            return await call()
        except Exception:
            if len(self._children) > 1:
                fb = self._children[1]
                fn = getattr(fb, "aeval", None) or getattr(fb, "arun", None)
                if fn is not None:
                    return await fn(ctx)
            raise


# --- subclass validator ------------------------------------------------------


def _validate_span(cls: type) -> None:
    """Concrete Span subclasses declare `body_slot`."""
    if cls in (Bracket, Policy):
        return
    # Abstract intermediate (no body_slot, no concrete children) - skip.
    if "body_slot" not in cls.__dict__:
        # Allow purely abstract intermediates; concrete leaves will be checked
        # by their own __init_subclass__ trip.
        # A concrete kind without body_slot is invalid.
        # Heuristic: if the class declares `__abstractmethods__` non-empty,
        # treat as abstract.
        if getattr(cls, "__abstractmethods__", frozenset()):
            return
        # Concrete: require body_slot.
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: Span subclasses must "
            "declare `body_slot` (a single int)."
        )
        raise TypeError(msg)
    if not isinstance(cls.__dict__["body_slot"], int):
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: `body_slot` must be a "
            f"single int (got {cls.__dict__['body_slot']!r}). Use "
            "`body_slots` (tuple) on Flow.Control instead."
        )
        raise TypeError(msg)


register_subclass_validator(Span, _validate_span)


# --- composition validator: Span has body -----------------------------------


def _validate_span_has_body(nu: Any) -> None:  # noqa: ANN401
    """A Span instance must have a child at its declared `body_slot`."""
    if not isinstance(nu, Span):
        return
    body_slot = getattr(type(nu), "body_slot", None)
    if body_slot is None:
        return
    if body_slot >= len(nu._children):
        msg = (
            f"{type(nu).__name__}: Span has no body (body_slot={body_slot}, "
            f"got {len(nu._children)} children)."
        )
        raise TypeError(msg)


from .nu import register_composition_validator as _register_comp  # noqa: E402


_register_comp(_validate_span_has_body)
