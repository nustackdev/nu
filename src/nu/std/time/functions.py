"""Module-level functions for ``nu.std.time`` - the function namespace.

``time`` has no central class, so this is the whole surface: typed wrappers that
mirror ``time.time`` / ``time.monotonic`` / ``time.sleep`` 1-1. Each wrapper
builds its interaction atom (lazily imported, like ``nu.std.math``) and returns
the Form that matches the host return type:

- clock reads in seconds (``time``, ``monotonic``, ``perf_counter``,
  ``process_time``) -> ``FloatForm``
- clock reads in nanoseconds (``time_ns``, ``monotonic_ns``, ``perf_counter_ns``)
  -> ``IntForm``
- ``sleep`` -> ``NoneForm`` (an effect-only ScalarQuery; it yields ``None``, it
  just blocks)

Every clock read is NON-DETERMINISTIC (it reads the clock), so its atom declares
``deterministic=False`` and must not be constant-folded. ``sleep`` is sync-only
and effect-only - see ``interactions``. The async sleep lives in
``nu.std.asyncio``.

Deferred (effectful / stateful, need the effect model first): ``strftime`` /
``strptime`` (pure, could be added), ``clock_settime`` / ``tzset`` (mutate global
clock state).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import FloatForm, IntForm, NoneForm


if TYPE_CHECKING:
    from nu.lang import FloatArg


__all__ = [
    "monotonic",
    "monotonic_ns",
    "perf_counter",
    "perf_counter_ns",
    "process_time",
    "sleep",
    "time",
    "time_ns",
]


# --- clock reads (float seconds) --------------------------------------------


def time() -> FloatForm:
    """Seconds since the epoch as a float: mirrors ``time.time()``. Non-deterministic."""
    from .interactions import TimeTime

    return FloatForm(TimeTime())


def monotonic() -> FloatForm:
    """A monotonic clock in seconds: mirrors ``time.monotonic()``. Non-deterministic."""
    from .interactions import TimeMonotonic

    return FloatForm(TimeMonotonic())


def perf_counter() -> FloatForm:
    """The highest-resolution timer in seconds: mirrors ``time.perf_counter()``. Non-deterministic."""
    from .interactions import TimePerfCounter

    return FloatForm(TimePerfCounter())


def process_time() -> FloatForm:
    """Process CPU time in seconds: mirrors ``time.process_time()``. Non-deterministic."""
    from .interactions import TimeProcessTime

    return FloatForm(TimeProcessTime())


# --- clock reads (int nanoseconds) ------------------------------------------


def time_ns() -> IntForm:
    """Nanoseconds since the epoch as an int: mirrors ``time.time_ns()``. Non-deterministic."""
    from .interactions import TimeTimeNs

    return IntForm(TimeTimeNs())


def monotonic_ns() -> IntForm:
    """A monotonic clock in nanoseconds: mirrors ``time.monotonic_ns()``. Non-deterministic."""
    from .interactions import TimeMonotonicNs

    return IntForm(TimeMonotonicNs())


def perf_counter_ns() -> IntForm:
    """The highest-resolution timer in nanoseconds: mirrors ``time.perf_counter_ns()``. Non-deterministic."""
    from .interactions import TimePerfCounterNs

    return IntForm(TimePerfCounterNs())


# --- blocking sleep ---------------------------------------------------------


def sleep(secs: FloatArg) -> NoneForm:
    """Block for ``secs`` seconds, yielding ``None``: mirrors ``time.sleep()``. Sync-only, effect-only."""
    from .interactions import TimeSleep

    return NoneForm(TimeSleep(secs))
