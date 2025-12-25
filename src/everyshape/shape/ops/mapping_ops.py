"""Mapping (dict) operations for RValue expressions.

This module provides type-safe operations on dict RValues:

Access: DictKeysOp, DictValuesOp, DictItemsOp, DictGetOp
Membership: ContainsOp

Design principles:
1. Atomic classes: one operation = one class
2. Runtime type checking: validate input is dict at execution
3. Special value propagation: Empty/NaN flow through operations
4. Type safety: preserve generic K, V for type inference

Usage:
    # Direct instantiation
    DictKeysOp(users.extract())
    DictGetOp(user.extract(), LiteralValue("name"), LiteralValue("Unknown"))

    # Via ergonomics mixin
    users.extract().keys_()
    user.extract().get_("name", "Unknown")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.types import SpecialValue

from ..term import Operation


if TYPE_CHECKING:
    from ..context import ContextProtocol
    from ..term import RValue
    from ..values.bases import (
        ArithmeticBase,
        BitwiseBase,
        ComparisonBase,
        LogicalBase,
        MappingBase,
        SequenceBase,
        StringBase,
    )

__all__ = [
    "ContainsOp",
    "DictGetOp",
    "DictItemsOp",
    "DictKeysOp",
    "DictValuesOp",
]


# =============================================================================
# ABSTRACT MAPPING OPERATION
# =============================================================================


type OpArgument = (
    RValue
    | ArithmeticBase
    | SequenceBase
    | StringBase
    | BitwiseBase
    | LogicalBase
    | MappingBase
    | ComparisonBase
)


class MappingOp[ResultT, ContextT: ContextProtocol](Operation[ResultT, ContextT]):
    """Base class for mapping operations.

    Defines execution pattern: evaluate operand → validate mapping →
    apply operation → return result.
    """

    def __init__(self, operand: OpArgument) -> None:
        """Initialize mapping operation.

        Args:
            operand: RValue that should produce a mapping
        """
        self.children = (cast("RValue", operand),)

    def execute(self, context: ContextT) -> ResultT:
        """Execute mapping operation.

        Args:
            context: Execution context

        Returns:
            Operation result
        """
        # Evaluate operand
        operand_val = self.children[0].execute(context)

        # Apply operator-specific logic
        return self._apply_op(operand_val)

    def _apply_op(self, operand: object) -> ResultT:
        """Apply the operation to operand.

        Subclasses override with operation-specific logic.

        Args:
            operand: The evaluated mapping

        Returns:
            Operation result
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children[0]!r})"


# =============================================================================
# ACCESS OPERATIONS
# =============================================================================


class DictKeysOp[K, ContextT: ContextProtocol](MappingOp[list[K], ContextT]):
    """Get keys from dict: list(dict.keys())."""

    def _apply_op(self, operand: object) -> list[K]:
        if not isinstance(operand, dict):
            raise TypeError(f"keys_() requires dict, got {type(operand).__name__}")
        return list(operand.keys())  # type: ignore


class DictValuesOp[V, ContextT: ContextProtocol](MappingOp[list[V], ContextT]):
    """Get values from dict: list(dict.values())."""

    def _apply_op(self, operand: object) -> list[V]:
        if not isinstance(operand, dict):
            raise TypeError(f"values_() requires dict, got {type(operand).__name__}")
        return list(operand.values())  # type: ignore


class DictItemsOp[K, V, ContextT: ContextProtocol](MappingOp[list[tuple[K, V]], ContextT]):
    """Get items from dict: list(dict.items())."""

    def _apply_op(self, operand: object) -> list[tuple[K, V]]:
        if not isinstance(operand, dict):
            raise TypeError(f"items_() requires dict, got {type(operand).__name__}")
        return list(operand.items())  # type: ignore


class DictGetOp[V, ContextT: ContextProtocol](Operation[V | SpecialValue, ContextT]):
    """Get value from dict with default: dict.get(key, default)."""

    def __init__(self, operand: OpArgument, key: OpArgument, default: OpArgument) -> None:
        """Init."""
        self.children = (
            cast("RValue", operand),
            cast("RValue", key),
            cast("RValue", default),
        )

    def execute(self, context: ContextT) -> V | SpecialValue:
        """Execute."""
        dict_val = self.children[0].execute(context)
        key_val = self.children[1].execute(context)
        default_val = self.children[2].execute(context)

        if not isinstance(dict_val, dict):
            raise TypeError(f"get_() requires dict, got {type(dict_val).__name__}")

        return dict_val.get(key_val, default_val)  # type: ignore

    def __repr__(self) -> str:
        return f"DictGetOp({self.children[0]!r}, {self.children[1]!r}, {self.children[2]!r})"


# =============================================================================
# MEMBERSHIP OPERATIONS
# =============================================================================


class ContainsOp[ContextT: ContextProtocol](Operation[bool, ContextT]):
    """Containment check: item in container.

    Works for:
    - list/tuple: checks if item is in sequence
    - dict: checks if key is in dict
    - str: checks if substring is in string
    - set: checks if item is in set
    """

    def __init__(self, operand: OpArgument, item: OpArgument) -> None:
        """Init."""
        self.children = (cast("RValue", operand), cast("RValue", item))

    def execute(self, context: ContextT) -> bool:
        """Execute."""
        container_val = self.children[0].execute(context)
        item_val = self.children[1].execute(context)

        if not isinstance(container_val, (list, tuple, dict, set, frozenset, str)):
            raise TypeError(
                f"contains_() requires list, tuple, dict, set, or str, "
                f"got {type(container_val).__name__}"
            )

        return item_val in container_val

    def __repr__(self) -> str:
        return f"ContainsOp({self.children[0]!r}, {self.children[1]!r})"
