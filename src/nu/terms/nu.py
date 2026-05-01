"""NuBase - the algebraic primitive.

A Nu is a Γ-transformer. The kind hierarchy below is the programming-model
presentation; the algebra sees only `_children` and the validators
registered at import time.

`__init_subclass__` and `__init__` iterate two registries:

- `_INIT_SUBCLASS_VALIDATORS` - per-class declaration checks
  (`{base: fn}`, fired when a concrete subclass of `base` is defined).
- `_COMPOSITION_VALIDATORS` - per-instance composition checks
  (list of fns, fired in `__init__` after `_children` is assigned).

`nu.py` does NOT import from kind modules or algebra modules. Each kind /
algebra module pushes into the registry at import time. Dependency
direction is one-way; no cycles.

See task-083 architecture.md.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Self,
)


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from .protocol import Nu
    from .types import Effect


__all__ = [
    "NuBase",
    "register_composition_validator",
    "register_subclass_validator",
    "walk",
]


_COMPOSITION_VALIDATORS: list[Callable[[Nu], None]] = []
_INIT_SUBCLASS_VALIDATORS: dict[type, list[Callable[[type], None]]] = {}


def register_composition_validator(fn: Callable[[Nu], None]) -> None:
    """Push a per-instance check. Fired in `NuBase.__init__`."""
    _COMPOSITION_VALIDATORS.append(fn)


def register_subclass_validator(base: type, fn: Callable[[type], None]) -> None:
    """Push a per-class check, keyed on a base class.

    Fired when a concrete subclass of `base` is defined. Multiple hooks
    per base run in registration order.
    """
    _INIT_SUBCLASS_VALIDATORS.setdefault(base, []).append(fn)


class NuBase:
    """The algebraic primitive. Every kind class subclasses this.

    Two declared fields drive the slot trichotomy:

    - `own_effects` - dict of `slot_idx -> Effect | frozenset[Effect]`.
      Slots keyed here are Ref-only; the kind contributes the named
      directional effect through this Ref.
    - `body_slots` (Flow Control) or `body_slot` (Span) - declared on
      those subclasses, NOT here. Body slots accept Command / Flow / Span.

    Every other slot is a Query slot.
    """

    own_effects: ClassVar[Mapping[int, Effect | frozenset[Effect]]] = {}

    _children: tuple[Nu, ...]

    def __init__(self, *children: Any) -> None:  # noqa: ANN401
        # Auto-wrap any non-NuBase child as Literal. Ergonomic, not legacy:
        # `Add(7, 3)` becomes `Add(Literal(7), Literal(3))`.
        wrapped: list[NuBase] = []
        for c in children:
            if isinstance(c, NuBase):
                wrapped.append(c)
            else:
                from ..queries.literal import Literal

                wrapped.append(Literal(c))
        self._children = tuple(wrapped)  # type: ignore[assignment]
        for validator in _COMPOSITION_VALIDATORS:
            validator(self)  # type: ignore[arg-type]

    def _with_children(self, children: tuple[Nu, ...]) -> Self:
        import copy

        new = copy.copy(self)
        new._children = children
        for validator in _COMPOSITION_VALIDATORS:
            validator(new)  # type: ignore[arg-type]
        return new

    def __rshift__(self, other: Nu) -> Nu:
        from ..flows.strategy import Sequential

        return Sequential(self, other)  # type: ignore[arg-type]

    def __or__(self, other: Nu) -> Nu:
        from ..flows.strategy import Parallel

        return Parallel(self, other)  # type: ignore[arg-type]

    def __and__(self, other: Nu) -> Nu:
        from ..flows.strategy import Race

        return Race(self, other)  # type: ignore[arg-type]

    def eq(self, other: Nu) -> bool:
        """Structural tree equality. Compares class + children recursively."""
        raise NotImplementedError

    def __init_subclass__(cls, **kw: Any) -> None:  # noqa: ANN401
        super().__init_subclass__(**kw)
        for base, validators in _INIT_SUBCLASS_VALIDATORS.items():
            if issubclass(cls, base) and cls is not base:
                for validator in validators:
                    validator(cls)


def walk(nu: Nu) -> Iterator[Nu]:
    """Depth-first traversal. Yields `nu` then recurses into children.

    Reused by `effects`, `algebra`, `dispatch`. Pure structural - reads
    only `_children`.
    """
    yield nu
    for child in nu._children:
        yield from walk(child)


# --- slot trichotomy + composition matrix validator -------------------------
#
# Two declared fields generate three exclusive slot kinds:
#   1. Ref-only slot - keyed in `own_effects`. Holds a Ref.
#   2. Body slot - keyed in `body_slots` (Control) or matched by
#      `body_slot` (Span). Holds Command / Flow / Span.
#   3. Query slot - everything else. Holds Query / Ref / Span.
#
# Composition matrix from projects/nu/model/02-atoms/00-map.md is per
# parent-kind / child-kind. Encoded below as `_MATRIX`.


def _slot_kinds(nu: Nu) -> tuple[frozenset[int], frozenset[int]]:
    """(ref_only_slots, body_slots) for this instance.

    Strategy with `body_slots = ()` means "all child slots are body".
    """
    cls = type(nu)
    own = getattr(cls, "own_effects", {}) or {}
    ref_only = frozenset(own.keys())
    body_slots = getattr(cls, "body_slots", None)
    if body_slots is not None:
        if body_slots == ():
            body = frozenset(range(len(nu._children)))
        else:
            body = frozenset(body_slots)
    else:
        body_slot = getattr(cls, "body_slot", None)
        body = frozenset({body_slot}) if body_slot is not None else frozenset()
    return ref_only, body


def _kind_label(child: Any) -> str:  # noqa: ANN401
    """Short label for the composition matrix lookup. None if unknown."""
    # Lazy imports - kind modules import nu.py, so we can't import them
    # at module-import time.
    from .command import ScalarCommand
    from .flow import Control, Strategy
    from .query import ScalarQuery, StreamQuery
    from .ref import Ref
    from .span import Bracket, Policy

    if isinstance(child, Ref):
        return "Ref"
    if isinstance(child, ScalarQuery):
        return "ScalarQ"
    if isinstance(child, StreamQuery):
        return "StreamQ"
    if isinstance(child, ScalarCommand):
        return "ScalarC"
    if isinstance(child, Strategy):
        return "Strategy"
    if isinstance(child, Control):
        return "Control"
    if isinstance(child, Bracket):
        return "Bracket"
    if isinstance(child, Policy):
        return "Policy"
    return ""


# Composition matrix: rows are parents, columns are children.
# True = accepted, False = rejected. Mirrors model/02-atoms/00-map.md.
_MATRIX: dict[str, dict[str, bool]] = {
    "Ref": {
        "Ref": True,
        "ScalarQ": True,
        "StreamQ": True,
        "ScalarC": False,
        "Strategy": False,
        "Control": False,
        "Bracket": True,
        "Policy": True,
    },
    "ScalarQ": {
        "Ref": True,
        "ScalarQ": True,
        "StreamQ": True,
        "ScalarC": False,
        "Strategy": False,
        "Control": False,
        "Bracket": True,
        "Policy": True,
    },
    "StreamQ": {
        "Ref": True,
        "ScalarQ": True,
        "StreamQ": True,
        "ScalarC": False,
        "Strategy": False,
        "Control": False,
        "Bracket": True,
        "Policy": True,
    },
    "ScalarC": {
        "Ref": True,
        "ScalarQ": True,
        "StreamQ": True,
        "ScalarC": False,
        "Strategy": False,
        "Control": False,
        "Bracket": True,
        "Policy": True,
    },
    "Strategy": {
        "Ref": False,
        "ScalarQ": False,
        "StreamQ": False,
        "ScalarC": True,
        "Strategy": True,
        "Control": True,
        "Bracket": True,
        "Policy": True,
    },
    "Control": {
        "Ref": True,
        "ScalarQ": True,
        "StreamQ": True,
        "ScalarC": True,
        "Strategy": True,
        "Control": True,
        "Bracket": True,
        "Policy": True,
    },
    "Bracket": {
        "Ref": True,
        "ScalarQ": True,
        "StreamQ": True,
        "ScalarC": True,
        "Strategy": True,
        "Control": True,
        "Bracket": True,
        "Policy": True,
    },
    "Policy": {
        "Ref": True,
        "ScalarQ": True,
        "StreamQ": True,
        "ScalarC": True,
        "Strategy": True,
        "Control": True,
        "Bracket": True,
        "Policy": True,
    },
}


def _validate_slot_trichotomy(nu: Nu) -> None:
    """Per-instance slot trichotomy and composition-matrix check.

    1. `own_effects` keys ∩ body_slot indices = ∅ (disjointness).
    2. Ref-only slots receive Refs.
    3. Body slots receive Command / Flow / Span.
    4. Query slots receive Query / Ref / Span.
    5. Parent-kind / child-kind allowed by the composition matrix.

    Non-NuBase children are skipped (e.g. raw values that haven't been
    wrapped, though `NuBase.__init__` auto-wraps via `Literal`).
    """
    # Lazy imports - avoid cycle.
    from .command import Command
    from .flow import Flow
    from .ref import Ref
    from .span import Span as _Span

    cls = type(nu)
    ref_only, body = _slot_kinds(nu)

    # 1. disjointness.
    overlap = ref_only & body
    if overlap:
        msg = (
            f"{cls.__name__}: slots {sorted(overlap)} appear in both "
            "`own_effects` and body slots. The slot trichotomy requires "
            "them disjoint."
        )
        raise TypeError(msg)

    parent_label = _kind_label(nu)

    for slot_idx, child in enumerate(nu._children):
        # Skip non-NuBase children (legacy / wrapped values).
        if not isinstance(child, NuBase):
            continue

        # 2. Ref-only slots.
        if slot_idx in ref_only:
            if not isinstance(child, Ref):
                msg = (
                    f"{cls.__name__}.slot[{slot_idx}] is a Ref-only slot "
                    f"(declared in own_effects); got "
                    f"{type(child).__name__}."
                )
                raise TypeError(msg)
            continue

        # 3. Body slots.
        if slot_idx in body:
            # Span's body_slot is transparent: it inherits role from its body
            # so any Nu kind is acceptable. Strategy/Control's body_slots are
            # strict: Command / Flow / Span only.
            is_span_body = isinstance(nu, _Span)
            if not is_span_body and not isinstance(child, (Command, Flow, _Span)):
                msg = (
                    f"{cls.__name__}.slot[{slot_idx}] is a body slot; "
                    f"expected Command / Flow / Span, got "
                    f"{type(child).__name__}."
                )
                raise TypeError(msg)
            # Continue to the matrix check below.

        # 4. Query slots: legacy three-kind union (Query / Ref / Span).
        # The matrix check covers it more precisely; no extra check here.

        # 5. Composition matrix.
        if not parent_label:
            continue
        child_label = _kind_label(child)
        if not child_label:
            continue
        if not _MATRIX[parent_label].get(child_label, False):
            msg = (
                f"{cls.__name__}.slot[{slot_idx}]: composition matrix "
                f"rejects {parent_label} -> {child_label} "
                f"({type(child).__name__})."
            )
            raise TypeError(msg)


_COMPOSITION_VALIDATORS.append(_validate_slot_trichotomy)
