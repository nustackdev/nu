"""The reactive surface: every flow is exported where the old names were, under its new name only."""

from __future__ import annotations

import pytest

import nu
import nu.core.flows
import nu.core.reactive


REACTIVE = [
    "OnAny",
    "ReactEach",
    "ReactEvery",
    "ReactLatest",
    "ReactLatestEach",
    "ReactOnce",
    "ReactWhile",
    "Reconcile",
    "ReconcileEach",
    "ReconcileLatest",
    "ReconcileLatestEach",
    "ReconcileWhile",
    "Stream",
    "WaitUntil",
]


@pytest.mark.parametrize("name", REACTIVE)
def test_reactive_names_are_exported(name: str) -> None:
    assert getattr(nu, name) is getattr(nu.core.reactive, name)
    assert name in nu.core.reactive.__all__


def test_park_is_exported() -> None:
    assert nu.Park is nu.core.flows.Park


@pytest.mark.parametrize(
    "name", ["React", "ReactForever", "WaitReactive", "ReconcileReactive", "ForEachParReactive"]
)
def test_old_names_are_gone(name: str) -> None:
    assert not hasattr(nu, name)
    assert not hasattr(nu.core.reactive, name)
