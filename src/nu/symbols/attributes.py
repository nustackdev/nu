"""Nu's attributes: the engine Schema that compiles a Nu description.

Every Nu concern lands as an attribute. Declared attributes (sort, effects,
support) are constants on the kinds. The computed attributes below fold or
thread those constants into the analyses Nu cares about: effect tracking,
purity, realization, and execution mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Attribute, Schema
from nu.symbols.sorts import Effect, Mode


if TYPE_CHECKING:
    from nu.engine import Program
    from nu.engine.program import Path

__all__ = ["build_schema"]

type EffectSet = frozenset[tuple[str, Effect]]


# --- effects -------------------------------------------------------------


def _own_effects(program: Program, path: Path) -> EffectSet:
    """The (ref, effect) tuples a node contributes through its own Refs.

    Class-time: each ``own_effects`` slot holding a Ref. Composition-time:
    every other slot holding a Ref binds in read role.
    """
    declared: dict[int, Effect] = program.attr(path, "own_effects")
    kids = program.children(path)
    out: set[tuple[str, Effect]] = set()
    for slot, effect in declared.items():
        if slot < len(kids) and program.attr(kids[slot], "sort") == "Ref":
            out.add((program.payload(kids[slot])["name"], effect))
    for slot, child in enumerate(kids):
        if slot not in declared and program.attr(child, "sort") == "Ref":
            out.add((program.payload(child)["name"], Effect.READ))
    return frozenset(out)


def _union(own: object, kids: list[object]) -> EffectSet:
    """Fold a subtree's tracked effects: own contribution plus children's."""
    result: EffectSet = frozenset(own)  # type: ignore[arg-type]
    for kid in kids:
        result |= frozenset(kid)  # type: ignore[arg-type]
    return result


def _pure_base(program: Program, path: Path) -> bool:
    """A node is locally pure when its subtree tracks no effects."""
    return not program.attr(path, "tracked_effects")


def _pure_combine(own: object, kids: list[object]) -> bool:
    """Purity folds: a node is pure when it and all children are pure."""
    return bool(own) and all(kids)


# --- realization ---------------------------------------------------------


def _realization_base(program: Program, path: Path) -> str:
    """A node's own realization, declared by its kind."""
    return program.attr(path, "realization")


def _resolve_realization(own: object, kids: list[object]) -> str:
    """Resolve realization: a Span forwards its body's; every kind is fixed."""
    if own == "body":
        return str(kids[0]) if kids else "none"
    return str(own)


# --- execution mode ------------------------------------------------------


def _async_only(program: Program, path: Path) -> bool:
    """True when a node's kind requires an event loop."""
    support: frozenset[Mode] = program.attr(path, "support")
    return Mode.ASYNC in support and Mode.SYNC not in support


def _sync_only(program: Program, path: Path) -> bool:
    """True when a node's kind belongs in a sync context only."""
    support: frozenset[Mode] = program.attr(path, "support")
    return Mode.SYNC in support and Mode.ASYNC not in support


def _any(own: object, kids: list[object]) -> bool:
    """Fold a flag up a subtree by disjunction."""
    return bool(own) or any(kids)


def _exec_root(program: Program, path: Path) -> str:
    """The root runs on a loop iff its subtree holds an async-only atom."""
    return "loop" if program.attr(path, "needs_loop") else "no_loop"


def _exec_derive(program: Program, parent: Path, slot: int, up: str) -> str:
    """Thread exec_state down; resolve per-child at a concurrent parent.

    At a concurrent Flow each child resolves on its own subtree: an
    async-only child goes on the loop, a sync-only child goes off it, and a
    fully-portable child inherits the parent's state.
    """
    if not program.attr(parent, "concurrent"):
        return up
    child = (*parent, slot)
    if program.attr(child, "needs_loop"):
        return "loop"
    if program.attr(child, "has_sync_only"):
        return "no_loop"
    return up


def build_schema() -> Schema:
    """Build and finalize the Nu schema: declared defaults plus the folds."""
    schema = Schema()

    schema.register(Attribute.declared({}, name="own_effects"))
    schema.register(Attribute.declared(frozenset({Mode.SYNC, Mode.ASYNC}), name="support"))
    schema.register(Attribute.declared(False, name="is_reduction"))
    schema.register(Attribute.declared(False, name="concurrent"))

    schema.register(
        Attribute.synthesized(
            "tracked_effects",
            base=_own_effects,
            combine=_union,
            reads=("own_effects", "sort"),
        )
    )
    schema.register(
        Attribute.synthesized(
            "is_pure",
            base=_pure_base,
            combine=_pure_combine,
            reads=("tracked_effects",),
        )
    )
    schema.register(
        Attribute.synthesized(
            "realization_eff",
            base=_realization_base,
            combine=_resolve_realization,
            reads=("realization",),
        )
    )
    schema.register(
        Attribute.synthesized(
            "needs_loop",
            base=_async_only,
            combine=_any,
            reads=("support",),
        )
    )
    schema.register(
        Attribute.synthesized(
            "has_sync_only",
            base=_sync_only,
            combine=_any,
            reads=("support",),
        )
    )
    schema.register(
        Attribute.inherited(
            "exec_state",
            root=_exec_root,
            derive=_exec_derive,
            reads=("needs_loop", "has_sync_only"),
        )
    )

    return schema.finalize()
