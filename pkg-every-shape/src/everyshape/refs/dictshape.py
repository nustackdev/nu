"""ShapesDict ref hierarchy — shapes dict bases + Ref navigation.

ShapesDictRefBase         = ShapesDictBase + Ref
MutableShapesDictRefBase  = MutableShapesDictBase + ShapesDictRefBase
ReactiveShapesDictRefBase = ReactiveShapesDictBase + MutableShapesDictRefBase
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from ..collections import MutableShapesDictBase, ReactiveShapesDictBase, ShapesDictBase
from .base import Ref


if TYPE_CHECKING:
    from everyabc import Arg, Sentinel

    from ..shape import Shape as ShapeBase
    from .structured import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "MutableShapesDictRefBase",
    "ReactiveShapesDictRefBase",
    "ShapesDictRefBase",
]


class ShapesDictRefBase[K, T: ShapeBase](
    ShapesDictBase[K, T],
    Ref[dict[K, dict[str, object]]],
):
    """Shapes dict ref — mapping of shapes with navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> ShapeRef[T]:
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)


class MutableShapesDictRefBase[K, T: ShapeBase](
    MutableShapesDictBase[K, T],
    ShapesDictRefBase[K, T],
):
    """Mutable shapes dict ref — collection ops + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> MutableShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> MutableShapeRef[T]:
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)


class ReactiveShapesDictRefBase[K, T: ShapeBase](
    ReactiveShapesDictBase[K, T],
    MutableShapesDictRefBase[K, T],
):
    """Reactive shapes dict ref — observation + collection ops + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ReactiveShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> ReactiveShapeRef[T]:
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)
