"""Functional tests for Percentage type.

Tests PercentageType and PercentageSlot execution with real storage context.
"""

from everybase.type import Percentage, PercentageType


# ============================================================================
# PERCENTAGE SET AND GET TESTS
# ============================================================================


class TestPercentageSetAndGet:
    """Test setting and getting percentage values through storage."""

    def test_set_and_get_percentage(self, percentage_shape, ctx):
        """Set and retrieve a percentage value."""
        pct = Percentage(75.5)
        percentage_shape.completion.set(pct).execute(ctx)
        result = percentage_shape.completion.get().execute(ctx)
        assert result.value == pct.value

    def test_set_percentage_from_float(self, percentage_shape, ctx):
        """Set percentage from float."""
        percentage_shape.completion.set(50.0).execute(ctx)
        result = percentage_shape.completion.get().execute(ctx)
        assert result.value == 50.0

    def test_set_multiple_percentages(self, percentage_shape, ctx):
        """Set multiple percentage slots."""
        completion = Percentage(75.0)
        discount = Percentage(10.0)

        percentage_shape.completion.set(completion).execute(ctx)
        percentage_shape.discount.set(discount).execute(ctx)

        assert percentage_shape.completion.get().execute(ctx).value == 75.0
        assert percentage_shape.discount.get().execute(ctx).value == 10.0


# ============================================================================
# PERCENTAGETYPE CONSTRUCTOR TESTS
# ============================================================================


class TestPercentageTypeConstructors:
    """Test PercentageType constructors with execution."""

    def test_from_float(self, ctx):
        """Create from float (percentage value)."""
        result = PercentageType.from_float(75.5).execute(ctx)
        assert result.value == 75.5

    def test_from_dec(self, ctx):
        """Create from decimal (0.0 to 1.0)."""
        result = PercentageType.from_dec(0.755).execute(ctx)
        assert result.value == 75.5

    def test_from_bps(self, ctx):
        """Create from basis points."""
        result = PercentageType.from_bps(7550).execute(ctx)
        assert result.value == 75.5


# ============================================================================
# PERCENTAGE CONVERSION TESTS
# ============================================================================


class TestPercentageConversions:
    """Test percentage conversions."""

    def test_to_dec(self, percentage_shape, ctx):
        """Convert to decimal."""
        percentage_shape.completion.set(Percentage(75.5)).execute(ctx)
        result = percentage_shape.completion.to_dec().execute(ctx)
        assert result == 0.755

    def test_to_bps(self, percentage_shape, ctx):
        """Convert to basis points."""
        percentage_shape.completion.set(Percentage(75.5)).execute(ctx)
        result = percentage_shape.completion.to_bps().execute(ctx)
        assert result == 7550

    def test_to_float(self, percentage_shape, ctx):
        """Get raw percentage value."""
        percentage_shape.completion.set(Percentage(75.5)).execute(ctx)
        result = percentage_shape.completion.to_float().execute(ctx)
        assert result == 75.5


# ============================================================================
# PERCENTAGE APPLICATION TESTS
# ============================================================================


class TestPercentageApplication:
    """Test percentage application operations."""

    def test_apply(self, percentage_shape, ctx):
        """Apply percentage to amount."""
        percentage_shape.discount.set(Percentage(50.0)).execute(ctx)
        result = percentage_shape.discount.apply(200).execute(ctx)
        assert result == 100.0

    def test_of(self, percentage_shape, ctx):
        """'of' alias for apply."""
        percentage_shape.discount.set(Percentage(25.0)).execute(ctx)
        result = percentage_shape.discount.of(400).execute(ctx)
        assert result == 100.0

    def test_add_to(self, percentage_shape, ctx):
        """Add percentage to amount."""
        percentage_shape.tax_rate.set(Percentage(10.0)).execute(ctx)
        result = percentage_shape.tax_rate.add_to(100).execute(ctx)
        assert result == 110.0

    def test_sub_from(self, percentage_shape, ctx):
        """Subtract percentage from amount."""
        percentage_shape.discount.set(Percentage(20.0)).execute(ctx)
        result = percentage_shape.discount.sub_from(100).execute(ctx)
        assert result == 80.0


# ============================================================================
# PERCENTAGE VALIDATION TESTS
# ============================================================================


class TestPercentageValidation:
    """Test percentage validation operations."""

    def test_is_valid_in_range(self, percentage_shape, ctx):
        """Check validity for percentage in default range."""
        percentage_shape.completion.set(Percentage(50.0)).execute(ctx)
        result = percentage_shape.completion.is_valid().execute(ctx)
        assert result is True

    def test_is_valid_out_of_range(self, percentage_shape, ctx):
        """Check validity for percentage out of range."""
        percentage_shape.completion.set(Percentage(150.0)).execute(ctx)
        result = percentage_shape.completion.is_valid().execute(ctx)
        assert result is False

    def test_clamp_above(self, percentage_shape, ctx):
        """Clamp percentage above range."""
        percentage_shape.completion.set(Percentage(150.0)).execute(ctx)
        result = percentage_shape.completion.clamp().execute(ctx)
        assert result.value == 100.0

    def test_clamp_below(self, percentage_shape, ctx):
        """Clamp percentage below range."""
        percentage_shape.completion.set(Percentage(-10.0)).execute(ctx)
        result = percentage_shape.completion.clamp().execute(ctx)
        assert result.value == 0.0

    def test_clamp_in_range(self, percentage_shape, ctx):
        """Clamp percentage already in range."""
        percentage_shape.completion.set(Percentage(50.0)).execute(ctx)
        result = percentage_shape.completion.clamp().execute(ctx)
        assert result.value == 50.0


# ============================================================================
# PERCENTAGE ARITHMETIC TESTS
# ============================================================================


class TestPercentageArithmetic:
    """Test percentage arithmetic operations."""

    def test_addition(self, percentage_shape, ctx):
        """Add percentages."""
        percentage_shape.completion.set(Percentage(30.0)).execute(ctx)
        result = (percentage_shape.completion.get() + 20.0).execute(ctx)
        assert result.value == 50.0

    def test_addition_slots(self, percentage_shape, ctx):
        """Add two percentage slots."""
        percentage_shape.completion.set(Percentage(30.0)).execute(ctx)
        percentage_shape.discount.set(Percentage(20.0)).execute(ctx)

        result = (percentage_shape.completion.get() + percentage_shape.discount.get()).execute(ctx)
        assert result.value == 50.0

    def test_subtraction(self, percentage_shape, ctx):
        """Subtract percentages."""
        percentage_shape.completion.set(Percentage(50.0)).execute(ctx)
        result = (percentage_shape.completion.get() - 20.0).execute(ctx)
        assert result.value == 30.0

    def test_multiplication(self, percentage_shape, ctx):
        """Multiply percentage by factor."""
        percentage_shape.completion.set(Percentage(25.0)).execute(ctx)
        result = (percentage_shape.completion.get() * 2).execute(ctx)
        assert result.value == 50.0

    def test_division(self, percentage_shape, ctx):
        """Divide percentage by factor."""
        percentage_shape.completion.set(Percentage(50.0)).execute(ctx)
        result = (percentage_shape.completion.get() / 2).execute(ctx)
        assert result.value == 25.0

    def test_negation(self, percentage_shape, ctx):
        """Negate percentage."""
        percentage_shape.completion.set(Percentage(50.0)).execute(ctx)
        result = (-percentage_shape.completion.get()).execute(ctx)
        assert result.value == -50.0


# ============================================================================
# PERCENTAGE COMPARISON TESTS
# ============================================================================


class TestPercentageComparison:
    """Test percentage comparison operations."""

    def test_less_than(self, percentage_shape, ctx):
        """Compare percentages with less than."""
        percentage_shape.completion.set(Percentage(30.0)).execute(ctx)
        percentage_shape.discount.set(Percentage(50.0)).execute(ctx)

        result = (percentage_shape.completion.get() < percentage_shape.discount.get()).execute(ctx)
        assert result is True

    def test_greater_than(self, percentage_shape, ctx):
        """Compare percentages with greater than."""
        percentage_shape.completion.set(Percentage(75.0)).execute(ctx)
        percentage_shape.discount.set(Percentage(50.0)).execute(ctx)

        result = (percentage_shape.completion.get() > percentage_shape.discount.get()).execute(ctx)
        assert result is True

    def test_equals(self, percentage_shape, ctx):
        """Compare percentages for equality."""
        percentage_shape.completion.set(Percentage(50.0)).execute(ctx)
        percentage_shape.discount.set(Percentage(50.0)).execute(ctx)

        result = (percentage_shape.completion.get() == percentage_shape.discount.get()).execute(ctx)
        assert result is True

    def test_less_than_float(self, percentage_shape, ctx):
        """Compare percentage to float."""
        percentage_shape.completion.set(Percentage(30.0)).execute(ctx)

        result = (percentage_shape.completion.get() < 50.0).execute(ctx)
        assert result is True


# ============================================================================
# PERCENTAGE USE CASE TESTS
# ============================================================================


class TestPercentageUseCases:
    """Test real-world percentage use cases."""

    def test_calculate_discount(self, percentage_shape, ctx):
        """Calculate discounted price."""
        original_price = 100.0
        percentage_shape.discount.set(Percentage(20.0)).execute(ctx)

        discount_amount = percentage_shape.discount.apply(original_price).execute(ctx)
        assert discount_amount == 20.0

        final_price = original_price - discount_amount
        assert final_price == 80.0

    def test_calculate_tax(self, percentage_shape, ctx):
        """Calculate price with tax."""
        base_price = 100.0
        percentage_shape.tax_rate.set(Percentage(8.5)).execute(ctx)

        final_price = percentage_shape.tax_rate.add_to(base_price).execute(ctx)
        assert final_price == 108.5

    def test_progress_tracking(self, percentage_shape, ctx):
        """Track progress percentage."""
        percentage_shape.completion.set(Percentage(75.0)).execute(ctx)

        is_complete = (percentage_shape.completion.get() >= 100.0).execute(ctx)
        assert is_complete is False

        is_majority_done = (percentage_shape.completion.get() > 50.0).execute(ctx)
        assert is_majority_done is True
