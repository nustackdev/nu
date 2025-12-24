"""Base RValue implementation.

This module defines the base class for concrete RValue implementations.
RValueBase provides the foundation for building type-specific values
that represent already computed/available values in the DSL.

Key difference from LValues:
- RValues are ALREADY COMPUTED values available in memory
- LValues are LOCATIONS in storage that need to be accessed

RValues compose through the Term system's children tuple and
support operator overloading via ergonomics mixins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from everyshape.shape.context import ContextProtocol
from everyshape.shape.core.ergonomics import ErgonomicsMixin


if TYPE_CHECKING:
    from everyshape.shape.term import Term


__all__ = [
    "RValueBase",
]


class RValueBase[T, ContextT: ContextProtocol](ErgonomicsMixin[T, ContextT], ABC):
    """Base class for all RValue implementations.

    RValueBase provides the foundation for concrete value types:
    - IntValue, FloatValue, BoolValue, StrValue (primitives)
    - ListValue, DictValue, SetValue, TupleValue (collections)

    RValues represent computed/literal values that are available
    during expression building. They participate in the Term tree
    and can be executed to produce their value.

    Type Parameters:
        T: The native Python type this RValue wraps
        ContextT: The execution context type

    Attributes:
        children: Tuple of child terms this RValue depends on
        is_pure: Whether this RValue has side effects (always True for values)

    Design Principles:
        - Immutable: RValue instances don't change after creation
        - Composable: Can be combined via operators to form expressions
        - Type-safe: Generic type parameter ensures type consistency
        - Lazy-friendly: Can be evaluated lazily through execute()

    Example:
        >>> # Direct value creation
        >>> price = FloatValue(99.99)
        >>> # Operations produce new RValues
        >>> total = price * quantity  # Returns Operation
    """

    # Class-level type hint for the wrapped value type
    VALUE_TYPE: ClassVar[type]

    @property
    def children(self) -> tuple[Term, ...]:
        """Terms this RValue depends on.

        For literal values, this is empty. For computed RValues
        (like operation results), this includes the operands.

        Returns:
            Tuple of dependent terms
        """
        return ()

    @property
    def is_pure(self) -> bool:
        """Whether this RValue has side effects.

        RValues are always pure - they represent values, not mutations.

        Returns:
            True (always pure)
        """
        return True

    @abstractmethod
    def execute(self, context: ContextT) -> T:
        """Execute this RValue to produce its native Python value.

        For literal values, this simply returns the wrapped value.
        For computed RValues, this evaluates the expression tree.

        Args:
            context: Execution context (may be unused for literals)

        Returns:
            The native Python value of type T
        """
        ...

    @abstractmethod
    def unwrap(self) -> T:
        """Get the raw wrapped value without execution context.

        This is useful for literal values where execution context
        is not needed. Computed RValues may raise an error.

        Returns:
            The native Python value of type T

        Raises:
            RuntimeError: If the value requires execution context
        """
        ...


class LiteralBase[T, ContextT: ContextProtocol](RValueBase[T, ContextT], ABC):
    """Base class for literal (constant) RValues.

    Literal values wrap native Python values directly and don't
    require any computation to produce their value.

    Type Parameters:
        T: The native Python type this literal wraps
        ContextT: The execution context type

    Example:
        >>> lit = IntLiteral(42)
        >>> lit.unwrap()  # Returns 42
        >>> lit.execute(ctx)  # Returns 42
    """

    _value: T

    def __init__(self, value: T) -> None:
        """Initialize literal with value.

        Args:
            value: The native Python value to wrap
        """
        self._value = value

    def execute(self, context: ContextT) -> T:
        """Execute returns the wrapped value.

        Args:
            context: Unused for literals

        Returns:
            The wrapped value
        """
        return self._value

    def unwrap(self) -> T:
        """Get the wrapped value directly.

        Returns:
            The wrapped value
        """
        return self._value

    def __repr__(self) -> str:
        """Machine-readable representation."""
        return f"{self.__class__.__name__}({self._value!r})"

    def __str__(self) -> str:
        """Human-readable representation."""
        return str(self._value)
