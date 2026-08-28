"""Diagnostic: what comes back when source fails to construct a Nu.

Constructing a Nu from python source fails in ordinary python ways: the
source does not parse, module-level code raises, the entry point is
missing, it raises, or it returns something that is not a Nu. All of them
land here as one flat record.

Why a record and not the exception. The construction happens inside a
*brace* (see :mod:`nu.prog.brace`), which may be another interpreter in
another venv. Only two things cross that boundary: a constructed Nu, or
one of these. An arbitrary live exception is not reliably transportable
and its traceback object is not transportable at all, so the failure is
flattened at the point it happens, on the side that has the frames.

Three fields, no taxonomy:

- ``message``    -- what went wrong, one line.
- ``lineno``     -- line in *the source* it happened on, ``None`` when the
  failure has no source position (missing entry point, wrong return type).
- ``traceback``  -- the formatted frames, already rendered.

There is deliberately no phase/kind enum. The message says what happened
and the traceback says where; a classifier on top would be our guess at
what a caller wants to branch on, and nothing branches on it yet.

Frozen but not slotted. A catch branch inside a tree reads the caught
exception with ``AttrRef("error")`` and walks into it with ``Vars``, which
is ``vars()`` and so needs a ``__dict__``. Slots would save a pointer per
record on a type that exists once per failure, and cost the field-level
read path that is the whole point of carrying the record around.
"""

from __future__ import annotations

from dataclasses import dataclass


__all__ = ["ConstructionError", "Diagnostic"]


@dataclass(frozen=True)
class Diagnostic:
    """A single construction failure, flattened for transport."""

    message: str
    lineno: int | None = None
    traceback: str = ""

    def __str__(self) -> str:
        where = f" (line {self.lineno})" if self.lineno is not None else ""
        return f"{self.message}{where}"


class ConstructionError(Exception):
    """Raised on the caller's side when construction produced a Diagnostic.

    Carries the record on ``.diagnostic``. The exception is the ergonomic
    surface; the record is the transportable one.
    """

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(str(diagnostic))
        self.diagnostic = diagnostic
