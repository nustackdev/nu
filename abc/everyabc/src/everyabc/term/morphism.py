"""Morphism — transformation hierarchy.

This module defines the execution model for transformations:

    Term                        - executable node
    └── RValue                  - evaluable expression (has children)
        └── Morphism            - transformation (maps inputs to outputs)
            └── NAryMorphism    - morphism with operands and children management
                ├── UnaryMorphism   - single operand (e.g., -x, abs(x), not x)
                ├── BinaryMorphism  - two operands (e.g., x + y, x > y)
                └── TernaryMorphism - three operands (e.g., if a then b else c)

Purity mixins (orthogonal to arity):
    - Operation: pure (no side effects)
    - Command: impure (has side effects)

Convenience classes (purity + arity):
    - NAryOperation / NAryCommand
    - UnaryOperation / UnaryCommand
    - BinaryOperation / BinaryCommand
    - TernaryOperation / TernaryCommand

Composition pattern:
    class AddOp(BinaryOperation[float]):
        def apply(self, left: float, right: float) -> float:
            return left + right

Design principles:
    - Minimal contracts: only essential methods
    - Uniform composition: children tuple for all operands
    - Type propagation: generic T flows through chains
    - Purity explicit: Operation/Command mixins
    - Sentinel propagation: INVALID returned on any sentinel operand

Children Management Interface:
    NAryMorphism provides a uniform interface for working with operands:
    - children: Get all children as tuple
    - iter_children(): Iterate over children
    - child_count: Number of children
    - get_child(index): Get child by index

Example usage:
>>> # Define a pure binary operation
>>> class AddOp(BinaryOperation[float]):
...     def apply(self, left: float, right: float) -> float:
...         return left + right

>>> # Use it
>>> add = AddOp(GetOp(price_ref), 100)
>>> result = add.execute(ctx)  # Resolves price_ref, adds 100

>>> # Define an impure command
>>> class SetCmd(UnaryCommand[T]):
...     def __init__(self, ref: Ref[T], value: T | Term[T]):
...         super().__init__(value)
...         self._ref = ref
...
...     def apply(self, value: T) -> T:
...         # Side effect: write to storage
...         self._ref.set(value, ctx)
...         return value
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .sentinel import INVALID, Sentinel, is_sentinel
from .term import RValue, Term


if TYPE_CHECKING:
    from everyabc.context import Context


__all__ = [  # noqa: RUF022
    # Base
    "Morphism",
    "NAryMorphism",
    "UnaryMorphism",
    "BinaryMorphism",
    "TernaryMorphism",
    # Purity mixins
    "Operation",
    "Command",
    # Purity + arity combinations
    "NAryOperation",
    "NAryCommand",
    "UnaryOperation",
    "UnaryCommand",
    "BinaryOperation",
    "BinaryCommand",
    "TernaryOperation",
    "TernaryCommand",
]


# =============================================================================
# MORPHISM BASE
# =============================================================================


class Morphism[T](RValue[T], ABC):
    """Transformation. Maps inputs to outputs.

    Morphisms are the fundamental unit of computation in the term system.
    They have operands (children) and produce results through transformation.

    This is the base class for all transformations. Concrete implementations
    should extend one of the arity-specific subclasses:
    - UnaryMorphism: single operand
    - BinaryMorphism: two operands
    - TernaryMorphism: three operands

    Or extend NAryMorphism directly for variable arity.

    Type Parameters:
        T: The type of result this morphism produces
    """

    def __init__(self, *children: object) -> None:
        """Initialize with operands.

        Args:
            *children: Variable number of operands
        """
        # FIXME: This is a core circular dependency!!
        from everybase import ensure_term

        super().__init__(*[ensure_term(c) for c in children])


# =============================================================================
# N-ARY MORPHISM WITH CHILDREN MANAGEMENT
# =============================================================================


class NAryMorphism[T](Morphism[T | Sentinel], ABC):
    """Base for morphisms with operands. Handles resolution and sentinels.

    Provides a uniform children management interface for working with operands.
    Subclasses with fixed arity should use UnaryMorphism, BinaryMorphism, or
    TernaryMorphism. Subclasses with variable arity can override __init__.

    Children can be:
    - Terms: executed to get values
    - Python literals: wrapped into PyRefs

    Sentinel propagation:
        If any operand resolves to a sentinel (EMPTY, INVALID),
        the morphism returns INVALID without calling apply().
    """

    def __init__(self, *children: object) -> None:
        """Initialize with operands.

        Args:
            *children: Variable number of operands
        """
        super().__init__(*children)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Resolve operands, propagate sentinels, apply transformation.

        Execution steps:
        1. Resolve all operands to values
        2. If any value is a sentinel, return INVALID
        3. Call apply() with resolved values
        4. Return result

        Args:
            ctx: Execution context

        Returns:
            Result of apply(), or INVALID if any operand is sentinel
        """
        values = []
        for child in self.children:
            val = await child.execute(ctx)
            if is_sentinel(val):
                return INVALID
            values.append(val)
        return self.apply(*values)

    @abstractmethod
    def apply(self, *values: Any) -> T | Sentinel:  # noqa: ANN401
        """Apply the transformation to resolved values.

        Called after all operands are resolved and verified non-sentinel.
        Implement this method to define the actual transformation logic.

        Args:
            *values: Resolved operand values (never sentinels)

        Returns:
            Result of the transformation
        """
        ...


# =============================================================================
# ARITY-SPECIFIC MORPHISMS
# =============================================================================


class UnaryMorphism[T](NAryMorphism[T], ABC):
    """Single operand morphism.

    For transformations with one input: -x, abs(x), not x, len(x), etc.

    Example:
        >>> class NegateOp(UnaryOperation[float]):
        ...     def apply(self, operand: float) -> float:
        ...         return -operand
        ...
        >>> neg = NegateOp(price_ref.get())
        >>> result = neg.execute(ctx)  # Returns negated price
    """

    def __init__(self, operand: object) -> None:
        """Initialize with single operand.

        Args:
            operand: The input
        """
        super().__init__(operand)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.operand!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.operand})"

    @property
    def operand(self) -> Term:
        """The single operand.

        Returns:
            The operand passed to __init__
        """
        return self._children[0]

    @abstractmethod
    def apply(self, operand: Any) -> T | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply transformation to resolved operand.

        Args:
            operand: Resolved operand value (never a sentinel)

        Returns:
            Result of the transformation
        """
        ...


class BinaryMorphism[T](NAryMorphism[T], ABC):
    """Two operand morphism.

    For transformations with two inputs: x + y, x > y, x and y, x[y], etc.

    Example:
        >>> class AddOp(BinaryOperation[float]):
        ...     def apply(self, left: float, right: float) -> float:
        ...         return left + right
        ...
        >>> add = AddOp(price_ref.get(), 100)
        >>> result = add.execute(ctx)  # Returns price + 100
    """

    def __init__(self, left: object, right: object) -> None:
        """Initialize with two operands.

        Args:
            left: Left operand
            right: Right operand
        """
        super().__init__(left, right)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.left!r}, {self.right!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.left}, {self.right})"

    @property
    def left(self) -> Term:
        """Left operand.

        Returns:
            First operand passed to __init__
        """
        return self._children[0]

    @property
    def right(self) -> Term:
        """Right operand.

        Returns:
            Second operand passed to __init__
        """
        return self._children[1]

    @abstractmethod
    def apply(self, left: Any, right: Any) -> T | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply transformation to resolved operands.

        Args:
            left: Resolved left operand value (never a sentinel)
            right: Resolved right operand value (never a sentinel)

        Returns:
            Result of the transformation
        """
        ...


class TernaryMorphism[T](NAryMorphism[T], ABC):
    """Three operand morphism.

    For transformations with three inputs: if a then b else c, slice(a, b, c), etc.

    Example:
        >>> class IfThenElseOp(TernaryOperation[T]):
        ...     def apply(self, cond: bool, then_val: T, else_val: T) -> T:
        ...         return then_val if cond else else_val
        ...
        >>> ite = IfThenElseOp(is_valid.get(), price.get(), default_price)
        >>> result = ite.execute(ctx)  # Returns price or default based on condition
    """

    def __init__(self, first: Term, second: Term, third: Term) -> None:
        """Initialize with three operands.

        Args:
            first: First operand
            second: Second operand
            third: Third operand
        """
        super().__init__(first, second, third)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.first!r}, {self.second!r}, {self.third!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.first}, {self.second}, {self.third})"

    @property
    def first(self) -> Term:
        """First operand.

        Returns:
            First operand passed to __init__
        """
        return self._children[0]

    @property
    def second(self) -> Term:
        """Second operand.

        Returns:
            Second operand passed to __init__
        """
        return self._children[1]

    @property
    def third(self) -> Term:
        """Third operand.

        Returns:
            Third operand passed to __init__
        """
        return self._children[2]

    @abstractmethod
    def apply(self, first: Any, second: Any, third: Any) -> T | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply transformation to resolved operands.

        Args:
            first: Resolved first operand value (never a sentinel)
            second: Resolved second operand value (never a sentinel)
            third: Resolved third operand value (never a sentinel)

        Returns:
            Result of the transformation
        """
        ...


# =============================================================================
# PURITY MIXINS
# =============================================================================


class Operation:
    """Mixin marking a morphism as pure (no side effects).

    Pure operations are:
    - Deterministic: same inputs → same output
    - Side-effect free: don't modify state
    - Cacheable: results can be memoized
    - Reorderable: execution order doesn't matter

    Usage:
        class AddOp(BinaryOperation[float]):
            def apply(self, left: float, right: float) -> float:
                return left + right
    """

    @property
    def is_self_pure(self) -> bool:
        """Operations are pure by definition.

        Returns:
            True - operations never have side effects
        """
        return True


class Command:
    """Mixin marking a morphism as impure (has side effects).

    Commands modify state and must be executed carefully:
    - Order-dependent: sequence of execution matters
    - Transactional: should run within transaction context
    - Not cacheable: results may differ each execution

    Usage:
        class SetCmd(UnaryCommand[T]):
            def __init__(self, ref: Ref[T], value: T | Term[T]):
                super().__init__(value)
                self._ref = ref

            def apply(self, value: T) -> T:
                # Side effect here
                return value
    """

    @property
    def is_self_pure(self) -> bool:
        """Commands are always impure by definition.

        Returns:
            False - commands always have side effects
        """
        return False


# =============================================================================
# CONVENIENCE: PURITY + ARITY COMBINATIONS
# =============================================================================


class NAryOperation[T](Operation, NAryMorphism[T]):
    """Pure NAry morphism. Shorthand for ``Operation, NAryMorphism[T]``."""

    pass


class NAryCommand[T](Command, NAryMorphism[T]):
    """Impure NAry morphism. Shorthand for ``Command, NAryMorphism[T]``."""

    pass


class UnaryOperation[T](Operation, UnaryMorphism[T]):
    """Pure unary morphism. Shorthand for ``Operation, UnaryMorphism[T]``."""

    pass


class UnaryCommand[T](Command, UnaryMorphism[T]):
    """Impure unary morphism. Shorthand for ``Command, UnaryMorphism[T]``."""

    pass


class BinaryOperation[T](Operation, BinaryMorphism[T]):
    """Pure binary morphism. Shorthand for ``Operation, BinaryMorphism[T]``."""

    pass


class BinaryCommand[T](Command, BinaryMorphism[T]):
    """Impure binary morphism. Shorthand for ``Command, BinaryMorphism[T]``."""

    pass


class TernaryOperation[T](Operation, TernaryMorphism[T]):
    """Pure ternary morphism. Shorthand for ``Operation, TernaryMorphism[T]``."""

    pass


class TernaryCommand[T](Command, TernaryMorphism[T]):
    """Impure ternary morphism. Shorthand for ``Command, TernaryMorphism[T]``."""

    pass
