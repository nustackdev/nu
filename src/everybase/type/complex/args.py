"""Complex args."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    pass


__all__ = [
    "ComplexArg",
]

type ComplexArg = Arg[complex]
