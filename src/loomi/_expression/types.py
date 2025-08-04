from __future__ import annotations

from typing import Literal, TypeAlias, Union

from loomi._tree.backend import SnapshotProtocol, TransactionProtocol
from loomi._tree.path import ExtendedPath, Path
from loomi._tree.query import Query
from loomi._tree.tree import Empty
from loomi._tree.tree.types import Value

__all__ = [
    "ErrorBehavior",
    "ExpressionValue",
    "ExpressionPath",
    "StorageContext",
]

ErrorBehavior: TypeAlias = Literal["fail", "continue"]

ExpressionValue = Value | Empty | Query | Path | ExtendedPath
ExpressionPath = tuple[str, ...] | str | Path | ExtendedPath
StorageContext = Union["SnapshotProtocol | TransactionProtocol"]
