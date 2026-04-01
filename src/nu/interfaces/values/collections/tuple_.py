"""Concrete tuple value for Python memory storage."""

from __future__ import annotations

from ...types import TupleType
from ..base import ValueBase


class TupleValue[*Ts](ValueBase[tuple[*Ts]], TupleType[*Ts]):
    """Concrete tuple value for Python memory storage."""

    pass
