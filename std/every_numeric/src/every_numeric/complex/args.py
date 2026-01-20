"""Complex args."""

from __future__ import annotations

from every._abc import Arg


__all__ = [
    "ComplexArg",
]

type ComplexArg = Arg[complex]
