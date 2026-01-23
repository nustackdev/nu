"""Infrastructure Shape definitions for state management.

These Shapes provide type-safe, domain-specific access to flow infrastructure state
(cancellation, checkpoints, signals).
"""

from __future__ import annotations

import every.pv.slots as slots
from every._abc import Shape


__all__ = [
    "CancellationState",
    "CheckpointState",
    "FlowState",
    "FlowStepSate",
]


class CancellationState(Shape):
    """State for flow cancellation."""

    cancelled = slots.BoolSlot()
    reason = slots.StrSlot()
    timestamp = slots.FloatSlot()
    path = slots.StrSlot()


class CheckpointState(Shape):
    """State for flow checkpoints."""

    started = slots.BoolSlot()
    started_at = slots.FloatSlot()
    finished = slots.BoolSlot()
    finished_at = slots.FloatSlot()
    errored = slots.BoolSlot()
    error_message = slots.StrSlot()
    errored_at = slots.FloatSlot()


class FlowStepSate(Shape):
    """Combined state for a flow execution step."""

    checkpoint = slots.ShapeSlot(CheckpointState)
    cancellation = slots.ShapeSlot(CancellationState)
    # Step-local state
    attrs = slots.DictSlot(object)  # type: ignore
    # TODO: more flexible slot. ArbitrarySlot or AutoSlot (?)


class FlowAttrs(Shape):
    aitems = slots.DictSlot(object)  # type: ignore


class FlowState(Shape):
    """Combined state for a flow execution."""

    steps = slots.ShapesDictSlot(FlowStepSate)
    # Flow-local state
    attrs = slots.ShapesDictSlot(FlowAttrs)
    # TODO: more flexible slot. ArbitrarySlot or AutoSlot (?)
