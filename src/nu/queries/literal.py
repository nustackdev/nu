"""Literal - the trivial scalar Query.

Holds a Python value and yields it. Used as the universal auto-wrap
target for non-Nu children (see `nu.terms.nu.NuBase.__init__`).
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery


__all__ = [
    "Literal",
]


class Literal(ScalarQuery):
    """Pure leaf. Holds a value, evaluates to it.

    No operands; exempt from sentinel-propagation by virtue of zero
    operands.
    """

    accepts_sentinels: ClassVar[bool] = True
    _value: object

    def __init__(self, value: object) -> None:
        super().__init__()
        self._value = value

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        return self._value

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        return self._value

    def __repr__(self) -> str:
        return f"Literal({self._value!r})"
