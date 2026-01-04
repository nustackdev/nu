"""RValue capability protocols.

These protocols define optional capabilities for RValue expressions.
Not all RValues support all operations - check protocol support before use.

The capability hierarchy enables composition:
- Numeric operations (addable, subtractable, etc.)
- Comparison operations (comparable, equalable)
- Logical operations (andable, orable)
- Collection access (indexable, iterable, sliceable)
- String operations (concatenable, formattable)

Example:
    >>> if isinstance(value, Addable):
    ...     result = value + other
"""

from __future__ import annotations

from typing import Protocol, TypeGuard, runtime_checkable


__all__ = [  # noqa: RUF022
    # Arithmetic capabilities
    "Addable",
    "Subtractable",
    "Multipliable",
    "Divisible",
    "FloorDivisible",
    "Modulable",
    "Powerable",
    "Negatable",
    "Absoluteable",
    # Comparison capabilities
    "Comparable",
    "Equalable",
    # Logical capabilities
    "Andable",
    "Orable",
    "Invertible",
    # Bitwise capabilities
    "BitwiseAndable",
    "BitwiseOrable",
    "BitwiseXorable",
    "BitwiseInvertible",
    "LeftShiftable",
    "RightShiftable",
    # Collection capabilities
    "Indexable",
    "Sliceable",
    "Lengthable",
    "Containable",
    "Iterable",
    # String capabilities
    "Concatenable",
    "Formattable",
    # Type guards
    "is_addable",
    "is_subtractable",
    "is_multipliable",
    "is_divisible",
    "is_comparable",
    "is_equalable",
    "is_andable",
    "is_orable",
    "is_indexable",
    "is_sliceable",
    "is_lengthable",
    "is_containable",
    "is_iterable",
]


# =============================================================================
# ARITHMETIC CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Addable[OtherT, ResultT](Protocol):
    """Protocol for values that support addition.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Addable):
        ...     result = value + 10
    """

    def __add__(self, other: OtherT) -> ResultT:
        """Add other to this value.

        Args:
            other: Value to add

        Returns:
            Result of addition
        """
        ...

    def __radd__(self, other: OtherT) -> ResultT:
        """Add this value to other (reverse).

        Args:
            other: Value to add to

        Returns:
            Result of addition
        """
        ...


@runtime_checkable
class Subtractable[OtherT, ResultT](Protocol):
    """Protocol for values that support subtraction.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Subtractable):
        ...     result = value - 10
    """

    def __sub__(self, other: OtherT) -> ResultT:
        """Subtract other from this value.

        Args:
            other: Value to subtract

        Returns:
            Result of subtraction
        """
        ...

    def __rsub__(self, other: OtherT) -> ResultT:
        """Subtract this value from other (reverse).

        Args:
            other: Value to subtract from

        Returns:
            Result of subtraction
        """
        ...


@runtime_checkable
class Multipliable[OtherT, ResultT](Protocol):
    """Protocol for values that support multiplication.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Multipliable):
        ...     result = value * 2
    """

    def __mul__(self, other: OtherT) -> ResultT:
        """Multiply this value by other.

        Args:
            other: Value to multiply by

        Returns:
            Result of multiplication
        """
        ...

    def __rmul__(self, other: OtherT) -> ResultT:
        """Multiply other by this value (reverse).

        Args:
            other: Value to multiply

        Returns:
            Result of multiplication
        """
        ...


@runtime_checkable
class Divisible[OtherT, ResultT](Protocol):
    """Protocol for values that support true division.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Divisible):
        ...     result = value / 2
    """

    def __truediv__(self, other: OtherT) -> ResultT:
        """Divide this value by other.

        Args:
            other: Value to divide by

        Returns:
            Result of division
        """
        ...

    def __rtruediv__(self, other: OtherT) -> ResultT:
        """Divide other by this value (reverse).

        Args:
            other: Value to divide

        Returns:
            Result of division
        """
        ...


@runtime_checkable
class FloorDivisible[OtherT, ResultT](Protocol):
    """Protocol for values that support floor division.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, FloorDivisible):
        ...     result = value // 2
    """

    def __floordiv__(self, other: OtherT) -> ResultT:
        """Floor divide this value by other.

        Args:
            other: Value to divide by

        Returns:
            Result of floor division
        """
        ...

    def __rfloordiv__(self, other: OtherT) -> ResultT:
        """Floor divide other by this value (reverse).

        Args:
            other: Value to divide

        Returns:
            Result of floor division
        """
        ...


@runtime_checkable
class Modulable[OtherT, ResultT](Protocol):
    """Protocol for values that support modulo operation.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Modulable):
        ...     result = value % 2
    """

    def __mod__(self, other: OtherT) -> ResultT:
        """Compute modulo of this value by other.

        Args:
            other: Value to modulo by

        Returns:
            Result of modulo
        """
        ...

    def __rmod__(self, other: OtherT) -> ResultT:
        """Compute modulo of other by this value (reverse).

        Args:
            other: Value to compute modulo of

        Returns:
            Result of modulo
        """
        ...


@runtime_checkable
class Powerable[OtherT, ResultT](Protocol):
    """Protocol for values that support exponentiation.

    Type Parameters:
        OtherT: Type of the exponent
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Powerable):
        ...     result = value**2
    """

    def __pow__(self, other: OtherT) -> ResultT:
        """Raise this value to the power of other.

        Args:
            other: Exponent

        Returns:
            Result of exponentiation
        """
        ...

    def __rpow__(self, other: OtherT) -> ResultT:
        """Raise other to the power of this value (reverse).

        Args:
            other: Base

        Returns:
            Result of exponentiation
        """
        ...


@runtime_checkable
class Negatable[ResultT](Protocol):
    """Protocol for values that support unary negation.

    Type Parameters:
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Negatable):
        ...     result = -value
    """

    def __neg__(self) -> ResultT:
        """Negate this value.

        Returns:
            Negated value
        """
        ...


@runtime_checkable
class Absoluteable[ResultT](Protocol):
    """Protocol for values that support absolute value.

    Type Parameters:
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Absoluteable):
        ...     result = abs(value)
    """

    def __abs__(self) -> ResultT:
        """Get absolute value.

        Returns:
            Absolute value
        """
        ...


# =============================================================================
# COMPARISON CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Comparable[OtherT, ResultT](Protocol):
    """Protocol for values that support ordering comparisons.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result (typically bool or BoolValue)

    Example:
        >>> if isinstance(value, Comparable):
        ...     is_greater = value > 100
    """

    def __gt__(self, other: OtherT) -> ResultT:
        """Check if this value is greater than other.

        Args:
            other: Value to compare to

        Returns:
            Comparison result
        """
        ...

    def __lt__(self, other: OtherT) -> ResultT:
        """Check if this value is less than other.

        Args:
            other: Value to compare to

        Returns:
            Comparison result
        """
        ...

    def __ge__(self, other: OtherT) -> ResultT:
        """Check if this value is greater than or equal to other.

        Args:
            other: Value to compare to

        Returns:
            Comparison result
        """
        ...

    def __le__(self, other: OtherT) -> ResultT:
        """Check if this value is less than or equal to other.

        Args:
            other: Value to compare to

        Returns:
            Comparison result
        """
        ...


@runtime_checkable
class Equalable[OtherT, ResultT](Protocol):
    """Protocol for values that support equality comparison.

    Note: We use .eq() and .ne() methods instead of == and != operators
    to avoid Python's default comparison semantics in the DSL context.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result (typically bool or BoolValue)

    Example:
        >>> if isinstance(value, Equalable):
        ...     is_equal = value.eq(100)
    """

    def eq(self, other: OtherT) -> ResultT:
        """Check if this value equals other.

        Args:
            other: Value to compare to

        Returns:
            Equality result
        """
        ...

    def ne(self, other: OtherT) -> ResultT:
        """Check if this value does not equal other.

        Args:
            other: Value to compare to

        Returns:
            Inequality result
        """
        ...


# =============================================================================
# LOGICAL CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Andable[OtherT, ResultT](Protocol):
    """Protocol for values that support logical AND.

    Note: We use .and_() method instead of & operator to avoid
    confusion with bitwise operations and Python's short-circuit semantics.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Andable):
        ...     result = value.and_(other)
    """

    def and_(self, other: OtherT) -> ResultT:
        """Logical AND with other.

        Args:
            other: Value to AND with

        Returns:
            Result of logical AND
        """
        ...


@runtime_checkable
class Orable[OtherT, ResultT](Protocol):
    """Protocol for values that support logical OR.

    Note: We use .or_() method instead of | operator to avoid
    confusion with bitwise operations and Python's short-circuit semantics.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Orable):
        ...     result = value.or_(other)
    """

    def or_(self, other: OtherT) -> ResultT:
        """Logical OR with other.

        Args:
            other: Value to OR with

        Returns:
            Result of logical OR
        """
        ...


@runtime_checkable
class Invertible[ResultT](Protocol):
    """Protocol for values that support logical NOT.

    Note: We use .not_() method instead of ~ operator.

    Type Parameters:
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Invertible):
        ...     result = value.not_()
    """

    def not_(self) -> ResultT:
        """Logical NOT.

        Returns:
            Result of logical NOT
        """
        ...


# =============================================================================
# BITWISE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class BitwiseAndable[OtherT, ResultT](Protocol):
    """Protocol for values that support bitwise AND.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, BitwiseAndable):
        ...     result = value.bitand(other)
    """

    def bitand(self, other: OtherT) -> ResultT:
        """Bitwise AND with other.

        Args:
            other: Value to AND with

        Returns:
            Result of bitwise AND
        """
        ...


@runtime_checkable
class BitwiseOrable[OtherT, ResultT](Protocol):
    """Protocol for values that support bitwise OR.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, BitwiseOrable):
        ...     result = value.bitor(other)
    """

    def bitor(self, other: OtherT) -> ResultT:
        """Bitwise OR with other.

        Args:
            other: Value to OR with

        Returns:
            Result of bitwise OR
        """
        ...


@runtime_checkable
class BitwiseXorable[OtherT, ResultT](Protocol):
    """Protocol for values that support bitwise XOR.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, BitwiseXorable):
        ...     result = value ^ other
    """

    def __xor__(self, other: OtherT) -> ResultT:
        """Bitwise XOR with other.

        Args:
            other: Value to XOR with

        Returns:
            Result of bitwise XOR
        """
        ...


@runtime_checkable
class BitwiseInvertible[ResultT](Protocol):
    """Protocol for values that support bitwise NOT.

    Type Parameters:
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, BitwiseInvertible):
        ...     result = value.bitnot()
    """

    def bitnot(self) -> ResultT:
        """Bitwise NOT.

        Returns:
            Result of bitwise NOT
        """
        ...


@runtime_checkable
class LeftShiftable[OtherT, ResultT](Protocol):
    """Protocol for values that support left shift.

    Type Parameters:
        OtherT: Type of the shift amount
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, LeftShiftable):
        ...     result = value << 2
    """

    def __lshift__(self, other: OtherT) -> ResultT:
        """Left shift by other.

        Args:
            other: Shift amount

        Returns:
            Result of left shift
        """
        ...


@runtime_checkable
class RightShiftable[OtherT, ResultT](Protocol):
    """Protocol for values that support right shift.

    Type Parameters:
        OtherT: Type of the shift amount
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, RightShiftable):
        ...     result = value >> 2
    """

    def __rshift__(self, other: OtherT) -> ResultT:
        """Right shift by other.

        Args:
            other: Shift amount

        Returns:
            Result of right shift
        """
        ...


# =============================================================================
# COLLECTION CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Indexable[KeyT, ValueT](Protocol):
    """Protocol for values that support index access.

    Type Parameters:
        KeyT: Type of the index/key
        ValueT: Type of the value

    Example:
        >>> if isinstance(value, Indexable):
        ...     item = value[0]
    """

    def __getitem__(self, key: KeyT) -> ValueT:
        """Get item at index/key.

        Args:
            key: Index or key

        Returns:
            Value at the position
        """
        ...


@runtime_checkable
class Sliceable[ResultT](Protocol):
    """Protocol for values that support slicing.

    Type Parameters:
        ResultT: Type of the slice result

    Example:
        >>> if isinstance(value, Sliceable):
        ...     subseq = value[1:5]
    """

    def slice_(self, start: int | None, stop: int | None, step: int | None = None) -> ResultT:
        """Get a slice of the value.

        Args:
            start: Start index (inclusive)
            stop: Stop index (exclusive)
            step: Step size

        Returns:
            Sliced result
        """
        ...


@runtime_checkable
class Lengthable[ResultT](Protocol):
    """Protocol for values that have a length.

    Type Parameters:
        ResultT: Type of the length result (typically int or IntValue)

    Example:
        >>> if isinstance(value, Lengthable):
        ...     size = value.len_()
    """

    def len_(self) -> ResultT:
        """Get the length of this value.

        Returns:
            Length value
        """
        ...


@runtime_checkable
class Containable[OtherT, ResultT](Protocol):
    """Protocol for values that support containment testing.

    Type Parameters:
        OtherT: Type of the item to check
        ResultT: Type of the result (typically bool or BoolValue)

    Example:
        >>> if isinstance(value, Containable):
        ...     exists = value.contains(item)
    """

    def contains(self, item: OtherT) -> ResultT:
        """Check if item is in this value.

        Args:
            item: Item to check for

        Returns:
            Containment result
        """
        ...


@runtime_checkable
class Iterable[ItemT](Protocol):
    """Protocol for values that can be iterated.

    Note: In the DSL context, we use .iter_() method to return
    an operation that produces the iterable at execution time.

    Type Parameters:
        ItemT: Type of the items

    Example:
        >>> if isinstance(value, Iterable):
        ...     for item in value.iter_().execute(ctx):
        ...         process(item)
    """

    def iter_(self) -> ItemT:
        """Get an iterable over this value.

        Returns:
            Iterable or operation producing iterable
        """
        ...


# =============================================================================
# STRING CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Concatenable[OtherT, ResultT](Protocol):
    """Protocol for values that support concatenation.

    Type Parameters:
        OtherT: Type of the other operand
        ResultT: Type of the result

    Example:
        >>> if isinstance(value, Concatenable):
        ...     result = value + " suffix"
    """

    def concat(self, other: OtherT) -> ResultT:
        """Concatenate with other.

        Args:
            other: Value to concatenate

        Returns:
            Concatenated result
        """
        ...


@runtime_checkable
class Formattable[ResultT](Protocol):
    """Protocol for values that support string formatting.

    Type Parameters:
        ResultT: Type of the result (typically str or StrValue)

    Example:
        >>> if isinstance(value, Formattable):
        ...     formatted = value.format_("Price: {}")
    """

    def format_(self, template: str) -> ResultT:
        """Format this value using template.

        Args:
            template: Format string template

        Returns:
            Formatted result
        """
        ...


# =============================================================================
# TYPE GUARDS
# =============================================================================


def is_addable(obj: object) -> TypeGuard[Addable]:
    """Check if object supports addition.

    Args:
        obj: Object to check

    Returns:
        True if object implements Addable protocol
    """
    return isinstance(obj, Addable)


def is_subtractable(obj: object) -> TypeGuard[Subtractable]:
    """Check if object supports subtraction.

    Args:
        obj: Object to check

    Returns:
        True if object implements Subtractable protocol
    """
    return isinstance(obj, Subtractable)


def is_multipliable(obj: object) -> TypeGuard[Multipliable]:
    """Check if object supports multiplication.

    Args:
        obj: Object to check

    Returns:
        True if object implements Multipliable protocol
    """
    return isinstance(obj, Multipliable)


def is_divisible(obj: object) -> TypeGuard[Divisible]:
    """Check if object supports division.

    Args:
        obj: Object to check

    Returns:
        True if object implements Divisible protocol
    """
    return isinstance(obj, Divisible)


def is_comparable(obj: object) -> TypeGuard[Comparable]:
    """Check if object supports ordering comparisons.

    Args:
        obj: Object to check

    Returns:
        True if object implements Comparable protocol
    """
    return isinstance(obj, Comparable)


def is_equalable(obj: object) -> TypeGuard[Equalable]:
    """Check if object supports equality comparison.

    Args:
        obj: Object to check

    Returns:
        True if object implements Equalable protocol
    """
    return isinstance(obj, Equalable)


def is_andable(obj: object) -> TypeGuard[Andable]:
    """Check if object supports logical AND.

    Args:
        obj: Object to check

    Returns:
        True if object implements Andable protocol
    """
    return isinstance(obj, Andable)


def is_orable(obj: object) -> TypeGuard[Orable]:
    """Check if object supports logical OR.

    Args:
        obj: Object to check

    Returns:
        True if object implements Orable protocol
    """
    return isinstance(obj, Orable)


def is_indexable(obj: object) -> TypeGuard[Indexable]:
    """Check if object supports index access.

    Args:
        obj: Object to check

    Returns:
        True if object implements Indexable protocol
    """
    return isinstance(obj, Indexable)


def is_sliceable(obj: object) -> TypeGuard[Sliceable]:
    """Check if object supports slicing.

    Args:
        obj: Object to check

    Returns:
        True if object implements Sliceable protocol
    """
    return isinstance(obj, Sliceable)


def is_lengthable(obj: object) -> TypeGuard[Lengthable]:
    """Check if object has length.

    Args:
        obj: Object to check

    Returns:
        True if object implements Lengthable protocol
    """
    return isinstance(obj, Lengthable)


def is_containable(obj: object) -> TypeGuard[Containable]:
    """Check if object supports containment testing.

    Args:
        obj: Object to check

    Returns:
        True if object implements Containable protocol
    """
    return isinstance(obj, Containable)


def is_iterable(obj: object) -> TypeGuard[Iterable]:
    """Check if object can be iterated.

    Args:
        obj: Object to check

    Returns:
        True if object implements Iterable protocol
    """
    return isinstance(obj, Iterable)
