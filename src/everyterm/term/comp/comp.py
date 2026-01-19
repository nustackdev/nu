"""Computation definitions.

Operation = deterministic, no side effects, cacheable
Command   = modifies state, transactional, explicit effects

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..term import RValue, Term


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Command",
    "Computation",
    "Operation",
]


# =============================================================================
# COMPUTATION - COMPUTES OR MUTATES
# =============================================================================


class Computation[ComputationResultT](RValue[ComputationResultT], ABC):
    """Base class for computations - both pure and impure.

    Computations perform computations or mutations on data.
    Unlike Values, Computations focus on transformation logic.

    Two types of computations:
    - Operation: Pure computation (no side effects)
    - Command: Impure mutation (has side effects)

    Type Parameters:
        ComputationResultT: The type of result this computation produces

    Example:
        >>> add_op = AddOp(a, b)  # Pure computation
        >>> set_cmd = SetCmd(ref, value)  # Impure computation
    """

    pass


# =============================================================================
# OPERATION - PURE COMPUTATIONS
# =============================================================================


class Operation[OperationResultT](Computation[OperationResultT]):
    """Pure computation that returns a value of type T.

    Operations are deterministic expressions with no side effects:
    - Reading values from tree
    - Arithmetic and logical computations
    - Comparisons and transformations

    Purity is compositional:
    - Operation is pure if all RValue children are pure
    - LValue children don't affect purity (they're locations)

    Generic type T specifies return type:
        Operation[float] → returns float
        Operation[bool]  → returns bool
        Operation[list[str]] → returns list of strings

    Examples (concrete implementations see in standard library or ecosystem repo):
        GetOp(price_ref)              → Operation[float]
        BinaryOp("gt", price, 100)    → Operation[bool]
        UnaryOp("neg", balance)       → Operation[float]
    """

    @property
    def is_pure(self) -> bool:
        """Operations are pure if all RValue children are pure.

        LValue children (refs) don't affect purity - they're just locations.
        Only RValue children can introduce impurity.

        Returns:
            True if all RValue children are pure
        """
        return all(child.is_pure for child in self.children if isinstance(child, Term))

    @abstractmethod
    def execute(self, context: Context) -> OperationResultT:
        """Execute pure computation and return typed result.

        Typical execution pattern:
        1. Evaluate all children
        2. Apply operation logic
        3. Return typed result

        Args:
            context: Execution environment

        Returns:
            Computed value of type T
        """
        ...


# =============================================================================
# COMMAND - IMPURE MUTATIONS
# =============================================================================


class Command[CommandResultT](Computation[CommandResultT]):
    """Impure mutation that returns a result of type T.

    Commands modify tree state with explicit side effects:
    - Writing values
    - Deleting entries
    - Updating based on current state

    Commands always return values:
    - Enables composition: outer.set(inner.set(x))
    - Useful patterns: "write and return", "delete and return old"
    - Natural chaining: price.set(100).get()

    Must execute in transactional context for atomicity.

    Examples (concrete implementations see in standard library or ecosystem repo):
        SetCmd(price_ref, 150.0)           → Command[float]
        DeleteCmd(orders_ref, "AAPL")      → Command[Order]
        UpdateCmd(balance_ref, lambda x: x * 1.1) → Command[float]
    """

    @property
    def is_pure(self) -> bool:
        """Commands are always impure by definition.

        Returns:
            False - commands always have side effects
        """
        return False

    @abstractmethod
    def execute(self, context: Context) -> CommandResultT:
        """Execute mutation and return result.

        Typical execution pattern:
        1. Resolve target location
        2. Perform mutation (write/delete/update)
        3. Return result (written value, old value, etc.)

        Must run within transaction context:
            with storage.transaction() as tx:
                ctx = Context(root_view, tx)
                result = command.execute(ctx)

        Args:
            context: Execution environment with transaction

        Returns:
            Result of type T (often the written/deleted value)
        """
        ...
