from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, TypeVar

if TYPE_CHECKING:
    from loomi.state.interface.tree import AsyncStateProtocol, SyncStateProtocol

    from .context import ContextProtocol
    from .evaluator import AsyncEvaluatorProtocol, SyncEvaluatorProtocol
    from .operations import (
        AppOperationProtocol,
        BranchOperationProtocol,
        DelayOperationProtocol,
        FunctionOperationProtocol,
        LoopOperationProtocol,
        MapOperationProtocol,
        OperationProtocol,
        ParallelOperationProtocol,
        RetryOperationProtocol,
        SequenceOperationProtocol,
        SubscribeOperationProtocol,
        TimeoutOperationProtocol,
    )

__all__ = [
    # Context types
    "ContextT",
    "ContextT_co",
    "ContextT_contra",
    "SyncContextT",
    "SyncContextT_co",
    "SyncContextT_contra",
    "StateT_co",
    # Base operation types
    "OperationT",
    "OperationT_co",
    "OperationT_contra",
    # Atomic operations
    "FunctionOperationT",
    "FunctionOperationT_contra",
    "AppOperationT",
    "AppOperationT_contra",
    # Flow control operations
    "SequenceOperationT",
    "SequenceOperationT_contra",
    "ParallelOperationT",
    "ParallelOperationT_contra",
    "BranchOperationT",
    "BranchOperationT_contra",
    "LoopOperationT",
    "LoopOperationT_contra",
    # Timing operations
    "DelayOperationT",
    "DelayOperationT_contra",
    "TimeoutOperationT",
    "TimeoutOperationT_contra",
    "RetryOperationT",
    "RetryOperationT_contra",
    # Collection operations
    "MapOperationT",
    "MapOperationT_contra",
    # Reactive operations
    "SubscribeOperationT",
    "SubscribeOperationT_contra",
    # Evaluator types
    "EvaluatorT",
    "EvaluatorT_co",
    "EvaluatorT_contra",
    "SyncEvaluatorT",
    "SyncEvaluatorT_co",
    "SyncEvaluatorT_contra",
    "AsyncEvaluatorT",
    "AsyncEvaluatorT_co",
    "AsyncEvaluatorT_contra",
]


# --- Context types --- #

_Context: TypeAlias = "ContextProtocol[OperationProtocol, AsyncStateProtocol | SyncStateProtocol]"
_SyncContext: TypeAlias = "ContextProtocol[OperationProtocol, SyncStateProtocol]"

ContextT = TypeVar("ContextT", bound="_Context")
ContextT_co = TypeVar("ContextT_co", bound="_Context", covariant=True)
ContextT_contra = TypeVar("ContextT_contra", bound=_Context, contravariant=True)

SyncContextT = TypeVar("SyncContextT", bound="_SyncContext")
SyncContextT_co = TypeVar("SyncContextT_co", bound="_SyncContext", covariant=True)
SyncContextT_contra = TypeVar("SyncContextT_contra", bound="_SyncContext", contravariant=True)

StateT_co = TypeVar("StateT_co", bound="AsyncStateProtocol | SyncStateProtocol", covariant=True)

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

# --- Atomic operations --- #

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

# App operation
AppOperationT = TypeVar(
    "AppOperationT",
    bound="AppOperationProtocol",
)
AppOperationT_contra = TypeVar(
    "AppOperationT_contra",
    bound="AppOperationProtocol",
    contravariant=True,
)

# --- Flow control operations --- #

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

# Parallel operation
ParallelOperationT = TypeVar(
    "ParallelOperationT",
    bound="ParallelOperationProtocol",
)
ParallelOperationT_contra = TypeVar(
    "ParallelOperationT_contra",
    bound="ParallelOperationProtocol",
    contravariant=True,
)

# Branch operation
BranchOperationT = TypeVar(
    "BranchOperationT",
    bound="BranchOperationProtocol",
)
BranchOperationT_contra = TypeVar(
    "BranchOperationT_contra",
    bound="BranchOperationProtocol",
    contravariant=True,
)

# Loop operation
LoopOperationT = TypeVar(
    "LoopOperationT",
    bound="LoopOperationProtocol",
)
LoopOperationT_contra = TypeVar(
    "LoopOperationT_contra",
    bound="LoopOperationProtocol",
    contravariant=True,
)

# --- Timing operations --- #

# Delay operation
DelayOperationT = TypeVar(
    "DelayOperationT",
    bound="DelayOperationProtocol",
)
DelayOperationT_contra = TypeVar(
    "DelayOperationT_contra",
    bound="DelayOperationProtocol",
    contravariant=True,
)

# Timeout operation
TimeoutOperationT = TypeVar(
    "TimeoutOperationT",
    bound="TimeoutOperationProtocol",
)
TimeoutOperationT_contra = TypeVar(
    "TimeoutOperationT_contra",
    bound="TimeoutOperationProtocol",
    contravariant=True,
)

# Retry operation
RetryOperationT = TypeVar(
    "RetryOperationT",
    bound="RetryOperationProtocol",
)
RetryOperationT_contra = TypeVar(
    "RetryOperationT_contra",
    bound="RetryOperationProtocol",
    contravariant=True,
)

# --- Collection operations --- #

# Map operation
MapOperationT = TypeVar(
    "MapOperationT",
    bound="MapOperationProtocol",
)
MapOperationT_contra = TypeVar(
    "MapOperationT_contra",
    bound="MapOperationProtocol",
    contravariant=True,
)

# --- Reactive operations --- #

# Subscribe operation
SubscribeOperationT = TypeVar(
    "SubscribeOperationT",
    bound="SubscribeOperationProtocol",
)
SubscribeOperationT_contra = TypeVar(
    "SubscribeOperationT_contra",
    bound="SubscribeOperationProtocol",
    contravariant=True,
)

# --- Evaluator --- #

EvaluatorT = TypeVar(
    "EvaluatorT",
    bound="AsyncEvaluatorProtocol | SyncEvaluatorProtocol",
)
EvaluatorT_co = TypeVar(
    "EvaluatorT_co",
    bound="AsyncEvaluatorProtocol | SyncEvaluatorProtocol",
    covariant=True,
)
EvaluatorT_contra = TypeVar(
    "EvaluatorT_contra",
    bound="AsyncEvaluatorProtocol | SyncEvaluatorProtocol",
    contravariant=True,
)
AsyncEvaluatorT = TypeVar(
    "AsyncEvaluatorT",
    bound="AsyncEvaluatorProtocol",
)
AsyncEvaluatorT_co = TypeVar(
    "AsyncEvaluatorT_co",
    bound="AsyncEvaluatorProtocol",
    covariant=True,
)
AsyncEvaluatorT_contra = TypeVar(
    "AsyncEvaluatorT_contra",
    bound="AsyncEvaluatorProtocol",
    contravariant=True,
)
SyncEvaluatorT = TypeVar(
    "SyncEvaluatorT",
    bound="SyncEvaluatorProtocol",
)
SyncEvaluatorT_co = TypeVar(
    "SyncEvaluatorT_co",
    bound="SyncEvaluatorProtocol",
    covariant=True,
)
SyncEvaluatorT_contra = TypeVar(
    "SyncEvaluatorT_contra",
    bound="SyncEvaluatorProtocol",
    contravariant=True,
)
