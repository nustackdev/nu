from __future__ import annotations

from loomistd.kv_storage import StorageValueT

__all__ = [
    "TreePathComponent",
    "TreePath",
    "StorageValueContainer",
]

TreePathComponent = str
TreePath = tuple[TreePathComponent, ...]

# Return types that could be values or containers of values
StorageValueContainer = (
    StorageValueT | list["StorageValueT"] | dict[TreePathComponent, "StorageValueT"]
)
