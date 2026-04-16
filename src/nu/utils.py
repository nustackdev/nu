"""Convert Python objects to Nu expressions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu.terms import Nu

__all__ = [
    "ensure_nu",
]

logger = logging.getLogger(__name__)


def ensure_nu(value: object) -> Nu:
    """Ensure value is a Nu,."""
    from nu.terms import Literal, Nu

    if isinstance(value, Nu):
        return value
    else:
        return Literal(value)
