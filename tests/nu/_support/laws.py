"""Shared helpers for law tests.

``assert_passes`` and ``assert_fails`` are the two-line API every law test
reads against. They compile a Term through the real Nu schema, run every
``LAWS`` entry, and assert on the resulting violations.

A test file in ``tests/nu/lang/laws/`` does::

    from _support.laws import assert_fails, assert_passes

The ``_support`` package is on ``sys.path`` via the ``pythonpath`` entry in
``pyproject.toml``; tests need no ``__init__`` and no relative imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Severity, gate
from nu.lang.helpers import compile as nu_compile
from nu.lang.laws import LAWS


if TYPE_CHECKING:
    from nu.engine import Term, Violation


__all__ = ["assert_fails", "assert_passes", "violations"]


def violations(term: Term) -> list[Violation]:
    """Compile ``term`` against Nu's schema and gate it against every law.

    ``LAWS`` is a mutable list on ``nu.lang.laws``: any layer that registered
    additional laws at import time (e.g. ``nu.flows.parallel``) has already
    appended to the same list object we hold a reference to.
    """
    return gate(nu_compile(term), *LAWS)


def assert_passes(term: Term) -> None:
    """Assert the term raises no error-level violations.

    Warning-level violations pass through silently; assert on them
    directly via ``violations(term)`` when a test cares.
    """
    errors = [v for v in violations(term) if v.severity is Severity.ERROR]
    assert not errors, f"expected no errors, got: {errors}"


def assert_fails(term: Term, law_name: str) -> None:
    """Assert the term triggers a violation from the named law.

    Severity is not constrained; pass a WARNING-severity law name and the
    matching warning will satisfy the assertion.
    """
    fired = [v for v in violations(term) if v.law == law_name]
    assert fired, f"expected law '{law_name}' to fire; got: {violations(term)}"
