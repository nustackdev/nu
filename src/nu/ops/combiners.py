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
    - and_(left, right): Combine two conditions with AND
    - or_(left, right): Combine two conditions with OR
    - all_(*conditions): All conditions must be true (AND)
    - any_(*conditions): At least one condition must be true (OR)
    - none_(*conditions): None of the conditions should be true

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
"""

from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING

from nu.interfaces.capabilities import AndableProtocol, OrableProtocol


if TYPE_CHECKING:
    from .values import BoolValue as BoolType


__all__ = [
    "all_",
    "and_",
    "any_",
    "none_",
    "or_",
]


# =============================================================================
# LOGICAL COMBINERS
# =============================================================================


def and_(left: object, right: object) -> BoolType:
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
    from nu.utils import ensure_term

    left_op = ensure_term(left)
    if not isinstance(left_op, AndableProtocol):
        raise TypeError(f"Operand {type(left).__name__} does not support AND logical operation")

    return left_op.and_(ensure_term(right))


def or_(left: object, right: object) -> BoolType:
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
    from nu.utils import ensure_term

    left_op = ensure_term(left)
    if not isinstance(left_op, OrableProtocol):
        raise TypeError(f"Operand {type(left).__name__} does not support OR logical operation")

    return left_op.or_(ensure_term(right))


def all_(*conditions: object) -> BoolType:
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

    from nu.utils import ensure_term

    # Convert all to RValues
    rvalues = [ensure_term(c) for c in conditions]

    # Reduce with and_()
    return reduce(lambda a, b: a.and_(b), rvalues)  # type: ignore


def any_(*conditions: object) -> BoolType:
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

    from nu.utils import ensure_term

    # Convert all to RValues
    rvalues = [ensure_term(c) for c in conditions]

    # Reduce with or_()
    return reduce(lambda a, b: a.or_(b), rvalues)  # type: ignore


def none_(*conditions: object) -> BoolType:
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

    return any_(*conditions).not_()
