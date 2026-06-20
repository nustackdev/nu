"""Transform atoms: Python's stream-to-stream builtins.

Maps Python's builtins that take an iterable and yield another iterable onto Nu
StreamQueries (lazy lenses - pulled per item, no materialization). Pure shape
over their source; effects only ride in through Ref children.

Builtins to cover (Python -> Nu):
- ``map`` -> ``Map``, ``filter`` -> ``Filter``, ``sorted`` -> ``Sorted``

Plus two transforms v1 keeps as core (no single bare builtin, but native shape
over a stream): ``Flatten`` (one-level concat of a stream of streams) and
``Unique`` (drop already-seen items, order preserved).

``sorted`` is eager: it is the one barrier among these lazy lenses. ``Map`` /
``Filter`` / ``Flatten`` / ``Unique`` pull one item at a time and yield as they
go, but ``Sorted`` must drain its whole source before it can order it, so it
pulls everything then yields - a pull on its output blocks until upstream is
exhausted. No attribute marks this; it is a runtime property noted here.

Extra lenses Python spells with itertools (chain, takewhile, ...) are NOT core -
they go to ``nu.std`` later; keep here only bare builtins plus the two v1
core transforms. ``reversed`` is a source, so it lives in ``iteration``.

These supersede the placeholder ``Map`` / ``Filter`` in ``_legacy.streams`` -
this module is their real home.

Sorts: all StreamQuery (Q). Declared structurally (subclass + Declared attrs,
no ``compile``) - they are lenses over the stream runtime, which is not wired
yet; eval lands once that fabric comes online.

v1 reference: ``src/nu/queries/stream_transform.py`` (Filter, Map, TakeWhile),
``transform.py`` (Sorted, Reversed, Flatten, Unique), ``sort_by.py``.
"""

from __future__ import annotations

from nu2.lang import StreamQuery


__all__ = ["Filter", "Flatten", "Map", "Sorted", "Unique"]


class Map(StreamQuery):
    """Applies a query child to every item of its stream child (lazy)."""


class Filter(StreamQuery):
    """Keeps the items of its stream child for which a predicate holds (lazy)."""


class Sorted(StreamQuery):
    """Its stream child, ordered. Eager: drains the source, then yields.

    The one barrier among these lenses - a pull on its output blocks until the
    whole source is exhausted and sorted.
    """


class Flatten(StreamQuery):
    """Concatenates a stream of streams one level into a flat stream (lazy)."""


class Unique(StreamQuery):
    """Yields each item of its stream child once, first-seen order (lazy)."""
