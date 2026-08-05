"""Module-level functions for ``nu.std.random`` - the function namespace.

``random`` has no central class, so this is the whole surface: typed wrappers
that mirror ``random.random`` / ``random.randint`` / ``random.choice`` 1-1. Each
wrapper builds its interaction atom (lazily imported, like ``nu.std.math``) and
returns the Form that matches the host return type:

- reals (``random``, ``uniform``, ``gauss``, ...) -> ``Float``
- ints (``randint``, ``randrange``, ``getrandbits``) -> ``Int``
- ``choice`` -> ``Any`` (one element of the population)
- ``choices`` / ``sample`` -> ``List``

Every function here is NON-DETERMINISTIC: it reads the global RNG, so its atom
declares ``deterministic=False`` and must not be constant-folded (see
``interactions``).

Deferred (effectful / stateful, need the effect model first): ``seed``,
``shuffle`` (mutates the sequence in place), ``getstate`` / ``setstate``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms import Any, Float, Int, List


if TYPE_CHECKING:
    from nu.lang import FloatArg, IntArg, ListArg


__all__ = [
    "choice",
    "choices",
    "expovariate",
    "gauss",
    "getrandbits",
    "normalvariate",
    "randint",
    "random",
    "randrange",
    "sample",
    "triangular",
    "uniform",
]


# --- uniform reals and ints -------------------------------------------------


def random() -> Float:
    """A random float in ``[0.0, 1.0)``: mirrors ``random.random()``. Non-deterministic."""
    from .interactions import RandomRandom

    return Float(RandomRandom())


def uniform(a: FloatArg, b: FloatArg) -> Float:
    """A random float in ``[a, b]``: mirrors ``random.uniform()``. Non-deterministic."""
    from .interactions import RandomUniform

    return Float(RandomUniform(a, b))


def randint(a: IntArg, b: IntArg) -> Int:
    """A random int ``N`` with ``a <= N <= b``: mirrors ``random.randint()``. Non-deterministic."""
    from .interactions import RandomRandint

    return Int(RandomRandint(a, b))


def randrange(start: IntArg, stop: IntArg) -> Int:
    """A random int in ``range(start, stop)``: mirrors ``random.randrange()``. Non-deterministic."""
    from .interactions import RandomRandrange

    return Int(RandomRandrange(start, stop))


def getrandbits(k: IntArg) -> Int:
    """A non-negative int with ``k`` random bits: mirrors ``random.getrandbits()``. Non-deterministic."""
    from .interactions import RandomGetrandbits

    return Int(RandomGetrandbits(k))


# --- sequence draws ---------------------------------------------------------


def choice(seq: ListArg[object]) -> Any:
    """A random element of ``seq``: mirrors ``random.choice()``. Non-deterministic."""
    from .interactions import RandomChoice

    return Any(RandomChoice(seq))


def choices(population: ListArg[object], k: IntArg) -> List:
    """A ``k``-sized list drawn with replacement: mirrors ``random.choices()``. Non-deterministic."""
    from .interactions import RandomChoices

    return List(RandomChoices(population, k))


def sample(population: ListArg[object], k: IntArg) -> List:
    """A ``k``-sized list drawn without replacement: mirrors ``random.sample()``. Non-deterministic."""
    from .interactions import RandomSample

    return List(RandomSample(population, k))


# --- continuous distributions -----------------------------------------------


def gauss(mu: FloatArg, sigma: FloatArg) -> Float:
    """A Gaussian draw with mean ``mu`` and stdev ``sigma``: mirrors ``random.gauss()``. Non-deterministic."""
    from .interactions import RandomGauss

    return Float(RandomGauss(mu, sigma))


def normalvariate(mu: FloatArg, sigma: FloatArg) -> Float:
    """A normal draw with mean ``mu`` and stdev ``sigma``: mirrors ``random.normalvariate()``. Non-deterministic."""
    from .interactions import RandomNormalvariate

    return Float(RandomNormalvariate(mu, sigma))


def expovariate(lambd: FloatArg) -> Float:
    """An exponential draw with rate ``lambd``: mirrors ``random.expovariate()``. Non-deterministic."""
    from .interactions import RandomExpovariate

    return Float(RandomExpovariate(lambd))


def triangular(low: FloatArg, high: FloatArg) -> Float:
    """A triangular draw between ``low`` and ``high``: mirrors ``random.triangular()``. Non-deterministic."""
    from .interactions import RandomTriangular

    return Float(RandomTriangular(low, high))
