"""Register virtuals view types with Python ABCs.

This allows everybase core ops (KeysOp, ValuesOp, SetItemCmd, etc.)
to recognize virtuals views via isinstance() checks against
collections.abc.Mapping, MutableMapping, etc.
"""

from collections.abc import MutableMapping, MutableSequence, MutableSet

from virtuals.views import (
    DictViewBase,
    FlatDictView,
    FlatListView,
    IndexedDictViewBase,
    LightDictView,
    ListViewBase,
    SetView,
)


# DictViewBase covers both EagerDictView and LazyDictView
MutableMapping.register(DictViewBase)

# IndexedDictViewBase covers both EagerIndexedDictView and LazyIndexedDictView
# (IndexedDictViewBase is a separate hierarchy from DictViewBase)
MutableMapping.register(IndexedDictViewBase)

# Flat/Light dict views (primitives-only, no nesting)
MutableMapping.register(FlatDictView)
MutableMapping.register(LightDictView)

# ListViewBase covers both EagerListView and LazyListView
MutableSequence.register(ListViewBase)

# FlatListView (primitives-only, separate hierarchy)
MutableSequence.register(FlatListView)

# SetView has no lazy/eager facets (primitives only)
MutableSet.register(SetView)
