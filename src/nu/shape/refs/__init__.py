"""Document-model refs — collection bases + Ref navigation.

These combine pure collection bases from nu.shape.collections with
Ref (address/parent/shape navigation) for substrate implementations.

Substrates (eb_virtuals) inherit from these.
"""

from .base import Ref
from .items import ItemRef, MutableItemRef, ReactiveItemRef
from .mapping import MappingRefBase, MutableMappingRefBase, ReactiveMappingRefBase
from .sequence import MutableSequenceRefBase, ReactiveSequenceRefBase, SequenceRefBase
from .set import MutableSetRefBase, ReactiveSetRefBase, SetLikeRefBase
from .shapesmapping import (
    MutableShapesMappingRefBase,
    ReactiveShapesMappingRefBase,
    ShapesMappingRefBase,
)
from .shapessequence import (
    MutableShapesSequenceRefBase,
    ReactiveShapesSequenceRefBase,
    ShapesSequenceRefBase,
)
from .structured import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [  # noqa: RUF022
    # Ref base
    "Ref",
    # Item refs
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
    # Shape refs (structured)
    "ShapeRef",
    "MutableShapeRef",
    "ReactiveShapeRef",
    # Sequence refs
    "SequenceRefBase",
    "MutableSequenceRefBase",
    "ReactiveSequenceRefBase",
    # Mapping refs
    "MappingRefBase",
    "MutableMappingRefBase",
    "ReactiveMappingRefBase",
    # Set refs
    "SetLikeRefBase",
    "MutableSetRefBase",
    "ReactiveSetRefBase",
    # ShapesSequence refs
    "ShapesSequenceRefBase",
    "MutableShapesSequenceRefBase",
    "ReactiveShapesSequenceRefBase",
    # ShapesMapping refs
    "ShapesMappingRefBase",
    "MutableShapesMappingRefBase",
    "ReactiveShapesMappingRefBase",
]
