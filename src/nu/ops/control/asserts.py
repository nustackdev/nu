"""Assert and conditional-skip utility functions.

Composable helpers that return ``Assert`` or ``If`` flow instances.
These are pure functions (not classes) that construct flows from
duck-typed refs supporting ``.length()``, ``.exists()``,
``.missing()``, ``.get()``, and comparison operators.

All functions use PascalCase to match legacy naming convention.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from nu.terms import Nu

from .control import If
from .error import Assert


__all__ = [
    "AssertEmpty",
    "AssertEquals",
    "AssertExists",
    "AssertGreaterOrEqual",
    "AssertGreaterThan",
    "AssertLessOrEqual",
    "AssertLessThan",
    "AssertMissing",
    "AssertNotEmpty",
    "AssertNotEquals",
    "SkipIfEmpty",
    "SkipIfExists",
    "SkipIfMissing",
    "SkipIfNotEmpty",
]


# ---------------------------------------------------------------------------
# Collection assertions
# ---------------------------------------------------------------------------


def AssertEmpty(  # noqa: N802
    ref: Any, message: str = "Expected empty collection"
) -> Assert:
    """Assert that a collection ref is empty.

    Args:
        ref: A ref whose ``.length()`` returns a Nu evaluating to int.
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.length() == 0``.

    Example::

        items = ListRef()
        AssertEmpty(items)
        AssertEmpty(items, message="items should be cleared first")
    """
    return Assert(ref.length() == 0, message)


def AssertNotEmpty(  # noqa: N802
    ref: Any, message: str = "Expected non-empty collection"
) -> Assert:
    """Assert that a collection ref is not empty.

    Args:
        ref: A ref whose ``.length()`` returns a Nu evaluating to int.
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.length() > 0``.

    Example::

        items = ListRef()
        AssertNotEmpty(items)
        AssertNotEmpty(items, message="need at least one item to proceed")
    """
    return Assert(ref.length() > 0, message)


# ---------------------------------------------------------------------------
# Existence assertions
# ---------------------------------------------------------------------------


def AssertExists(  # noqa: N802
    ref: Any, message: str = "Expected value to exist"
) -> Assert:
    """Assert that a ref's value exists (is not empty/missing).

    Args:
        ref: A ref whose ``.exists()`` returns a Nu evaluating to bool.
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.exists()`` is truthy.

    Example::

        user = MapRef()
        AssertExists(user["name"])
        AssertExists(user["email"], message="user must have an email")
    """
    return Assert(ref.exists(), message)


def AssertMissing(  # noqa: N802
    ref: Any, message: str = "Expected value to be missing"
) -> Assert:
    """Assert that a ref's value is missing.

    Args:
        ref: A ref whose ``.missing()`` returns a Nu evaluating to bool.
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.missing()`` is truthy.

    Example::

        cache = MapRef()
        AssertMissing(cache["stale_key"])
        AssertMissing(cache["old"], message="old entry should have been evicted")
    """
    return Assert(ref.missing(), message)


# ---------------------------------------------------------------------------
# Comparison assertions
# ---------------------------------------------------------------------------


def AssertEquals(  # noqa: N802
    ref: Any, value: Any, message: str = "Expected values to be equal"
) -> Assert:
    """Assert that a ref's value equals *value*.

    Args:
        ref: A ref whose ``.get()`` returns a Nu evaluating to the stored value.
        value: The expected value to compare against.
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.get() == value``.

    Example::

        counter = Var(0)
        AssertEquals(counter, 0)
        AssertEquals(counter, 5, message="counter should be 5 after loop")
    """
    return Assert(ref.get() == value, message)


def AssertNotEquals(  # noqa: N802
    ref: Any, value: Any, message: str = "Expected values to differ"
) -> Assert:
    """Assert that a ref's value does not equal *value*.

    Args:
        ref: A ref whose ``.get()`` returns a Nu evaluating to the stored value.
        value: The value that the ref must not equal.
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.get() != value``.

    Example::

        status = Var("pending")
        AssertNotEquals(status, "error")
        AssertNotEquals(status, "pending", message="status should have changed")
    """
    return Assert(ref.get() != value, message)


def AssertGreaterThan(  # noqa: N802
    ref: Any, value: Any, message: str = "Expected greater than"
) -> Assert:
    """Assert that a ref's value is strictly greater than *value*.

    Args:
        ref: A ref whose ``.get()`` returns a Nu evaluating to a comparable value.
        value: The lower bound (exclusive).
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.get() > value``.

    Example::

        score = Var(0)
        AssertGreaterThan(score, 0)
        AssertGreaterThan(score, 100, message="score must exceed 100")
    """
    return Assert(ref.get() > value, message)


def AssertGreaterOrEqual(  # noqa: N802
    ref: Any, value: Any, message: str = "Expected greater than or equal"
) -> Assert:
    """Assert that a ref's value is greater than or equal to *value*.

    Args:
        ref: A ref whose ``.get()`` returns a Nu evaluating to a comparable value.
        value: The lower bound (inclusive).
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.get() >= value``.

    Example::

        balance = Var(0)
        AssertGreaterOrEqual(balance, 0)
        AssertGreaterOrEqual(balance, 10, message="insufficient balance")
    """
    return Assert(ref.get() >= value, message)


def AssertLessThan(  # noqa: N802
    ref: Any, value: Any, message: str = "Expected less than"
) -> Assert:
    """Assert that a ref's value is strictly less than *value*.

    Args:
        ref: A ref whose ``.get()`` returns a Nu evaluating to a comparable value.
        value: The upper bound (exclusive).
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.get() < value``.

    Example::

        retries = Var(0)
        AssertLessThan(retries, 10)
        AssertLessThan(retries, 3, message="too many retries")
    """
    return Assert(ref.get() < value, message)


def AssertLessOrEqual(  # noqa: N802
    ref: Any, value: Any, message: str = "Expected less than or equal"
) -> Assert:
    """Assert that a ref's value is less than or equal to *value*.

    Args:
        ref: A ref whose ``.get()`` returns a Nu evaluating to a comparable value.
        value: The upper bound (inclusive).
        message: Error message raised when the assertion fails.

    Returns:
        An ``Assert`` flow that passes when ``ref.get() <= value``.

    Example::

        latency = Var(0.0)
        AssertLessOrEqual(latency, 1.0)
        AssertLessOrEqual(latency, 0.5, message="latency exceeds SLA")
    """
    return Assert(ref.get() <= value, message)


# ---------------------------------------------------------------------------
# Conditional execution helpers
# ---------------------------------------------------------------------------


def SkipIfEmpty(  # noqa: N802
    ref: Any, child: Nu, else_: Nu | None = None
) -> If:
    """Execute *child* only if collection is NOT empty.

    Optionally run *else_* when the collection is empty.

    Args:
        ref: A ref whose ``.length()`` returns a Nu evaluating to int.
        child: Executed when ``ref.length() > 0``.
        else_: Executed when ``ref.length() == 0`` (optional).

    Returns:
        An ``If`` flow conditioned on ``ref.length() > 0``.

    Example::

        items = ListRef()
        SkipIfEmpty(items, process_items)
        SkipIfEmpty(items, process_items, else_=log_empty)
    """
    if else_ is not None:
        return If(ref.length() > 0, child, else_)
    return If(ref.length() > 0, child)


def SkipIfNotEmpty(  # noqa: N802
    ref: Any, child: Nu, else_: Nu | None = None
) -> If:
    """Execute *child* only if collection IS empty.

    Optionally run *else_* when the collection is not empty.

    Args:
        ref: A ref whose ``.length()`` returns a Nu evaluating to int.
        child: Executed when ``ref.length() == 0``.
        else_: Executed when ``ref.length() > 0`` (optional).

    Returns:
        An ``If`` flow conditioned on ``ref.length() == 0``.

    Example::

        queue = ListRef()
        SkipIfNotEmpty(queue, initialize_queue)
        SkipIfNotEmpty(queue, initialize_queue, else_=drain_queue)
    """
    if else_ is not None:
        return If(ref.length() == 0, child, else_)
    return If(ref.length() == 0, child)


def SkipIfMissing(  # noqa: N802
    ref: Any, child: Nu, else_: Nu | None = None
) -> If:
    """Execute *child* only if ref's value exists.

    Optionally run *else_* when the value is missing.

    Args:
        ref: A ref whose ``.exists()`` returns a Nu evaluating to bool.
        child: Executed when ``ref.exists()`` is truthy.
        else_: Executed when ``ref.exists()`` is falsy (optional).

    Returns:
        An ``If`` flow conditioned on ``ref.exists()``.

    Example::

        config = MapRef()
        SkipIfMissing(config["api_key"], call_api)
        SkipIfMissing(config["api_key"], call_api, else_=use_default)
    """
    if else_ is not None:
        return If(ref.exists(), child, else_)
    return If(ref.exists(), child)


def SkipIfExists(  # noqa: N802
    ref: Any, child: Nu, else_: Nu | None = None
) -> If:
    """Execute *child* only if ref's value is missing.

    Optionally run *else_* when the value exists.

    Args:
        ref: A ref whose ``.missing()`` returns a Nu evaluating to bool.
        child: Executed when ``ref.missing()`` is truthy.
        else_: Executed when ``ref.missing()`` is falsy (optional).

    Returns:
        An ``If`` flow conditioned on ``ref.missing()``.

    Example::

        cache = MapRef()
        SkipIfExists(cache["result"], compute_result)
        SkipIfExists(cache["result"], compute_result, else_=use_cached)
    """
    if else_ is not None:
        return If(ref.missing(), child, else_)
    return If(ref.missing(), child)
