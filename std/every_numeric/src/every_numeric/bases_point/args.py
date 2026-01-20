"""Bases Point args."""

from __future__ import annotations

from typing import TYPE_CHECKING

from every._abc import Arg


if TYPE_CHECKING:
    from .cls import BasisPoint


__all__ = [
    "BasesPointArg",
]

type BasesPointArg = Arg[BasisPoint]
