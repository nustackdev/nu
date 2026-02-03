"""Document-model collection bases — items, sequences, mappings, shapes.

Pure bases without Ref semantics. These combine everybase's pythonic
collection ops with everyshape's document-model capabilities (existable,
extractable, storable, observable).

For Ref versions (with address/parent/shape navigation), see everyshape.refs.

Substrates (every_pv, every_dict) inherit from everyshape.refs, which
combine these bases with Ref.
"""

from .items import ItemBase, MutableItemBase, ReactiveItemBase
from .mapping import MappingBase, MutableMappingBase, ReactiveMappingBase
from .sequence import MutableSequenceBase, ReactiveSequenceBase, SequenceBase
from .shapes_dict import MutableShapesDictBase, ReactiveShapesDictBase, ShapesDictBase
from .shapes_list import MutableShapesListBase, ReactiveShapesListBase, ShapesListBase


__all__ = [  # noqa: RUF022
    # Item bases
    "ItemBase",
    "MutableItemBase",
    "ReactiveItemBase",
    # Sequence bases
    "MutableSequenceBase",
    "ReactiveSequenceBase",
    "SequenceBase",
    # Mapping bases
    "MappingBase",
    "MutableMappingBase",
    "ReactiveMappingBase",
    # ShapesList bases
    "MutableShapesListBase",
    "ReactiveShapesListBase",
    "ShapesListBase",
    # ShapesDict bases
    "MutableShapesDictBase",
    "ReactiveShapesDictBase",
    "ShapesDictBase",
]
