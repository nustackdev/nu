"""The docstring contract for an interaction atom: the shared half plus this.

This text has two jobs. It is the spec a person reads before writing an atom's
docstring, and it is directly usable as the prompt for an agent doing a
docstring pass over a package. :mod:`nu.info.interaction.validate` enforces it
and :mod:`nu.info.interaction.parse` assumes it.

The conformant example below is a real class, and ``GUIDE`` splices its source
in rather than restating it. The test suite runs the validator over that same
class, so the guide cannot describe a contract its own checker rejects.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from nu.info.core.contract import SECTIONS
from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "GUIDE",
    "RULES",
    "Clamp",
]


class Clamp(ScalarQuery):
    """The first child, held between the second and the third.

    Args:
        value: the value to hold.
        low: the lowest value to yield.
        high: the highest value to yield.

    Notes:
        - A value already inside the bounds is yielded unchanged.
        - The bounds are ordinary children, so either can be a Ref read at
          runtime rather than a constant.
        - Bounds the wrong way round yield INVALID rather than swapping.

    Yields:
        The held value. INVALID when any child is EMPTY or INVALID.

    Example:
        >>> nu.run(Clamp(nu.Int(12), nu.Int(0), nu.Int(10)))[0]
        10
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        value, low, high = children

        def thunk(rt: Runtime) -> object:
            operands = [child(rt) for child in (value, low, high)]
            if any(operand is EMPTY or operand is INVALID for operand in operands):
                return INVALID
            held, floor, ceiling = operands
            if floor > ceiling:  # type: ignore[operator]
                return INVALID
            return min(max(held, floor), ceiling)  # type: ignore[call-overload, type-var]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        value, low, high = children

        async def athunk(rt: Runtime) -> object:
            operands = [await child(rt) for child in (value, low, high)]
            if any(operand is EMPTY or operand is INVALID for operand in operands):
                return INVALID
            held, floor, ceiling = operands
            if floor > ceiling:  # type: ignore[operator]
                return INVALID
            return min(max(held, floor), ceiling)  # type: ignore[call-overload, type-var]

        return athunk


RULES = """\
For an interaction atom, on top of the shared rules:

- Args is required whenever the atom takes children, which is nearly always.
  Most atoms inherit the variadic constructor, so the docstring is the only
  place the real child count is written down. It is checked against what the
  thunk unpacks, and a mismatch is reported.

- Notes is where a calling convention goes. A loop binding its element as a
  context attribute read with `AttrRef`, rather than passing it as an
  argument, is impossible to guess and belongs in a note.

- Yields is required, except on a Command, which writes rather than yields.

- An atom yielding a lazy stream must force it in the example (`nu.List(...)`)
  or the expected value is a generator repr and the example teaches nothing.

- `nu.run` returns `(value, context)`, so an example indexes it: `[0]`.
"""

GUIDE = f"""{SECTIONS}
{RULES}
A conformant atom, in full:

{inspect.getsource(Clamp)}"""
