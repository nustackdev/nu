"""Playground: Test Domain Types (Two-Class Pattern).

Validates:
- DomainTypeExpr creation and evaluation
- MethodCallValue creation and evaluation
- EMA and RSI domain types
- Composition with regular expressions
- Two-class pattern separation
"""

from redwood.codec import TextCodecSpec
from redwood.dsl import PrimitiveField, PrimitivePath, Schema
from redwood.dsl.term import PathTerm, ValueTerm
from redwood.dsl.values import DomainTypeExpr, MethodCallValue, PathValue
from redwood.observer.in_memory_observer import InMemoryObserver, InMemoryObserverSpec
from redwood.storage.file_storage import FileStorage, FileStorageSpec
from redwood.tree.backend import ObservableStorage
from redwood.tree.registry import ViewRegistry
from redwood.tree.tree import Tree
from redwood.tree.view import DictView


# ============================================================================
# EMA (Exponential Moving Average)
# ============================================================================


class EMAExpr:
    """Expression builder for EMA - used during query construction.

    All methods return expressions (lazy), never actual values.
    This is the "building" side of the two-class pattern.

    Example:
        ema = EMAExpr(Market.price, window=20)
        is_trending = ema.is_trending_up()  # Returns expression, not bool!
        result = is_trending.evaluate(tree, ctx)  # Now executes
    """

    def __init__(self, source: PathTerm | ValueTerm, window: int = 20) -> None:
        """Initialize EMA expression.

        Args:
            source: Source path or value term (e.g., Market.price)
            window: EMA window size (default: 20)
        """
        self.window = window

        # Convert source to ValueTerm if it's a PathTerm
        if isinstance(source, PathTerm):
            source_expr = PathValue(source)
        elif isinstance(source, ValueTerm):
            source_expr = source
        else:
            raise TypeError(f"EMAExpr source must be PathTerm or ValueTerm, got {type(source)}")

        # Store as DomainTypeExpr - links to implementation
        self._expr = DomainTypeExpr(
            expr_class=EMAExpr,
            impl_class=EMA,
            inner=source_expr,
            init_kwargs={"window": window},
        )

    def is_trending_up(self) -> ValueTerm:
        """Check if EMA is trending upward - returns expression.

        Returns:
            ValueTerm that evaluates to bool
        """
        return MethodCallValue(
            domain_expr=self._expr,
            method_name="is_trending_up",
            method=EMA.is_trending_up,
        )

    def cross_over(self, other: "EMAExpr") -> ValueTerm:
        """Check if this EMA crossed over another - returns expression.

        Args:
            other: Another EMAExpr to compare against

        Returns:
            ValueTerm that evaluates to bool
        """
        if not isinstance(other, EMAExpr):
            raise TypeError(f"cross_over requires EMAExpr, got {type(other)}")

        return MethodCallValue(
            domain_expr=self._expr,
            method_name="cross_over",
            method=EMA.cross_over,
            arg_exprs={"other": other._expr},
        )


class EMA:
    """Implementation of EMA calculations - used during evaluation.

    All methods work with actual values and return actual results.
    This is the "execution" side of the two-class pattern.

    Never instantiated directly - created by DomainTypeExpr during evaluation.
    """

    def __init__(self, value: float, window: int = 20) -> None:
        """Initialize EMA with value.

        Args:
            value: Current EMA value
            window: EMA window size

        Raises:
            ValueError: If value is None or invalid
        """
        if value is None:
            raise ValueError("EMA received None value - check if path exists in tree")

        self.value = float(value)
        self.window = window

    def is_trending_up(self) -> bool:
        """Check if EMA is trending upward - returns actual bool.

        Simple heuristic: value is above 98% of itself (momentum check).

        Returns:
            True if trending up
        """
        threshold = self.value * 0.98
        return self.value > threshold

    def cross_over(self, other: "EMA") -> bool:
        """Check if this EMA crossed over another - returns actual bool.

        Args:
            other: Another EMA instance

        Returns:
            True if this EMA is above the other
        """
        return self.value > other.value


# ============================================================================
# RSI (Relative Strength Index)
# ============================================================================


class RSIExpr:
    """Expression builder for RSI - used during query construction.

    All methods return expressions (lazy), never actual values.

    Example:
        rsi = RSIExpr(Market.rsi_value, period=14)
        is_oversold = rsi.is_oversold(threshold=30)  # Expression!
        result = is_oversold.evaluate(tree, ctx)  # Executes
    """

    def __init__(self, source: PathTerm | ValueTerm, period: int = 14) -> None:
        """Initialize RSI expression.

        Args:
            source: Source path or value term (e.g., Market.rsi_value)
            period: RSI period (default: 14)
        """
        self.period = period

        # Convert source to ValueTerm if it's a PathTerm
        if isinstance(source, PathTerm):
            source_expr = PathValue(source)
        elif isinstance(source, ValueTerm):
            source_expr = source
        else:
            raise TypeError(f"RSIExpr source must be PathTerm or ValueTerm, got {type(source)}")

        # Store as DomainTypeExpr
        self._expr = DomainTypeExpr(
            expr_class=RSIExpr,
            impl_class=RSI,
            inner=source_expr,
            init_kwargs={"period": period},
        )

    def is_overbought(self, threshold: float = 70.0) -> ValueTerm:
        """Check if RSI is overbought - returns expression.

        Args:
            threshold: Overbought threshold (default: 70)

        Returns:
            ValueTerm that evaluates to bool
        """
        return MethodCallValue(
            domain_expr=self._expr,
            method_name="is_overbought",
            method=RSI.is_overbought,
            kwargs={"threshold": threshold},
        )

    def is_oversold(self, threshold: float = 30.0) -> ValueTerm:
        """Check if RSI is oversold - returns expression.

        Args:
            threshold: Oversold threshold (default: 30)

        Returns:
            ValueTerm that evaluates to bool
        """
        return MethodCallValue(
            domain_expr=self._expr,
            method_name="is_oversold",
            method=RSI.is_oversold,
            kwargs={"threshold": threshold},
        )


class RSI:
    """Implementation of RSI calculations - used during evaluation.

    All methods work with actual values and return actual results.

    Never instantiated directly - created by DomainTypeExpr during evaluation.
    """

    def __init__(self, value: float, period: int = 14) -> None:
        """Initialize RSI with value.

        Args:
            value: Current RSI value (0-100)
            period: RSI period

        Raises:
            ValueError: If value is None or invalid
        """
        if value is None:
            raise ValueError("RSI received None value - check if path exists in tree")

        self.value = float(value)
        self.period = period

    def is_overbought(self, threshold: float = 70.0) -> bool:
        """Check if RSI is overbought - returns actual bool.

        Args:
            threshold: Overbought threshold

        Returns:
            True if RSI is above threshold
        """
        return self.value > threshold

    def is_oversold(self, threshold: float = 30.0) -> bool:
        """Check if RSI is oversold - returns actual bool.

        Args:
            threshold: Oversold threshold

        Returns:
            True if RSI is below threshold
        """
        return self.value < threshold


def test_domain_type_creation() -> None:
    """Test creating domain type expressions."""
    print("=" * 70)
    print("TEST: Domain Type Creation")
    print("=" * 70)

    class Market(Schema):
        price: PrimitivePath[float] = PrimitiveField(float)

    # Create EMA expression
    ema = EMAExpr(Market.price, window=20)
    assert hasattr(ema, "_expr")
    assert isinstance(ema._expr, DomainTypeExpr)
    print("✓ EMAExpr created with DomainTypeExpr")

    # Create RSI expression
    rsi = RSIExpr(Market.price, period=14)
    assert hasattr(rsi, "_expr")
    assert isinstance(rsi._expr, DomainTypeExpr)
    print("✓ RSIExpr created with DomainTypeExpr")

    print()


def test_method_calls() -> None:
    """Test method call expressions."""
    print("=" * 70)
    print("TEST: Method Calls")
    print("=" * 70)

    class Market(Schema):
        price: PrimitivePath[float] = PrimitiveField(float)

    ema = EMAExpr(Market.price, window=20)

    # Method call returns MethodCallValue
    is_trending = ema.is_trending_up()
    assert isinstance(is_trending, MethodCallValue)
    assert is_trending.meta.is_pure is True
    print("✓ Method call returns MethodCallValue")

    print()


def test_ema_evaluation() -> None:
    """Test EMA evaluation with real tree."""
    print("=" * 70)
    print("TEST: EMA Evaluation")
    print("=" * 70)

    class Market(Schema):
        ema_20: PrimitivePath[float] = PrimitiveField(float)
        ema_50: PrimitivePath[float] = PrimitiveField(float)

    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        FileStorage(FileStorageSpec(codec=TextCodecSpec())) as storage,
    ):
        tree = Tree(
            backend=ObservableStorage(storage=storage, observer=observer),
            registry=ViewRegistry(),
        )

        # Setup data
        with tree.transaction() as ctx:
            root = tree.view(DictView, ctx=ctx)
            root.set("ema_20", 148.5)
            root.set("ema_50", 145.0)

        # Test is_trending_up
        with tree.transaction() as ctx:
            ema = EMAExpr(Market.ema_20, window=20)
            result = ema.is_trending_up().evaluate(tree, ctx)
            assert isinstance(result, bool)
            print(f"✓ EMA.is_trending_up() = {result}")

        # Test cross_over
        with tree.transaction() as ctx:
            ema_20 = EMAExpr(Market.ema_20, window=20)
            ema_50 = EMAExpr(Market.ema_50, window=50)
            result = ema_20.cross_over(ema_50).evaluate(tree, ctx)
            assert isinstance(result, bool)
            assert result is True  # 148.5 > 145.0
            print(f"✓ EMA.cross_over() = {result}")

    print()


def test_rsi_evaluation() -> None:
    """Test RSI evaluation with real tree."""
    print("=" * 70)
    print("TEST: RSI Evaluation")
    print("=" * 70)

    class Market(Schema):
        rsi: PrimitivePath[float] = PrimitiveField(float)

    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        FileStorage(FileStorageSpec(codec=TextCodecSpec())) as storage,
    ):
        tree = Tree(
            backend=ObservableStorage(storage=storage, observer=observer),
            registry=ViewRegistry(),
        )

        # Setup data
        with tree.transaction() as ctx:
            root = tree.view(DictView, ctx=ctx)
            root.set("rsi", 75.0)  # Overbought

        # Test is_overbought
        with tree.transaction() as ctx:
            rsi = RSIExpr(Market.rsi, period=14)
            result = rsi.is_overbought(threshold=70.0).evaluate(tree, ctx)
            assert result is True
            print(f"✓ RSI.is_overbought(70) = {result}")

        # Test is_oversold
        with tree.transaction() as ctx:
            root = tree.view(DictView, ctx=ctx)
            root.set("rsi", 25.0)  # Oversold

            rsi = RSIExpr(Market.rsi, period=14)
            result = rsi.is_oversold(threshold=30.0).evaluate(tree, ctx)
            assert result is True
            print(f"✓ RSI.is_oversold(30) = {result}")

    print()


def test_composition() -> None:
    """Test composing domain types with regular expressions."""
    print("=" * 70)
    print("TEST: Composition")
    print("=" * 70)

    class Market(Schema):
        price: PrimitivePath[float] = PrimitiveField(float)
        ema_20: PrimitivePath[float] = PrimitiveField(float)
        rsi: PrimitivePath[float] = PrimitiveField(float)

    with (
        InMemoryObserver(InMemoryObserverSpec(codec=TextCodecSpec())) as observer,
        FileStorage(FileStorageSpec(codec=TextCodecSpec())) as storage,
    ):
        tree = Tree(
            backend=ObservableStorage(storage=storage, observer=observer),
            registry=ViewRegistry(),
        )

        # Setup data
        with tree.transaction() as ctx:
            root = tree.view(DictView, ctx=ctx)
            root.set("price", 150.0)
            root.set("ema_20", 148.5)
            root.set("rsi", 65.0)

        # Domain + regular expression
        with tree.transaction() as ctx:
            ema = EMAExpr(Market.ema_20, window=20)
            signal = ema.is_trending_up() & (Market.price > 100)
            result = signal.evaluate(tree, ctx)
            assert isinstance(result, bool)
            print(f"✓ EMA.is_trending_up() & (price > 100) = {result}")

        # Multiple domain types
        with tree.transaction() as ctx:
            ema = EMAExpr(Market.ema_20, window=20)
            rsi = RSIExpr(Market.rsi, period=14)
            signal = ema.is_trending_up() & ~rsi.is_overbought(70.0)
            result = signal.evaluate(tree, ctx)
            assert isinstance(result, bool)
            print(f"✓ EMA.is_trending_up() & ~RSI.is_overbought(70) = {result}")

    print()


def main() -> None:
    """Run all domain type tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "DOMAIN TYPES VALIDATION" + " " * 26 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    test_domain_type_creation()
    test_method_calls()
    test_ema_evaluation()
    test_rsi_evaluation()
    test_composition()

    print("=" * 70)
    print("✅ ALL DOMAIN TYPE TESTS PASSED!")
    print("=" * 70)
    print()
    print("Two-Class Pattern Working Perfectly! 🎉")
    print("  Expression Classes: EMAExpr, RSIExpr (building)")
    print("  Implementation Classes: EMA, RSI (execution)")
    print()


if __name__ == "__main__":
    main()
