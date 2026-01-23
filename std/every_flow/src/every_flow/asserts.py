"""Assertion helper flows.

This module provides specialized assertion flows built on top of Assert.
These are pure compositions - no Python/async logic needed.

Collection Assertions:
    - AssertEmpty: Assert collection has no items
    - AssertNotEmpty: Assert collection has items

Existence Assertions:
    - AssertExists: Assert ref has a value (not missing)
    - AssertMissing: Assert ref is missing

Comparison Assertions:
    - AssertEquals: Assert ref equals a value
    - AssertNotEquals: Assert ref does not equal a value
    - AssertGreaterThan: Assert ref > value
    - AssertLessThan: Assert ref < value

Conditional Execution:
    - SkipIfEmpty: Execute child only if collection not empty
    - SkipIfNotEmpty: Execute child only if collection is empty
    - SkipIfMissing: Execute child only if ref exists
    - SkipIfExists: Execute child only if ref is missing
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everybase import (
    Existable,
    Gettable,
    KeysQueryable,
    Lengthable,
)

from .control import If
from .error import Assert


if TYPE_CHECKING:
    from every import Flow, Term


__all__ = [  # noqa: RUF022
    # Collection assertions
    "AssertEmpty",
    "AssertNotEmpty",
    # Existence assertions
    "AssertExists",
    "AssertMissing",
    # Comparison assertions
    "AssertEquals",
    "AssertNotEquals",
    "AssertGreaterThan",
    "AssertLessThan",
    "AssertGreaterOrEqual",
    "AssertLessOrEqual",
    # Conditional execution
    "SkipIfEmpty",
    "SkipIfNotEmpty",
    "SkipIfMissing",
    "SkipIfExists",
]


# =============================================================================
# COLLECTION ASSERTIONS
# =============================================================================


def AssertEmpty(  # noqa: N802
    ref: Any,  # Any ref with .length() method
    message: str = "Expected empty collection",
) -> Flow:
    """Assert that a collection is empty.

    Works with any ref that has a .length() method (ListRef, etc.)
    or a .keys().len_() chain (mappings).

    Args:
        ref: Reference to collection (must have .length() or .keys().len_())
        message: Error message if assertion fails

    Example:
        >>> AssertEmpty(MyState.items, "Items must be empty before init")
    """
    # Try .length() first (sequences), then .keys().len_() (mappings)
    if isinstance(ref, KeysQueryable):
        condition = ref.keys().len_() == 0
    elif isinstance(ref, Lengthable):
        condition = ref.length() == 0
    else:
        raise TypeError(f"ref must have .length() or .keys() method, got {type(ref)}")

    return Assert(condition, message)


def AssertNotEmpty(  # noqa: N802
    ref: Any,  # Any ref with .length() method
    message: str = "Expected non-empty collection",
) -> Flow:
    """Assert that a collection is not empty.

    Works with any ref that has a .length() method (ListRef, etc.)
    or a .keys().len_() chain (mappings).

    Args:
        ref: Reference to collection
        message: Error message if assertion fails

    Example:
        >>> AssertNotEmpty(MyState.items, "Items required")
    """
    if isinstance(ref, KeysQueryable):
        condition = ref.keys().len_() > 0
    elif isinstance(ref, Lengthable):
        condition = ref.length() > 0
    else:
        raise TypeError(f"ref must have .length() or .keys() method, got {type(ref)}")

    return Assert(condition, message)


# =============================================================================
# EXISTENCE ASSERTIONS
# =============================================================================


def AssertExists(  # noqa: N802
    ref: Any,  # Any ref with .exists() method
    message: str = "Expected value to exist",
) -> Flow:
    """Assert that a ref has a value (is not missing).

    Works with any ref that has an .exists() method.

    Args:
        ref: Reference to check
        message: Error message if assertion fails

    Example:
        >>> AssertExists(MyState.config, "Config must be set")
    """
    if not isinstance(ref, Existable):
        raise TypeError(f"ref must have .exists() method, got {type(ref)}")

    return Assert(ref.exists(), message)


def AssertMissing(  # noqa: N802
    ref: Any,  # Any ref with .missing() method
    message: str = "Expected value to be missing",
) -> Flow:
    """Assert that a ref has no value (is missing).

    Works with any ref that has a .missing() method.

    Args:
        ref: Reference to check
        message: Error message if assertion fails

    Example:
        >>> AssertMissing(MyState.lock, "Lock must not exist")
    """
    if not isinstance(ref, Existable):
        raise TypeError(f"ref must have .missing() method, got {type(ref)}")

    return Assert(ref.missing(), message)


# =============================================================================
# COMPARISON ASSERTIONS
# =============================================================================


def AssertEquals(  # noqa: N802
    ref: Any,  # Any ref with .get() method
    value: Any,
    message: str = "Values must be equal",
) -> Flow:
    """Assert that a ref's value equals the expected value.

    Args:
        ref: Reference to check (must have .get())
        value: Expected value
        message: Error message if assertion fails

    Example:
        >>> AssertEquals(MyState.status.get(), "active", "Status must be active")
    """
    # If ref is already a Term (e.g., from .get()), use it directly
    if isinstance(ref, Gettable):
        condition = ref.get() == value
    else:
        raise TypeError(f"ref must have .get() method, got {type(ref)}")

    return Assert(condition, message)


def AssertNotEquals(  # noqa: N802
    ref: Any,
    value: Any,
    message: str = "Values must not be equal",
) -> Flow:
    """Assert that a ref's value does not equal the given value.

    Args:
        ref: Reference to check
        value: Value that should not match
        message: Error message if assertion fails
    """
    if isinstance(ref, Gettable):
        condition = ref.get() != value
    else:
        raise TypeError(f"ref must have .get() method, got {type(ref)}")

    return Assert(condition, message)


def AssertGreaterThan(  # noqa: N802
    ref: Any,
    value: Any,
    message: str = "Value must be greater",
) -> Flow:
    """Assert that a ref's value is greater than the given value.

    Args:
        ref: Reference to check
        value: Value to compare against
        message: Error message if assertion fails

    Example:
        >>> AssertGreaterThan(MyState.count.get(), 0, "Count must be positive")
    """
    if isinstance(ref, Gettable):
        condition = ref.get() > value
    else:
        raise TypeError(f"ref must have .get() method, got {type(ref)}")

    return Assert(condition, message)


def AssertLessThan(  # noqa: N802
    ref: Any,
    value: Any,
    message: str = "Value must be less",
) -> Flow:
    """Assert that a ref's value is less than the given value.

    Args:
        ref: Reference to check
        value: Value to compare against
        message: Error message if assertion fails
    """
    if isinstance(ref, Gettable):
        condition = ref.get() < value
    else:
        raise TypeError(f"ref must have .get() method, got {type(ref)}")

    return Assert(condition, message)


def AssertGreaterOrEqual(  # noqa: N802
    ref: Any,
    value: Any,
    message: str = "Value must be greater or equal",
) -> Flow:
    """Assert that a ref's value is >= the given value.

    Args:
        ref: Reference to check
        value: Value to compare against
        message: Error message if assertion fails
    """
    if isinstance(ref, Gettable):
        condition = ref.get() >= value
    else:
        raise TypeError(f"ref must have .get() method, got {type(ref)}")

    return Assert(condition, message)


def AssertLessOrEqual(  # noqa: N802
    ref: Any,
    value: Any,
    message: str = "Value must be less or equal",
) -> Flow:
    """Assert that a ref's value is <= the given value.

    Args:
        ref: Reference to check
        value: Value to compare against
        message: Error message if assertion fails
    """
    if isinstance(ref, Gettable):
        condition = ref.get() <= value
    else:
        raise TypeError(f"ref must have .get() method, got {type(ref)}")

    return Assert(condition, message)


# =============================================================================
# CONDITIONAL EXECUTION
# =============================================================================


def SkipIfEmpty(  # noqa: N802
    ref: Any,
    child: Flow | Term,
    else_: Flow | Term | None = None,
) -> Flow:
    """Execute child only if collection is not empty.

    Args:
        ref: Reference to collection
        child: Flow to execute if not empty
        else_: Optional flow to execute if empty

    Example:
        >>> SkipIfEmpty(
        ...     MyState.items,
        ...     ProcessItems(),
        ...     Log("No items to process", "debug"),
        ... )
    """
    if isinstance(ref, KeysQueryable):
        condition = ref.keys().len_() > 0
    elif isinstance(ref, Lengthable):
        condition = ref.length() > 0
    else:
        raise TypeError(f"ref must have .length() or .keys() method, got {type(ref)}")

    return If(condition, child, else_)


def SkipIfNotEmpty(  # noqa: N802
    ref: Any,
    child: Flow | Term,
    else_: Flow | Term | None = None,
) -> Flow:
    """Execute child only if collection is empty.

    Args:
        ref: Reference to collection
        child: Flow to execute if empty
        else_: Optional flow to execute if not empty

    Example:
        >>> SkipIfNotEmpty(MyState.items, InitializeItems())
    """
    if isinstance(ref, KeysQueryable):
        condition = ref.keys().len_() == 0
    elif isinstance(ref, Lengthable):
        condition = ref.length() == 0
    else:
        raise TypeError(f"ref must have .length() or .keys() method, got {type(ref)}")

    return If(condition, child, else_)


def SkipIfMissing(  # noqa: N802
    ref: Any,
    child: Flow | Term,
    else_: Flow | Term | None = None,
) -> Flow:
    """Execute child only if ref exists (has value).

    Args:
        ref: Reference to check
        child: Flow to execute if exists
        else_: Optional flow to execute if missing

    Example:
        >>> SkipIfMissing(MyState.config, UseConfig())
    """
    if not isinstance(ref, Existable):
        raise TypeError(f"ref must have .exists() method, got {type(ref)}")

    return If(ref.exists(), child, else_)


def SkipIfExists(  # noqa: N802
    ref: Any,
    child: Flow | Term,
    else_: Flow | Term | None = None,
) -> Flow:
    """Execute child only if ref is missing (no value).

    Args:
        ref: Reference to check
        child: Flow to execute if missing
        else_: Optional flow to execute if exists

    Example:
        >>> SkipIfExists(MyState.lock, AcquireLock())
    """
    if not isinstance(ref, Existable):
        raise TypeError(f"ref must have .missing() method, got {type(ref)}")

    return If(ref.missing(), child, else_)
