"""``UploadViewFor``: the view follows the session id ``session_for`` bound.

The id is read off the arm's ``SessionId`` frame, the nearest one winning, and
a bracket with none in scope says who binds it.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

import nu
from nu.lang import ScalarQuery
from nustd.session import SessionId
from nustd.ui.uploads import UploadArea, UploadView, UploadViewFor


if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from nu.lang.runtime import Runtime


class _BoundSid(ScalarQuery):
    """The sid of the ``UploadView`` bound around it."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return rt.ctx.get(UploadView).sid

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return rt.ctx.get(UploadView).sid

        return athunk


def _ctx(tmp_path: Path) -> nu.Context:
    return nu.Context().bind(UploadArea, UploadArea(tmp_path, None))


def test_the_view_follows_the_bound_session_id(tmp_path: Path) -> None:
    bracket = nu.let(SessionId, UploadViewFor(_BoundSid()), sid="t1")
    assert asyncio.run(nu.arun(bracket, _ctx(tmp_path)))[0] == "t1"


def test_the_nearest_session_id_wins(tmp_path: Path) -> None:
    inner = nu.let(SessionId, UploadViewFor(_BoundSid()), sid="t2")
    bracket = nu.let(SessionId, inner, sid="t1")
    assert asyncio.run(nu.arun(bracket, _ctx(tmp_path)))[0] == "t2"


def test_no_session_id_says_who_binds_it(tmp_path: Path) -> None:
    with pytest.raises(LookupError, match="session_for"):
        asyncio.run(nu.arun(UploadViewFor(_BoundSid()), _ctx(tmp_path)))
