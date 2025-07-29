from __future__ import annotations

from typing import Literal, TypeAlias, Union

from loomi._behaviors.state.backend import SnapshotProtocol, TransactionProtocol
from loomi._behaviors.state.path import Path
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

ExpressionValue = Value | Empty | Query | Path
ExpressionPath = tuple[str, ...] | str | Path
StorageContext = Union["SnapshotProtocol | TransactionProtocol"]
