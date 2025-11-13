"""FrozenSetView - Frozenset-like view over container (immutable set)."""

from __future__ import annotations

import hashlib
import pickle
from typing import TYPE_CHECKING, ClassVar

from redwood.tree import ContainerProtocol, ContainerStructure
from redwood.types import cast_value, is_empty

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from redwood.loc import key as key_
    from redwood.types import Convertible, Initializable


__all__ = ["FrozenSetView"]


class FrozenSetView(StdView):
    """Frozenset-like view over container (immutable set).

    Provides read-only set interface:
    - __contains__, __len__, __iter__

    Type Parameters:
        V: Type of values (default: Value)

    Example:
        >>> perms: FrozenSetView[str] = FrozenSetView(container, registry)
        >>> # Must be initialized via store()
        >>> perms.store({"read", "write", "execute"})
        >>> print("read" in perms)  # True
        >>> print(len(perms))  # 3
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(5)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.SET
    CONTAINER_CLS: ClassVar[type] = frozenset

    def _make_key(self, value: object) -> key_.KeySegment:
        """Convert value to storage key.

        Deterministic hash for any hashable object.

        Args:
            value: Value to store in set

        Returns:
            Key for storage
        """
        pickled = pickle.dumps(value, protocol=4)  # Use fixed protocol
        # Returns int for use in hash tables, or use .hexdigest() for string
        return int.from_bytes(hashlib.sha256(pickled).digest()[:64], "big")

    def __contains__(self, value: object) -> bool:
        """Check if value in set.

        Args:
            value: Value to check

        Returns:
            True if value in set
        """
        key = self._make_key(value)
        return self.container.has_child(key)

    def __len__(self) -> int:
        """Get number of values.

        Returns:
            Number of values
        """
        return self.container.count_children()

    def __iter__(self) -> Generator[object, None, None]:
        """Iterate over values.

        Yields:
            Values in set
        """
        for key in self.container.list_child_keys():
            stored_value = self.container.get_child_primitive(key)
            if not is_empty(stored_value):
                yield cast_value(stored_value)  # type: ignore[misc]

    def extract(self) -> frozenset[object]:
        """Extract all values as frozenset.

        Returns:
            Frozenset of all values
        """
        return frozenset(self)

    def store(self, value: Iterable[object]) -> None:
        """Store frozenset contents.

        Args:
            value: Iterable to store
            replace: If True, clear existing content first
        """
        self.container.clear_children()

        for item in value:
            key = self._make_key(item)
            self._set_child_value(key, item)


if TYPE_CHECKING:
    _c: type[Convertible[object]] = FrozenSetView
    _i: type[Initializable[Iterable[object]]] = FrozenSetView
