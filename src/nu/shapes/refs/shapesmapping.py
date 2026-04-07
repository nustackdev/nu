"""ShapesMapping ref hierarchy — mapping of shapes + Ref navigation.

ShapesMappingRef         = MappingI[K, dict[str, object], ...] + Ref
MutableShapesMappingRef  = MutableMappingI[K, dict[str, object], ...] + Ref
ReactiveShapesMappingRef = ReactiveMappingI[K, dict[str, object], ...] + Ref

Specialized mapping refs where each value is a shape (dict[str, object]).
Child navigation returns ShapeRef variants instead of ItemRef.

Type Parameters:
    K: Key type (str, int, etc.)
    T: Shape type (bound to ShapeBase)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from nu.shapes.collections import MappingI, MutableMappingI, ReactiveMappingI
from .base import Ref


if TYPE_CHECKING:
    from nu import Arg, Sentinel

    from nu.shapes.shape import Shape as ShapeBase
    from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "MutableShapesMappingRef",
    "ReactiveShapesMappingRef",
    "ShapesMappingRef",
]


class ShapesMappingRef[K, T: ShapeBase](
    MappingI[K, dict[str, object], object, object],
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


class MutableShapesMappingRef[K, T: ShapeBase](
    MutableMappingI[K, dict[str, object], object, object],
    ShapesMappingRef[K, T],
):
    """Mutable shapes mapping ref — mutations + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> MutableShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> T:  # type: ignore[override]
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)  # type: ignore[return-value]


class ReactiveShapesMappingRef[K, T: ShapeBase](
    ReactiveMappingI[K, dict[str, object], object, object],
    MutableShapesMappingRef[K, T],
):
    """Reactive shapes mapping ref — observation + mutations + navigation."""

    @abstractmethod
    def _create_child_ref(self, key: Arg[K] | Sentinel) -> ReactiveShapeRef[T]:
        """Create a reference to the shape at the given key."""
        ...

    def __getitem__(self, key: Arg[K]) -> T:  # type: ignore[override]
        """Subscript access — returns a ref to the shape at key."""
        return self._create_child_ref(key)  # type: ignore[return-value]
