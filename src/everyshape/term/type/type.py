"""Unified typed expression.

RValue                  - evaluable expression (has children)
├── Type                - typed value (literal or computed, unified)
│   ├── IntType, FloatType, StrType, BoolType, BytesType
│   ├── NilType, ListType, DictType, SetType, TupleType
│   ├── AnyType         - dynamic/unknown type
│   └── SentinelType    - special values (EmptyType, InvalidType)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.typing import Sentinel

from ..term import RValue, Term


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Type",
]


class Type[T](RValue[T | Sentinel]):
    """Unified typed expression - either literal or computed.

    Type is the base for all typed values in the system. It handles
    both literal values (known at definition time) and computed values
    (wrapped operations) through a unified interface.

    Constructor accepts:
        - Literal value: Type(42), Type("hello")
        - RValue expression: Type(some_operation)
        - Sentinel: Type(EMPTY), Type(INVALID)

    On execution:
        - If source is RValue: executes it and returns result
        - If source is literal: returns value directly

    Type Parameters:
        T: The type of value this represents

    Example:
        >>> # From literal
        >>> x = IntType(42)
        >>> x.execute(ctx)  # Returns 42

        >>> # From operation
        >>> y = IntType(GetOp(price_ref))
        >>> y.execute(ctx)  # Executes GetOp, returns result

        >>> # Unified constructor
        >>> IntType(42)  # Literal
        >>> IntType(other.get())  # Computed
    """

    def __init__(self, source: T | Sentinel | Term[T | Sentinel]) -> None:
        """Initialize with a literal value or Term expression.

        Args:
            source: Either a raw value of type T, an Term that produces T,
                    or a Sentinel value (EMPTY, INVALID)
        """
        self._source = source
        if isinstance(source, Term):
            self.children = (source,)
        else:
            self.children = ()

    @property
    def source(self) -> T | Sentinel | Term[T | Sentinel]:
        """Get the underlying source (literal or Term).

        Returns:
            The stored value, Term, or Sentinel
        """
        return self._source

    @property
    def is_literal(self) -> bool:
        """Check if this is a literal (non-computed) value.

        Returns:
            True if source is a literal value, False if computed
        """
        return not isinstance(self._source, Term)

    @property
    def is_pure(self) -> bool:
        """Types are pure if children Term's do not have impure component.

        Returns:
            Bool indicating whether term tree is pure or not
        """
        return all(child.is_pure for child in self.children if isinstance(child, Term))

    def execute(self, context: Context) -> T | Sentinel:
        """Execute and return the typed value.

        If source is an RValue, executes it.
        Otherwise returns the literal value directly.

        Args:
            context: Execution context

        Returns:
            The typed value of type T
        """
        if isinstance(self._source, Term):
            return self._source.execute(context)
        return self._source

    def __repr__(self) -> str:
        """Return machine-friendly representation."""
        return f"{self.__class__.__name__}({self._source!r})"
