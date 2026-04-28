"""Span - transparent execution span around a body.

Role and realization inherited from `body_slot`. Bracket: lifecycle
hooks (`before` / `after` / `after_failure`). Policy: re-run / fall
back on failure.

`body_slot` is a single int (deliberately distinct from
`Flow.Control.body_slots`, a tuple - two different concepts).
"""

from __future__ import annotations

from typing import Any, ClassVar

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


class Span(NuBase):
    """Abstract Span base. Concrete subclasses declare `body_slot`."""

    @property
    def realization(self) -> Realization:
        """Span realization recurses into the body."""
        body = self._children[type(self).body_slot]  # type: ignore[attr-defined]
        body_real = getattr(type(body), "realization", None)
        if isinstance(body_real, Realization):
            return body_real
        # Body is itself a Span: walk through.
        if isinstance(body, Span):
            return body.realization
        msg = f"{type(self).__name__}: body has no realization"
        raise TypeError(msg)


# --- Bracket -----------------------------------------------------------------


class Bracket(Span):
    """Lifecycle Span. Hooks: before / after / after_failure."""

    def before(self, ctx: Any) -> Any:  # noqa: ANN401
        """Set up the bracket. Return the (possibly scoped) context."""
        return ctx

    def after(self, ctx: Any) -> None:  # noqa: ANN401
        """Clean up after successful execution."""
        return None

    def after_failure(self, ctx: Any, error: BaseException) -> None:  # noqa: ANN401
        """Clean up after a failure."""
        return None


class Snapshot(Bracket):
    """Snapshot the body's reads. No commit on success."""

    body_slot: ClassVar[int] = 0


class Transaction(Bracket):
    """Atomic body execution: commit on success, rollback on failure."""

    body_slot: ClassVar[int] = 0


# --- Policy ------------------------------------------------------------------


class Policy(Span):
    """Execution Policy. Mechanism: re-run, fall back on failure."""


class Retry(Policy):
    """`Retry(body, attempts_q)` - re-run body on failure up to `attempts_q` times."""

    body_slot: ClassVar[int] = 0


class TryCatch(Policy):
    """`TryCatch(body, fallback_body)` - run body; on failure run fallback."""

    body_slot: ClassVar[int] = 0


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
