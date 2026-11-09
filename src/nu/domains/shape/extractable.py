"""Extractable: a runtime value that hands out its plain data on request.

A fabric whose read is a live handle (a lazy view over its store, say) does not
yield plain data from a read. ``Extract`` has to ask the handle for it, and core
knows no fabric type to ask. So the fabric registers its handle types here, and
``Extract`` calls ``extract()`` on any value that is an ``Extractable``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


__all__ = [
    "Extractable",
]


class Extractable(ABC):
    """A runtime value whose ``extract()`` returns it as plain Python data.

    Notes:
        - A fabric registers its live-handle types once, at import:
          ``Extractable.register(MyView)``. Subclassing works too.
        - Membership is by registration or subclassing only. Core never
          probes a value for an ``extract`` attribute.
        - ``extract()`` is synchronous and returns the whole subtree as plain
          data (dicts, lists, sets, scalars), with nested handles extracted.

    Example:
        >>> class Handle:
        ...     def __init__(self, data):
        ...         self._data = data
        ...     def extract(self):
        ...         return dict(self._data)
        >>> _ = nu.shape.Extractable.register(Handle)
        >>> nu.run(nu.Dict(nu.Literal(Handle({"a": 1}))).extract())[0]
        {'a': 1}
    """

    __slots__ = ()

    @abstractmethod
    def extract(self) -> object:
        """The value as plain Python data."""
