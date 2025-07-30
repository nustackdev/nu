from __future__ import annotations

from typing import Literal, TypeAlias, Union

from loomi._behaviors.state.backend import SnapshotProtocol, TransactionProtocol
from loomi._behaviors.state.path import ExtendedPath, Path
from loomi._behaviors.state.query import Query
from loomi._behaviors.state.tree import Empty
from loomi._behaviors.state.tree.types import Value

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
