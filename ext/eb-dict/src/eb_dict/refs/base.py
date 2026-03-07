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
from everybase.shape import Ref


if TYPE_CHECKING:
    from everybase import Context


__all__ = [
    "RefBase",
]


class RefBase[T](Ref[T]):
    """Base for all dict-substrate refs.

    Dict refs navigate nested Python dicts using a parent chain
    of string keys. No storage backend, no views, no reactivity.

    The root dict is retrieved from Context via ctx[dict, scope].
    """

    async def resolve(self, ctx: Context) -> tuple[str | int, ...]:
        """Build key path from parent chain."""
        address = await self.resolve_address(ctx)

        if self.parent is None:
            return (address,) if address != "" else ()

        parent_path = await self.parent.resolve(ctx)
        return (*parent_path, address)

    async def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch value by navigating the dict."""
        key_path = await self.resolve(ctx)
        data = self._get_root_data(ctx)
        try:
            return _navigate(data, key_path)
        except (KeyError, IndexError):
            return EMPTY

    async def fetch_parent(self, ctx: Context) -> object:
        """Fetch the parent container, auto-creating intermediate dicts."""
        key_path = await self.resolve(ctx)
        data = self._get_root_data(ctx)

        if len(key_path) <= 1:
            return data
        return _navigate_vivify(data, key_path[:-1])

    def _get_root_data(self, ctx: Context) -> dict:
        """Get the root dict from context."""
        scope = self.get_root_shape()
        return ctx[dict, scope]


def _navigate(data: object, key_path: tuple[str | int, ...]) -> object:
    """Walk a nested structure following path keys."""
    current = data
    for key in key_path:
        current = current[key]  # type: ignore[index]
    return current


def _navigate_vivify(data: dict, key_path: tuple[str | int, ...]) -> object:
    """Walk a nested structure, auto-creating missing dicts."""
    current: object = data
    for key in key_path:
        if isinstance(current, dict):
            if key not in current:
                current[key] = {}
            current = current[key]
        else:
            current = current[key]  # type: ignore[index]
    return current
