"""Document-model collection bases — items, sequences, mappings, sets.

Pure bases without Ref semantics. These combine everybase's pythonic
collection ops with eb_shape's document-model capabilities (existable,
extractable, storable, observable).

For concrete Python types (list, dict, tuple, set, frozenset), see eb_shape.types.
For Ref versions (with address/parent/shape navigation), see eb_shape.refs.

Substrates (eb_pv, eb_dict) inherit from eb_shape.refs, which
combine these bases with Ref.
"""

from .items import ItemBase, MutableItemBase, ReactiveItemBase
from .mapping import MappingBase, MutableMappingBase, ReactiveMappingBase
from .sequence import MutableSequenceBase, ReactiveSequenceBase, SequenceBase
from .set import MutableSetBase, ReactiveSetBase, SetLikeBase


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
    # Set bases
    "MutableSetBase",
    "ReactiveSetBase",
    "SetLikeBase",
]
