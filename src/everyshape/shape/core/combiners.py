"""Combiners for visually ergonomic chaining of logical operations.

This module provides convenience functions for combining multiple conditions
in a more readable way than linear chaining with .and_() and .or_() methods.

Linear chaining has poor DX for complex logical operations:
    # Hard to read with linear chaining
    result = cond1.and_(cond2).and_(cond3).and_(cond4).and_(cond5)

Combiners provide a cleaner syntax:
    # More readable with all_()
    result = all_(cond1, cond2, cond3, cond4, cond5)

Available combiners:
    - all_(*conditions): Combines conditions with AND (all must be true)
    - any_(*conditions): Combines conditions with OR (at least one must be true)
    - none_(*conditions): None of the conditions should be true
    - one_of(*conditions): Exactly one condition should be true
    - at_least(n, *conditions): At least n conditions should be true
    - at_most(n, *conditions): At most n conditions should be true

Example:
    >>> price = item.price.get()
    >>> quantity = item.quantity.get()
    >>> in_stock = item.in_stock.get()
    >>>
    >>> # Complex condition with all_()
    >>> valid_purchase = all_(price > 0, price < 1000, quantity > 0, in_stock.eq(True))
    >>>
    >>> # Multiple valid states with any_()
    >>> can_ship = any_(
    ...     status.eq("ready"), status.eq("pending"), status.eq("processing")
    ... )
    >>>
    >>> # Exclusive conditions with one_of()
    >>> payment_method = one_of(
    ...     paid_with_card.eq(True), paid_with_cash.eq(True), paid_with_crypto.eq(True)
    ... )
"""

from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..term import RValue


__all__ = [
    "all_",
    "and_",
    "any_",
    "none_",
    "or_",
]


def and_(left: object, right: object) -> RValue:
    """Combine exactly two conditions with AND.

    Both conditions must be true for the result to be true.

    Args:
        left: First condition (RValue or literal)
        right: Second condition (RValue or literal)

    Returns:
        RValue expression combining both conditions with AND

    Example:
        >>> and_(price > 0, price < 100)
    """
    from .literal_value import literal

    return literal(left).and_(literal(right))


def or_(left: object, right: object) -> RValue:
    """Combine exactly two conditions with OR.

    At least one condition must be true for the result to be true.

    Args:
        left: First condition (RValue or literal)
        right: Second condition (RValue or literal)

    Returns:
        RValue expression combining both conditions with OR

    Example:
        >>> or_(status.eq("ready"), status.eq("pending"))
    """
    from .literal_value import literal

    return literal(left).or_(literal(right))


def all_(*conditions: object) -> RValue:
    """Combine multiple conditions with AND.

    All conditions must be true for the result to be true.

    Args:
        *conditions: Variable number of conditions (RValue or literals)

    Returns:
        RValue expression combining all conditions with AND

    Raises:
        ValueError: If no conditions provided

    Example:
        >>> all_(price > 0, price < 100, quantity > 0)
    """
    if not conditions:
        raise ValueError("all_() requires at least one condition")

    from .literal_value import literal

    # Convert all to RValues
    rvalues = [literal(c) for c in conditions]

    # Reduce with and_()
    return reduce(lambda a, b: a.and_(b), rvalues)


def any_(*conditions: object) -> RValue:
    """Combine multiple conditions with OR.

    At least one condition must be true for the result to be true.

    Args:
        *conditions: Variable number of conditions (RValue or literals)

    Returns:
        RValue expression combining all conditions with OR

    Raises:
        ValueError: If no conditions provided

    Example:
        >>> any_(status.eq("ready"), status.eq("pending"), status.eq("done"))
    """
    if not conditions:
        raise ValueError("any_() requires at least one condition")

    from .literal_value import literal

    # Convert all to RValues
    rvalues = [literal(c) for c in conditions]

    # Reduce with or_()
    return reduce(lambda a, b: a.or_(b), rvalues)


def none_(*conditions: object) -> RValue:
    """None of the conditions should be true.

    This is equivalent to NOT(any_(...)).

    Args:
        *conditions: Variable number of conditions (RValue or literals)

    Returns:
        RValue expression that is true when all conditions are false

    Raises:
        ValueError: If no conditions provided

    Example:
        >>> none_(is_cancelled, is_expired, is_invalid)
    """
    if not conditions:
        raise ValueError("none_() requires at least one condition")

    # NOT(any_(...))
    return any_(*conditions).not_()
