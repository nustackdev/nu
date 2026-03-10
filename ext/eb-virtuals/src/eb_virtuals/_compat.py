"""Register virtuals view types with Python ABCs.

This allows everybase core morphisms (KeysOp, ValuesOp, SetItemCmd, etc.)
to recognize virtuals views via isinstance() checks against
collections.abc.Mapping, MutableMapping, etc.
"""

from collections.abc import MutableMapping, MutableSequence, MutableSet

from virtuals.views import DictViewBase, ListViewBase, SetView


# DictViewBase covers both EagerDictView and LazyDictView
MutableMapping.register(DictViewBase)

# ListViewBase covers both EagerListView and LazyListView
MutableSequence.register(ListViewBase)

# SetView has no lazy/eager facets (primitives only)
MutableSet.register(SetView)
