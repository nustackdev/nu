"""Shared fixtures for nustd.service (in-process fabric) tests.

`Calculator` is a plain Python target with a mix of read/mutate/void/stream
methods (sync and async) that back a `Calc` `nu.Service`. Every test uses
a fresh Calculator instance so state is not shared across tests.
"""

from __future__ import annotations

import pytest

import nu
import nustd


class Calculator:
    """Plain Python target: attributes back methods on the Calc Service."""

    def __init__(self) -> None:
        self.total = 0.0
        self.log: list[tuple[str, tuple[object, ...]]] = []

    # scalar queries
    def add(self, a: float, b: float) -> float:
        return a + b

    def mul(self, a: float, b: float) -> float:
        return a * b

    # scalar actions
    def bump(self, by: float) -> float:
        self.total += by
        self.log.append(("bump", (by,)))
        return self.total

    # void command
    def reset(self) -> None:
        self.total = 0.0
        self.log.append(("reset", ()))

    # stream queries
    def range(self, n: int):
        for i in range(n):
            yield i * i

    def range_list(self, n: int) -> list[int]:
        return [i * 10 for i in range(n)]

    # stream action
    def drain(self):
        while self.log:
            yield self.log.pop(0)

    # async variants
    async def aadd(self, a: float, b: float) -> float:
        return a + b

    async def abump(self, by: float) -> float:
        self.total += by
        return self.total

    async def areset(self) -> None:
        self.total = 0.0

    async def arange(self, n: int):
        for i in range(n):
            yield i + 100


class Calc(nu.Service):
    """Service exposing Calculator via nustd.service refs."""

    add = nustd.service.QueryRef.method()
    mul = nustd.service.QueryRef.method()
    bump = nustd.service.ActionRef.method()
    reset = nustd.service.CommandRef.method()
    squares = nustd.service.StreamQueryRef.method(name="range")
    tens = nustd.service.StreamQueryRef.method(name="range_list")
    drain = nustd.service.StreamActionRef.method()

    # async wiring
    aadd = nustd.service.QueryRef.method()
    abump = nustd.service.ActionRef.method()
    areset = nustd.service.CommandRef.method()
    arange = nustd.service.StreamQueryRef.method()


class CalcWithDefaults(nu.Service):
    """Service using per-endpoint default kwargs merged into every call."""

    add = nustd.service.QueryRef.method(b=100)
    mul = nustd.service.QueryRef.method(name="mul", a=2)


@pytest.fixture
def target() -> Calculator:
    """Fresh Calculator per test."""
    return Calculator()


@pytest.fixture
def app(target: Calculator):
    """Factory: wrap a body in a With(bind(Calc, ...)) app."""

    def make(body):
        return nu.With(nustd.service.bind(Calc, target=target), body=body)

    return make


@pytest.fixture
def defaults_app(target: Calculator):
    """Factory for the CalcWithDefaults service."""

    def make(body):
        return nu.With(nustd.service.bind(CalcWithDefaults, target=target), body=body)

    return make
