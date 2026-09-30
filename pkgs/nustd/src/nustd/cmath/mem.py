"""The mem leaf for a complex: kept as the str Python prints for it in a plain dict.

The leaf pairs the ``nustd.cmath`` value form with the mem leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaf lives with
its library, not in ``nu.mem``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import ToStr
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nu.mem.refs import ItemRef
from nustd.cmath.forms import complex as ComplexForm


if TYPE_CHECKING:
    from nu.lang import Arg


__all__ = ["ComplexRef"]


class ComplexRef(ItemRef, ComplexForm):
    """A complex slot in the dict substrate, stored as ``str(complex)``.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - ``str(complex)`` is what ``complex(str)`` reads back, so the value
          round-trips exactly, parentheses and all.

    Yields:
        A complex, parsed from the stored string. EMPTY when the slot was
        never written.

    Example:
        >>> class Signal(nu.Shape):
        ...     amp = nustd.cmath.mem.ComplexRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Signal)
        >>> _ = nu.run(Signal.amp.set(complex(1, 2)), ctx)
        >>> data
        {'amp': '(1+2j)'}
        >>> nu.run(Signal.amp.real(), ctx)[0]
        1.0
    """

    def _lift(self, raw: object) -> complex:
        """Parse the stored str back to a complex."""
        return raw if isinstance(raw, complex) else complex(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[complex | str]) -> SetCmd:
        """Write a complex into the slot as its string form.

        Notes:
            - A plain Python value is serialised at tree-build time; a Nu
              operand gets a ``ToStr`` node instead.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
