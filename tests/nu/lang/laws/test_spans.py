"""Span transparency laws.

Mirrors ``src/nu/lang/laws/spans.py``. Exercises ``span_has_body`` and
``span_cardinality_matches_body``.
"""

from __future__ import annotations

import pytest
from _support.law_terms import Brk, Cmd, Pol, Q, R, Stream
from _support.laws import assert_fails, assert_passes

# Import concrete Span families so ``Span.__subclasses__()`` sees them for
# the body-at-slot-0 sweep. Side-effect imports; reference the modules to
# keep the linter quiet.
import nu.context.attrs.interactions as _ctx_attrs  # noqa: F401
import nu.context.fabric.lifecycle as _ctx_lifecycle  # noqa: F401
import nu.inspect.annotate as _inspect_annotate  # noqa: F401
import nu.kv.interactions.atomicity as _kv_atomicity  # noqa: F401
import nu.mp.interactions as _mp_interactions  # noqa: F401
import nu.spans.bracket as _spans_bracket  # noqa: F401
import nu.spans.policy as _spans_policy  # noqa: F401
from nu.engine.compilation import UnknownAttributeError
from nu.engine.structure import Declared
from nu.lang import Bracket, Policy, Span
from nu.lang import compile as nu_compile
from nu.lang.attributes import Cardinality


# --- malformed shapes for negative cases -------------------------------


class BrkEmpty(Bracket):
    """A Bracket built with no body for span_has_body coverage."""


class PolEmpty(Policy):
    """A Policy built with no body for span_has_body coverage."""


class BrkScalar(Bracket):
    """A Bracket that wrongly fixes its cardinality to SCALAR.

    Span's whole point is transparency: own cardinality must be
    TRANSPARENT so child_cardinality forwards the body's yield. Pinning it
    to SCALAR breaks the invariant whenever the body is not scalar.
    """

    _cardinality = Declared(value=Cardinality.SCALAR, name="cardinality")


# --- span_has_body -----------------------------------------------------


def test_span_has_body_passes_when_bracket_wraps_a_body() -> None:
    """A Bracket holding a ScalarQuery has its body slot filled."""
    assert_passes(Brk(Q(R())))


def test_span_has_body_passes_when_policy_wraps_a_body() -> None:
    """A Policy holding a Command has its body slot filled."""
    assert_passes(Pol(Cmd(R())))


def test_span_has_body_fails_when_bracket_has_no_children() -> None:
    """A childless Bracket wraps nothing."""
    assert_fails(BrkEmpty(), "span_has_body")


def test_span_has_body_fails_when_policy_has_no_children() -> None:
    """A childless Policy wraps nothing."""
    assert_fails(PolEmpty(), "span_has_body")


# --- span_cardinality_matches_body -------------------------------------


def test_span_cardinality_matches_body_passes_for_scalar_body() -> None:
    """A canonical Bracket forwards its body's scalar cardinality."""
    assert_passes(Brk(Q(R())))


def test_span_cardinality_matches_body_passes_for_stream_body() -> None:
    """A canonical Bracket forwards its body's stream cardinality."""
    assert_passes(Brk(Stream(R())))


def test_span_cardinality_matches_body_passes_through_nested_span() -> None:
    """Transparency composes: a Bracket wrapping a Policy wrapping a stream."""
    assert_passes(Brk(Pol(Stream(R()))))


def test_span_cardinality_matches_body_fails_when_span_pins_scalar_over_stream() -> None:
    """A Span declaring SCALAR cardinality with a STREAM body lies about its yield."""
    assert_fails(BrkScalar(Stream(R())), "span_cardinality_matches_body")


# --- bare Span construction --------------------------------------------


def test_bare_span_compiles_but_attribute_lookup_errors() -> None:
    """Bare ``Span`` is constructible but has no ``_sort``, so attribute
    compilation dies deep. Pin this behavior: if a guard is ever added the
    test will scream and the intent becomes explicit."""
    with pytest.raises(UnknownAttributeError, match="Span has no attribute"):
        nu_compile(Span(Q(R())))


# --- body-at-slot-0 convention -----------------------------------------


def _all_span_subclasses() -> list[type]:
    def walk(cls: type):
        yield cls
        for sub in cls.__subclasses__():
            yield from walk(sub)

    return [c for c in walk(Span) if c is not Span]


@pytest.mark.parametrize("cls", _all_span_subclasses(), ids=lambda c: c.__name__)
def test_span_subclass_keeps_body_at_slot_zero(cls: type) -> None:
    """Every Span subclass keeps slot 0 as body (no param slot at 0).

    The transparency walks in ``_resolve_cardinality``, ``_slot_fit_sort``,
    ``_effective_sort``, ``has_body``, ``cardinality_matches_body``, and
    ``_LifecycleBracket._compile`` all hard-code ``children[0]``. A subclass
    that declared ``_param_slots`` including 0 would silently break every
    one of those walks. Guard the invariant here.
    """
    declared = cls.__dict__.get("_param_slots")
    if declared is None:
        return  # inherits Interaction's default ``frozenset()`` -> slot 0 is body
    assert 0 not in declared.value, (
        f"{cls.__name__} declares slot 0 as a param; Span transparency assumes body-at-0"
    )
