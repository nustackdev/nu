"""Tests for Context - tagged value store for execution.

Context is the runtime address space. Immutability is critical:
bind/lazy return new Contexts, originals are never mutated.
Resolution uses type-keyed lookup with scope tag specificity fallback.
"""

from __future__ import annotations

import pytest

from nu import Context


# ---------------------------------------------------------------------------
# Dummy service types for binding
# ---------------------------------------------------------------------------


class ServiceA:
    pass


class ServiceB:
    pass


class ScopeX:
    pass


class ScopeY:
    pass


@pytest.fixture
def ctx() -> Context:
    return Context()


# ---------------------------------------------------------------------------
# Immutability - bind/lazy return new Context
# ---------------------------------------------------------------------------


def test_bind_returns_new_context(ctx):
    ctx2 = ctx.bind(ServiceA, ServiceA())
    assert ctx2 is not ctx


def test_bind_does_not_mutate_original(ctx):
    ctx.bind(ServiceA, ServiceA())
    assert ctx.has(ServiceA) is False


def test_lazy_returns_new_context(ctx):
    ctx2 = ctx.lazy(ServiceA, ServiceA)
    assert ctx2 is not ctx


def test_lazy_does_not_mutate_original(ctx):
    ctx.lazy(ServiceA, ServiceA)
    assert ctx.has(ServiceA) is False


# ---------------------------------------------------------------------------
# Eager resolution
# ---------------------------------------------------------------------------


def test_get_resolves_eager(ctx):
    s = ServiceA()
    ctx2 = ctx.bind(ServiceA, s)
    assert ctx2.get(ServiceA) is s


def test_get_different_types_independent(ctx):
    s = ServiceA()
    v = ServiceB()
    ctx2 = ctx.bind(ServiceA, s).bind(ServiceB, v)
    assert ctx2.get(ServiceA) is s
    assert ctx2.get(ServiceB) is v


# ---------------------------------------------------------------------------
# Lazy resolution
# ---------------------------------------------------------------------------


def test_get_resolves_lazy(ctx):
    s = ServiceA()
    ctx2 = ctx.lazy(ServiceA, lambda: s)
    assert ctx2.get(ServiceA) is s


def test_lazy_caches_result(ctx):
    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return ServiceA()

    ctx2 = ctx.lazy(ServiceA, factory)
    first = ctx2.get(ServiceA)
    second = ctx2.get(ServiceA)

    assert first is second
    assert call_count == 1


def test_was_opened_tracks_lazy(ctx):
    ctx2 = ctx.lazy(ServiceA, ServiceA)
    assert ctx2.was_opened(ServiceA) is False
    ctx2.get(ServiceA)
    assert ctx2.was_opened(ServiceA) is True


def test_was_opened_false_for_eager(ctx):
    ctx2 = ctx.bind(ServiceA, ServiceA())
    assert ctx2.was_opened(ServiceA) is False


# ---------------------------------------------------------------------------
# has
# ---------------------------------------------------------------------------


def test_has_before_bind(ctx):
    assert ctx.has(ServiceA) is False


def test_has_after_bind(ctx):
    ctx2 = ctx.bind(ServiceA, ServiceA())
    assert ctx2.has(ServiceA) is True


def test_has_after_lazy(ctx):
    ctx2 = ctx.lazy(ServiceA, ServiceA)
    assert ctx2.has(ServiceA) is True


# ---------------------------------------------------------------------------
# Missing binding
# ---------------------------------------------------------------------------


def test_missing_binding_raises(ctx):
    with pytest.raises(LookupError):
        ctx.get(ServiceA)


# ---------------------------------------------------------------------------
# Scope tags
# ---------------------------------------------------------------------------


def test_scope_tag_exact_match(ctx):
    s = ServiceA()
    ctx2 = ctx.bind(ServiceA, s, ScopeX)
    assert ctx2.get(ServiceA, ScopeX) is s


def test_scope_tag_no_match_without_tag(ctx):
    """Binding with tag is not found by untagged get."""
    ctx2 = ctx.bind(ServiceA, ServiceA(), ScopeX)
    with pytest.raises(LookupError):
        ctx2.get(ServiceA)


def test_untagged_fallback(ctx):
    """Untagged binding serves as fallback for tagged get."""
    s = ServiceA()
    ctx2 = ctx.bind(ServiceA, s)
    assert ctx2.get(ServiceA, ScopeX) is s


def test_tagged_takes_priority(ctx):
    general = ServiceA()
    specific = ServiceA()
    ctx2 = ctx.bind(ServiceA, general).bind(ServiceA, specific, ScopeX)
    assert ctx2.get(ServiceA, ScopeX) is specific
    assert ctx2.get(ServiceA) is general


# ---------------------------------------------------------------------------
# Specificity fallback
# ---------------------------------------------------------------------------


def test_specificity_fallback_subset(ctx):
    """get(T, A, B) falls back to binding with just (A) or (B)."""
    s = ServiceA()
    ctx2 = ctx.bind(ServiceA, s, ScopeX)
    # get with (ScopeX, ScopeY) should fall back to (ScopeX,)
    assert ctx2.get(ServiceA, ScopeX, ScopeY) is s


def test_specificity_fallback_to_empty(ctx):
    """get(T, A, B) falls back to untagged binding."""
    s = ServiceA()
    ctx2 = ctx.bind(ServiceA, s)
    assert ctx2.get(ServiceA, ScopeX, ScopeY) is s


def test_specificity_exact_wins_over_subset(ctx):
    """Exact tag match takes priority over subset fallback."""
    general = ServiceA()
    exact = ServiceA()
    ctx2 = ctx.bind(ServiceA, general, ScopeX).bind(ServiceA, exact, ScopeX, ScopeY)
    assert ctx2.get(ServiceA, ScopeX, ScopeY) is exact


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def test_predicate_match(ctx):
    s = ServiceA()
    ctx2 = ctx.bind(ServiceA, s, check=lambda check: check is True)
    assert ctx2.get(ServiceA, check=True) is s


def test_predicate_no_match(ctx):
    ctx2 = ctx.bind(ServiceA, ServiceA(), check=lambda check: check > 10)
    with pytest.raises(LookupError):
        ctx2.get(ServiceA, check=5)


def test_multiple_predicates_all_must_pass(ctx):
    """All predicate kwargs must pass (AND logic)."""
    s = ServiceA()
    ctx2 = ctx.bind(
        ServiceA, s,
        role=lambda **kw: kw["role"] == "admin",
        level=lambda **kw: kw["level"] >= 5,
    )
    assert ctx2.get(ServiceA, role="admin", level=10) is s


def test_multiple_predicates_partial_match_fails(ctx):
    """One predicate passes, another fails -> no match."""
    ctx2 = ctx.bind(
        ServiceA, ServiceA(),
        role=lambda **kw: kw["role"] == "admin",
        level=lambda **kw: kw["level"] >= 5,
    )
    with pytest.raises(LookupError):
        ctx2.get(ServiceA, role="admin", level=2)


# ---------------------------------------------------------------------------
# Attrs isolation
# ---------------------------------------------------------------------------


def test_attrs_independent_after_bind(ctx):
    ctx.attrs["x"] = 1
    ctx2 = ctx.bind(ServiceA, ServiceA())
    ctx2.attrs["x"] = 2

    assert ctx.attrs["x"] == 1
    assert ctx2.attrs["x"] == 2


def test_attrs_independent_after_lazy(ctx):
    ctx.attrs["x"] = 1
    ctx2 = ctx.lazy(ServiceA, ServiceA)
    ctx2.attrs["x"] = 2

    assert ctx.attrs["x"] == 1
    assert ctx2.attrs["x"] == 2


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_repr_empty(ctx):
    assert "Context" in repr(ctx)


def test_repr_with_binding(ctx):
    ctx2 = ctx.bind(ServiceA, ServiceA())
    r = repr(ctx2)
    assert "ServiceA" in r
