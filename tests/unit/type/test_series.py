"""Unit tests for Series type.

Tests for:
- Point native Python class (construction, data access)
- Series native Python class (access, calculations, mutations)
- PointType and SeriesTypes
"""

import pytest

from everybase.type.series import Point, PointType, Series, SeriesType
from everyterm.ops import FuncCallOp, LenOp
from everyterm.types import FloatType, IntType


# =============================================================================
# POINT NATIVE CLASS TESTS
# =============================================================================


class TestPointConstruction:
    """Point construction tests."""

    def test_basic_construction(self):
        """Create Point with value only."""
        p = Point(100.0)
        assert p.value == 100.0
        assert p.timestamp == 0
        assert p.data == {}

    def test_with_timestamp(self):
        """Create Point with timestamp."""
        p = Point(100.0, timestamp=1234567890)
        assert p.value == 100.0
        assert p.timestamp == 1234567890

    def test_with_data(self):
        """Create Point with extra data."""
        p = Point(100.0, data={"volume": 1000})
        assert p.data == {"volume": 1000}

    def test_frozen_immutable(self):
        """Point is immutable (frozen dataclass)."""
        p = Point(100.0)
        with pytest.raises(AttributeError):
            p.value = 200.0  # type: ignore


class TestPointDataAccess:
    """Point data access tests."""

    def test_get_existing_key(self):
        """Get existing data field."""
        p = Point(100.0, data={"volume": 1000})
        assert p.get("volume") == 1000

    def test_get_missing_key(self):
        """Get missing data field returns default."""
        p = Point(100.0)
        assert p.get("volume") == 0.0

    def test_get_custom_default(self):
        """Get missing data field with custom default."""
        p = Point(100.0)
        assert p.get("volume", -1.0) == -1.0

    def test_with_data_method(self):
        """Create new Point with additional data."""
        p = Point(100.0, data={"a": 1})
        p2 = p.with_data(b=2)
        assert p2.data == {"a": 1, "b": 2}
        assert p.data == {"a": 1}  # Original unchanged


class TestPointSerialization:
    """Point serialization tests."""

    def test_to_dict(self):
        """Convert to dictionary."""
        p = Point(100.0, timestamp=123, data={"vol": 500})
        d = p.to_dict()
        assert d == {"value": 100.0, "timestamp": 123, "vol": 500}

    def test_from_dict(self):
        """Create from dictionary."""
        d = {"value": 100.0, "timestamp": 123, "vol": 500}
        p = Point.from_dict(d)
        assert p.value == 100.0
        assert p.timestamp == 123
        assert p.data == {"vol": 500}

    def test_str(self):
        """String representation."""
        p = Point(100.0, timestamp=123)
        assert str(p) == "Point(100.0, t=123)"


# =============================================================================
# SERIES NATIVE CLASS TESTS
# =============================================================================


class TestSeriesConstruction:
    """Series construction tests."""

    def test_empty_construction(self):
        """Create empty Series."""
        s = Series()
        assert len(s) == 0

    def test_with_points(self):
        """Create Series with points."""
        s = Series(points=[Point(100.0), Point(110.0)])
        assert len(s) == 2


class TestSeriesAccess:
    """Series access tests."""

    def test_len(self):
        """Length of series."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        assert len(s) == 3

    def test_iter(self):
        """Iterate over points."""
        pts = [Point(100.0), Point(110.0)]
        s = Series(points=pts)
        assert list(s) == pts

    def test_getitem(self):
        """Get point by index."""
        s = Series(points=[Point(100.0), Point(110.0)])
        assert s[0].value == 100.0
        assert s[1].value == 110.0

    def test_latest(self):
        """Get most recent point."""
        s = Series(points=[Point(100.0), Point(110.0)])
        assert s.latest().value == 110.0

    def test_latest_empty(self):
        """Get latest from empty series."""
        s = Series()
        assert s.latest().value == 0.0

    def test_first(self):
        """Get first point."""
        s = Series(points=[Point(100.0), Point(110.0)])
        assert s.first().value == 100.0

    def test_first_empty(self):
        """Get first from empty series."""
        s = Series()
        assert s.first().value == 0.0

    def test_at(self):
        """Get point at index."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        assert s.at(1).value == 110.0
        assert s.at(-1).value == 120.0

    def test_at_out_of_bounds(self):
        """Get point at out of bounds index."""
        s = Series(points=[Point(100.0)])
        assert s.at(10).value == 0.0

    def test_values(self):
        """Get all values."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        assert s.values() == [100.0, 110.0, 120.0]

    def test_values_last_n(self):
        """Get last n values."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        assert s.values(2) == [110.0, 120.0]


class TestSeriesMutation:
    """Series mutation tests."""

    def test_append_point(self):
        """Append Point to series."""
        s = Series(points=[Point(100.0)])
        s2 = s.append(Point(110.0))
        assert len(s2) == 2
        assert len(s) == 1  # Original unchanged

    def test_append_float(self):
        """Append float to series."""
        s = Series(points=[Point(100.0)])
        s2 = s.append(110.0)
        assert len(s2) == 2
        assert s2.latest().value == 110.0

    def test_slice(self):
        """Get slice of series."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        s2 = s.slice(1, 3)
        assert len(s2) == 2
        assert s2.first().value == 110.0

    def test_tail(self):
        """Get last n points."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        s2 = s.tail(2)
        assert len(s2) == 2
        assert s2.first().value == 110.0


class TestSeriesMovingAverages:
    """Series moving average tests."""

    def test_sma(self):
        """Simple Moving Average."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        assert s.sma(3) == 110.0

    def test_sma_partial(self):
        """SMA with fewer points than period."""
        s = Series(points=[Point(100.0), Point(110.0)])
        assert s.sma(5) == 105.0

    def test_sma_empty(self):
        """SMA of empty series."""
        s = Series()
        assert s.sma(3) == 0.0

    def test_ema(self):
        """Exponential Moving Average."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        result = s.ema(3)
        assert isinstance(result, float)

    def test_wma(self):
        """Weighted Moving Average."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        result = s.wma(3)
        # WMA = (100*1 + 110*2 + 120*3) / (1+2+3) = 680/6 = 113.33...
        assert abs(result - 113.333) < 0.01


class TestSeriesStatistics:
    """Series statistics tests."""

    def test_min(self):
        """Minimum value."""
        s = Series(points=[Point(110.0), Point(100.0), Point(120.0)])
        assert s.min() == 100.0

    def test_min_period(self):
        """Minimum with period."""
        s = Series(points=[Point(90.0), Point(110.0), Point(100.0), Point(120.0)])
        assert s.min(2) == 100.0

    def test_max(self):
        """Maximum value."""
        s = Series(points=[Point(110.0), Point(100.0), Point(120.0)])
        assert s.max() == 120.0

    def test_avg(self):
        """Average value."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        assert s.avg() == 110.0

    def test_sum(self):
        """Sum of values."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        assert s.sum() == 330.0

    def test_std(self):
        """Standard deviation."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        result = s.std()
        assert isinstance(result, float)
        assert result > 0


class TestSeriesRateOfChange:
    """Series rate of change tests."""

    def test_change(self):
        """Absolute change."""
        s = Series(points=[Point(100.0), Point(150.0)])
        assert s.change() == 50.0

    def test_change_pct(self):
        """Percentage change."""
        s = Series(points=[Point(100.0), Point(150.0)])
        assert s.change_pct() == 50.0

    def test_roc(self):
        """Rate of change over period."""
        s = Series(points=[Point(100.0), Point(110.0), Point(120.0)])
        # ROC(1) = (120 - 110) / 110 * 100
        result = s.roc(1)
        assert abs(result - 9.09) < 0.1


class TestSeriesIndicators:
    """Series indicator tests."""

    def test_rsi(self):
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
        result = s.rsi(14)
        assert 0 <= result <= 100

    def test_bollinger(self):
        """Bollinger Bands."""
        s = Series(points=[Point(float(v)) for v in range(100, 121)])
        lower, middle, upper = s.bollinger(20, 2.0)
        assert lower < middle < upper


class TestSeriesSerialization:
    """Series serialization tests."""

    def test_to_list(self):
        """Convert to list of dicts."""
        s = Series(points=[Point(100.0), Point(110.0)])
        result = s.to_list()
        assert len(result) == 2
        assert result[0]["value"] == 100.0

    def test_from_list(self):
        """Create from list of dicts."""
        data = [{"value": 100.0}, {"value": 110.0}]
        s = Series.from_list(data)
        assert len(s) == 2
        assert s.first().value == 100.0

    def test_str(self):
        """String representation."""
        s = Series(points=[Point(100.0), Point(110.0)])
        assert str(s) == "Series(2 points)"


# =============================================================================
# POINTTYPE TESTS
# =============================================================================


class TestPointTypeConstruction:
    """PointType construction tests."""

    def test_create(self):
        """Create PointType."""
        pt = PointType.create(100.0, timestamp=123)
        assert isinstance(pt, PointType)


class TestPointTypeAccessors:
    """PointType accessor tests."""

    def test_value_returns_floattype(self):
        """value() returns FloatType."""
        pt = PointType.create(100.0)
        result = pt.value()
        assert isinstance(result, FloatType)

    def test_timestamp_returns_inttype(self):
        """timestamp() returns IntType."""
        pt = PointType.create(100.0, timestamp=123)
        result = pt.timestamp()
        assert isinstance(result, IntType)

    def test_get_returns_floattype(self):
        """get() returns FloatType."""
        pt = PointType.create(100.0)
        result = pt.get("volume", 0.0)
        assert isinstance(result, FloatType)


# =============================================================================
# SERIESTYPE TESTS
# =============================================================================


class TestSeriesTypeConstruction:
    """SeriesType construction tests."""

    def test_empty(self):
        """Create empty SeriesType."""
        st = SeriesType.empty()
        assert isinstance(st, SeriesType)
        assert isinstance(st.source, FuncCallOp)


class TestSeriesTypeAccess:
    """SeriesType access method tests."""

    def test_length_returns_inttype(self):
        """length() returns IntType."""
        st = SeriesType.empty()
        result = st.length()
        assert isinstance(result, IntType)
        assert isinstance(result.source, LenOp)

    def test_latest_returns_pointtype(self):
        """latest() returns PointType."""
        st = SeriesType.empty()
        result = st.latest()
        assert isinstance(result, PointType)

    def test_first_returns_pointtype(self):
        """first() returns PointType."""
        st = SeriesType.empty()
        result = st.first()
        assert isinstance(result, PointType)

    def test_at_returns_pointtype(self):
        """at() returns PointType."""
        st = SeriesType.empty()
        result = st.at(0)
        assert isinstance(result, PointType)


class TestSeriesTypeMovingAverages:
    """SeriesType moving average method tests."""

    def test_sma_returns_floattype(self):
        """sma() returns FloatType."""
        st = SeriesType.empty()
        result = st.sma(20)
        assert isinstance(result, FloatType)

    def test_ema_returns_floattype(self):
        """ema() returns FloatType."""
        st = SeriesType.empty()
        result = st.ema(12)
        assert isinstance(result, FloatType)

    def test_wma_returns_floattype(self):
        """wma() returns FloatType."""
        st = SeriesType.empty()
        result = st.wma(10)
        assert isinstance(result, FloatType)


class TestSeriesTypeStatistics:
    """SeriesType statistics method tests."""

    def test_min_returns_floattype(self):
        """min() returns FloatType."""
        st = SeriesType.empty()
        result = st.min()
        assert isinstance(result, FloatType)

    def test_max_returns_floattype(self):
        """max() returns FloatType."""
        st = SeriesType.empty()
        result = st.max()
        assert isinstance(result, FloatType)

    def test_avg_returns_floattype(self):
        """avg() returns FloatType."""
        st = SeriesType.empty()
        result = st.avg()
        assert isinstance(result, FloatType)

    def test_sum_returns_floattype(self):
        """sum() returns FloatType."""
        st = SeriesType.empty()
        result = st.sum()
        assert isinstance(result, FloatType)

    def test_std_returns_floattype(self):
        """std() returns FloatType."""
        st = SeriesType.empty()
        result = st.std()
        assert isinstance(result, FloatType)


class TestSeriesTypeRateOfChange:
    """SeriesType rate of change method tests."""

    def test_change_returns_floattype(self):
        """change() returns FloatType."""
        st = SeriesType.empty()
        result = st.change()
        assert isinstance(result, FloatType)

    def test_change_pct_returns_floattype(self):
        """change_pct() returns FloatType."""
        st = SeriesType.empty()
        result = st.change_pct()
        assert isinstance(result, FloatType)

    def test_roc_returns_floattype(self):
        """roc() returns FloatType."""
        st = SeriesType.empty()
        result = st.roc(1)
        assert isinstance(result, FloatType)


class TestSeriesTypeIndicators:
    """SeriesType indicator method tests."""

    def test_rsi_returns_floattype(self):
        """rsi() returns FloatType."""
        st = SeriesType.empty()
        result = st.rsi(14)
        assert isinstance(result, FloatType)


class TestSeriesTypeMutation:
    """SeriesType mutation method tests."""

    def test_append_returns_seriestype(self):
        """append() returns SeriesType."""
        st = SeriesType.empty()
        result = st.append(100.0)
        assert isinstance(result, SeriesType)

    def test_tail_returns_seriestype(self):
        """tail() returns SeriesType."""
        st = SeriesType.empty()
        result = st.tail(10)
        assert isinstance(result, SeriesType)
