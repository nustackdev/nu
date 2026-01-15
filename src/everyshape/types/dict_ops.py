"""Dict operations for Term expressions.

This module provides type-safe operations on dict Terms:

Access: DictKeysOp, DictValuesOp, DictItemsOp, DictGetOp

Design principles:
1. Atomic classes: one operation = one class
2. Runtime type checking: validate input is dict at execution
3. Special value propagation: Empty/NaN flow through operations
4. Type safety: preserve generic K, V for type inference
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape.term import Operation
from everyshape.typing import NOT_SET, NotSet, Sentinel, is_notset


if TYPE_CHECKING:
    from everyshape.term import Context, Term

    from .bases import UnionBaseType


__all__ = [
    "DictGetOp",
    "DictItemsOp",
    "DictKeysOp",
    "DictValuesOp",
]


type OpArgument = Term | UnionBaseType


class MappingOp[ResultT](Operation[ResultT]):
    """Base class for mapping operations."""

    def __init__(self, operand: OpArgument) -> None:
        """Init."""
        self.children = (cast("Term", operand),)

    def execute(self, context: Context) -> ResultT:
        """Execute."""
        operand_val = self.children[0].execute(context)
        return self._apply_op(operand_val)

    def _apply_op(self, operand: object) -> ResultT:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.children[0]!r})"


class DictKeysOp[K](MappingOp[list[K]]):
    """Get keys from dict: list(dict.keys())."""

    def _apply_op(self, operand: object) -> list[K]:
        if not isinstance(operand, dict):
            raise TypeError(f"keys_() requires dict, got {type(operand).__name__}")
        return list(operand.keys())  # type: ignore


class DictValuesOp[V](MappingOp[list[V]]):
    """Get values from dict: list(dict.values())."""

    def _apply_op(self, operand: object) -> list[V]:
        if not isinstance(operand, dict):
            raise TypeError(f"values_() requires dict, got {type(operand).__name__}")
        return list(operand.values())  # type: ignore


class DictItemsOp[K, V](MappingOp[list[tuple[K, V]]]):
    """Get items from dict: list(dict.items())."""

    def _apply_op(self, operand: object) -> list[tuple[K, V]]:
        if not isinstance(operand, dict):
            raise TypeError(f"items_() requires dict, got {type(operand).__name__}")
        return list(operand.items())  # type: ignore


class DictGetOp[V](Operation[V | Sentinel]):
    """Get value from dict with default: dict.get(key, default)."""

    def __init__(
        self, operand: OpArgument, key: OpArgument, default: OpArgument | NotSet = NOT_SET
    ) -> None:
        """Init."""
        self.children = (
            cast("Term", operand),
            cast("Term", key),
            cast("Term", default),
        )

    def execute(self, context: Context) -> V | Sentinel:
        """Execute."""
        dict_val = self.children[0].execute(context)
        key_val = self.children[1].execute(context)

        default_exists = False
        if not is_notset(self.children[2]):
            default_val = self.children[2].execute(context)
            default_exists = True

        if not isinstance(dict_val, dict):
            raise TypeError(f"get_() requires dict, got {type(dict_val).__name__}")

        if default_exists:
            return dict_val.get(key_val, default_val)  # type: ignore
        return dict_val[key_val]

    def __repr__(self) -> str:
        return f"DictGetOp({self.children[0]!r}, {self.children[1]!r}, {self.children[2]!r})"
