"""Root test fixtures for Nu.

Provides the minimal universal test foundation. Test Nus specific to
particular test areas live closer to their tests.
"""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from nu import Context
from nu.terms.nu import NuBase
from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class StubNu(ScalarQuery):
    """Pure leaf-ish ScalarQuery. Returns a fixed label.

    Accepts children for tree-structure tests.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, label: object = None, *children: Any) -> None:
        super().__init__(*children)
        self._label = label

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:
        return self._label

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


class FailingNu(ScalarQuery):
    """Raises a specified exception when evaluated.

    For testing error propagation, TryCatch, Retry.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, exc: type[BaseException] = RuntimeError, msg: str = "fail") -> None:
        super().__init__()
        self._exc = exc
        self._msg = msg

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:
        raise self._exc(self._msg)


_ = NuBase  # keep import-side


@pytest.fixture
def ctx() -> Context:
    """Fresh Context per test."""
    return Context()
