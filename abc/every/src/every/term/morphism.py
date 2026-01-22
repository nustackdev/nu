"""Morphism-based transformation hierarchy.

This module defines the execution model for transformations:

    Term                        - executable node
    └── RValue                  - evaluable expression (has children)
        └── Morphism            - transformation (maps inputs to outputs)
            └── NAryMorphism    - morphism with operands and children management
                ├── UnaryMorphism   - single operand (e.g., -x, abs(x), not x)
                ├── BinaryMorphism  - two operands (e.g., x + y, x > y)
                └── TernaryMorphism - three operands (e.g., if a then b else c)

Purity is orthogonal - use mixins:
    - Operation: marks morphism as pure (no side effects)
    - Command: marks morphism as impure (has side effects)

Composition pattern:
    class AddOp(BinaryMorphism[float], Operation):
        def _apply(self, left: float, right: float) -> float:
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
    - child_count(): Number of children
    - get_child(index): Get child by index
    - iter_term_children(): Iterate only over Term children
    - iter_resolved(ctx): Iterate over resolved child values

Resolution order for operands:
    1. Term → execute()
    2. Gettable → get()
    3. Literal → use directly

Example usage:
>>> # Define a pure binary operation
>>> class AddOp(BinaryMorphism[float], Operation):
...     def _apply(self, left: float, right: float) -> float:
...         return left + right

>>> # Use it
>>> add = AddOp(GetOp(price_ref), 100)
>>> result = add.execute(ctx)  # Resolves price_ref, adds 100

>>> # Define an impure command
>>> class SetCmd(UnaryMorphism[T], Command):
...     def __init__(self, ref: Ref[T], value: T | Term[T]):
...         super().__init__(value)
...         self._ref = ref
...
...     def _apply(self, value: T) -> T:
...         # Side effect: write to storage
...         self._ref.set(value, ctx)
...         return value
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from every.protocols import Gettable
from every.sentinel import INVALID, Sentinel, is_sentinel

from .term import RValue, Term


if TYPE_CHECKING:
    from collections.abc import Iterator

    from .context import Context


__all__ = [
    "BinaryMorphism",
    "Command",
    "Morphism",
    "NAryMorphism",
    "Operation",
    "TernaryMorphism",
    "UnaryMorphism",
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

    pass


# =============================================================================
# N-ARY MORPHISM WITH CHILDREN MANAGEMENT
# =============================================================================


class NAryMorphism[T](Morphism[T], ABC):
    """Base for morphisms with operands. Handles resolution and sentinels.

    Provides a uniform children management interface for working with operands.
    Subclasses with fixed arity should use UnaryMorphism, BinaryMorphism, or
    TernaryMorphism. Subclasses with variable arity can override __init__.

    Children can be:
    - Terms: executed to get values
    - Gettable objects: get() called to extract values
    - Literals: used directly as values

    Sentinel propagation:
        If any operand resolves to a sentinel (EMPTY, INVALID),
        the morphism returns INVALID without calling _apply().

    Attributes:
        _children: Tuple of operands (Terms, Gettables, or literals)
    """

    _children: tuple[Term, ...]

    def __init__(self, *children: Term) -> None:
        """Initialize with operands.

        Args:
            *children: Variable number of operands (Terms, Gettables, or literals)
        """
        self._children = children

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    # =========================================================================
    # CHILDREN MANAGEMENT INTERFACE
    # =========================================================================

    @property
    def children(self) -> tuple[Term, ...]:
        """Get all children (operands).

        Returns:
            Tuple of all operands in order
        """
        return self._children

    def iter_children(self) -> Iterator[Term]:
        """Iterate over children.

        Yields:
            Each child in order
        """
        return iter(self._children)

    def child_count(self) -> int:
        """Number of children.

        Returns:
            Count of operands
        """
        return len(self._children)

    def get_child(self, index: int) -> Term:
        """Get child by index.

        Args:
            index: Zero-based index of the child

        Returns:
            The child at the given index

        Raises:
            IndexError: If index is out of bounds
        """
        return self._children[index]

    def iter_term_children(self) -> Iterator[Term]:
        """Iterate over children that are Terms (skip literals).

        Useful for traversal operations that only care about
        Term nodes in the expression tree.

        Yields:
            Each child that is a Term instance
        """
        for child in self._children:
            if isinstance(child, Term):
                yield child

    def iter_resolved(self, ctx: Context) -> Iterator[Any]:
        """Iterate over resolved child values.

        Resolves each child according to resolution order:
        1. Term → execute()
        2. Gettable → get()
        3. Literal → use directly

        Note: Does not propagate sentinels - caller must check.

        Args:
            ctx: Execution context

        Yields:
            Resolved value for each child (may include sentinels)
        """
        for child in self._children:
            yield self._resolve(child, ctx)

    # =========================================================================
    # EXECUTION
    # =========================================================================

    def execute(self, ctx: Context) -> T | Sentinel:
        """Resolve operands, propagate sentinels, apply transformation.

        Execution steps:
        1. Resolve all operands to values
        2. If any value is a sentinel, return INVALID
        3. Call _apply() with resolved values
        4. Return result

        Args:
            ctx: Execution context

        Returns:
            Result of _apply(), or INVALID if any operand is sentinel
        """
        values = []
        for child in self._children:
            val = self._resolve(child, ctx)
            if is_sentinel(val):
                return INVALID
            values.append(val)
        return self._apply(*values)

    def _resolve(self, operand: Any, ctx: Context) -> Any:  # noqa: ANN401
        """Resolve operand to value.

        Resolution order:
        1. Term → execute()
        2. Gettable → get()
        3. Literal → use directly

        Args:
            operand: The operand to resolve
            ctx: Execution context

        Returns:
            Resolved value (may be a sentinel)
        """
        if isinstance(operand, Term):
            return operand.execute(ctx)
        if isinstance(operand, Gettable):
            return operand.get(ctx)
        return operand

    @abstractmethod
    def _apply(self, *values: Any) -> T | Sentinel:  # noqa: ANN401
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
        >>> class NegateOp(UnaryMorphism[float], Operation):
        ...     def _apply(self, operand: float) -> float:
        ...         return -operand
        ...
        >>> neg = NegateOp(price_ref.get())
        >>> result = neg.execute(ctx)  # Returns negated price
    """

    def __init__(self, operand: Term) -> None:
        """Initialize with single operand.

        Args:
            operand: The input (Term, Gettable, or literal)
        """
        self._children = (operand,)

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
    def _apply(self, operand: Any) -> T | Sentinel:  # noqa: ANN401
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
        >>> class AddOp(BinaryMorphism[float], Operation):
        ...     def _apply(self, left: float, right: float) -> float:
        ...         return left + right
        ...
        >>> add = AddOp(price_ref.get(), 100)
        >>> result = add.execute(ctx)  # Returns price + 100
    """

    def __init__(self, left: Term, right: Term) -> None:
        """Initialize with two operands.

        Args:
            left: Left operand (Term, Gettable, or literal)
            right: Right operand (Term, Gettable, or literal)
        """
        self._children = (left, right)

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
    def _apply(self, left: Any, right: Any) -> T | Sentinel:  # noqa: ANN401
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
        >>> class IfThenElseOp(TernaryMorphism[T], Operation):
        ...     def _apply(self, cond: bool, then_val: T, else_val: T) -> T:
        ...         return then_val if cond else else_val
        ...
        >>> ite = IfThenElseOp(is_valid.get(), price.get(), default_price)
        >>> result = ite.execute(ctx)  # Returns price or default based on condition
    """

    def __init__(self, first: Term, second: Term, third: Term) -> None:
        """Initialize with three operands.

        Args:
            first: First operand (Term, Gettable, or literal)
            second: Second operand (Term, Gettable, or literal)
            third: Third operand (Term, Gettable, or literal)
        """
        self._children = (first, second, third)

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
    def _apply(self, first: Any, second: Any, third: Any) -> T | Sentinel:  # noqa: ANN401
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

    Purity is compositional: an Operation is pure only if
    all its Term children are also pure.

    Usage:
        class AddOp(BinaryMorphism[float], Operation):
            def _apply(self, left: float, right: float) -> float:
                return left + right
    """

    # Type hint for children from NAryMorphism
    _children: tuple[Term | Any, ...]

    @property
    def is_pure(self) -> bool:
        """Whether this operation is pure.

        An operation is pure if all its Term children are pure.
        Non-Term children (literals) don't affect purity.

        Returns:
            True if all Term children are pure
        """
        return all(child.is_pure for child in self._children if isinstance(child, Term))


class Command:
    """Mixin marking a morphism as impure (has side effects).

    Commands modify state and must be executed carefully:
    - Order-dependent: sequence of execution matters
    - Transactional: should run within transaction context
    - Not cacheable: results may differ each execution

    Usage:
        class SetCmd(UnaryMorphism[T], Command):
            def __init__(self, ref: Ref[T], value: T | Term[T]):
                super().__init__(value)
                self._ref = ref

            def _apply(self, value: T) -> T:
                # Side effect here
                return value
    """

    @property
    def is_pure(self) -> bool:
        """Commands are always impure by definition.

        Returns:
            False - commands always have side effects
        """
        return False
