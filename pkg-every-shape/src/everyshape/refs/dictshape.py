"""ShapesDict ref hierarchy — dict type + Ref navigation.

ShapesDictRefBase         = DictBase + Ref          (dict IS mutable)
ReactiveShapesDictRefBase = ReactiveDictBase + Ref  (+ observation)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from everyshape.types import DictBase, ReactiveDictBase

from .base import Ref


if TYPE_CHECKING:
    from everybase import Arg, Sentinel

    from ..shape import Shape as ShapeBase
    from .structured import MutableShapeRef, ReactiveShapeRef


__all__ = [
    "ReactiveShapesDictRefBase",
    "ShapesDictRefBase",
]


class ShapesDictRefBase[K, T: ShapeBase](
    DictBase[K, dict[str, object]],
    Ref[dict[K, dict[str, object]]],
):
    """Shapes dict ref — mutable dict of shapes with navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> MutableShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> MutableShapeRef[T]:
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)


class ReactiveShapesDictRefBase[K, T: ShapeBase](
    ReactiveDictBase[K, dict[str, object]],
    ShapesDictRefBase[K, T],
):
    """Reactive shapes dict ref — observation + collection ops + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ReactiveShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> ReactiveShapeRef[T]:
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)
