from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from loomi.interfaces.state.tree import AsyncTreeDictProtocol, SyncTreeDictProtocol

    from .context.context import Context
    from .operations.base import Operation
    from .operations.function import Function
    from .operations.sequence import Sequence

__all__ = [
    "ContextT",
    "OperationT",
    "OperationT_co",
    "OperationT_contra",
    "FunctionOperationT",
    "FunctionOperationT_co",
    "FunctionOperationT_contra",
    "SequenceOperationT",
    "SequenceOperationT_co",
    "SequenceOperationT_contra",
]

ContextT = TypeVar("ContextT", bound=Context["AsyncTreeDictProtocol | SyncTreeDictProtocol"])
OperationT = TypeVar("OperationT", bound=Operation)
OperationT_co = TypeVar("OperationT_co", bound=Operation, covariant=True)
OperationT_contra = TypeVar("OperationT_contra", bound=Operation, contravariant=True)
FunctionOperationT = TypeVar("FunctionOperationT", bound=Function)
FunctionOperationT_co = TypeVar("FunctionOperationT_co", bound=Function, covariant=True)
FunctionOperationT_contra = TypeVar("FunctionOperationT_contra", bound=Function, contravariant=True)
SequenceOperationT = TypeVar("SequenceOperationT", bound=Sequence)
SequenceOperationT_co = TypeVar("SequenceOperationT_co", bound=Sequence, covariant=True)
SequenceOperationT_contra = TypeVar("SequenceOperationT_contra", bound=Sequence, contravariant=True)
