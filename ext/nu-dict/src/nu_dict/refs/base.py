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

from typing import TYPE_CHECKING, ClassVar

from nu import EMPTY, Sentinel
from nu.shapes import Ref
from nu.terms import Mode


if TYPE_CHECKING:
    from nu import Context


__all__ = [
    "RefBase",
]


class RefBase[T](Ref[T]):
    """Base for all dict-substrate refs.

    Dict refs navigate nested Python dicts using a parent chain
    of string keys. No storage backend, no views, no reactivity.

    The root dict is retrieved from Context via ctx[dict, scope].
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    async def aresolve(self, ctx: Context) -> tuple[str | int, ...]:
        """Build key path from parent chain."""
        address = await self.aresolve_address(ctx)

        if self.parent is None:
            return (address,) if address != "" else ()

        parent_path = await self.parent.aresolve(ctx)
        return (*parent_path, address)

    def resolve(self, ctx: Context) -> tuple[str | int, ...]:
        """Build key path from parent chain (sync)."""
        address = self.resolve_address(ctx)

        if self.parent is None:
            return (address,) if address != "" else ()

        parent_path = self.parent.resolve(ctx)
        return (*parent_path, address)

    async def afetch(self, ctx: Context) -> T | Sentinel:
        """Fetch value by navigating the dict."""
        key_path = await self.aresolve(ctx)
        data = self._get_root_data(ctx, key_path)
        try:
            raw = _navigate(data, key_path)
            return self.coerce(raw)
        except (KeyError, IndexError):
            return EMPTY

    def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch value by navigating the dict (sync)."""
        key_path = self.resolve(ctx)
        data = self._get_root_data(ctx, key_path)
        try:
            raw = _navigate(data, key_path)
            return self.coerce(raw)
        except (KeyError, IndexError):
            return EMPTY

    async def afetch_parent(self, ctx: Context) -> object:
        """Fetch the parent container, auto-creating intermediate dicts."""
        key_path = await self.aresolve(ctx)
        data = self._get_root_data(ctx, key_path)

        if len(key_path) <= 1:
            return data
        return _navigate_vivify(data, key_path[:-1])

    def fetch_parent(self, ctx: Context) -> object:
        """Fetch the parent container, auto-creating intermediate dicts (sync)."""
        key_path = self.resolve(ctx)
        data = self._get_root_data(ctx, key_path)

        if len(key_path) <= 1:
            return data
        return _navigate_vivify(data, key_path[:-1])

    def _get_root_data(self, ctx: Context, key_path: tuple | None = None) -> dict:
        """Get the root dict from context.

        Passes site= to ctx.get() so predicate bindings (sharding etc.)
        can route to the correct storage based on the key path.
        """
        scope = self.get_root_shape()
        if key_path is not None:
            return ctx.get(dict, scope, site=key_path)
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
