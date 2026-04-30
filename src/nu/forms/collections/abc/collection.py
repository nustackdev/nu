"""Collection capability.

CollectionForm = Sized + Iterable + Container.

Follows Python's collections.abc.Collection pattern.

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
    ElementResultT: Wrapped result for element-level operations
"""

from __future__ import annotations

from .container import ContainerForm
from .iterable import IterableForm
from .sized import SizedForm


__all__ = [
    "CollectionForm",
]


class CollectionForm[ElementT, CollectionResultT, ElementResultT](
    SizedForm,
    IterableForm[ElementT, CollectionResultT, ElementResultT],
    ContainerForm,
):
    """Base for collection values - like collections.abc.Collection.

    Inherits len() from SizedForm, __contains__ from ContainerForm,
    and wrapping infrastructure from IterableForm.

    Type Parameters:
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops
        ElementResultT: Result for element-level ops
    """

    pass
