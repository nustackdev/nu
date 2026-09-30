"""The mem leaf for a Decimal: kept as its exact str, so no digit is lost in a plain dict.

The leaf pairs the ``nustd.decimal`` value form with the mem leaf and
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
from nustd.decimal.forms import Decimal as DecimalForm


if TYPE_CHECKING:
    from decimal import Decimal

    from nu.lang import Arg


__all__ = ["DecimalRef"]


class DecimalRef(ItemRef, DecimalForm):
    """A Decimal slot in the dict substrate, stored as its exact string form.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored string is ``str(Decimal)``, so precision and trailing
          zeros survive the round trip where a float would lose them.
        - A Decimal already sitting in the data dict is read as it is, so a
          dict populated by hand works either way.

    Yields:
        A Decimal, parsed from the stored string. EMPTY when the slot was
        never written.

    Example:
        >>> from decimal import Decimal
        >>> class Quote(nu.Shape):
        ...     price = nustd.decimal.mem.DecimalRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Quote)
        >>> _ = nu.run(Quote.price.set(Decimal("1.250")), ctx)
        >>> data
        {'price': '1.250'}
        >>> nu.run(Quote.price, ctx)[0]
        Decimal('1.250')
    """

    def _lift(self, raw: object) -> Decimal:
        """Parse the stored str back to a Decimal."""
        from decimal import Decimal as DecimalCls

        return raw if isinstance(raw, DecimalCls) else DecimalCls(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[Decimal | str]) -> SetCmd:
        """Write a Decimal into the slot as its string form.

        Notes:
            - A plain Python value is serialised now, at tree-build time; a
              Nu operand gets a ``ToStr`` node instead, serialised when the
              tree runs.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
