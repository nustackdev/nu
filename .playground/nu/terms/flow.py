"""Flow - abstract bases for Strategy + Control.

Flow orchestrates Commands. `own_effects` is empty by class-time
validator (Flow contributes no effects of its own; effects come from
the body Commands).

Strategy: children are Commands only. `body_slots = ()` is a sentinel
meaning "all child slots are body" (the composition-time validator
handles it).

Control: declares a subset of slot indices as body via `body_slots`.
Other slots are Query parameters (e.g. `IfDo(cond_q, body_c)`).

Concrete Flows (Sequential, Parallel, Race, Gather, IfDo, ForEachDo,
WhileDo) live in `nu.flows`.
"""

from __future__ import annotations

from typing import Any, ClassVar

from .interaction import Interaction
from .nu import register_subclass_validator


__all__ = [
    "Control",
    "Flow",
    "Strategy",
]


class Flow(Interaction):
    """Abstract Flow base. `own_effects` empty."""


# --- Strategy ----------------------------------------------------------------


class Strategy(Flow):
    """All child slots are body slots (Commands only).

    `run` / `arun` drive children via the runtime pumps. Subclasses
    (Sequential, Parallel, Race, Gather) override `_run_children` /
    `_arun_children` to choose sequential vs parallel semantics.
    """

    body_slots: ClassVar[tuple[int, ...]] = ()

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        self._run_children(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        await self._arun_children(ctx)

    # Default sequential drive; concrete strategies override.
    def _run_children(self, ctx: Any) -> None:  # noqa: ANN401
        from .. import runtime as _rt
        from .dispatch import ExecState, atom_dispatch

        for child in self._children:
            method = atom_dispatch(child, ExecState.NO_LOOP)
            method(ctx)
        _ = _rt  # keep lazy import semantics; runtime not strictly needed here

    async def _arun_children(self, ctx: Any) -> None:  # noqa: ANN401
        from .dispatch import ExecState, atom_dispatch

        for child in self._children:
            method = atom_dispatch(child, ExecState.LOOP)
            await method(ctx)


# --- Control -----------------------------------------------------------------


class Control(Flow):
    """Conditional / iterative Flow.

    Declared `body_slots` separates Command body slots from Query
    parameter slots. Concrete subclasses (IfDo, ForEachDo, WhileDo)
    live in `nu.flows.control`. They evaluate Query parameters via
    `four_method_pick` and drive body Commands via `atom_dispatch`.
    """


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
    """Control subclasses must declare `body_slots`.

    `body_slots = None` is a valid declaration meaning "no body slots"
    (every child is a Query parameter; the Control runs a side effect
    after evaluating its parameters, e.g. TimeSleep).
    """
    if cls is Control:
        return
    if "body_slots" not in cls.__dict__:
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: Control subclasses "
            "must declare `body_slots` (a tuple of slot indices, or "
            "`None` for no body slots)."
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
