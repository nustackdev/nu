"""Stream atoms: StreamQuery sources and stream-to-stream operators.

Range is a pure source; Map and Filter and Take reshape a stream child. Watch
is an event subscription - it holds an async-only operation, so a program that
contains one runs on an event loop.
"""

from __future__ import annotations

from nu2.engine.structure import Declared
from nu2.lang import StreamQuery


__all__ = ["Filter", "Map", "Range", "Take", "Watch"]


class Range(StreamQuery):
    """A stream of integers between two scalar bounds."""


class Map(StreamQuery):
    """Applies a query child to every item of its stream child."""


class Filter(StreamQuery):
    """Keeps the items of its stream child for which a predicate holds."""


class Take(StreamQuery):
    """The first n items of its stream child."""


class Watch(StreamQuery):
    """An event subscription; yields items as they arrive on a loop."""

    requires_async = Declared(value=True)
