"""Execution-mode laws: sync / async coherence.

An atom that requires async is resolved on the loop. An atom that has no
async affinity should not be resolved on the loop (warning, not error).
"""

from __future__ import annotations

from nu.engine import Law, Severity
from nu.lang.attributes import Attr

from .predicates import attr_true


__all__ = ["LAWS"]


LAWS: tuple[Law, ...] = (
    Law(
        "async_atom_needs_loop",
        scope=attr_true(Attr.REQUIRES_ASYNC),
        holds=attr_true(Attr.ON_LOOP),
        message="an async-only atom is resolved off the loop",
    ),
    Law(
        "sync_atom_on_loop",
        scope=~attr_true(Attr.ASYNC_AFFINITY),
        holds=~attr_true(Attr.ON_LOOP),
        message="a sync-only atom is resolved onto the loop",
        severity=Severity.WARNING,
    ),
)
