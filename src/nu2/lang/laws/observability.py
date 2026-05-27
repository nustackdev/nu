"""Observability laws: a Nu program must mutate Context to be meaningful.

A program with no WRITE anywhere in its subtree is non-observable - it
runs and returns, but Context is unchanged. Whether to reject or warn is
a design call kept open in the model doc; this module surfaces it as a
warning so pure expressions still type-check and run.

These laws read ``composition_effects``; nothing here recomputes attributes.
"""

from __future__ import annotations

from nu2.engine import Law, Predicate, Severity
from nu2.lang.attributes import Effect

from .predicates import no_composition_effect


__all__ = ["LAWS"]


# --- scope predicates ---------------------------------------------------


is_root: Predicate = Predicate(lambda program, path: len(path) == 0)


# --- laws ---------------------------------------------------------------


LAWS: tuple[Law, ...] = (
    Law(
        "program_mutates",
        scope=is_root,
        holds=~no_composition_effect(Effect.WRITE),
        message="the program performs no Context mutation",
        severity=Severity.WARNING,
    ),
)
