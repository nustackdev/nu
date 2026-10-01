"""Every docstring example written in doctest form runs, and shows what it claims.

Examples are documentation first, so they use the short user-facing names:
``nu`` and ``nustd`` are in scope in every module, the way a reader has them.
A snippet that cannot run offline (it needs a live server, a browser, a
network peer) is written without prompts, which keeps it out of doctest and
marks it as illustrative to the docstring inspector too. So nothing is skipped
here; a failing example is either wrong or a real regression.
"""

from __future__ import annotations

import doctest
import importlib
import pkgutil

import pytest

import nu
import nustd


PACKAGES = ("nu", "nustd", "nucli")


def _modules() -> list[str]:
    names = []
    for package in PACKAGES:
        root = importlib.import_module(package)
        names.append(package)
        names.extend(info.name for info in pkgutil.walk_packages(root.__path__, f"{package}."))
    return names


def _has_examples(name: str) -> bool:
    module = importlib.import_module(name)
    return any(test.examples for test in doctest.DocTestFinder().find(module))


MODULES = [name for name in _modules() if _has_examples(name)]


@pytest.mark.parametrize("name", MODULES)
def test_doctests(name: str) -> None:
    module = importlib.import_module(name)
    result = doctest.testmod(
        module,
        extraglobs={"nu": nu, "nustd": nustd},
        optionflags=doctest.ELLIPSIS,
    )
    assert result.failed == 0, f"{result.failed} of {result.attempted} examples failed"
