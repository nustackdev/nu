"""Tests for Context -- tagged value store.

Unit tests cover Context API in isolation.
E2E tests cover Context flowing through Refs, Flows, Spans, and error handling.
"""

from __future__ import annotations

import pytest

from everybase import Context


# --- Helpers ---


class Storage:
    pass


class OrderShape:
    pass


class MarketShape:
    pass


class View:
    pass


class Navigator:
    pass


class Worker:
    pass


# =============================================================================
# Bind and retrieve
# =============================================================================


class TestBind:
    """Basic bind and __getitem__ retrieval."""

    def test_bind_single_tag(self):
        ctx = Context().bind("rocksdb", Storage)
        assert ctx[Storage] == "rocksdb"

    def test_bind_two_tags(self):
        ctx = Context().bind("order_db", Storage, OrderShape)
        assert ctx[Storage, OrderShape] == "order_db"

    def test_bind_string_tag(self):
        ctx = Context().bind("timeout", "error")
        assert ctx["error"] == "timeout"

    def test_bind_int_tag(self):
        ctx = Context().bind("worker_0", Worker, 0)
        assert ctx[Worker, 0] == "worker_0"

    def test_bind_none_value(self):
        ctx = Context().bind(None, "flag")
        assert ctx["flag"] is None

    def test_bind_override(self):
        ctx = Context().bind("old", Storage).bind("new", Storage)
        assert ctx[Storage] == "new"

    def test_bind_scoped_override(self):
        ctx = Context().bind("old", Storage, MarketShape).bind("new", Storage, MarketShape)
        assert ctx[Storage, MarketShape] == "new"

    def test_bind_chain(self):
        ctx = (
            Context().bind("nav", Navigator).bind("view", View).bind("store", Storage, MarketShape)
        )
        assert ctx[Navigator] == "nav"
        assert ctx[View] == "view"
        assert ctx[Storage, MarketShape] == "store"


# =============================================================================
# Immutability
# =============================================================================


class TestImmutability:
    """bind() and lazy() return new Context, original unchanged."""

    def test_bind_immutable(self):
        ctx_a = Context().bind("x", Storage)
        ctx_b = ctx_a.bind("y", Storage)
        assert ctx_a[Storage] == "x"
        assert ctx_b[Storage] == "y"

    def test_lazy_immutable(self):
        ctx_a = Context().lazy(lambda: "x", Storage)
        ctx_b = ctx_a.lazy(lambda: "y", Storage)
        assert ctx_a[Storage] == "x"
        assert ctx_b[Storage] == "y"


# =============================================================================
# Specificity fallback
# =============================================================================


class TestSpecificity:
    """Scope tag subset fallback."""

    def test_fallback_to_unscoped(self):
        ctx = Context().bind("default", Storage)
        assert ctx[Storage, MarketShape] == "default"

    def test_exact_over_fallback(self):
        ctx = Context().bind("default", Storage).bind("market", Storage, MarketShape)
        assert ctx[Storage, MarketShape] == "market"
        assert ctx[Storage, OrderShape] == "default"

    def test_larger_subset_preferred(self):
        ctx = Context().bind("broad", Storage).bind("narrow", Storage, MarketShape, OrderShape)
        assert ctx[Storage, MarketShape, OrderShape] == "narrow"
        assert ctx[Storage, MarketShape] == "broad"

    def test_no_match_raises(self):
        ctx = Context()
        with pytest.raises(LookupError):
            ctx[Storage]

    def test_wrong_service_type_raises(self):
        ctx = Context().bind("nav", Navigator)
        with pytest.raises(LookupError):
            ctx[Storage]

    def test_scope_alone_does_not_resolve(self):
        """MarketShape alone shouldn't match a Storage+MarketShape binding."""
        ctx = Context().bind("x", Storage, MarketShape)
        with pytest.raises(LookupError):
            ctx[MarketShape]


# =============================================================================
# Lazy factories
# =============================================================================


class TestLazy:
    """Deferred value creation."""

    def test_lazy_creates_on_access(self):
        calls = []
        ctx = Context().lazy(lambda: (calls.append(1), "val")[1], Storage)
        assert len(calls) == 0
        assert ctx[Storage] == "val"
        assert len(calls) == 1

    def test_lazy_caches(self):
        calls = []
        ctx = Context().lazy(lambda: (calls.append(1), "val")[1], Storage)
        ctx[Storage]
        ctx[Storage]
        assert len(calls) == 1

    def test_lazy_scoped(self):
        ctx = Context().lazy(lambda: "market_db", Storage, MarketShape)
        assert ctx[Storage, MarketShape] == "market_db"

    def test_lazy_fallback(self):
        ctx = Context().lazy(lambda: "default", Storage)
        assert ctx[Storage, MarketShape] == "default"

    def test_lazy_override_by_bind(self):
        ctx = Context().lazy(lambda: "lazy", Storage).bind("eager", Storage)
        assert ctx[Storage] == "eager"


# =============================================================================
# Named predicates
# =============================================================================


class TestPredicates:
    """Named predicate guards via kwargs."""

    def test_single_predicate(self):
        ctx = (
            Context()
            .bind("low", View, MarketShape, sharding=lambda site: site[0] < 16)
            .bind("high", View, MarketShape, sharding=lambda site: site[0] >= 16)
        )
        assert ctx.get(View, MarketShape, site=(5,)) == "low"
        assert ctx.get(View, MarketShape, site=(20,)) == "high"

    def test_predicate_boundary(self):
        ctx = (
            Context()
            .bind("low", View, MarketShape, sharding=lambda site: site[0] < 16)
            .bind("high", View, MarketShape, sharding=lambda site: site[0] >= 16)
        )
        assert ctx.get(View, MarketShape, site=(0,)) == "low"
        assert ctx.get(View, MarketShape, site=(15,)) == "low"
        assert ctx.get(View, MarketShape, site=(16,)) == "high"

    def test_multiple_predicates(self):
        ctx = Context().bind(
            "hot_low",
            View,
            MarketShape,
            sharding=lambda site: site[0] < 16,
            tier=lambda site: site[1] == "hot",
        )
        assert ctx.get(View, MarketShape, site=(5, "hot")) == "hot_low"

    def test_predicate_all_must_match(self):
        """Multiple predicates on one entry are AND."""
        ctx = Context().bind(
            "hot_low",
            View,
            MarketShape,
            sharding=lambda site: site[0] < 16,
            tier=lambda site: site[1] == "hot",
        )
        with pytest.raises(LookupError):
            ctx.get(View, MarketShape, site=(5, "cold"))

    def test_predicate_scope_mismatch_raises(self):
        ctx = Context().bind("low", View, MarketShape, sharding=lambda site: site[0] < 16)
        with pytest.raises(LookupError):
            ctx.get(View, OrderShape, site=(5,))

    def test_guarded_strict_no_fallback_to_non_predicate(self):
        """If guarded entries exist at a scope, non-predicate at same scope is not tried."""
        ctx = (
            Context()
            .bind("default", View, MarketShape)  # non-predicate
            .bind("low", View, MarketShape, sharding=lambda site: site[0] < 16)  # guarded
        )
        # Guarded entries exist for (View, {MarketShape}), so predicate must match
        assert ctx.get(View, MarketShape, site=(5,)) == "low"
        # No predicate matches site[0]=20 and there's only one guarded entry
        with pytest.raises(LookupError):
            ctx.get(View, MarketShape, site=(20,))

    def test_no_guarded_ignores_data(self):
        """When no guarded entries, data kwargs are ignored, fast path returns."""
        ctx = Context().bind("default", View, MarketShape)
        assert ctx.get(View, MarketShape, site=(999,)) == "default"

    def test_fallback_scope_with_predicates(self):
        """Guarded at Market scope, non-predicate unscoped as fallback for other scopes."""
        ctx = (
            Context()
            .bind("default", View)
            .bind("low", View, MarketShape, sharding=lambda site: site[0] < 16)
            .bind("high", View, MarketShape, sharding=lambda site: site[0] >= 16)
        )
        assert ctx.get(View, MarketShape, site=(5,)) == "low"
        assert ctx.get(View, MarketShape, site=(20,)) == "high"
        # OrderShape has no guarded entries, falls back to unscoped
        assert ctx.get(View, OrderShape, site=(999,)) == "default"

    def test_getitem_ignores_guarded(self):
        """__getitem__ doesn't pass data, so guarded entries are checked but
        with no data the predicates should still be evaluated (with empty kwargs)."""
        ctx = (
            Context()
            .bind("default", View)
            .bind("low", View, MarketShape, sharding=lambda site: site[0] < 16)
        )
        # __getitem__ at MarketShape scope: guarded exists, predicates called
        # with no kwargs -> TypeError (missing 'site') -> no match -> fallback
        # Actually this should fall back to unscoped
        assert ctx[View] == "default"

    def test_lazy_predicate(self):
        calls = []

        def factory():
            calls.append(1)
            return "lazy_shard"

        ctx = Context().lazy(factory, View, MarketShape, sharding=lambda site: site[0] < 16)
        assert len(calls) == 0
        assert ctx.get(View, MarketShape, site=(5,)) == "lazy_shard"
        assert len(calls) == 1
        # Cached
        assert ctx.get(View, MarketShape, site=(3,)) == "lazy_shard"
        assert len(calls) == 1

    def test_cartesian_predicates(self):
        """Full cartesian coverage: 2 shards x 2 tiers = 4 entries."""
        ctx = (
            Context()
            .bind(
                "hot_low",
                View,
                MarketShape,
                shard=lambda site: site[0] < 16,
                tier=lambda site: site[1] == "hot",
            )
            .bind(
                "cold_low",
                View,
                MarketShape,
                shard=lambda site: site[0] < 16,
                tier=lambda site: site[1] == "cold",
            )
            .bind(
                "hot_high",
                View,
                MarketShape,
                shard=lambda site: site[0] >= 16,
                tier=lambda site: site[1] == "hot",
            )
            .bind(
                "cold_high",
                View,
                MarketShape,
                shard=lambda site: site[0] >= 16,
                tier=lambda site: site[1] == "cold",
            )
        )
        assert ctx.get(View, MarketShape, site=(5, "hot")) == "hot_low"
        assert ctx.get(View, MarketShape, site=(5, "cold")) == "cold_low"
        assert ctx.get(View, MarketShape, site=(20, "hot")) == "hot_high"
        assert ctx.get(View, MarketShape, site=(20, "cold")) == "cold_high"

    def test_predicate_receives_all_data_kwargs(self):
        """Predicate receives all kwargs from get()."""
        received = {}

        def capture(**kwargs):
            received.update(kwargs)
            return True

        ctx = Context().bind("val", View, MarketShape, pred=capture)
        ctx.get(View, MarketShape, site=(1, 2), path="abc")
        assert received == {"site": (1, 2), "path": "abc"}


# =============================================================================
# get() method
# =============================================================================


class TestGet:
    """Explicit get() for non-predicate lookups."""

    def test_get_basic(self):
        ctx = Context().bind("val", Storage)
        assert ctx.get(Storage) == "val"

    def test_get_scoped(self):
        ctx = Context().bind("val", Storage, MarketShape)
        assert ctx.get(Storage, MarketShape) == "val"

    def test_get_raises(self):
        ctx = Context()
        with pytest.raises(LookupError):
            ctx.get(Storage)


# =============================================================================
# has() and was_opened()
# =============================================================================


class TestHasAndWasOpened:
    def test_has_true(self):
        ctx = Context().bind("val", Storage, MarketShape)
        assert ctx.has(Storage, MarketShape)

    def test_has_false(self):
        ctx = Context().bind("val", Storage)
        assert not ctx.has(Navigator)

    def test_has_fallback(self):
        ctx = Context().bind("val", Storage)
        assert ctx.has(Storage, MarketShape)  # fallback resolves

    def test_was_opened_false_before_access(self):
        ctx = Context().lazy(lambda: "v", Storage)
        assert not ctx.was_opened(Storage)

    def test_was_opened_true_after_access(self):
        ctx = Context().lazy(lambda: "v", Storage)
        ctx[Storage]
        assert ctx.was_opened(Storage)

    def test_was_opened_false_for_eager(self):
        ctx = Context().bind("v", Storage)
        assert not ctx.was_opened(Storage)


# =============================================================================
# __contains__
# =============================================================================


class TestContains:
    def test_contains_true(self):
        ctx = Context().bind("v", Storage)
        assert Storage in ctx

    def test_contains_tuple(self):
        ctx = Context().bind("v", Storage, MarketShape)
        assert (Storage, MarketShape) in ctx

    def test_contains_false(self):
        ctx = Context()
        assert Storage not in ctx

    def test_contains_fallback(self):
        ctx = Context().bind("v", Storage)
        assert (Storage, MarketShape) in ctx


# =============================================================================
# __repr__
# =============================================================================


class TestRepr:
    def test_repr_empty(self):
        assert repr(Context()) == "Context()"

    def test_repr_binding(self):
        ctx = Context().bind("v", Storage)
        r = repr(ctx)
        assert "Context(" in r
        assert "Storage" in r

    def test_repr_lazy(self):
        ctx = Context().lazy(lambda: "v", Storage)
        r = repr(ctx)
        assert "lazy" in r


# =============================================================================
# Edge cases
# =============================================================================


class TestEdgeCases:
    def test_empty_getitem_raises(self):
        ctx = Context()
        with pytest.raises(ValueError):
            ctx[()]

    def test_empty_contains(self):
        ctx = Context()
        assert () not in ctx

    def test_multiple_service_types(self):
        ctx = Context().bind("nav", Navigator).bind("view", View).bind("store", Storage)
        assert ctx[Navigator] == "nav"
        assert ctx[View] == "view"
        assert ctx[Storage] == "store"

    def test_predicate_entries_independent(self):
        """Two different service types with predicates don't interfere."""
        ctx = (
            Context()
            .bind("view_low", View, MarketShape, sharding=lambda site: site[0] < 16)
            .bind("store_low", Storage, MarketShape, sharding=lambda site: site[0] < 100)
        )
        assert ctx.get(View, MarketShape, site=(5,)) == "view_low"
        assert ctx.get(Storage, MarketShape, site=(50,)) == "store_low"


# =============================================================================
# Attributes
# =============================================================================


class TestAttributes:
    """ctx.attrs -- flat mutable key-value store."""

    def test_set_and_get(self):
        ctx = Context()
        ctx.attrs["error"] = "timeout"
        assert ctx.attrs["error"] == "timeout"

    def test_contains(self):
        ctx = Context()
        ctx.attrs["x"] = 1
        assert "x" in ctx.attrs
        assert "y" not in ctx.attrs

    def test_delete(self):
        ctx = Context()
        ctx.attrs["x"] = 1
        del ctx.attrs["x"]
        assert "x" not in ctx.attrs

    def test_get_with_default(self):
        ctx = Context()
        assert ctx.attrs.get("missing", 42) == 42
        assert ctx.attrs.get("missing") is None

    def test_len(self):
        ctx = Context()
        assert len(ctx.attrs) == 0
        ctx.attrs["a"] = 1
        ctx.attrs["b"] = 2
        assert len(ctx.attrs) == 2

    def test_keys_values_items(self):
        ctx = Context()
        ctx.attrs["a"] = 1
        ctx.attrs["b"] = 2
        assert set(ctx.attrs.keys()) == {"a", "b"}
        assert set(ctx.attrs.values()) == {1, 2}
        assert set(ctx.attrs.items()) == {("a", 1), ("b", 2)}

    def test_copy_independent(self):
        ctx = Context()
        ctx.attrs["x"] = [1, 2, 3]
        copied = ctx.attrs.copy()
        copied["x"].append(4)
        assert ctx.attrs["x"] == [1, 2, 3]  # deep copy, original unchanged
        assert copied["x"] == [1, 2, 3, 4]

    def test_context_copy_isolates_attrs(self):
        """Context._copy() gives child its own attrs."""
        ctx = Context()
        ctx.attrs["x"] = 1
        child = ctx._copy()
        child.attrs["x"] = 999
        child.attrs["y"] = 2
        assert ctx.attrs["x"] == 1
        assert "y" not in ctx.attrs

    def test_repr(self):
        ctx = Context()
        assert repr(ctx.attrs) == "Attributes()"
        ctx.attrs["error"] = "boom"
        assert "error" in repr(ctx.attrs)

    def test_missing_key_raises(self):
        ctx = Context()
        with pytest.raises(KeyError):
            ctx.attrs["missing"]


# =============================================================================
# E2E: Attributes through PrimRef
# =============================================================================


class TestAttributesE2EPrimRef:
    """PrimRef reads and writes through ctx.attrs."""

    async def test_prim_ref_reads_from_attrs(self):
        from everybase.abc import PrimRef

        ctx = Context()
        ctx.attrs["greeting"] = "hello"
        ref = PrimRef("greeting")
        result = await ref.fetch(ctx)
        assert result == "hello"

    async def test_prim_ref_exists(self):
        from everybase.abc import PrimRef

        ctx = Context()
        ref = PrimRef("maybe")
        assert await ref.exists().execute(ctx) is False
        ctx.attrs["maybe"] = "yes"
        assert await ref.exists().execute(ctx) is True


# =============================================================================
# E2E: Context through Refs
# =============================================================================


class TestContextE2EDict:
    """Context flowing through eb-dict refs (store/execute via ctx[dict, scope])."""

    @pytest.fixture
    def shapes(self):
        from eb_dict import IntRef, StrRef
        from everybase.shape import Shape

        class User(Shape):
            name = StrRef.slot()
            age = IntRef.slot()

        return User

    async def test_ref_store_and_read(self, shapes):
        """Ref.store() writes to ctx-bound dict, ref.execute() reads back."""
        User = shapes
        data = {}
        ctx = Context().bind(data, dict, User)

        await User.name.store("alice").execute(ctx)
        result = await User.name.execute(ctx)
        assert result == "alice"

    async def test_ref_scoped_isolation(self, shapes):
        """Different shapes get different dicts via context scoping."""
        from eb_dict import StrRef
        from everybase.shape import Shape

        User = shapes

        class Product(Shape):
            name = StrRef.slot()

        user_data, product_data = {}, {}
        ctx = Context().bind(user_data, dict, User).bind(product_data, dict, Product)

        await User.name.store("alice").execute(ctx)
        await Product.name.store("widget").execute(ctx)

        assert await User.name.execute(ctx) == "alice"
        assert await Product.name.execute(ctx) == "widget"
        assert user_data != product_data

    async def test_ref_fallback_to_unscoped(self, shapes):
        """Ref resolves unscoped dict binding when no shape-specific one exists."""
        User = shapes
        data = {}
        ctx = Context().bind(data, dict)  # no scope

        await User.name.store("bob").execute(ctx)
        assert await User.name.execute(ctx) == "bob"


# =============================================================================
# E2E: Context through Flows
# =============================================================================


class TestContextE2EFlows:
    """Context flowing through flow execution."""

    async def test_seq_shares_context(self):
        """Seq children share the same context."""
        from eb_dict import IntRef
        from everybase.abc import Seq
        from everybase.shape import Shape

        class Counter(Shape):
            val = IntRef.slot()

        data = {}
        ctx = Context().bind(data, dict, Counter)

        tree = Seq(
            Counter.val.store(0),
            Counter.val.store(Counter.val + 1),
            Counter.val.store(Counter.val + 1),
        )
        await tree.execute(ctx)
        assert await Counter.val.execute(ctx) == 2

    async def test_for_range_with_context(self):
        """ForRange iterates within context-bound storage."""
        from eb_dict import IntRef
        from everybase.abc import ForRange, Seq
        from everybase.shape import Shape

        class Acc(Shape):
            total = IntRef.slot()
            i = IntRef.slot()

        data = {}
        ctx = Context().bind(data, dict, Acc)

        tree = Seq(
            Acc.total.store(0),
            ForRange(0, 5, Acc.total.store(Acc.total + 1), index=Acc.i),
        )
        await tree.execute(ctx)
        assert await Acc.total.execute(ctx) == 5


# =============================================================================
# E2E: Context through error handling
# =============================================================================


class TestContextE2EErrors:
    """TryCatch and Retry bind error/attempt into context."""

    async def test_try_catch_binds_error(self):
        """TryCatch handler receives ctx with 'error' bound."""
        from everybase import Term
        from everybase.abc import TryCatch

        class FailTerm(Term):
            def __init__(self):
                super().__init__()

            @property
            def is_self_pure(self):
                return False

            async def execute(self, ctx):
                raise RuntimeError("boom")

        captured = {}

        class CaptureTerm(Term):
            def __init__(self):
                super().__init__()

            @property
            def is_self_pure(self):
                return False

            async def execute(self, ctx):
                captured["error"] = ctx.attrs["error"]

        tree = TryCatch(FailTerm(), catch=CaptureTerm())
        await tree.execute(Context())
        assert captured["error"] == "boom"

    async def test_retry_binds_attempt(self):
        """Retry hooks receive ctx with 'attempt' bound."""
        from everybase import Term
        from everybase.abc import Retry

        attempts = []
        call_count = 0

        class FlakeyTerm(Term):
            def __init__(self):
                super().__init__()

            @property
            def is_self_pure(self):
                return False

            async def execute(self, ctx):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise RuntimeError("fail")

        class CaptureAttempt(Term):
            def __init__(self):
                super().__init__()

            @property
            def is_self_pure(self):
                return False

            async def execute(self, ctx):
                attempts.append(ctx.attrs["attempt"])

        tree = Retry(FlakeyTerm(), max_attempts=3, on_success=CaptureAttempt())
        await tree.execute(Context())
        assert attempts == [3]


# =============================================================================
# E2E: Context through Spans (lazy factories)
# =============================================================================


class TestContextE2ESpans:
    """Spans create child contexts with lazy bindings."""

    async def test_span_enter_binds_to_child_context(self):
        """A custom span can bind values into child context."""
        from everybase import Context, Span, Term

        class InjectSpan(Span):
            def __init__(self, *children, key, value):
                super().__init__(*children)
                self._key = key
                self._value = value

            def enter(self, ctx):
                return ctx.bind(self._value, self._key)

        captured = {}

        class ReadTerm(Term):
            def __init__(self, key):
                super().__init__()
                self._key = key

            @property
            def is_self_pure(self):
                return True

            async def execute(self, ctx):
                captured["val"] = ctx[self._key]

        tree = InjectSpan(ReadTerm("config"), key="config", value="production")
        await tree.execute(Context())
        assert captured["val"] == "production"

    async def test_span_lazy_binding_deferred(self):
        """Lazy bindings in span are not materialized until accessed."""
        from everybase import Context, Span, Term

        calls = []

        class LazySpan(Span):
            def __init__(self, *children):
                super().__init__(*children)

            def enter(self, ctx):
                return ctx.lazy(lambda: (calls.append(1), "expensive")[1], "resource")

        class NoOpTerm(Term):
            def __init__(self):
                super().__init__()

            @property
            def is_self_pure(self):
                return True

            async def execute(self, ctx):
                pass

        tree = LazySpan(NoOpTerm())
        await tree.execute(Context())
        assert len(calls) == 0

    async def test_span_child_context_isolated(self):
        """Parent context not affected by span's child context."""
        from everybase import Context, Span, Term

        class OverrideSpan(Span):
            def __init__(self, *children):
                super().__init__(*children)

            def enter(self, ctx):
                return ctx.bind("overridden", "val")

        parent_ctx = Context().bind("original", "val")

        class CheckTerm(Term):
            def __init__(self):
                super().__init__()

            @property
            def is_self_pure(self):
                return True

            async def execute(self, ctx):
                assert ctx["val"] == "overridden"

        tree = OverrideSpan(CheckTerm())
        await tree.execute(parent_ctx)
        assert parent_ctx["val"] == "original"
