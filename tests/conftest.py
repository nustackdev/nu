"""Root test fixtures for Nu.

Provides the minimal universal test foundation. Test Nus specific to
particular test areas (ops, iteration, etc.) live closer to their tests.
"""

from __future__ import annotations

import pytest

from nu import Context, Nu


# ---------------------------------------------------------------------------
# Test Nus
# ---------------------------------------------------------------------------


class StubNu(Nu):
    """Pure leaf. Returns a fixed label on execute.

    Accepts children for tree structure tests (_Node methods,
    with_children, is_leaf, purity propagation).

    Does NOT execute children - structural carrier only.
    """

    def __init__(self, label: object = None, *children: Nu) -> None:
        super().__init__(*children)
        self._label = label

    async def execute(self, ctx: Context) -> object:
        return self._label

    @property
    def is_self_pure(self) -> bool:
        return True

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
    """Raises a specified exception on execute.

    For testing error propagation, Span exit_failure, TryCatch, Retry.
    """

    def __init__(self, exc: type[BaseException] = RuntimeError, msg: str = "fail") -> None:
        super().__init__()
        self._exc = exc
        self._msg = msg

    async def execute(self, ctx: Context) -> object:
        raise self._exc(self._msg)

    @property
    def is_self_pure(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ctx() -> Context:
    """Fresh Context per test."""
    return Context()
