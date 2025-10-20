"""Operation contract - pure RValues that produce values.

This module defines the Operation abstract class, which serves as the
base for all pure computations in the semantics layer.

Contract:
    - Operation[T](RValue): Pure computation returning type T
    - is_pure: Always True (enforced by base class)
    - execute(context): Returns value of type T

Operations represent deterministic computations with NO side effects:
    - Reading values from tree
    - Mathematical computations
    - Logical comparisons
    - Data transformations

Operations are:
    - Cacheable: Same input → same output
    - Composable: Can be nested freely
    - Parallelizable: No mutation conflicts
    - Serializable: Can be stored as data

Type Parameter:
    T: The return type of the operation

Examples:
        Operation[float]: Returns float (e.g., GetOp reading price)
        Operation[bool]: Returns bool (e.g., comparison operation)
        Operation[list[str]]: Returns list of strings (e.g., keys operation)

Design Philosophy:
    - Purity by contract (not enforcement)
    - Type-safe returns (generic type parameter)
    - Minimal interface (just execute)
    - Trust over verify (no runtime purity checks)

Concrete Implementations (in behavior/operations.py):
    - GetOp[T]: Read value from ref → T
    - LiteralValue[T]: Constant value → T
    - BinaryOp[T]: Binary operation → T
    - UnaryOp[T]: Unary operation → T
    - DomainOp[T]: Domain-specific computation → T

Example Usage:
    class GetOp(Operation[T]):
        def execute(self, context: Context) -> T:
            # Read from tree, return value
            return value

    # Type checker knows result type
    op: Operation[float] = GetOp(price_ref)
    result: float = op.execute(ctx)

Why Separate from RValue?
    - Explicit purity contract (Operation = always pure)
    - Type safety (generic return type)
    - Clear semantics (Operation vs Command distinction)
    - Better error messages (type checker can catch purity violations)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from .term import RValue


if TYPE_CHECKING:
    from ..types import Context


class Operation[T](RValue):
    """RValue that produces a value of type T.

    Base operations are always pure computations.
    Though, when composing operations, the overall operation remains pure as long as its children are pure.

    Operations are deterministic computations with no side effects.
    They can be cached, composed, and executed in any order.

    Type parameter T specifies the return type.
    """

    children: tuple[RValue, ...]
    """Child RValues that this operation depends on."""

    @property
    def is_pure(self) -> bool:
        """Operations purity depends on their children.

        Returns:
            True if all children are pure, False otherwise.
        """
        return all(child.is_pure for child in self.children)

    @abstractmethod
    def execute(self, context: Context) -> T:
        """Execute the operation and return a value.

        Args:
            context: Execution environment (tree + storage context)

        Returns:
            Computed value of type T
        """
        ...


__all__ = [
    "Operation",
]
