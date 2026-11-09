"""Register the virtuals views with core ``Extractable``.

Every view is already the ``collections.abc`` type its virtuals collection base
is registered as (a ``Sequence``, ``MutableMapping``, ``Set``, ...), so core ops
recognize it with no help from here. What core cannot know is that a view is a
live handle over storage: a kv read hands out the view, not plain data. Each
view is registered with ``Extractable`` so that core ``Extract`` asks it for
``extract()`` (``nu.Dict(ref).extract()`` yields a dict, not a live view).
"""

from nu.domains.shape import Extractable
from virtuals.views import (
    ByteArrayView,
    EagerDictView,
    EagerFractionalIndexedDictView,
    EagerIndexedDictView,
    EagerKh57View,
    EagerListView,
    EagerLogIndexedDictView,
    FlatDictView,
    FlatListView,
    FrozenSetView,
    LazyDictView,
    LazyFractionalIndexedDictView,
    LazyIndexedDictView,
    LazyKh57View,
    LazyListView,
    LazyLogIndexedDictView,
    LightDictView,
    RingView,
    SetView,
    TupleView,
)


for _view in (
    EagerDictView,
    LazyDictView,
    EagerIndexedDictView,
    LazyIndexedDictView,
    EagerFractionalIndexedDictView,
    LazyFractionalIndexedDictView,
    EagerLogIndexedDictView,
    LazyLogIndexedDictView,
    EagerKh57View,
    LazyKh57View,
    FlatDictView,
    LightDictView,
    EagerListView,
    LazyListView,
    FlatListView,
    TupleView,
    ByteArrayView,
    RingView,
    SetView,
    FrozenSetView,
):
    Extractable.register(_view)
