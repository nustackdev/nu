"""Composition algebra - declared flags + structural derivations.

Declared on the kind class: `commutative`, `associative`, `idempotent`,
`deterministic`. Derived from the effect set: `independent`, `is_pure`.

Subtree propagation table from
projects/nu/model/04-laws/01-composition-algebra.md, encoded as function
bodies.

The algebra modules type-hint the protocols in `protocol.py`, not
concrete kinds. Walk uses `_children`; everything else reads class
attributes.
"""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING

from .effects import fabrics, is_pure, tracked_effects
from .nu import walk


if TYPE_CHECKING:
    from .protocol import Nu


__all__ = [
    "independent",
    "is_associative",
    "is_commutative",
    "is_deterministic_subtree",
    "is_idempotent_subtree",
    "is_pure",
]


def _flag(atom: Nu, name: str, default: object = False) -> object:
    """Read a declared flag from the kind class. Undeclared = default."""
    return getattr(type(atom), name, default)


def is_commutative(atom: Nu) -> bool:
    """Atom-level commutativity.

    Reads the kind's declared flag. The sentinel string `"if-independent"`
    resolves at the atom: commutative iff every child pair is independent.
    """
    flag = _flag(atom, "commutative", False)
    if flag is True:
        return True
    if flag is False:
        return False
    if flag == "if-independent":
        return all(independent(a, b) for a, b in combinations(atom._children, 2))
    msg = f"{type(atom).__name__}.commutative: invalid flag {flag!r}"
    raise TypeError(msg)


def is_associative(atom: Nu) -> bool:
    """Atom-level associativity. Declared flag; default False.

    Propagates trivially over a subtree (it's about same-kind nesting,
    not subtree contents) - so the atom-level value is the subtree
    answer too.
    """
    return bool(_flag(atom, "associative", False))


def is_idempotent_subtree(nu: Nu) -> bool:
    """Subtree idempotence.

    Holds iff every atom in the subtree is idempotent and the
    composition shape preserves it. The general "shape preserves it"
    check is punted (see model doc, "subtle in general"); current rule
    is the conservative one - every atom carries `idempotent = True`.
    """
    return all(bool(_flag(a, "idempotent", False)) for a in walk(nu))


def is_deterministic_subtree(nu: Nu) -> bool:
    """Subtree determinism.

    Breaks at the first non-deterministic atom anywhere in the subtree.
    """
    return all(bool(_flag(a, "deterministic", False)) for a in walk(nu))


def independent(a: Nu, b: Nu) -> bool:
    """Two subtrees are independent iff their fabrics are disjoint.

    `indep(a, b) <=> fabrics(effects(a)) ∩ fabrics(effects(b)) = ∅`.
    """
    fa = fabrics(tracked_effects(a))
    fb = fabrics(tracked_effects(b))
    return fa.isdisjoint(fb)
