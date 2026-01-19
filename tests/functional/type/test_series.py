"""Functional tests for Series type.

Tests SeriesType, PointType, and SeriesSlot execution with real storage context.
"""

from everybase.type import Point, Series, SeriesType


# ============================================================================
# SERIES SET AND GET TESTS
# ============================================================================


class TestSeriesSetAndGet:
    """Test setting and getting series values through storage."""

    def test_set_and_get_series(self, series_shape, ctx):
        """Set and retrieve a series value."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.get().execute(ctx)
        assert len(result) == 3
        assert result.first().value == 100.0
        assert result.latest().value == 120.0

    def test_set_empty_series(self, series_shape, ctx):
        """Set empty series."""
        s = Series()
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.get().execute(ctx)
        assert len(result) == 0

    def test_set_multiple_series(self, series_shape, ctx):
        """Set multiple series slots."""
        prices = Series(points=[Point(100.0), Point(110.0)])
        volumes = Series(points=[Point(1000.0), Point(1200.0)])

        series_shape.prices.set(prices).execute(ctx)
        series_shape.volumes.set(volumes).execute(ctx)

        assert len(series_shape.prices.get().execute(ctx)) == 2
        assert len(series_shape.volumes.get().execute(ctx)) == 2


# ============================================================================
# SERIESTYPE CONSTRUCTOR TESTS
# ============================================================================


class TestSeriesTypeConstructors:
    """Test SeriesType constructors with execution."""

    def test_empty(self, ctx):
        """Create empty series."""
        result = SeriesType.empty().execute(ctx)
        assert len(result) == 0


# ============================================================================
# SERIES ACCESS TESTS
# ============================================================================


class TestSeriesAccess:
    """Test series access operations."""

    def test_length(self, series_shape, ctx):
        """Get series length."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.length().execute(ctx)
        assert result == 3

    def test_latest(self, series_shape, ctx):
        """Get latest point."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.latest().execute(ctx)
        assert result.value == 120.0

    def test_first(self, series_shape, ctx):
        """Get first point."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.first().execute(ctx)
        assert result.value == 100.0

    def test_at(self, series_shape, ctx):
        """Get point at index."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.at(1).execute(ctx)
        assert result.value == 110.0

    def test_at_negative(self, series_shape, ctx):
        """Get point at negative index."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.at(-1).execute(ctx)
        assert result.value == 120.0


# ============================================================================
# SERIES MOVING AVERAGE TESTS
# ============================================================================


class TestSeriesMovingAverages:
    """Test series moving average operations."""

    def test_sma(self, series_shape, ctx):
        """Simple Moving Average."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.sma(3).execute(ctx)
        assert result == 110.0

    def test_sma_partial_period(self, series_shape, ctx):
        """SMA with fewer points than period."""
        s = Series(points=[Point(100.0), Point(110.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.sma(5).execute(ctx)
        assert result == 105.0

    def test_ema(self, series_shape, ctx):
        """Exponential Moving Average."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.ema(3).execute(ctx)
        assert isinstance(result, float)

    def test_wma(self, series_shape, ctx):
        """Weighted Moving Average."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.wma(3).execute(ctx)
        # WMA = (100*1 + 110*2 + 120*3) / (1+2+3) = 680/6 = 113.33...
        assert abs(result - 113.333) < 0.01


# ============================================================================
# SERIES STATISTICS TESTS
# ============================================================================


class TestSeriesStatistics:
    """Test series statistics operations."""

    def test_min(self, series_shape, ctx):
        """Minimum value."""
        s = Series(points=[Point(110.0), Point(100.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.min().execute(ctx)
        assert result == 100.0

    def test_min_with_period(self, series_shape, ctx):
        """Minimum with period."""
        s = Series(points=[Point(90.0), Point(110.0), Point(100.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.min(2).execute(ctx)
        assert result == 100.0

    def test_max(self, series_shape, ctx):
        """Maximum value."""
        s = Series(points=[Point(110.0), Point(100.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.max().execute(ctx)
        assert result == 120.0

    def test_avg(self, series_shape, ctx):
        """Average value."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.avg().execute(ctx)
        assert result == 110.0

    def test_sum(self, series_shape, ctx):
        """Sum of values."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.sum().execute(ctx)
        assert result == 330.0

    def test_std(self, series_shape, ctx):
        """Standard deviation."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.std().execute(ctx)
        assert isinstance(result, float)
        assert result > 0


# ============================================================================
# SERIES RATE OF CHANGE TESTS
# ============================================================================


class TestSeriesRateOfChange:
    """Test series rate of change operations."""

    def test_change(self, series_shape, ctx):
        """Absolute change."""
        s = Series(points=[Point(100.0), Point(150.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.change().execute(ctx)
        assert result == 50.0

    def test_change_pct(self, series_shape, ctx):
        """Percentage change."""
        s = Series(points=[Point(100.0), Point(150.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.change_pct().execute(ctx)
        assert result == 50.0

    def test_roc(self, series_shape, ctx):
        """Rate of change over period."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.roc(1).execute(ctx)
        # ROC(1) = (120 - 110) / 110 * 100
        assert abs(result - 9.09) < 0.1


# ============================================================================
# SERIES INDICATOR TESTS
# ============================================================================


class TestSeriesIndicators:
    """Test series indicator operations."""

    def test_rsi(self, series_shape, ctx):
        """Relative Strength Index."""
        # Create series with gains and losses
        points = [
            Point(float(v))
            for v in [
                44,
                44.5,
                43.5,
                44.5,
                44,
                43.5,
                44,
                44.5,
                45,
                45.5,
                46,
                45.5,
                46,
                45.5,
                46,
                46.5,
            ]
        ]
        s = Series(points=points)
        series_shape.prices.set(s).execute(ctx)
        result = series_shape.prices.rsi(14).execute(ctx)
        assert 0 <= result <= 100


# ============================================================================
# SERIES MUTATION TESTS
# ============================================================================


class TestSeriesMutation:
    """Test series mutation operations."""

    def test_append_float(self, series_shape, ctx):
        """Append float to series."""
        s = Series(points=[Point(100.0)])
        series_shape.prices.set(s).execute(ctx)

        result = series_shape.prices.append(110.0).execute(ctx)
        assert len(result) == 2
        assert result.latest().value == 110.0

    def test_tail(self, series_shape, ctx):
        """Get last n points."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        series_shape.prices.set(s).execute(ctx)

        result = series_shape.prices.tail(2).execute(ctx)
        assert len(result) == 2
        assert result.first().value == 110.0


# ============================================================================
# POINTTYPE TESTS
# ============================================================================


class TestPointTypeAccess:
    """Test PointType access operations."""

    def test_point_value(self, series_shape, ctx):
        """Get point value."""
        s = Series(points=[Point(100.0, timestamp=123)])
        series_shape.prices.set(s).execute(ctx)

        point = series_shape.prices.latest()
        result = point.value().execute(ctx)
        assert result == 100.0

    def test_point_timestamp(self, series_shape, ctx):
        """Get point timestamp."""
        s = Series(points=[Point(100.0, timestamp=123)])
        series_shape.prices.set(s).execute(ctx)

        point = series_shape.prices.latest()
        result = point.timestamp().execute(ctx)
        assert result == 123


# ============================================================================
# SERIES USE CASE TESTS
# ============================================================================


class TestSeriesUseCases:
    """Test real-world series use cases."""

    def test_price_analysis(self, series_shape, ctx):
        """Analyze stock prices."""
        prices = Series(
            points=[
                Point(100.0),
                Point(102.0),
                Point(98.0),
                Point(105.0),
                Point(110.0),
            ]
        )
        series_shape.prices.set(prices).execute(ctx)

        # Calculate basic metrics
        latest = series_shape.prices.latest().execute(ctx)
        assert latest.value == 110.0

        high = series_shape.prices.max().execute(ctx)
        assert high == 110.0

        low = series_shape.prices.min().execute(ctx)
        assert low == 98.0

        avg = series_shape.prices.avg().execute(ctx)
        assert avg == 103.0

    def test_moving_average_crossover(self, series_shape, ctx):
        """Track moving average crossover."""
        # Create trending series
        prices = Series(points=[Point(float(100 + i * 2)) for i in range(20)])
        series_shape.prices.set(prices).execute(ctx)

        # Short and long moving averages
        short_ma = series_shape.prices.sma(5).execute(ctx)
        long_ma = series_shape.prices.sma(10).execute(ctx)

        # In an uptrend, short MA should be above long MA
        assert short_ma > long_ma

    def test_volatility_check(self, series_shape, ctx):
        """Check price volatility."""
        # Create volatile series
        prices = Series(
            points=[
                Point(100.0),
                Point(120.0),
                Point(90.0),
                Point(130.0),
                Point(85.0),
            ]
        )
        series_shape.prices.set(prices).execute(ctx)

        std = series_shape.prices.std().execute(ctx)
        avg = series_shape.prices.avg().execute(ctx)

        # Coefficient of variation
        cv = std / avg if avg != 0 else 0
        assert cv > 0.1  # High volatility
