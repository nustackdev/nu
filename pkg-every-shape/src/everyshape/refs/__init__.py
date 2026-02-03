"""Document-model refs — collection bases + Ref navigation.

These combine pure collection bases from everyshape.collections with
Ref (address/parent/shape navigation) for substrate implementations.

Substrates (every_pv, every_dict) inherit from these.
"""

from .base import Ref
from .dict import MappingRefBase, MutableMappingRefBase, ReactiveMappingRefBase
from .dictshape import ReactiveShapesDictRefBase, ShapesDictRefBase
from .items import ItemRef, MutableItemRef, ReactiveItemRef
from .list import MutableSequenceRefBase, ReactiveSequenceRefBase, SequenceRefBase
from .listshape import ReactiveShapesListRefBase, ShapesListRefBase
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
    "MutableSequenceRefBase",
    "ReactiveSequenceRefBase",
    "SequenceRefBase",
    # Mapping refs
    "MappingRefBase",
    "MutableMappingRefBase",
    "ReactiveMappingRefBase",
    # ShapesList refs
    "ReactiveShapesListRefBase",
    "ShapesListRefBase",
    # ShapesDict refs
    "ReactiveShapesDictRefBase",
    "ShapesDictRefBase",
]
