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
    """FabricLifecycle Navigator. Reads its storage from ctx during setup."""

    def __init__(
        self,
        *,
        storage_type: type = RocksDBStorage,
        root_view: type = DictView,
    ) -> None:
        self._storage_type = storage_type
        self._root_view = root_view
        self._opened = False

    async def asetup(self, ctx: Context) -> None:
        storage = ctx.get(self._storage_type)
        _Navigator.__init__(self, storage, self._root_view)
        self._opened = True

    async def acleanup(self) -> None:
        self._opened = False
