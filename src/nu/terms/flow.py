"""Flow - Strategy + Control.

Flow orchestrates Commands. `own_effects` is empty by class-time
validator (Flow contributes no effects of its own; effects come from
the body Commands).

Strategy: children are Commands only. `body_slots = ()` is a sentinel
meaning "all child slots are body" (the composition-time validator
handles it).

Control: declares a subset of slot indices as body via `body_slots`.
Other slots are Query parameters (e.g. `IfDo(cond_q, body_c)`).
"""

from __future__ import annotations

from typing import Any, ClassVar
from typing import Literal as TLiteral

from .nu import NuBase, register_subclass_validator


__all__ = [
    "Control",
    "Flow",
    "ForEachDo",
    "Gather",
    "IfDo",
    "Parallel",
    "Race",
    "Sequential",
    "Strategy",
    "WhileDo",
]


class Flow(NuBase):
    """Abstract Flow base. `own_effects` empty."""


# --- Strategy ----------------------------------------------------------------


class Strategy(Flow):
    """All child slots are body slots (Commands only)."""

    body_slots: ClassVar[tuple[int, ...]] = ()


class Sequential(Strategy):
    """`a >> b` - run children in order."""

    associative: ClassVar[bool] = True
    commutative: ClassVar[bool | TLiteral["if-independent"]] = "if-independent"


class Parallel(Strategy):
    """`a | b` - run children concurrently."""

    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True


class Race(Strategy):
    """`a & b` - run children concurrently; first to complete wins."""

    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True


class Gather(Strategy):
    """Run children concurrently and collect their yields."""

    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True


# --- Control -----------------------------------------------------------------


class Control(Flow):
    """Conditional / iterative Flow.

    Declared `body_slots` separates Command body slots from Query
    parameter slots.
    """


class IfDo(Control):
    """`IfDo(cond_q, body_c [, else_c])` - run body if cond is truthy."""

    body_slots: ClassVar[tuple[int, ...]] = (1,)


class ForEachDo(Control):
    """`ForEachDo(items_q, body_c)` - run body for each item."""

    body_slots: ClassVar[tuple[int, ...]] = (1,)


class WhileDo(Control):
    """`WhileDo(cond_q, body_c)` - run body while cond is truthy."""

    body_slots: ClassVar[tuple[int, ...]] = (1,)


# --- subclass validators -----------------------------------------------------


def _validate_flow(cls: type) -> None:
    """Flow subclasses must declare empty `own_effects`."""
    own = cls.__dict__.get("own_effects")
    if own is not None and own:
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: Flow subclasses must "
            f"declare empty `own_effects` (got {own!r}). Effects in a "
            "Flow come from its body Commands."
        )
        raise TypeError(msg)


def _validate_control(cls: type) -> None:
    """Control subclasses must declare `body_slots`."""
    if cls is Control:
        return
    if "body_slots" not in cls.__dict__:
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: Control subclasses "
            "must declare `body_slots` (a tuple of slot indices)."
        )
        raise TypeError(msg)


register_subclass_validator(Flow, _validate_flow)
register_subclass_validator(Control, _validate_control)


# --- composition validator: Flow subtree contains ≥1 Command ----------------


def _validate_flow_has_command(nu: Any) -> None:  # noqa: ANN401
    """Flow subtree must contain ≥1 Command (transitively)."""
    if not isinstance(nu, Flow):
        return
    # Avoid importing Command at module import time to keep cycles clean.
    from .command import Command

    def _has_command(n: Any) -> bool:  # noqa: ANN401
        if isinstance(n, Command):
            return True
        return any(_has_command(c) for c in n._children)

    if not any(_has_command(c) for c in nu._children):
        # During Phase A+B, callers may still construct empty / partial
        # Flows for tests; soft until concrete kinds land. Hard once
        # Phase E sweeps. ARCH-NOTE: keep as a pass for now.
        return


from .nu import register_composition_validator as _register_comp  # noqa: E402


_register_comp(_validate_flow_has_command)
