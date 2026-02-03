"""Dict substrate refs — navigate nested Python dicts.

Hierarchy:
    everyshape.Ref[T]     - document-model base (address/parent/shape)
        |
    RefBase[T]            - dict substrate implementation

Core vocabulary:
    resolve(ctx) -> tuple[str | int, ...]  - build key path from parent chain
    fetch(ctx) -> T                        - navigate dict and extract value
    fetch_parent(ctx) -> container         - get parent dict/list
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import EMPTY, Sentinel
from everyshape import Ref


if TYPE_CHECKING:
    from everybase import Context


__all__ = [
    "RefBase",
]


class RefBase[T](Ref[T]):
    """Base for all dict-substrate refs.

    Dict refs navigate nested Python dicts using a parent chain
    of string keys. No storage backend, no views, no reactivity.

    The root dict is retrieved from Context via ctx.get(dict, shape=...).
    """

    async def resolve(self, ctx: Context) -> tuple[str | int, ...]:
        """Build key path from parent chain.

        Args:
            ctx: Execution context

        Returns:
            Tuple of keys from root to this segment.
        """
        address = await self.resolve_address(ctx)

        if self._parent is None:
            return (address,) if address != "" else ()

        parent_path = await self._parent.resolve(ctx)
        return (*parent_path, address)

    async def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch value by navigating the dict.

        Args:
            ctx: Execution context with root dict

        Returns:
            Value at this location, or EMPTY if absent.
        """
        key_path = await self.resolve(ctx)
        data = self._get_root_data(ctx)
        try:
            return _navigate(data, key_path)
        except (KeyError, IndexError):
            return EMPTY

    async def fetch_parent(self, ctx: Context) -> object:
        """Fetch the parent container.

        Args:
            ctx: Execution context

        Returns:
            The parent dict/list containing this ref's value.
        """
        key_path = await self.resolve(ctx)
        data = self._get_root_data(ctx)

        if len(key_path) <= 1:
            return data
        return _navigate(data, key_path[:-1])

    def _get_root_data(self, ctx: Context) -> dict:
        """Get the root dict from context."""
        shape = self.get_root_shape()
        return ctx.get(dict, shape=shape)


def _navigate(data: object, key_path: tuple[str | int, ...]) -> object:
    """Walk a nested structure following path keys.

    Args:
        data: Root dict/list to navigate
        key_path: Sequence of keys/indices

    Returns:
        Value at the end of the path.
    """
    current = data
    for key in key_path:
        current = current[key]  # type: ignore[index]
    return current
