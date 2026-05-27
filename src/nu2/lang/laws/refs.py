"""Ref invariants: how Refs may sit in a Nu program.

Most Ref constraints are covered by the composition matrix; this module
hosts what the matrix can't express (a Ref as a Nu program's root atom is
not a program in the observable sense).
"""

from __future__ import annotations

from nu2.engine import Law, Predicate, Severity
from nu2.lang.attributes import Sort

from .predicates import of_sort


__all__ = ["LAWS"]


is_root = Predicate(lambda program, path: len(path) == 0)


LAWS: tuple[Law, ...] = (
    Law(
        "ref_not_root",
        scope=is_root,
        holds=~of_sort(Sort.REF),
        message="a Ref is not a Nu program; it has no Context interaction on its own",
        severity=Severity.WARNING,
    ),
)
