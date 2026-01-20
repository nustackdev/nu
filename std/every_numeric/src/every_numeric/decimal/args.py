"""Decimal args."""

from __future__ import annotations

from decimal import Decimal

from every._abc import Arg


__all__ = [
    "DecimalArg",
]

type DecimalArg = Arg[Decimal]
