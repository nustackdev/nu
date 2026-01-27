"""Executor — tree walker with context resolution.

Implements:
    S1: Implicit grouping (Flow→Term = implicit Atomic)
    B1-B4: Resolution (needs propagation, nearest Group, ephemeral fallback, innermost wins)
    C1-C2: Lazy lifetime (open on first touch, close after last use)
    C3: Context inference (Atomic picks Snapshot vs Transaction)
"""

from __future__ import annotations

from typing import Any

from .context import (
    Context,
    ContextMap,
    KVContext,
    Substrate,
    SubstrateMap,
)
from .lang import (
    Atomic,
    Cond,
    Flow,
    Group,
    GroupedContext,
    Par,
    RootGroup,
    Seq,
    Term,
    Unit,
)


def execute(unit: Unit) -> Any:
    """Execute a unit tree. Entry point.

    Handles RootGroup setup, then delegates to _execute_unit.
    """
    if isinstance(unit, RootGroup):
        return _execute_root(unit)

    # No RootGroup — execute directly with empty context
    return _execute_unit(unit, ctx={}, substrates={})


def _execute_root(root: RootGroup) -> Any:
    """Execute a RootGroup: set up substrates, run child, clean up."""
    substrates: SubstrateMap = dict(root.substrates)
    ctx: ContextMap = {}
    try:
        return _execute_unit(root.child, ctx=ctx, substrates=substrates)
    finally:
        # Substrates are long-lived; in a real impl they'd have lifecycle
        pass


def _execute_unit(
    unit: Unit,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> Any:
    """Execute a single unit with context resolution."""
    if isinstance(unit, RootGroup):
        return _execute_root(unit)
    if isinstance(unit, (Atomic, GroupedContext)):
        return _execute_group(unit, ctx, substrates)
    if isinstance(unit, Flow):
        return _execute_flow(unit, ctx, substrates)
    if isinstance(unit, Term):
        return _execute_term(unit, ctx, substrates)
    if isinstance(unit, Group):
        return _execute_group(unit, ctx, substrates)

    msg = f"Unknown unit type: {type(unit)}"
    raise TypeError(msg)


# =============================================================================
# Flow execution — applies implicit grouping (S1)
# =============================================================================


def _execute_flow(
    flow: Flow,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> Any:
    """Execute a Flow, applying implicit grouping (S1).

    Every direct Term child of a Flow is implicitly wrapped in Atomic.
    """
    if isinstance(flow, Seq):
        return _execute_seq(flow, ctx, substrates)
    if isinstance(flow, Par):
        return _execute_par(flow, ctx, substrates)
    if isinstance(flow, Cond):
        return _execute_cond(flow, ctx, substrates)

    msg = f"Unknown flow type: {type(flow)}"
    raise TypeError(msg)


def _execute_seq(
    seq: Seq,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> Any:
    """Execute Seq with implicit grouping."""
    result = None
    for child in seq.children():
        wrapped = _maybe_implicit_group(child)
        result = _execute_unit(wrapped, ctx, substrates)
    return result


def _execute_par(
    par: Par,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> tuple[Any, ...]:
    """Execute Par with implicit grouping (sequential for PoC)."""
    results = []
    for child in par.children():
        wrapped = _maybe_implicit_group(child)
        results.append(_execute_unit(wrapped, ctx, substrates))
    return tuple(results)


def _execute_cond(
    cond: Cond,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> Any:
    """Execute Cond — predicate in its own Atomic, branches too."""
    pred_wrapped = _maybe_implicit_group(cond.pred)
    pred_val = _execute_unit(pred_wrapped, ctx, substrates)

    if pred_val:
        branch = _maybe_implicit_group(cond.then)
    else:
        branch = _maybe_implicit_group(cond.else_)

    return _execute_unit(branch, ctx, substrates)


def _maybe_implicit_group(unit: Unit) -> Unit:
    """S1: Wrap direct Term child of Flow in Atomic.

    If already a Flow or Group, leave as-is.
    """
    if isinstance(unit, Term) and not isinstance(unit, Group):
        return Atomic(unit)
    return unit


# =============================================================================
# Group execution — context lifecycle
# =============================================================================


def _execute_group(
    group: Group,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> Any:
    """Execute a Group: create context, run children, release."""
    if isinstance(group, Atomic):
        return _execute_atomic(group, ctx, substrates)
    if isinstance(group, GroupedContext):
        return _execute_grouped_context(group, ctx, substrates)

    # Generic group fallback
    result = None
    for child in group.children():
        result = _execute_unit(child, ctx, substrates)
    return result


def _execute_atomic(
    atomic: Atomic,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> Any:
    """Execute Atomic with inferred context type (C3)."""
    ctx_type = atomic.infer_context_type()

    if ctx_type is None:
        # No KV needs — just run children directly
        result = None
        for child in atomic.children():
            result = _execute_unit(child, ctx, substrates)
        return result

    # Create context from substrate (lazy open C1)
    substrate = _find_substrate(ctx_type, substrates)
    new_ctx = substrate.create(ctx_type)

    # Extend context map (B4: innermost wins)
    extended_ctx = dict(ctx)
    extended_ctx[ctx_type] = new_ctx
    # Also register under KVContext so Get can find it
    if issubclass(ctx_type, KVContext):
        extended_ctx[KVContext] = new_ctx

    try:
        result = None
        for child in atomic.children():
            result = _execute_unit(child, extended_ctx, substrates)
        return result
    finally:
        # Eager close (C2)
        new_ctx.release()


def _execute_grouped_context(
    group: GroupedContext,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> Any:
    """Execute GroupedContext with explicit context type."""
    ctx_type = group.ctx_type

    substrate = _find_substrate(ctx_type, substrates)
    new_ctx = substrate.create(ctx_type)

    extended_ctx = dict(ctx)
    extended_ctx[ctx_type] = new_ctx
    if issubclass(ctx_type, KVContext):
        extended_ctx[KVContext] = new_ctx

    try:
        result = None
        for child in group.children():
            result = _execute_unit(child, extended_ctx, substrates)
        return result
    finally:
        new_ctx.release()


def _find_substrate(
    ctx_type: type[Context],
    substrates: SubstrateMap,
) -> Substrate:
    """Find a substrate that can create the given context type.

    Walks the type hierarchy: if Transaction requested and KVContext registered,
    the KVContext substrate is used.
    """
    # Direct match
    if ctx_type in substrates:
        sub = substrates[ctx_type]
        if isinstance(sub, Substrate):
            return sub

    # Walk MRO for subtype match
    for base in ctx_type.__mro__:
        if base in substrates:
            sub = substrates[base]
            if isinstance(sub, Substrate):
                return sub

    msg = f"No substrate found for {ctx_type.__name__}"
    raise RuntimeError(msg)


# =============================================================================
# Term execution — direct run with current context
# =============================================================================


def _execute_term(
    term: Term,
    ctx: ContextMap,
    substrates: SubstrateMap,
) -> Any:
    """Execute a Term directly with current context.

    Terms inside a Group already have their context.
    Terms outside a Group get ephemeral context (B3) — but in practice,
    the implicit grouping (S1) ensures Terms under Flows are always
    in an Atomic group. Bare term execution is for isolated calls.
    """
    # Check if term needs context it doesn't have
    term_needs = term.needs()
    missing = {n for n in term_needs if not _ctx_satisfies(ctx, n)}

    if missing:
        # B3: Ephemeral fallback — create temporary context
        return _execute_with_ephemeral(term, ctx, substrates, missing)

    return term.run(ctx)


def _ctx_satisfies(ctx: ContextMap, need: type[Context]) -> bool:
    """Check if context map satisfies a need (including subtypes)."""
    if need in ctx:
        return True
    # Check if any context in the map is a subtype of the need
    for ctx_type in ctx:
        if issubclass(ctx_type, need):
            return True
    return False


def _execute_with_ephemeral(
    term: Term,
    ctx: ContextMap,
    substrates: SubstrateMap,
    missing: set[type[Context]],
) -> Any:
    """Create ephemeral contexts for missing needs, execute, release."""
    extended_ctx = dict(ctx)
    created: list[Context] = []

    for need in missing:
        substrate = _find_substrate(need, substrates)
        # For ephemeral, use cheapest context
        new_ctx = substrate.create(need)
        extended_ctx[need] = new_ctx
        created.append(new_ctx)

    try:
        return term.run(extended_ctx)
    finally:
        for c in reversed(created):
            c.release()
