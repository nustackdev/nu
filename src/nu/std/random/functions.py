"""Module-level functions for ``nu.std.random`` - the function namespace.

``random`` has no central class, so this is the whole surface: typed wrappers
that mirror ``random.random`` / ``random.randint`` / ``random.choice`` 1-1. Each
wrapper builds its interaction atom (lazily imported, like ``nu.std.math``) and
returns the Form that matches the host return type:

- reals (``random``, ``uniform``, ``gauss``, ...) -> ``FloatForm``
- ints (``randint``, ``randrange``, ``getrandbits``) -> ``IntForm``
- ``choice`` -> ``AnyForm`` (one element of the population)
- ``choices`` / ``sample`` -> ``ListForm``

Every function here is NON-DETERMINISTIC: it reads the global RNG, so its atom
declares ``deterministic=False`` and must not be constant-folded (see
``interactions``).

Deferred (effectful / stateful, need the effect model first): ``seed``,
``shuffle`` (mutates the sequence in place), ``getstate`` / ``setstate``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import AnyForm, FloatForm, IntForm, ListForm


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


def random() -> FloatForm:
    """A random float in ``[0.0, 1.0)``: mirrors ``random.random()``. Non-deterministic."""
    from .interactions import RandomRandom

    return FloatForm(RandomRandom())


def uniform(a: FloatArg, b: FloatArg) -> FloatForm:
    """A random float in ``[a, b]``: mirrors ``random.uniform()``. Non-deterministic."""
    from .interactions import RandomUniform

    return FloatForm(RandomUniform(a, b))


def randint(a: IntArg, b: IntArg) -> IntForm:
    """A random int ``N`` with ``a <= N <= b``: mirrors ``random.randint()``. Non-deterministic."""
    from .interactions import RandomRandint

    return IntForm(RandomRandint(a, b))


def randrange(start: IntArg, stop: IntArg) -> IntForm:
    """A random int in ``range(start, stop)``: mirrors ``random.randrange()``. Non-deterministic."""
    from .interactions import RandomRandrange

    return IntForm(RandomRandrange(start, stop))


def getrandbits(k: IntArg) -> IntForm:
    """A non-negative int with ``k`` random bits: mirrors ``random.getrandbits()``. Non-deterministic."""
    from .interactions import RandomGetrandbits

    return IntForm(RandomGetrandbits(k))


# --- sequence draws ---------------------------------------------------------


def choice(seq: ListArg[object]) -> AnyForm:
    """A random element of ``seq``: mirrors ``random.choice()``. Non-deterministic."""
    from .interactions import RandomChoice

    return AnyForm(RandomChoice(seq))


def choices(population: ListArg[object], k: IntArg) -> ListForm:
    """A ``k``-sized list drawn with replacement: mirrors ``random.choices()``. Non-deterministic."""
    from .interactions import RandomChoices

    return ListForm(RandomChoices(population, k))


def sample(population: ListArg[object], k: IntArg) -> ListForm:
    """A ``k``-sized list drawn without replacement: mirrors ``random.sample()``. Non-deterministic."""
    from .interactions import RandomSample

    return ListForm(RandomSample(population, k))


# --- continuous distributions -----------------------------------------------


def gauss(mu: FloatArg, sigma: FloatArg) -> FloatForm:
    """A Gaussian draw with mean ``mu`` and stdev ``sigma``: mirrors ``random.gauss()``. Non-deterministic."""
    from .interactions import RandomGauss

    return FloatForm(RandomGauss(mu, sigma))


def normalvariate(mu: FloatArg, sigma: FloatArg) -> FloatForm:
    """A normal draw with mean ``mu`` and stdev ``sigma``: mirrors ``random.normalvariate()``. Non-deterministic."""
    from .interactions import RandomNormalvariate

    return FloatForm(RandomNormalvariate(mu, sigma))


def expovariate(lambd: FloatArg) -> FloatForm:
    """An exponential draw with rate ``lambd``: mirrors ``random.expovariate()``. Non-deterministic."""
    from .interactions import RandomExpovariate

    return FloatForm(RandomExpovariate(lambd))


def triangular(low: FloatArg, high: FloatArg) -> FloatForm:
    """A triangular draw between ``low`` and ``high``: mirrors ``random.triangular()``. Non-deterministic."""
    from .interactions import RandomTriangular

    return FloatForm(RandomTriangular(low, high))
