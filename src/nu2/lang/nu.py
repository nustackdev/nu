"""Nu - the user-facing base class for every Nu construct.

A thin subclass of ``Term``. Every concrete Nu sort (``Ref``, ``Interaction``,
``ScalarQuery``, ``StreamQuery``, ...) descends from ``Nu``; users annotate
their applications with ``Nu`` rather than reaching for the engine-level
``Term``. Engine machinery still operates on ``Term`` and accepts any ``Nu``
transparently - this class adds no behavior, only a brand surface.

Typical use::

    def my_app() -> Nu:
        return Add(Literal(1), Literal(2))

Custom atoms extend ``Nu`` (or one of its sort subclasses); ``Term`` is reserved
for engine-level work.
"""

from __future__ import annotations

from nu2.engine.structure import Term


__all__ = ["Nu"]


class Nu(Term):
    """The user-facing base for every Nu construct. A tagged ``Term``."""
