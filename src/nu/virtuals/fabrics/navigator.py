"""``Navigator`` Nu fabric wrapping ``virtuals.Navigator``.

FabricLifecycle. Reads the storage from ctx (by ``storage_type`` - defaults
to ``RocksDBStorage``) and initializes the parent ``Navigator`` against it.
``root_view`` picks the top-level view type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from virtuals import Navigator as _Navigator
from virtuals.views import DictView

from .storage import RocksDBStorage


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["Navigator"]


class Navigator(_Navigator):
    """FabricLifecycle Navigator. Reads its storage from ctx during setup.

    ``storage_tags`` targets a specific storage binding when multiple shards
    are bound under the same ``storage_type`` with distinct tags. Empty for
    the default unscoped binding.

    ``_nu_bind_as`` steers ``Provide``/``InvisiblesProxy`` to bind instances
    under the raw ``virtuals.Navigator`` base so lookups (e.g. atomicity's
    ``ctx.get(Navigator, ...)``) resolve the same class the rest of the
    virtuals stack queries for.
    """

    _nu_bind_as = _Navigator

    def __init__(
        self,
        *,
        storage_type: type = RocksDBStorage,
        storage_tags: tuple[object, ...] = (),
        root_view: type = DictView,
    ) -> None:
        self._storage_type = storage_type
        self._storage_tags = tuple(storage_tags)
        self._root_view = root_view
        self._opened = False

    async def asetup(self, ctx: Context) -> None:
        storage = ctx.get(self._storage_type, *self._storage_tags)
        _Navigator.__init__(self, storage, self._root_view)
        self._opened = True

    async def acleanup(self) -> None:
        self._opened = False
