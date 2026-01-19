"""Series args."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyterm.term import Arg


if TYPE_CHECKING:
    from .cls import Point, Series
    from .type import PointType, SeriesType


__all__ = [
    "PointArg",
    "SeriesArg",
]

type PointArg = Arg[Point | PointType]
type SeriesArg = Arg[Series | SeriesType]
