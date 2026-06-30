"""Functional tests for ``nu.std.random`` - drive the Forms through the engine.

Results are random, so the assertions are property-based: ranges, membership,
list length, and return types - not exact values. Covers the float/int/list/any
return shapes and the async path.
"""

from __future__ import annotations

import asyncio
import random as _random

from nu.lang.helpers import arun, run
from nu.std.random import (
    choice,
    choices,
    expovariate,
    gauss,
    getrandbits,
    normalvariate,
    randint,
    random,
    randrange,
    sample,
    triangular,
    uniform,
)


def test_random_in_unit_interval() -> None:
    value, _ = run(random())
    assert isinstance(value, float)
    assert 0.0 <= value < 1.0


def test_uniform_in_range() -> None:
    value, _ = run(uniform(0, 1))
    assert isinstance(value, float)
    assert 0.0 <= value <= 1.0


def test_randint_in_range() -> None:
    value, _ = run(randint(1, 6))
    assert isinstance(value, int)
    assert 1 <= value <= 6


def test_randrange_in_range() -> None:
    value, _ = run(randrange(0, 10))
    assert isinstance(value, int)
    assert 0 <= value < 10


def test_getrandbits_in_range() -> None:
    value, _ = run(getrandbits(8))
    assert isinstance(value, int)
    assert 0 <= value <= 255


def test_choice_is_member() -> None:
    options = ["red", "green", "blue"]
    value, _ = run(choice(options))
    assert value in options


def test_choices_length_and_membership() -> None:
    population = [1, 2, 3]
    value, _ = run(choices(population, 5))
    assert isinstance(value, list)
    assert len(value) == 5
    assert all(item in population for item in value)


def test_sample_length_and_distinct() -> None:
    population = [1, 2, 3, 4, 5]
    value, _ = run(sample(population, 2))
    assert isinstance(value, list)
    assert len(value) == 2
    assert len(set(value)) == 2
    assert all(item in population for item in value)


def test_gauss_returns_float() -> None:
    value, _ = run(gauss(0, 1))
    assert isinstance(value, float)


def test_normalvariate_returns_float() -> None:
    value, _ = run(normalvariate(0, 1))
    assert isinstance(value, float)


def test_expovariate_is_positive() -> None:
    value, _ = run(expovariate(1.0))
    assert isinstance(value, float)
    assert value >= 0.0


def test_triangular_in_range() -> None:
    value, _ = run(triangular(0, 10))
    assert isinstance(value, float)
    assert 0.0 <= value <= 10.0


def test_seeded_randint_is_reproducible() -> None:
    # One deterministic assertion: a fixed seed pins the exact draw.
    _random.seed(1234)
    expected = _random.randint(1, 6)  # noqa: S311 -- test fixture, not crypto
    _random.seed(1234)
    value, _ = run(randint(1, 6))
    assert value == expected


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(randint(1, 6)))
    assert isinstance(value, int)
    assert 1 <= value <= 6
