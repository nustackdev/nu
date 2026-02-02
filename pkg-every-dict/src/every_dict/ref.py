"""Dict substrate refs — navigate nested Python dicts.

Hierarchy:
    RefBase[T]    - dict substrate root with address/parent/shape

Core vocabulary:
    resolve(ctx) → tuple[str | int, ...]  - build key path from parent chain
    fetch(ctx) → T                        - navigate dict and extract value
    fetch_parent(ctx) → container         - get parent dict/list
    resolve_address(ctx) → key            - get key/index at this segment
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import EMPTY, Ref, Sentinel, Term


if TYPE_CHECKING:
    from everyabc import Context
    from everyshape import Shape as ShapeBase


__all__ = [
    "RefBase",
]


class RefBase[T](Ref[T]):
    """Base for all dict-substrate refs.

    Dict refs navigate nested Python dicts using a parent chain
    of string keys. No storage backend, no views, no reactivity.

    The root dict is retrieved from Context via ctx.get(dict, shape=...).

    Attributes:
        _address: Key/index for this segment
        _parent: Parent ref in the navigation chain
        _shape: Shape class for context lookup
    """

    def __init__(
        self,
        address: str | int | Term,
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize dict ref.

        Args:
            address: Key/index for this segment (or Term for dynamic)
            parent: Parent ref in navigation chain
            shape: Shape class for context lookup
        """
        super().__init__()
        self._address = address
        self._parent = parent
        self._shape = shape

    @property
    def address(self) -> str | int | Term:
        """The key/index for this ref's segment."""
        return self._address

    @property
    def parent(self) -> RefBase | None:
        """Parent ref in the navigation chain."""
        return self._parent

    @property
    def shape(self) -> type[ShapeBase] | None:
        """Shape class for context lookup."""
        return self._shape

    def get_root_shape(self) -> type[ShapeBase] | None:
        """Get the root shape for context lookup.

        Traverses up the parent chain to find the shape.
        """
        if self._shape is not None:
            return self._shape
        if self._parent is not None:
            return self._parent.get_root_shape()
        return None

    async def _resolve_address(self, ctx: Context) -> str | int:
        """Resolve dynamic address if needed."""
        if isinstance(self._address, Term):
            return await self._address.execute(ctx)
        return self._address

    async def resolve(self, ctx: Context) -> tuple[str | int, ...]:
        """Build key path from parent chain.

        Args:
            ctx: Execution context

        Returns:
            Tuple of keys from root to this segment.
        """
        address = await self._resolve_address(ctx)

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

    async def resolve_address(self, ctx: Context) -> str | int:
        """Resolve the key/index for this segment.

        Args:
            ctx: Execution context

        Returns:
            The resolved key/index.
        """
        return await self._resolve_address(ctx)

    def _get_root_data(self, ctx: Context) -> dict:
        """Get the root dict from context."""
        shape = self.get_root_shape()
        return ctx.get(dict, shape=shape)

    def __repr__(self) -> str:
        if self._parent:
            return f"<{self.__class__.__name__}: {self._parent!r} -> {self._address!r}>"
        return f"<{self.__class__.__name__}: {self._address!r}>"


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
