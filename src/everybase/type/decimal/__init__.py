"""Decimal type for Shape system.

Provides DecimalType, DecimalRef, and DecimalSlot for working with
Python Decimal objects. Ideal for financial calculations.

Example:
    from everybase.type import DecimalSlot

    class Account(Shape):
        balance = DecimalSlot()
        interest_rate = DecimalSlot()

    # Operations
    Account.balance.set(Decimal("1000.00"))
    Account.balance.get() * Account.interest_rate.get()
"""

from __future__ import annotations

from .args import DecimalArg
from .ref import DecimalRef
from .slot import DecimalSlot
from .type import DecimalType


__all__ = [
    "DecimalType",
    "DecimalRef",
    "DecimalSlot",
    "DecimalArg",
]
