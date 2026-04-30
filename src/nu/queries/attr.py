"""Attribute access ops.

GetAttr: Get an attribute from an instance
SetAttr: Set an attribute on an instance
DelAttr: Delete an attribute from an instance
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = [
    "DelAttr",
    "GetAttr",
    "SetAttr",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class GetAttr(ScalarQuery):
    """Get an attribute from an instance."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, instance: Any, attr_name: Any) -> None:  # noqa: ANN401
        super().__init__(instance, attr_name)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        return getattr(ops[0], str(ops[1]))


class SetAttr(ScalarQuery):
    """Set an attribute on an instance."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, instance: Any, attr_name: Any, value: Any) -> None:  # noqa: ANN401
        super().__init__(instance, attr_name, value)

    def _apply(self, ctx: Any, ops: list[Any]) -> None:  # noqa: ANN401
        setattr(ops[0], str(ops[1]), ops[2])


class DelAttr(ScalarQuery):
    """Delete an attribute from an instance."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, instance: Any, attr_name: Any) -> None:  # noqa: ANN401
        super().__init__(instance, attr_name)

    def _apply(self, ctx: Any, ops: list[Any]) -> None:  # noqa: ANN401
        delattr(ops[0], str(ops[1]))
