"""Root test fixtures for Nu.

Provides the minimal universal test foundation. Test Nus specific to
particular test areas (ops, iteration, etc.) live closer to their tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from nu import Context, Nu


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


# ---------------------------------------------------------------------------
# Test Nus
# ---------------------------------------------------------------------------


class StubNu(Nu):
    """Pure leaf. Yields a fixed label.

    Accepts children for tree structure tests (_Node methods,
    _with_children, _is_leaf, purity propagation).

    Does NOT open children - structural carrier only.
    """

    def __init__(self, label: object = None, *children: Nu) -> None:
        super().__init__(*children)
        self._label = label

    async def aopen(self, ctx: Context) -> AsyncGenerator[object, None]:
        yield self._label

    def __repr__(self) -> str:
        if self._children:
            return f"StubNu({self._label!r}, children={len(self._children)})"
        return f"StubNu({self._label!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StubNu):
            return NotImplemented
        return self._label == other._label and self._children == other._children

    def __hash__(self) -> int:
        return hash(self._label)


class FailingNu(Nu):
    """Raises a specified exception when opened.

    For testing error propagation, TryCatch, Retry.
    """

    def __init__(self, exc: type[BaseException] = RuntimeError, msg: str = "fail") -> None:
        super().__init__()
        self._exc = exc
        self._msg = msg

    async def aopen(self, ctx: Context) -> AsyncGenerator[object, None]:
        raise self._exc(self._msg)
        yield  # unreachable; marks this as a generator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ctx() -> Context:
    """Fresh Context per test."""
    return Context()
