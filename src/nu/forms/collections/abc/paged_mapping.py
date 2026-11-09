"""PagedMapping: a runtime mapping that pages its own keys.

Python's ``dict.keys()`` takes no arguments, so a page of keys
(``keys(after=, limit=)``, ``reversed_keys(before=, limit=)``) is a contract of
its own. Core knows no fabric type that keeps one, so a fabric registers its
paging mappings here, and the paged reads call it on any value that is a
``PagedMapping``. Anything else raises.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable


__all__ = [
    "PagedMapping",
]


class PagedMapping(ABC):
    """A runtime mapping that hands out one page of its keys at a time.

    Notes:
        - A fabric registers its paging types once, at import:
          ``PagedMapping.register(MyView)``. Subclassing works too.
        - Membership is by registration or subclassing only. Core never
          probes a value for a paged ``keys``.
        - What a cursor means, whether it has to exist, and what a page
          costs are the mapping's own.

    Example:
        >>> class Paged(dict):
        ...     def keys(self, *, after=None, limit=None):
        ...         keys = list(super().keys())
        ...         start = 0 if after is None else keys.index(after) + 1
        ...         return keys[start:][:limit]
        ...     def reversed_keys(self, *, before=None, limit=None):
        ...         keys = list(reversed(list(super().keys())))
        ...         start = 0 if before is None else keys.index(before) + 1
        ...         return keys[start:][:limit]
        >>> _ = nu.forms.collections.abc.PagedMapping.register(Paged)
        >>> nu.run(nu.Dict(nu.Literal(Paged(a=1, b=2, c=3))).keys(after="a", limit=1))[0]
        ['b']
    """

    __slots__ = ()

    @abstractmethod
    def keys(self, *, after: object = None, limit: int | None = None) -> Iterable:
        """The keys strictly after ``after`` (from the start when None), at most ``limit``."""

    @abstractmethod
    def reversed_keys(self, *, before: object = None, limit: int | None = None) -> Iterable:
        """The keys last first, strictly before ``before`` (from the end when None), at most ``limit``."""
