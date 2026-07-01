"""Test configuration for nu.mem tests."""

from __future__ import annotations

import pytest

from nu import Context
from nu.domains.shape import Shape
from nu.mem import (
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    SetRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
)


# jqueue is a deferred v2 port (source commented out of refs, test still on the v1
# `runtime` / `nu.shapes` API). Skip collection until it is ported + re-exported.
collect_ignore = ["test_jqueue.py"]


@pytest.fixture
def data() -> dict:
    """Fresh root dict for each test."""
    return {}


@pytest.fixture
def ctx(data: dict) -> Context:
    """Context with root dict bound (no shape scope)."""
    return Context().bind(dict, data)


# ============================================================================
# SHAPE FIXTURES
# ============================================================================


class UserShape(Shape):
    name = StrRef.slot()
    age = IntRef.slot()
    score = FloatRef.slot()


class PortfolioShape(Shape):
    title = StrRef.slot()
    tags = ListRef.slot(str)
    metadata = DictRef.slot(str)
    members = SetRef.slot(str)


class OrderShape(Shape):
    symbol = StrRef.slot()
    price = FloatRef.slot()
    qty = IntRef.slot()


class TeamShape(Shape):
    name = StrRef.slot()
    members = ShapesDictRef.slot(UserShape)
    roster = ShapesListRef.slot(OrderShape)
    info = ShapeRef.slot(UserShape)


@pytest.fixture
def user_ctx(data: dict) -> Context:
    """Context scoped to UserShape."""
    return Context().bind(dict, data, UserShape)


@pytest.fixture
def portfolio_ctx(data: dict) -> Context:
    """Context scoped to PortfolioShape."""
    return Context().bind(dict, data, PortfolioShape)


@pytest.fixture
def team_ctx(data: dict) -> Context:
    """Context scoped to TeamShape."""
    return Context().bind(dict, data, TeamShape)
