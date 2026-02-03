"""Document-model collection bases — items, sequences, mappings, shapes.

These bases combine everybase's pythonic collection ops with everyshape's
document-model capabilities (existable, extractable, storable, observable).

Substrates (every_pv, every_dict) inherit from these and provide:
    - result(op): wrap collection-level operation results
    - element_result(op): wrap element-level operation results
    - iterable_result(op): (mappings only) wrap key/value/item query results
"""

from .items import ItemRef, MutableItemRef, ReactiveItemRef
from .mapping import MappingRefBase, MutableMappingRefBase, ReactiveMappingRefBase
from .sequence import MutableSequenceRefBase, ReactiveSequenceRefBase, SequenceRefBase
from .shapes_dict import MutableShapesDictRefBase, ReactiveShapesDictRefBase, ShapesDictRefBase
from .shapes_list import MutableShapesListRefBase, ReactiveShapesListRefBase, ShapesListRefBase


__all__ = [  # noqa: RUF022
    # Item refs
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
    # Sequence refs
    "MutableSequenceRefBase",
    "ReactiveSequenceRefBase",
    "SequenceRefBase",
    # Mapping refs
    "MappingRefBase",
    "MutableMappingRefBase",
    "ReactiveMappingRefBase",
    # ShapesList refs
    "MutableShapesListRefBase",
    "ReactiveShapesListRefBase",
    "ShapesListRefBase",
    # ShapesDict refs
    "MutableShapesDictRefBase",
    "ReactiveShapesDictRefBase",
    "ShapesDictRefBase",
]
