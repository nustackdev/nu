from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, TypeVar

if TYPE_CHECKING:
    from loomi.interfaces.state.tree import AsyncTreeDictProtocol, SyncTreeDictProtocol

    from .context import ContextProtocol
    from .executor import AsyncExecutorProtocol, SyncExecutorProtocol
    from .operations import FunctionOperationProtocol, OperationProtocol, SequenceOperationProtocol

__all__ = [
    "OperationT",
    "OperationT_co",
    "OperationT_contra",
    "FunctionOperationT",
    "FunctionOperationT_contra",
    "SequenceOperationT",
    "SequenceOperationT_contra",
    "ContextT",
    "ContextT_co",
    "ContextT_contra",
    "SyncContextT",
    "SyncContextT_co",
    "SyncContextT_contra",
    "StateDictT_co",
]


# --- Context types --- #

_Context: TypeAlias = (
    "ContextProtocol[OperationProtocol, AsyncTreeDictProtocol | SyncTreeDictProtocol]"
)
_SyncContext: TypeAlias = "ContextProtocol[OperationProtocol, SyncTreeDictProtocol]"

ContextT = TypeVar("ContextT", bound="_Context")
ContextT_co = TypeVar("ContextT_co", bound="_Context", covariant=True)
ContextT_contra = TypeVar("ContextT_contra", bound=_Context, contravariant=True)

SyncContextT = TypeVar("SyncContextT", bound="_SyncContext")
SyncContextT_co = TypeVar("SyncContextT_co", bound="_SyncContext", covariant=True)
SyncContextT_contra = TypeVar("SyncContextT_contra", bound="_SyncContext", contravariant=True)

StateDictT_co = TypeVar(
    "StateDictT_co", bound="AsyncTreeDictProtocol | SyncTreeDictProtocol", covariant=True
)

# --- Operation types --- #

# Base operation
OperationT = TypeVar(
    "OperationT",
    bound="OperationProtocol",
)
OperationT_co = TypeVar(
    "OperationT_co",
    bound="OperationProtocol",
    covariant=True,
)
OperationT_contra = TypeVar(
    "OperationT_contra",
    bound="OperationProtocol",
    contravariant=True,
)

# Function operation
FunctionOperationT = TypeVar(
    "FunctionOperationT",
    bound="FunctionOperationProtocol",
)
FunctionOperationT_contra = TypeVar(
    "FunctionOperationT_contra",
    bound="FunctionOperationProtocol",
    contravariant=True,
)

# Sequence operation
SequenceOperationT = TypeVar(
    "SequenceOperationT",
    bound="SequenceOperationProtocol",
)
SequenceOperationT_contra = TypeVar(
    "SequenceOperationT_contra",
    bound="SequenceOperationProtocol",
    contravariant=True,
)

# --- Executor --- #

ExecutorT = TypeVar(
    "ExecutorT",
    bound="AsyncExecutorProtocol | SyncExecutorProtocol",
)
ExecutorT_co = TypeVar(
    "ExecutorT_co",
    bound="AsyncExecutorProtocol | SyncExecutorProtocol",
    covariant=True,
)
ExecutorT_contra = TypeVar(
    "ExecutorT_contra",
    bound="AsyncExecutorProtocol | SyncExecutorProtocol",
    contravariant=True,
)
SyncExecutorT = TypeVar(
    "SyncExecutorT",
    bound="SyncExecutorProtocol",
)
SyncExecutorT_co = TypeVar(
    "SyncExecutorT_co",
    bound="SyncExecutorProtocol",
    covariant=True,
)
SyncExecutorT_contra = TypeVar(
    "SyncExecutorT_contra",
    bound="SyncExecutorProtocol",
    contravariant=True,
)
