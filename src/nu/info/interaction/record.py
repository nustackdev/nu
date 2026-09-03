"""What an interaction record carries beyond the shared prose.

There is no spelling here. An interaction has a name; the operators that reach
one (``+``, ``[]``, ``>>``) are declared on the Forms and Refs that define
them, and belong to those records.

There is no separate child shape either. An interaction's children *are* its
arguments, so arity and the required count are views over ``args`` rather than
a second thing to keep in step with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.info.record import Record


if TYPE_CHECKING:
    from nu.info.core.contract import Arg


__all__ = ["InteractionRecord"]


@dataclass(frozen=True)
class InteractionRecord(Record):
    """One interaction atom: the prose, plus what the code says it is.

    ``args`` is the call form, from the constructor when the atom declares one
    and from the docstring when it inherits the variadic ``Nu.__init__``.
    ``kind``, ``sort`` and ``cardinality`` are taxonomy facts read off
    ``nu.lang.kinds``.
    """

    args: tuple[Arg, ...] = ()
    yields: str = ""
    kind: str = ""
    sort: str = ""
    cardinality: str = ""

    @property
    def arity(self) -> int | None:
        """The exact child count, or None when it is not known.

        Not known covers two cases that both have to stay honest: an atom
        taking any number of children, and an atom whose Args section has not
        been written yet. Neither is zero, and reporting zero would be a lie a
        consumer cannot see through.
        """
        if not self.args or any(arg.variadic for arg in self.args):
            return None
        return len(self.args)

    @property
    def required(self) -> int:
        """How many children carry no default."""
        return sum(1 for arg in self.args if not arg.variadic and not arg.default)
