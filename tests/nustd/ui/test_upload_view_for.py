"""``UploadViewFor``: which attr holds the arm's sid is a config child.

The bracket opens with its config evaluated, so the attr name can be
computed like any other value, not only given as a constant.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import nu
from nu.lang import ScalarQuery
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


def _ctx(tmp_path: Path, **attrs: object) -> nu.Context:
    return nu.Context(attrs=attrs).bind(UploadArea, UploadArea(tmp_path, None))


def test_the_sid_attr_is_a_config_child(tmp_path: Path) -> None:
    bracket = UploadViewFor(_BoundSid(), sid_attr="tab")
    assert nu.tree.fields(bracket) == {}
    ctx = _ctx(tmp_path, tab="t1")
    assert asyncio.run(nu.arun(bracket, ctx))[0] == "t1"


def test_the_sid_attr_can_be_computed(tmp_path: Path) -> None:
    bracket = UploadViewFor(_BoundSid(), sid_attr=nu.context.Attr("which"))
    ctx = _ctx(tmp_path, which="tab", tab="t2")
    assert asyncio.run(nu.arun(bracket, ctx))[0] == "t2"
