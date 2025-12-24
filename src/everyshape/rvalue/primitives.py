"""RValue primitive type protocols.

This module defines protocols for primitive value types composed from
atomic capabilities. These form the type hierarchy for RValues.

Protocol Hierarchy:
    Number → Int, Float, Complex
    String
    Bool

Each protocol composes relevant capabilities for its type:
- Number: Addable, Subtractable, Multipliable, Divisible, Comparable
- String: Concatenable, Indexable, Sliceable, Lengthable
- Bool: Andable, Orable, Invertible
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .capabilities import (
    Absoluteable,
    Addable,
    Andable,
    BitwiseAndable,
    BitwiseInvertible,
    BitwiseOrable,
    BitwiseXorable,
    Comparable,
    Containable,
    Divisible,
    Equalable,
    FloorDivisible,
    Indexable,
    Invertible,
    LeftShiftable,
    Lengthable,
    Modulable,
    Multipliable,
    Negatable,
    Orable,
    Powerable,
    RightShiftable,
    Sliceable,
    Subtractable,
)


__all__ = [
    "Boolean",
    "Bytes",
    "Floating",
    "Integer",
    "Number",
    "String",
]


# =============================================================================
# NUMERIC PROTOCOLS
# =============================================================================


@runtime_checkable
class Number[T, R](
    Addable[T, R],
    Subtractable[T, R],
    Multipliable[T, R],
    Divisible[T, R],
    Comparable[T, R],
    Equalable[T, R],
    Negatable[R],
    Absoluteable[R],
    Protocol,
):
    """Protocol for numeric RValues.

    Numbers support arithmetic operations, comparisons, and sign operations.
    This is the base for all numeric types.

    Type Parameters:
        T: Type of operands for binary operations
        R: Type of results

    Example:
        >>> if isinstance(value, Number):
        ...     result = value + 10
        ...     is_positive = value > 0
        ...     magnitude = abs(value)
    """

    pass


@runtime_checkable
class Integer[T, R](
    Number[T, R],
    FloorDivisible[T, R],
    Modulable[T, R],
    Powerable[T, R],
    BitwiseAndable[T, R],
    BitwiseOrable[T, R],
    BitwiseXorable[T, R],
    BitwiseInvertible[R],
    LeftShiftable[T, R],
    RightShiftable[T, R],
    Protocol,
):
    """Protocol for integer RValues.

    Integers extend numbers with floor division, modulo, power,
    and bitwise operations.

    Type Parameters:
        T: Type of operands for binary operations
        R: Type of results

    Example:
        >>> if isinstance(value, Integer):
        ...     quotient = value // 2
        ...     remainder = value % 3
        ...     masked = value.bitand(0xFF)
    """

    pass


@runtime_checkable
class Floating[T, R](
    Number[T, R],
    Powerable[T, R],
    FloorDivisible[T, R],
    Modulable[T, R],
    Protocol,
):
    """Protocol for floating-point RValues.

    Floats extend numbers with power, floor division, and modulo.
    Unlike integers, floats don't support bitwise operations.

    Type Parameters:
        T: Type of operands for binary operations
        R: Type of results

    Example:
        >>> if isinstance(value, Floating):
        ...     squared = value**2
        ...     quotient = value // 2.0
    """

    pass


# =============================================================================
# BOOLEAN PROTOCOL
# =============================================================================


@runtime_checkable
class Boolean[T, R](
    Andable[T, R],
    Orable[T, R],
    Invertible[R],
    Equalable[T, R],
    Protocol,
):
    """Protocol for boolean RValues.

    Booleans support logical operations: AND, OR, NOT.

    Type Parameters:
        T: Type of operands for binary operations
        R: Type of results

    Example:
        >>> if isinstance(value, Boolean):
        ...     combined = value.and_(other)
        ...     opposite = value.not_()
    """

    pass


# =============================================================================
# STRING PROTOCOLS
# =============================================================================


@runtime_checkable
class String[T, R](
    Addable[T, R],
    Indexable[int, R],
    Sliceable[R],
    Lengthable[R],
    Containable[T, R],
    Comparable[T, R],
    Equalable[T, R],
    Protocol,
):
    """Protocol for string RValues.

    Strings support concatenation, indexing, slicing, length,
    containment testing, and comparison.

    Type Parameters:
        T: Type of operands for binary operations
        R: Type of results

    Example:
        >>> if isinstance(value, String):
        ...     full = value + " suffix"
        ...     first_char = value[0]
        ...     substring = value.slice_(0, 5)
        ...     has_sub = value.contains("test")
    """

    def upper(self) -> R:
        """Convert to uppercase.

        Returns:
            Uppercase version
        """
        ...

    def lower(self) -> R:
        """Convert to lowercase.

        Returns:
            Lowercase version
        """
        ...

    def strip(self) -> R:
        """Strip whitespace from both ends.

        Returns:
            Stripped string
        """
        ...

    def split(self, sep: str | None = None) -> R:
        """Split string by separator.

        Args:
            sep: Separator string, None for whitespace

        Returns:
            List of parts
        """
        ...

    def replace(self, old: str, new: str) -> R:
        """Replace occurrences of substring.

        Args:
            old: String to replace
            new: Replacement string

        Returns:
            String with replacements
        """
        ...

    def startswith(self, prefix: str) -> R:
        """Check if string starts with prefix.

        Args:
            prefix: Prefix to check

        Returns:
            True if starts with prefix
        """
        ...

    def endswith(self, suffix: str) -> R:
        """Check if string ends with suffix.

        Args:
            suffix: Suffix to check

        Returns:
            True if ends with suffix
        """
        ...


@runtime_checkable
class Bytes[T, R](
    Addable[T, R],
    Indexable[int, R],
    Sliceable[R],
    Lengthable[R],
    Containable[T, R],
    Comparable[T, R],
    Equalable[T, R],
    Protocol,
):
    """Protocol for bytes RValues.

    Bytes support concatenation, indexing, slicing, length,
    and containment testing.

    Type Parameters:
        T: Type of operands for binary operations
        R: Type of results

    Example:
        >>> if isinstance(value, Bytes):
        ...     combined = value + b" suffix"
        ...     first_byte = value[0]
        ...     chunk = value.slice_(0, 10)
    """

    def decode(self, encoding: str = "utf-8") -> R:
        """Decode bytes to string.

        Args:
            encoding: Character encoding

        Returns:
            Decoded string value
        """
        ...
