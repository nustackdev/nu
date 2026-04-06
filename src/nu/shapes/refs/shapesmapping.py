"""ShapesMapping ref hierarchy — mapping of shapes + Ref navigation.

ShapesMappingRefBase         = MappingBase[K, dict[str, object], ...] + Ref
MutableShapesMappingRefBase  = MutableMappingBase[K, dict[str, object], ...] + Ref
ReactiveShapesMappingRefBase = ReactiveMappingBase[K, dict[str, object], ...] + Ref

Specialized mapping refs where each value is a shape (dict[str, object]).
Child navigation returns ShapeRef variants instead of ItemRef.

Type Parameters:
    K: Key type (str, int, etc.)
    T: Shape type (bound to ShapeBase)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from ..collections import MappingBase, MutableMappingBase, ReactiveMappingBase
from .base import Ref


if TYPE_CHECKING:
    from nu import Arg, Sentinel

    from ..shape import Shape as ShapeBase
    from .structured import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "MutableShapesMappingRefBase",
    "ReactiveShapesMappingRefBase",
    "ShapesMappingRefBase",
]


class ShapesMappingRefBase[K, T: ShapeBase](
    MappingBase[K, dict[str, object], object, object],
    Ref[dict[K, dict[str, object]]],
):
    """Shapes mapping ref — read-only mapping of shapes with navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> T:  # type: ignore[override]
        """Subscript access — returns a ref to the shape at key.

        Return type is T (the Shape class) for Pyright slot navigation.
        Runtime returns ShapeRef[T].
        """
        return self._create_child_ref(key)  # type: ignore[return-value]


class MutableShapesMappingRefBase[K, T: ShapeBase](
    MutableMappingBase[K, dict[str, object], object, object],
    ShapesMappingRefBase[K, T],
):
    """Mutable shapes mapping ref — mutations + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> MutableShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> T:  # type: ignore[override]
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)  # type: ignore[return-value]


class ReactiveShapesMappingRefBase[K, T: ShapeBase](
    ReactiveMappingBase[K, dict[str, object], object, object],
    MutableShapesMappingRefBase[K, T],
):
    """Reactive shapes mapping ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ReactiveShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> T:  # type: ignore[override]
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)  # type: ignore[return-value]
