"""The kv leaf for a Decimal: kept as its exact str, so no digit is lost in KV storage.

The leaf pairs the ``nustd.decimal`` value form with the kv leaf and
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
from nustd.decimal.forms import Decimal as DecimalForm
from nustd.kv.refs import ItemRef


if TYPE_CHECKING:
    from decimal import Decimal

    from nu.lang import Arg


__all__ = ["DecimalRef"]


class DecimalRef(ItemRef, DecimalForm):
    """A Decimal leaf in KV storage, kept exact by storing its str form.

    Notes:
        - Stored as str, so the value round-trips digit for digit; that is
          the whole reason to pick this over FloatRef for money.
        - Reads parse back to a Decimal, so the arithmetic on the ref is
          decimal arithmetic, not float arithmetic.
        - An absent leaf reads as EMPTY, not as zero.

    Example:
        class Order(Shape):
            price = DecimalRef.slot()
        run(Order.price.set(Decimal("19.99")), ctx)
    """

    def _lift(self, raw: object) -> Decimal:
        """Parse the stored str back to a Decimal."""
        from decimal import Decimal as DecimalCls

        return raw if isinstance(raw, DecimalCls) else DecimalCls(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[Decimal | str]) -> SetCmd:
        """Write a Decimal to the leaf, serialized to its str form.

        Args:
            value: a Decimal, a str spelling one, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr so the conversion happens at run time.
            - The str is whatever ``str()`` gives, so it parses back exactly.

        Example:
            run(Order.price.set(Decimal("19.99")), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
