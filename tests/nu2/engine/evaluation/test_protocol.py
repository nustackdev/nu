"""Unit tests for ``nu2.engine.evaluation.protocol``.

The engine's evaluation layer is a single Protocol. These tests pin the
shape so a future accidental addition (a new method, an attribute slot,
losing ``runtime_checkable``) breaks loudly. Concrete dispatch behavior
lives in the language layer and is tested under ``tests/nu2/lang/``.
"""

from __future__ import annotations

from typing import Protocol

from nu2.engine.evaluation import Runtime


# --- shape -----------------------------------------------------------------


def test_runtime_is_a_protocol():
    assert Protocol in Runtime.__mro__


def test_runtime_surface_is_exactly_eval_and_aeval():
    own = {name for name in vars(Runtime) if not name.startswith("_")}
    assert own == {"eval", "aeval"}


# --- structural conformance ------------------------------------------------


def test_a_class_with_eval_and_aeval_satisfies_the_protocol():
    class Driver:
        def eval(self, nid: int = 0) -> object:
            return None

        async def aeval(self, nid: int = 0) -> object:
            return None

    assert isinstance(Driver(), Runtime)


def test_a_class_missing_aeval_does_not_satisfy_the_protocol():
    class HalfDriver:
        def eval(self, nid: int = 0) -> object:
            return None

    assert not isinstance(HalfDriver(), Runtime)


def test_a_class_missing_eval_does_not_satisfy_the_protocol():
    class AsyncOnlyDriver:
        async def aeval(self, nid: int = 0) -> object:
            return None

    assert not isinstance(AsyncOnlyDriver(), Runtime)


# --- the lang-layer concrete satisfies the engine contract -----------------


def test_nu_runtime_satisfies_the_runtime_protocol():
    # Imported here, not at module top, so this file does not couple the
    # engine test suite to the lang package on collection.
    from nu2.lang.runtime import NuRuntime

    assert issubclass(NuRuntime, Runtime)
