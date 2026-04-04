"""Tests for Context -- tagged value store.

Unit tests cover Context API in isolation.
E2E tests cover Context flowing through Refs, Flows, Spans, and error handling.
"""

from __future__ import annotations

import pytest

from nu import Context


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
    """Basic bind and get() retrieval."""

    def test_bind_single_tag(self):
        ctx = Context().bind(Storage, "rocksdb")
        assert ctx.get(Storage) == "rocksdb"

    def test_bind_two_tags(self):
        ctx = Context().bind(Storage, "order_db", OrderShape)
        assert ctx.get(Storage, OrderShape) == "order_db"

    def test_bind_string_tag(self):
        ctx = Context().bind("error", "timeout")
        assert ctx.get("error") == "timeout"

    def test_bind_int_tag(self):
        ctx = Context().bind(Worker, "worker_0", 0)
        assert ctx.get(Worker, 0) == "worker_0"

    def test_bind_none_value(self):
        ctx = Context().bind("flag", None)
        assert ctx.get("flag") is None

    def test_bind_override(self):
        ctx = Context().bind(Storage, "old").bind(Storage, "new")
        assert ctx.get(Storage) == "new"

    def test_bind_scoped_override(self):
        ctx = Context().bind(Storage, "old", MarketShape).bind(Storage, "new", MarketShape)
        assert ctx.get(Storage, MarketShape) == "new"

    def test_bind_chain(self):
        ctx = (
            Context()
            .bind(Navigator, "nav")
            .bind(View, "view")
            .bind(Storage, "store", MarketShape)
        )
        assert ctx.get(Navigator) == "nav"
        assert ctx.get(View) == "view"
        assert ctx.get(Storage, MarketShape) == "store"


# =============================================================================
# Immutability
# =============================================================================


class TestImmutability:
    """bind() and lazy() return new Context, original unchanged."""

    def test_bind_immutable(self):
        ctx_a = Context().bind(Storage, "x")
        ctx_b = ctx_a.bind(Storage, "y")
        assert ctx_a.get(Storage) == "x"
        assert ctx_b.get(Storage) == "y"

    def test_lazy_immutable(self):
        ctx_a = Context().lazy(Storage, lambda: "x")
        ctx_b = ctx_a.lazy(Storage, lambda: "y")
        assert ctx_a.get(Storage) == "x"
        assert ctx_b.get(Storage) == "y"


# =============================================================================
# Specificity fallback
# =============================================================================


class TestSpecificity:
    """Scope tag subset fallback."""

    def test_fallback_to_unscoped(self):
        ctx = Context().bind(Storage, "default")
        assert ctx.get(Storage, MarketShape) == "default"

    def test_exact_over_fallback(self):
        ctx = Context().bind(Storage, "default").bind(Storage, "market", MarketShape)
        assert ctx.get(Storage, MarketShape) == "market"
        assert ctx.get(Storage, OrderShape) == "default"

    def test_larger_subset_preferred(self):
        ctx = Context().bind(Storage, "broad").bind(Storage, "narrow", MarketShape, OrderShape)
        assert ctx.get(Storage, MarketShape, OrderShape) == "narrow"
        assert ctx.get(Storage, MarketShape) == "broad"

    def test_no_match_raises(self):
        ctx = Context()
        with pytest.raises(LookupError):
            ctx.get(Storage)

    def test_wrong_service_type_raises(self):
        ctx = Context().bind(Navigator, "nav")
        with pytest.raises(LookupError):
            ctx.get(Storage)

    def test_scope_alone_does_not_resolve(self):
        """MarketShape alone shouldn't match a Storage+MarketShape binding."""
        ctx = Context().bind(Storage, "x", MarketShape)
        with pytest.raises(LookupError):
            ctx.get(MarketShape)


# =============================================================================
# Lazy factories
# =============================================================================


class TestLazy:
    """Deferred value creation."""

    def test_lazy_creates_on_access(self):
        calls = []
        ctx = Context().lazy(Storage, lambda: (calls.append(1), "val")[1])
        assert len(calls) == 0
        assert ctx.get(Storage) == "val"
        assert len(calls) == 1

    def test_lazy_caches(self):
        calls = []
        ctx = Context().lazy(Storage, lambda: (calls.append(1), "val")[1])
        ctx.get(Storage)
        ctx.get(Storage)
        assert len(calls) == 1

    def test_lazy_scoped(self):
        ctx = Context().lazy(Storage, lambda: "market_db", MarketShape)
        assert ctx.get(Storage, MarketShape) == "market_db"

    def test_lazy_fallback(self):
        ctx = Context().lazy(Storage, lambda: "default")
        assert ctx.get(Storage, MarketShape) == "default"

    def test_lazy_override_by_bind(self):
        ctx = Context().lazy(Storage, lambda: "lazy").bind(Storage, "eager")
        assert ctx.get(Storage) == "eager"


# =============================================================================
# Named predicates
# =============================================================================


class TestPredicates:
    """Named predicate guards via kwargs."""

    def test_single_predicate(self):
        ctx = (
            Context()
            .bind(View, "low", MarketShape, sharding=lambda site: site[0] < 16)
            .bind(View, "high", MarketShape, sharding=lambda site: site[0] >= 16)
        )
        assert ctx.get(View, MarketShape, site=(5,)) == "low"
        assert ctx.get(View, MarketShape, site=(20,)) == "high"

    def test_predicate_boundary(self):
        ctx = (
            Context()
            .bind(View, "low", MarketShape, sharding=lambda site: site[0] < 16)
            .bind(View, "high", MarketShape, sharding=lambda site: site[0] >= 16)
        )
        assert ctx.get(View, MarketShape, site=(0,)) == "low"
        assert ctx.get(View, MarketShape, site=(15,)) == "low"
        assert ctx.get(View, MarketShape, site=(16,)) == "high"

    def test_multiple_predicates(self):
        ctx = Context().bind(
            View,
            "hot_low",
            MarketShape,
            sharding=lambda site: site[0] < 16,
            tier=lambda site: site[1] == "hot",
        )
        assert ctx.get(View, MarketShape, site=(5, "hot")) == "hot_low"

    def test_predicate_all_must_match(self):
        """Multiple predicates on one entry are AND."""
        ctx = Context().bind(
            View,
            "hot_low",
            MarketShape,
            sharding=lambda site: site[0] < 16,
            tier=lambda site: site[1] == "hot",
        )
        with pytest.raises(LookupError):
            ctx.get(View, MarketShape, site=(5, "cold"))

    def test_predicate_scope_mismatch_raises(self):
        ctx = Context().bind(View, "low", MarketShape, sharding=lambda site: site[0] < 16)
        with pytest.raises(LookupError):
            ctx.get(View, OrderShape, site=(5,))

    def test_guarded_strict_no_fallback_to_non_predicate(self):
        """If guarded entries exist at a scope, non-predicate at same scope is not tried."""
        ctx = (
            Context()
            .bind(View, "default", MarketShape)  # non-predicate
            .bind(View, "low", MarketShape, sharding=lambda site: site[0] < 16)  # guarded
        )
        # Guarded entries exist for (View, {MarketShape}), so predicate must match
        assert ctx.get(View, MarketShape, site=(5,)) == "low"
        # No predicate matches site[0]=20 and there's only one guarded entry
        with pytest.raises(LookupError):
            ctx.get(View, MarketShape, site=(20,))

    def test_no_guarded_ignores_data(self):
        """When no guarded entries, data kwargs are ignored, fast path returns."""
        ctx = Context().bind(View, "default", MarketShape)
        assert ctx.get(View, MarketShape, site=(999,)) == "default"

    def test_fallback_scope_with_predicates(self):
        """Guarded at Market scope, non-predicate unscoped as fallback for other scopes."""
        ctx = (
            Context()
            .bind(View, "default")
            .bind(View, "low", MarketShape, sharding=lambda site: site[0] < 16)
            .bind(View, "high", MarketShape, sharding=lambda site: site[0] >= 16)
        )
        assert ctx.get(View, MarketShape, site=(5,)) == "low"
        assert ctx.get(View, MarketShape, site=(20,)) == "high"
        # OrderShape has no guarded entries, falls back to unscoped
        assert ctx.get(View, OrderShape, site=(999,)) == "default"

    def test_get_without_data_ignores_guarded(self):
        """get() without data kwargs doesn't check guarded entries."""
        ctx = (
            Context()
            .bind(View, "default")
            .bind(View, "low", MarketShape, sharding=lambda site: site[0] < 16)
        )
        # No data -> guarded skipped -> fallback to unscoped
        assert ctx.get(View) == "default"

    def test_lazy_predicate(self):
        calls = []

        def factory():
            calls.append(1)
            return "lazy_shard"

        ctx = Context().lazy(View, factory, MarketShape, sharding=lambda site: site[0] < 16)
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
                View,
                "hot_low",
                MarketShape,
                shard=lambda site: site[0] < 16,
                tier=lambda site: site[1] == "hot",
            )
            .bind(
                View,
                "cold_low",
                MarketShape,
                shard=lambda site: site[0] < 16,
                tier=lambda site: site[1] == "cold",
            )
            .bind(
                View,
                "hot_high",
                MarketShape,
                shard=lambda site: site[0] >= 16,
                tier=lambda site: site[1] == "hot",
            )
            .bind(
                View,
                "cold_high",
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

        ctx = Context().bind(View, "val", MarketShape, pred=capture)
        ctx.get(View, MarketShape, site=(1, 2), path="abc")
        assert received == {"site": (1, 2), "path": "abc"}


# =============================================================================
# get() method
# =============================================================================


class TestGet:
    """Explicit get() for lookups."""

    def test_get_basic(self):
        ctx = Context().bind(Storage, "val")
        assert ctx.get(Storage) == "val"

    def test_get_scoped(self):
        ctx = Context().bind(Storage, "val", MarketShape)
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
        ctx = Context().bind(Storage, "val", MarketShape)
        assert ctx.has(Storage, MarketShape)

    def test_has_false(self):
        ctx = Context().bind(Storage, "val")
        assert not ctx.has(Navigator)

    def test_has_fallback(self):
        ctx = Context().bind(Storage, "val")
        assert ctx.has(Storage, MarketShape)  # fallback resolves

    def test_was_opened_false_before_access(self):
        ctx = Context().lazy(Storage, lambda: "v")
        assert not ctx.was_opened(Storage)

    def test_was_opened_true_after_access(self):
        ctx = Context().lazy(Storage, lambda: "v")
        ctx.get(Storage)
        assert ctx.was_opened(Storage)

    def test_was_opened_false_for_eager(self):
        ctx = Context().bind(Storage, "v")
        assert not ctx.was_opened(Storage)


# =============================================================================
# __repr__
# =============================================================================


class TestRepr:
    def test_repr_empty(self):
        assert repr(Context()) == "Context()"

    def test_repr_binding(self):
        ctx = Context().bind(Storage, "v")
        r = repr(ctx)
        assert "Context(" in r
        assert "Storage" in r

    def test_repr_lazy(self):
        ctx = Context().lazy(Storage, lambda: "v")
        r = repr(ctx)
        assert "lazy" in r


# =============================================================================
# Edge cases
# =============================================================================


class TestEdgeCases:
    def test_multiple_service_types(self):
        ctx = Context().bind(Navigator, "nav").bind(View, "view").bind(Storage, "store")
        assert ctx.get(Navigator) == "nav"
        assert ctx.get(View) == "view"
        assert ctx.get(Storage) == "store"

    def test_predicate_entries_independent(self):
        """Two different service types with predicates don't interfere."""
        ctx = (
            Context()
            .bind(View, "view_low", MarketShape, sharding=lambda site: site[0] < 16)
            .bind(Storage, "store_low", MarketShape, sharding=lambda site: site[0] < 100)
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
# E2E: Attributes through AttrRef
# =============================================================================


class TestAttributesE2EPrimRef:
    """AttrRef reads and writes through ctx.attrs."""

    async def test_prim_ref_reads_from_attrs(self):
        from nu import AttrRef

        ctx = Context()
        ctx.attrs["greeting"] = "hello"
        ref = AttrRef("greeting")
        result = await ref.fetch(ctx)
        assert result == "hello"

    async def test_prim_ref_exists(self):
        from nu import AttrRef

        ctx = Context()
        ref = AttrRef("maybe")
        assert await ref.exists().execute(ctx) is False
        ctx.attrs["maybe"] = "yes"
        assert await ref.exists().execute(ctx) is True


# =============================================================================
# E2E: Context through Refs
# =============================================================================


class TestContextE2EDict:
    """Context flowing through eb-dict refs (store/execute via ctx.get(dict, scope))."""

    @pytest.fixture
    def shapes(self):
        from nu_dict import IntRef, StrRef
        from nu.shapes import Shape

        class User(Shape):
            name = StrRef.slot()
            age = IntRef.slot()

        return User

    async def test_ref_store_and_read(self, shapes):
        """Ref.store() writes to ctx-bound dict, ref.execute() reads back."""
        User = shapes
        data = {}
        ctx = Context().bind(dict, data, User)

        await User.name.store("alice").execute(ctx)
        result = await User.name.execute(ctx)
        assert result == "alice"

    async def test_ref_scoped_isolation(self, shapes):
        """Different shapes get different dicts via context scoping."""
        from nu_dict import StrRef
        from nu.shapes import Shape

        User = shapes

        class Product(Shape):
            name = StrRef.slot()

        user_data, product_data = {}, {}
        ctx = Context().bind(dict, user_data, User).bind(dict, product_data, Product)

        await User.name.store("alice").execute(ctx)
        await Product.name.store("widget").execute(ctx)

        assert await User.name.execute(ctx) == "alice"
        assert await Product.name.execute(ctx) == "widget"
        assert user_data != product_data

    async def test_ref_fallback_to_unscoped(self, shapes):
        """Ref resolves unscoped dict binding when no shape-specific one exists."""
        User = shapes
        data = {}
        ctx = Context().bind(dict, data)  # no scope

        await User.name.store("bob").execute(ctx)
        assert await User.name.execute(ctx) == "bob"


# =============================================================================
# E2E: Context through Flows
# =============================================================================


class TestContextE2EFlows:
    """Context flowing through flow execution."""

    async def test_seq_shares_context(self):
        """Seq children share the same context."""
        from nu_dict import IntRef
        from nu import Seq
        from nu.shapes import Shape

        class Counter(Shape):
            val = IntRef.slot()

        data = {}
        ctx = Context().bind(dict, data, Counter)

        tree = Seq(
            Counter.val.store(0),
            Counter.val.store(Counter.val + 1),
            Counter.val.store(Counter.val + 1),
        )
        await tree.execute(ctx)
        assert await Counter.val.execute(ctx) == 2

    async def test_for_range_with_context(self):
        """ForRange iterates within context-bound storage."""
        from nu_dict import IntRef
        from nu import ForRange, Seq
        from nu.shapes import Shape

        class Acc(Shape):
            total = IntRef.slot()

        data = {}
        ctx = Context().bind(dict, data, Acc)

        tree = Seq(
            Acc.total.store(0),
            ForRange(0, 5, Acc.total.store(Acc.total + 1), index="i"),
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
        from nu import Nu
        from nu import TryCatch

        class FailTerm(Nu):
            def __init__(self):
                super().__init__()

            @property
            def is_self_pure(self):
                return False

            async def execute(self, ctx):
                raise RuntimeError("boom")

        captured = {}

        class CaptureTerm(Nu):
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
        from nu import Nu
        from nu import Retry

        attempts = []
        call_count = 0

        class FlakeyTerm(Nu):
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

        class CaptureAttempt(Nu):
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
        from nu import Context, Span, Nu

        class InjectSpan(Span):
            def __init__(self, *children, key, value):
                super().__init__(*children)
                self._key = key
                self._value = value

            def enter(self, ctx):
                return ctx.bind(self._key, self._value)

        captured = {}

        class ReadTerm(Nu):
            def __init__(self, key):
                super().__init__()
                self._key = key

            @property
            def is_self_pure(self):
                return True

            async def execute(self, ctx):
                captured["val"] = ctx.get(self._key)

        tree = InjectSpan(ReadTerm("config"), key="config", value="production")
        await tree.execute(Context())
        assert captured["val"] == "production"

    async def test_span_lazy_binding_deferred(self):
        """Lazy bindings in span are not materialized until accessed."""
        from nu import Context, Span, Nu

        calls = []

        class LazySpan(Span):
            def __init__(self, *children):
                super().__init__(*children)

            def enter(self, ctx):
                return ctx.lazy("resource", lambda: (calls.append(1), "expensive")[1])

        class NoOpTerm(Nu):
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
        from nu import Context, Span, Nu

        class OverrideSpan(Span):
            def __init__(self, *children):
                super().__init__(*children)

            def enter(self, ctx):
                return ctx.bind("val", "overridden")

        parent_ctx = Context().bind("val", "original")

        class CheckTerm(Nu):
            def __init__(self):
                super().__init__()

            @property
            def is_self_pure(self):
                return True

            async def execute(self, ctx):
                assert ctx.get("val") == "overridden"

        tree = OverrideSpan(CheckTerm())
        await tree.execute(parent_ctx)
        assert parent_ctx.get("val") == "original"
