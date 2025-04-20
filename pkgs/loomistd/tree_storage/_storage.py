from __future__ import annotations

from abc import ABC
from typing import Any, Generic

from loomi.attr import Attach
from loomi.interfaces.state.kv import (
    AsyncTransactionContextManagerProtocol,
    AsyncTransactionProtocol,
)
from loomi.service import AsyncService
from loomistd.kv_storage import StorageServiceProtocol

from ._core import TreeStorage as TreeStorageCore
from ._nodes import TreeDict, TreeList
from ._types import TreePath, TreePathComponent, TreeValueT

__all__ = [
    "TreeStorageBase",
    "TreeStorage",
]


class TreeStorageBase(ABC, Generic[TreeValueT]):
    """
    A class to manage tree storage using a dictionary.
    """

    _tree_storage_core: TreeStorageCore[TreeValueT]

    async def dict(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> TreeDict[TreeValueT]:
        """
        Get a nested dictionary node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new TreeDict instance for the nested dictionary node
        """
        dict_path = (path,) + paths
        return await self._tree_storage_core.dict(dict_path, txn=txn)

    async def list(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> TreeList[TreeValueT]:
        """
        Get a nested list node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new TreeList instance for the nested list node
        """
        list_path = (path,) + paths
        return await self._tree_storage_core.list(list_path, txn=txn)

    async def is_dict(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if the path is a dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path is a dictionary node, False otherwise
        """
        dict_path = (path,) + paths
        return await self._tree_storage_core.is_dict(dict_path, txn=txn)

    async def is_list(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if the path is a list node.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path is a list node, False otherwise
        """
        list_path = (path,) + paths
        return await self._tree_storage_core.is_list(list_path, txn=txn)

    async def exists(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if the path exists.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path exists, False otherwise
        """
        exists_path = (path,) + paths
        return await self._tree_storage_core.exists(exists_path, txn=txn)

    async def begin_transaction(self) -> AsyncTransactionProtocol[TreeValueT]:
        """
        Begin a new transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        return await self._tree_storage_core._storage.begin_transaction()

    async def transaction(self) -> AsyncTransactionContextManagerProtocol[TreeValueT]:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager for use in async with statements
        """
        return await self._tree_storage_core._storage.transaction()


class TreeStorage(AsyncService, TreeStorageBase[TreeValueT]):
    _kv_storage: StorageServiceProtocol[TreePath, TreeValueT, Any, Any] = Attach(
        StorageServiceProtocol
    )

    async def setup(self):
        """
        Setup the tree storage.
        """
        self._tree_storage_core = TreeStorageCore(self._kv_storage)
