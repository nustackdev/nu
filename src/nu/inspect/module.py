"""The module kind: record and parse.

A module is written to the same format its subjects are, and its docstring is
the only place the thing they have in common is said: what this surface is
for, what it is not, what holds across all of it. A page over a module opens
with it, and an agent pointed at one reads it before any name in it.

So it is parsed once, here, rather than read raw wherever somebody needs it.
There is no ``verify_module``: a module is not called, does not evaluate and
has no arity, so there is nothing for the code to contradict. Summary,
description, notes and examples are the whole surface, and absence of any of
them is data like everywhere else.

A module's catalogue is a separate question, answered by the per-kind
``catalogue`` functions. This record is the prose only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.inspect.core.docstring import split_docstring
from nu.inspect.record import Record, prose


if TYPE_CHECKING:
    from types import ModuleType


__all__ = [
    "ModuleRecord",
    "parse_module",
]


@dataclass(frozen=True)
class ModuleRecord(Record):
    """One module: its own docstring, split like any subject's.

    ``name`` is the last part (``arithmetic``), ``path`` and ``module`` are
    both the full dotted name, since for a module those two questions - where
    it is reached and where it is defined - have the same answer.
    """


def parse_module(module: ModuleType, path: str = "") -> ModuleRecord:
    """One ModuleRecord for ``module``."""
    where = path or module.__name__
    blocks = split_docstring(module.__doc__)
    return ModuleRecord(
        **prose(module, where.rsplit(".", 1)[-1], where, blocks, module=where),
    )
