"""The kv leaf for a complex: kept as the str Python prints for it in KV storage.

The leaf pairs the ``nustd.cmath`` value form with the kv leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaf lives with
its library, not in ``nustd.kv``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import ToStr
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nustd.cmath.forms import complex as ComplexForm
from nustd.kv.refs import ItemRef


if TYPE_CHECKING:
    from nu.lang import Arg


__all__ = ["ComplexRef"]


class ComplexRef(ItemRef, ComplexForm):
    """A complex leaf in KV storage, stored as the str Python prints for it.

    Notes:
        - Stored as str because a KV leaf holds one scalar; the pair is kept
          in the one text rather than in two slots.
        - Reads parse back to a complex, so ``real``, ``imag`` and the
          arithmetic all work on the value.
        - An absent leaf reads as EMPTY.

    Example:
        class Wave(Shape):
            amplitude = ComplexRef.slot()
        run(Wave.amplitude.set(complex(1, 2)), ctx)
    """

    def _lift(self, raw: object) -> complex:
        """Parse the stored str back to a complex."""
        return raw if isinstance(raw, complex) else complex(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[complex | str]) -> SetCmd:
        """Write a complex to the leaf, serialized to its str form.

        Args:
            value: a complex, a str spelling one, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr so the conversion happens at run time.

        Example:
            run(Wave.amplitude.set(complex(1, 2)), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
