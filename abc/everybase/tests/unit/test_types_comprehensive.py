"""Comprehensive unit tests for all Term types.

Tests type construction, operations, and method availability for:
- IntType, FloatType, BoolType (numeric/boolean)
- StrType, BytesType (text/binary)
- ListType, TupleType, DictType, SetType, FrozenSetType (collections)
- NoneType, AnyType (special types)
"""

import pytest

from everybase.conversion import literal
from everybase.ops import (
    AddOp,
    BitwiseAndOp,
    BitwiseNotOp,
    BitwiseOrOp,
    DivOp,
    FloorDivOp,
    GtOp,
    LShiftOp,
    LtOp,
    ModOp,
    MulOp,
    NegOp,
    PowOp,
    RShiftOp,
    SubOp,
    XorOp,
)
from everybase.types import (
    AnyType,
    BoolType,
    BytesType,
    DictType,
    FloatType,
    FrozenSetType,
    IntType,
    ListType,
    NoneType,
    SetType,
    StrType,
    TupleType,
)


# =============================================================================
# INT TYPE TESTS
# =============================================================================


class TestIntTypeArithmetic:
    """IntType arithmetic operations."""

    def test_addition_int_int(self):
        """int + int returns IntType."""
        x = IntType(10)
        result = x + 5
        assert isinstance(result, IntType)
        assert isinstance(result.source, AddOp)

    def test_addition_int_inttype(self):
        """IntType + IntType returns IntType."""
        x = IntType(10)
        y = IntType(5)
        result = x + y
        assert isinstance(result, IntType)

    def test_addition_int_float(self):
        """int + float returns FloatType."""
        x = IntType(10)
        result = x + 2.5
        assert isinstance(result, FloatType)

    def test_radd(self):
        """5 + IntType works via __radd__."""
        x = IntType(10)
        result = 5 + x
        assert isinstance(result, IntType)

    def test_subtraction(self):
        """IntType subtraction."""
        x = IntType(10)
        result = x - 3
        assert isinstance(result, IntType)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """20 - IntType works."""
        x = IntType(10)
        result = 20 - x
        assert isinstance(result, IntType)

    def test_multiplication(self):
        """IntType multiplication."""
        x = IntType(6)
        result = x * 7
        assert isinstance(result, IntType)
        assert isinstance(result.source, MulOp)

    def test_rmul(self):
        """7 * IntType works."""
        x = IntType(6)
        result = 7 * x
        assert isinstance(result, IntType)

    def test_division(self):
        """IntType division always returns FloatType."""
        x = IntType(10)
        result = x / 3
        assert isinstance(result, FloatType)
        assert isinstance(result.source, DivOp)

    def test_rdiv(self):
        """30 / IntType works."""
        x = IntType(10)
        result = 30 / x
        assert isinstance(result, FloatType)

    def test_floor_division(self):
        """IntType floor division."""
        x = IntType(10)
        result = x // 3
        assert isinstance(result, IntType)
        assert isinstance(result.source, FloorDivOp)

    def test_rfloordiv(self):
        """30 // IntType works."""
        x = IntType(10)
        result = 30 // x
        assert isinstance(result, IntType)

    def test_modulo(self):
        """IntType modulo."""
        x = IntType(10)
        result = x % 3
        assert isinstance(result, IntType)
        assert isinstance(result.source, ModOp)

    def test_rmod(self):
        """30 % IntType works."""
        x = IntType(7)
        result = 30 % x
        assert isinstance(result, IntType)

    def test_power(self):
        """IntType power."""
        x = IntType(2)
        result = x**10
        assert isinstance(result, IntType)
        assert isinstance(result.source, PowOp)

    def test_rpow(self):
        """2 ** IntType works."""
        x = IntType(10)
        result = 2**x
        assert isinstance(result, IntType)

    def test_negation(self):
        """IntType negation."""
        x = IntType(42)
        result = -x
        assert isinstance(result, IntType)
        assert isinstance(result.source, NegOp)

    def test_positive(self):
        """IntType unary plus."""
        x = IntType(42)
        result = +x
        assert isinstance(result, IntType)

    def test_absolute(self):
        """IntType absolute value."""
        x = IntType(-42)
        result = abs(x)
        assert isinstance(result, IntType)


class TestIntTypeBitwise:
    """IntType bitwise operations."""

    def test_bitwise_and(self):
        """IntType bitand() method."""
        x = IntType(0b1100)
        result = x.bitand(0b1010)
        assert isinstance(result, IntType)
        assert isinstance(result.source, BitwiseAndOp)

    def test_bitwise_or(self):
        """IntType bitor() method."""
        x = IntType(0b1100)
        result = x.bitor(0b1010)
        assert isinstance(result, IntType)
        assert isinstance(result.source, BitwiseOrOp)

    def test_bitwise_xor(self):
        """IntType xor via ^."""
        x = IntType(0b1100)
        result = x ^ 0b1010
        assert isinstance(result, IntType)
        assert isinstance(result.source, XorOp)

    def test_bitwise_not(self):
        """IntType bitnot() method."""
        x = IntType(0b1100)
        result = x.bitnot()
        assert isinstance(result, IntType)
        assert isinstance(result.source, BitwiseNotOp)

    def test_left_shift(self):
        """IntType left shift."""
        x = IntType(1)
        result = x << 4
        assert isinstance(result, IntType)
        assert isinstance(result.source, LShiftOp)

    def test_right_shift(self):
        """IntType right shift."""
        x = IntType(16)
        result = x >> 2
        assert isinstance(result, IntType)
        assert isinstance(result.source, RShiftOp)


class TestIntTypeComparison:
    """IntType comparison operations."""

    def test_greater_than(self):
        """IntType > comparison."""
        x = IntType(10)
        result = x > 5
        assert isinstance(result, BoolType)
        assert isinstance(result.source, GtOp)

    def test_less_than(self):
        """IntType < comparison."""
        x = IntType(10)
        result = x < 20
        assert isinstance(result, BoolType)
        assert isinstance(result.source, LtOp)

    def test_greater_equal(self):
        """IntType >= comparison."""
        x = IntType(10)
        result = x >= 10
        assert isinstance(result, BoolType)

    def test_less_equal(self):
        """IntType <= comparison."""
        x = IntType(10)
        result = x <= 10
        assert isinstance(result, BoolType)

    def test_equality_method(self):
        """IntType eq() method."""
        x = IntType(10)
        result = x.eq(10)
        assert isinstance(result, BoolType)

    def test_inequality_method(self):
        """IntType ne() method."""
        x = IntType(10)
        result = x.ne(5)
        assert isinstance(result, BoolType)

    def test_identity_method(self):
        """IntType is_() method."""
        x = IntType(10)
        result = x.is_(10)
        assert isinstance(result, BoolType)


class TestIntTypeLogical:
    """IntType logical operations."""

    def test_and(self):
        """IntType and_() method."""
        x = IntType(1)
        result = x.and_(IntType(2))
        assert isinstance(result, BoolType)

    def test_or(self):
        """IntType or_() method."""
        x = IntType(0)
        result = x.or_(IntType(1))
        assert isinstance(result, BoolType)

    def test_not(self):
        """IntType not_() method."""
        x = IntType(0)
        result = x.not_()
        assert isinstance(result, BoolType)

    def test_bool_method(self):
        """IntType bool_() method."""
        x = IntType(42)
        result = x.bool_()
        assert isinstance(result, BoolType)


class TestIntTypeConversions:
    """IntType type conversion methods."""

    def test_to_float(self):
        """IntType.to_float() returns FloatType."""
        x = IntType(42)
        result = x.to_float()
        assert isinstance(result, FloatType)

    def test_to_str(self):
        """IntType.to_str() returns StrType."""
        x = IntType(42)
        result = x.to_str()
        assert isinstance(result, StrType)

    def test_to_bool(self):
        """IntType.to_bool() returns BoolType."""
        x = IntType(42)
        result = x.to_bool()
        assert isinstance(result, BoolType)


class TestIntTypeSpecialChecks:
    """IntType special value checks."""

    def test_is_empty(self):
        """IntType.is_empty() returns BoolType."""
        x = IntType(42)
        result = x.is_empty()
        assert isinstance(result, BoolType)

    def test_is_invalid(self):
        """IntType.is_invalid() returns BoolType."""
        x = IntType(42)
        result = x.is_invalid()
        assert isinstance(result, BoolType)

    def test_is_sentinel(self):
        """IntType.is_sentinel() returns BoolType."""
        x = IntType(42)
        result = x.is_sentinel()
        assert isinstance(result, BoolType)

    def test_not_empty(self):
        """IntType.not_empty() returns BoolType."""
        x = IntType(42)
        result = x.not_empty()
        assert isinstance(result, BoolType)

    def test_not_invalid(self):
        """IntType.not_invalid() returns BoolType."""
        x = IntType(42)
        result = x.not_invalid()
        assert isinstance(result, BoolType)


class TestIntTypeConditional:
    """IntType conditional operations."""

    def test_ifelse(self):
        """IntType.ifelse() returns AnyType."""
        x = IntType(100)
        result = x.ifelse(BoolType(True), IntType(0))
        assert isinstance(result, AnyType)

    def test_or_default(self):
        """IntType.or_default() returns AnyType."""
        x = IntType(42)
        result = x.or_default(0)
        assert isinstance(result, AnyType)


# =============================================================================
# FLOAT TYPE TESTS
# =============================================================================


class TestFloatType:
    """FloatType operations."""

    def test_literal_creation(self):
        """FloatType can wrap literal."""
        f = FloatType(3.14)
        assert f.is_literal
        assert f.source == 3.14

    def test_addition(self):
        """FloatType addition."""
        f = FloatType(1.5)
        result = f + 2.5
        assert isinstance(result, FloatType)

    def test_subtraction(self):
        """FloatType subtraction."""
        f = FloatType(5.0)
        result = f - 2.0
        assert isinstance(result, FloatType)

    def test_multiplication(self):
        """FloatType multiplication."""
        f = FloatType(2.5)
        result = f * 4.0
        assert isinstance(result, FloatType)

    def test_division(self):
        """FloatType division."""
        f = FloatType(10.0)
        result = f / 4.0
        assert isinstance(result, FloatType)

    def test_floor_division(self):
        """FloatType floor division."""
        f = FloatType(10.0)
        result = f // 3.0
        assert isinstance(result, FloatType)

    def test_modulo(self):
        """FloatType modulo."""
        f = FloatType(10.0)
        result = f % 3.0
        assert isinstance(result, FloatType)

    def test_power(self):
        """FloatType power."""
        f = FloatType(2.0)
        result = f**3.0
        assert isinstance(result, FloatType)

    def test_negation(self):
        """FloatType negation."""
        f = FloatType(3.14)
        result = -f
        assert isinstance(result, FloatType)

    def test_comparison(self):
        """FloatType comparison."""
        f = FloatType(3.14)
        result = f > 3.0
        assert isinstance(result, BoolType)

    def test_to_int(self):
        """FloatType.to_int() returns IntType."""
        f = FloatType(3.14)
        result = f.to_int()
        assert isinstance(result, IntType)


# =============================================================================
# BOOL TYPE TESTS
# =============================================================================


class TestBoolType:
    """BoolType operations."""

    def test_literal_creation_true(self):
        """BoolType can wrap True."""
        b = BoolType(True)
        assert b.is_literal
        assert b.source is True

    def test_literal_creation_false(self):
        """BoolType can wrap False."""
        b = BoolType(False)
        assert b.is_literal
        assert b.source is False

    def test_and_operation(self):
        """BoolType and_() method."""
        a = BoolType(True)
        b = BoolType(False)
        result = a.and_(b)
        assert isinstance(result, BoolType)

    def test_or_operation(self):
        """BoolType or_() method."""
        a = BoolType(True)
        b = BoolType(False)
        result = a.or_(b)
        assert isinstance(result, BoolType)

    def test_not_operation(self):
        """BoolType not_() method."""
        a = BoolType(True)
        result = a.not_()
        assert isinstance(result, BoolType)

    def test_bool_method(self):
        """BoolType bool_() method."""
        a = BoolType(True)
        result = a.bool_()
        assert isinstance(result, BoolType)

    def test_comparison(self):
        """BoolType comparison."""
        a = BoolType(True)
        result = a > BoolType(False)
        assert isinstance(result, BoolType)

    def test_equality(self):
        """BoolType eq() method."""
        a = BoolType(True)
        result = a.eq(True)
        assert isinstance(result, BoolType)


# =============================================================================
# STR TYPE TESTS
# =============================================================================


class TestStrTypeBasic:
    """StrType basic operations."""

    def test_literal_creation(self):
        """StrType can wrap literal."""
        s = StrType("hello")
        assert s.is_literal
        assert s.source == "hello"

    def test_concatenation(self):
        """StrType + str returns StrType."""
        s = StrType("hello")
        result = s + " world"
        assert isinstance(result, StrType)
        assert isinstance(result.source, AddOp)

    def test_radd(self):
        """str + StrType works."""
        s = StrType("world")
        result = "hello " + s
        assert isinstance(result, StrType)


class TestStrTypeCaseMethods:
    """StrType case transformation methods."""

    def test_upper(self):
        """StrType.upper() returns StrType."""
        s = StrType("hello")
        result = s.upper()
        assert isinstance(result, StrType)
        assert not result.is_literal

    def test_lower(self):
        """StrType.lower() returns StrType."""
        s = StrType("HELLO")
        result = s.lower()
        assert isinstance(result, StrType)

    def test_title(self):
        """StrType.title() returns StrType."""
        s = StrType("hello world")
        result = s.title()
        assert isinstance(result, StrType)

    def test_capitalize(self):
        """StrType.capitalize() returns StrType."""
        s = StrType("hello")
        result = s.capitalize()
        assert isinstance(result, StrType)

    def test_swapcase(self):
        """StrType.swapcase() returns StrType."""
        s = StrType("HeLLo")
        result = s.swapcase()
        assert isinstance(result, StrType)


class TestStrTypeStrippingMethods:
    """StrType stripping methods."""

    def test_strip(self):
        """StrType.strip() returns StrType."""
        s = StrType("  hello  ")
        result = s.strip()
        assert isinstance(result, StrType)

    def test_strip_with_chars(self):
        """StrType.strip(chars) returns StrType."""
        s = StrType("xxhelloxx")
        result = s.strip("x")
        assert isinstance(result, StrType)

    def test_lstrip(self):
        """StrType.lstrip() returns StrType."""
        s = StrType("  hello")
        result = s.lstrip()
        assert isinstance(result, StrType)

    def test_rstrip(self):
        """StrType.rstrip() returns StrType."""
        s = StrType("hello  ")
        result = s.rstrip()
        assert isinstance(result, StrType)


class TestStrTypeSplittingMethods:
    """StrType splitting methods."""

    def test_split(self):
        """StrType.split() returns ListType."""
        s = StrType("a,b,c")
        result = s.split(",")
        assert isinstance(result, ListType)

    def test_split_no_sep(self):
        """StrType.split() with no separator."""
        s = StrType("a b c")
        result = s.split()
        assert isinstance(result, ListType)

    def test_rsplit(self):
        """StrType.rsplit() returns ListType."""
        s = StrType("a,b,c")
        result = s.rsplit(",")
        assert isinstance(result, ListType)


class TestStrTypeSearchMethods:
    """StrType search methods."""

    def test_find(self):
        """StrType.find() returns IntType."""
        s = StrType("hello world")
        result = s.find("world")
        assert isinstance(result, IntType)

    def test_rfind(self):
        """StrType.rfind() returns IntType."""
        s = StrType("hello world world")
        result = s.rfind("world")
        assert isinstance(result, IntType)

    def test_count_substring(self):
        """StrType.count_substring() returns IntType."""
        s = StrType("abcabc")
        result = s.count_substring("abc")
        assert isinstance(result, IntType)


class TestStrTypeTestMethods:
    """StrType testing methods."""

    def test_startswith(self):
        """StrType.startswith() returns BoolType."""
        s = StrType("hello")
        result = s.startswith("he")
        assert isinstance(result, BoolType)

    def test_endswith(self):
        """StrType.endswith() returns BoolType."""
        s = StrType("hello")
        result = s.endswith("lo")
        assert isinstance(result, BoolType)

    def test_isdigit(self):
        """StrType.isdigit() returns BoolType."""
        s = StrType("123")
        result = s.isdigit()
        assert isinstance(result, BoolType)

    def test_isalpha(self):
        """StrType.isalpha() returns BoolType."""
        s = StrType("abc")
        result = s.isalpha()
        assert isinstance(result, BoolType)

    def test_isalnum(self):
        """StrType.isalnum() returns BoolType."""
        s = StrType("abc123")
        result = s.isalnum()
        assert isinstance(result, BoolType)

    def test_isspace(self):
        """StrType.isspace() returns BoolType."""
        s = StrType("   ")
        result = s.isspace()
        assert isinstance(result, BoolType)


class TestStrTypePaddingMethods:
    """StrType padding methods."""

    def test_center(self):
        """StrType.center() returns StrType."""
        s = StrType("hi")
        result = s.center(10)
        assert isinstance(result, StrType)

    def test_ljust(self):
        """StrType.ljust() returns StrType."""
        s = StrType("hi")
        result = s.ljust(10)
        assert isinstance(result, StrType)

    def test_rjust(self):
        """StrType.rjust() returns StrType."""
        s = StrType("hi")
        result = s.rjust(10)
        assert isinstance(result, StrType)

    def test_zfill(self):
        """StrType.zfill() returns StrType."""
        s = StrType("42")
        result = s.zfill(5)
        assert isinstance(result, StrType)


class TestStrTypeOtherMethods:
    """StrType other methods."""

    def test_replace(self):
        """StrType.replace() returns StrType."""
        s = StrType("hello")
        result = s.replace("l", "L")
        assert isinstance(result, StrType)

    def test_encode(self):
        """StrType.encode() returns BytesType."""
        s = StrType("hello")
        result = s.encode()
        assert isinstance(result, BytesType)

    def test_len(self):
        """StrType.len_() returns IntType."""
        s = StrType("hello")
        result = s.len_()
        assert isinstance(result, IntType)

    def test_contains(self):
        """StrType.contains() returns BoolType."""
        s = StrType("hello")
        result = s.contains("ell")
        assert isinstance(result, BoolType)


class TestStrTypeComparison:
    """StrType comparison operations."""

    def test_greater_than(self):
        """StrType > comparison."""
        s = StrType("b")
        result = s > "a"
        assert isinstance(result, BoolType)

    def test_less_than(self):
        """StrType < comparison."""
        s = StrType("a")
        result = s < "b"
        assert isinstance(result, BoolType)

    def test_equality(self):
        """StrType eq() method."""
        s = StrType("hello")
        result = s.eq("hello")
        assert isinstance(result, BoolType)


# =============================================================================
# BYTES TYPE TESTS
# =============================================================================


class TestBytesType:
    """BytesType operations."""

    def test_literal_creation(self):
        """BytesType can wrap literal."""
        b = BytesType(b"hello")
        assert b.is_literal
        assert b.source == b"hello"

    def test_concatenation(self):
        """BytesType + bytes returns BytesType."""
        b = BytesType(b"hello")
        result = b + b" world"
        assert isinstance(result, BytesType)

    def test_decode(self):
        """BytesType.decode() returns StrType."""
        b = BytesType(b"hello")
        result = b.decode()
        assert isinstance(result, StrType)

    def test_hex(self):
        """BytesType.hex_() returns StrType."""
        b = BytesType(b"hello")
        result = b.hex_()
        assert isinstance(result, StrType)

    def test_upper(self):
        """BytesType.upper() returns BytesType."""
        b = BytesType(b"hello")
        result = b.upper()
        assert isinstance(result, BytesType)

    def test_lower(self):
        """BytesType.lower() returns BytesType."""
        b = BytesType(b"HELLO")
        result = b.lower()
        assert isinstance(result, BytesType)

    def test_strip(self):
        """BytesType.strip() returns BytesType."""
        b = BytesType(b"  hello  ")
        result = b.strip()
        assert isinstance(result, BytesType)

    def test_find_bytes(self):
        """BytesType.find_bytes() returns IntType."""
        b = BytesType(b"hello world")
        result = b.find_bytes(b"world")
        assert isinstance(result, IntType)

    def test_startswith(self):
        """BytesType.startswith() returns BoolType."""
        b = BytesType(b"hello")
        result = b.startswith(b"he")
        assert isinstance(result, BoolType)

    def test_len(self):
        """BytesType.len_() returns IntType."""
        b = BytesType(b"hello")
        result = b.len_()
        assert isinstance(result, IntType)


# =============================================================================
# LIST TYPE TESTS
# =============================================================================


class TestListTypeBasic:
    """ListType basic operations."""

    def test_literal_creation(self):
        """ListType can wrap literal."""
        lst = ListType([1, 2, 3])
        assert lst.is_literal
        assert lst.source == [1, 2, 3]

    def test_concatenation(self):
        """ListType + list returns ListType."""
        lst = ListType([1, 2])
        result = lst + [3, 4]  # noqa: RUF005
        assert isinstance(result, ListType)

    def test_indexing(self):
        """ListType[int] returns AnyType."""
        lst = ListType([1, 2, 3])
        result = lst[0]
        assert isinstance(result, AnyType)

    def test_slicing(self):
        """ListType[slice] returns ListType."""
        lst = ListType([1, 2, 3, 4, 5])
        result = lst[1:4]
        assert isinstance(result, ListType)


class TestListTypeSequenceMethods:
    """ListType sequence methods."""

    def test_len(self):
        """ListType.len_() returns IntType."""
        lst = ListType([1, 2, 3])
        result = lst.len_()
        assert isinstance(result, IntType)

    def test_contains(self):
        """ListType.contains() returns BoolType."""
        lst = ListType([1, 2, 3])
        result = lst.contains(2)
        assert isinstance(result, BoolType)

    def test_first(self):
        """ListType.first() returns AnyType."""
        lst = ListType([1, 2, 3])
        result = lst.first()
        assert isinstance(result, AnyType)

    def test_last(self):
        """ListType.last() returns AnyType."""
        lst = ListType([1, 2, 3])
        result = lst.last()
        assert isinstance(result, AnyType)

    def test_reversed(self):
        """ListType.reversed_() returns ListType."""
        lst = ListType([1, 2, 3])
        result = lst.reversed_()
        assert isinstance(result, ListType)

    def test_sorted(self):
        """ListType.sorted_() returns ListType."""
        lst = ListType([3, 1, 2])
        result = lst.sorted_()
        assert isinstance(result, ListType)

    def test_index(self):
        """ListType.index() returns IntType."""
        lst = ListType([1, 2, 3])
        result = lst.index(2)
        assert isinstance(result, IntType)

    def test_count(self):
        """ListType.count() returns IntType."""
        lst = ListType([1, 2, 2, 3])
        result = lst.count(2)
        assert isinstance(result, IntType)


class TestListTypeIterableMethods:
    """ListType iterable/functional methods."""

    def test_sum(self):
        """ListType.sum_() returns AnyType."""
        lst = ListType([1, 2, 3])
        result = lst.sum_()
        assert isinstance(result, AnyType)

    def test_min(self):
        """ListType.min_() returns AnyType."""
        lst = ListType([3, 1, 2])
        result = lst.min_()
        assert isinstance(result, AnyType)

    def test_max(self):
        """ListType.max_() returns AnyType."""
        lst = ListType([3, 1, 2])
        result = lst.max_()
        assert isinstance(result, AnyType)

    def test_any(self):
        """ListType.any_() returns BoolType."""
        lst = ListType([False, True, False])
        result = lst.any_()
        assert isinstance(result, BoolType)

    def test_all(self):
        """ListType.all_() returns BoolType."""
        lst = ListType([True, True, True])
        result = lst.all_()
        assert isinstance(result, BoolType)


# =============================================================================
# TUPLE TYPE TESTS
# =============================================================================


class TestTupleType:
    """TupleType operations."""

    def test_literal_creation(self):
        """TupleType can wrap literal."""
        t = TupleType((1, 2, 3))
        assert t.is_literal
        assert t.source == (1, 2, 3)

    def test_indexing(self):
        """TupleType[int] returns AnyType."""
        t = TupleType((1, 2, 3))
        result = t[0]
        assert isinstance(result, AnyType)

    def test_slicing(self):
        """TupleType[slice] returns TupleType."""
        t = TupleType((1, 2, 3, 4, 5))
        result = t[1:4]
        # TupleType slicing returns TupleType (not ListType)
        assert isinstance(result, TupleType)

    def test_len(self):
        """TupleType.len_() returns IntType."""
        t = TupleType((1, 2, 3))
        result = t.len_()
        assert isinstance(result, IntType)

    def test_contains(self):
        """TupleType.contains() returns BoolType."""
        t = TupleType((1, 2, 3))
        result = t.contains(2)
        assert isinstance(result, BoolType)


# =============================================================================
# DICT TYPE TESTS
# =============================================================================


class TestDictType:
    """DictType operations."""

    def test_literal_creation(self):
        """DictType can wrap literal."""
        d = DictType({"a": 1, "b": 2})
        assert d.is_literal
        assert d.source == {"a": 1, "b": 2}

    def test_key_access(self):
        """DictType[key] returns AnyType."""
        d = DictType({"a": 1, "b": 2})
        result = d["a"]
        assert isinstance(result, AnyType)

    def test_len(self):
        """DictType.len_() returns IntType."""
        d = DictType({"a": 1, "b": 2})
        result = d.len_()
        assert isinstance(result, IntType)

    def test_contains(self):
        """DictType.contains() returns BoolType."""
        d = DictType({"a": 1, "b": 2})
        result = d.contains("a")
        assert isinstance(result, BoolType)

    def test_keys(self):
        """DictType.keys_() returns ListType."""
        d = DictType({"a": 1, "b": 2})
        result = d.keys_()
        assert isinstance(result, ListType)

    def test_values(self):
        """DictType.values_() returns ListType."""
        d = DictType({"a": 1, "b": 2})
        result = d.values_()
        assert isinstance(result, ListType)

    def test_items(self):
        """DictType.items_() returns ListType."""
        d = DictType({"a": 1, "b": 2})
        result = d.items_()
        assert isinstance(result, ListType)

    def test_get(self):
        """DictType.get_() returns AnyType."""
        d = DictType({"a": 1, "b": 2})
        result = d.get_("a", 0)
        assert isinstance(result, AnyType)


# =============================================================================
# SET TYPE TESTS
# =============================================================================


class TestSetType:
    """SetType operations."""

    def test_literal_creation(self):
        """SetType can wrap literal."""
        s = SetType({1, 2, 3})
        assert s.is_literal
        assert s.source == {1, 2, 3}

    def test_len(self):
        """SetType.len_() returns IntType."""
        s = SetType({1, 2, 3})
        result = s.len_()
        assert isinstance(result, IntType)

    def test_contains(self):
        """SetType.contains() returns BoolType."""
        s = SetType({1, 2, 3})
        result = s.contains(2)
        assert isinstance(result, BoolType)

    def test_union(self):
        """SetType.union() returns SetType."""
        s = SetType({1, 2})
        result = s.union({3, 4})
        assert isinstance(result, SetType)

    def test_intersection(self):
        """SetType.intersection() returns SetType."""
        s = SetType({1, 2, 3})
        result = s.intersection({2, 3, 4})
        assert isinstance(result, SetType)

    def test_difference(self):
        """SetType.difference() returns SetType."""
        s = SetType({1, 2, 3})
        result = s.difference({2, 3})
        assert isinstance(result, SetType)

    def test_symmetric_difference(self):
        """SetType.symmetric_difference() returns SetType."""
        s = SetType({1, 2, 3})
        result = s.symmetric_difference({2, 3, 4})
        assert isinstance(result, SetType)

    def test_issubset(self):
        """SetType.issubset() returns BoolType."""
        s = SetType({1, 2})
        result = s.issubset({1, 2, 3})
        assert isinstance(result, BoolType)

    def test_issuperset(self):
        """SetType.issuperset() returns BoolType."""
        s = SetType({1, 2, 3})
        result = s.issuperset({1, 2})
        assert isinstance(result, BoolType)

    def test_isdisjoint(self):
        """SetType.isdisjoint() returns BoolType."""
        s = SetType({1, 2})
        result = s.isdisjoint({3, 4})
        assert isinstance(result, BoolType)


class TestFrozenSetType:
    """FrozenSetType operations."""

    def test_literal_creation(self):
        """FrozenSetType can wrap literal."""
        s = FrozenSetType(frozenset({1, 2, 3}))
        assert s.is_literal
        assert s.source == frozenset({1, 2, 3})

    def test_union(self):
        """FrozenSetType.union() returns FrozenSetType."""
        s = FrozenSetType(frozenset({1, 2}))
        result = s.union(frozenset({3, 4}))
        assert isinstance(result, FrozenSetType)


# =============================================================================
# NONE TYPE TESTS
# =============================================================================


class TestNoneType:
    """NoneType operations."""

    def test_default_creation(self):
        """NoneType() creates None literal."""
        n = NoneType()
        assert n.is_literal

    def test_explicit_none(self):
        """NoneType(None) works."""
        n = NoneType(None)
        assert n.is_literal

    def test_is_empty(self):
        """NoneType.is_empty() returns BoolType."""
        n = NoneType()
        result = n.is_empty()
        assert isinstance(result, BoolType)

    def test_logical_and(self):
        """NoneType.and_() works."""
        n = NoneType()
        result = n.and_(BoolType(True))
        assert isinstance(result, BoolType)


# =============================================================================
# ANY TYPE TESTS
# =============================================================================


class TestAnyType:
    """AnyType operations."""

    def test_from_literal(self):
        """AnyType can wrap literal."""
        a = AnyType(42)
        assert a.is_literal
        assert a.source == 42

    def test_arithmetic(self):
        """AnyType supports arithmetic."""
        a = AnyType(10)
        result = a + 5
        assert isinstance(result, AnyType)

    def test_comparison(self):
        """AnyType supports comparison."""
        a = AnyType(10)
        result = a > 5
        assert isinstance(result, BoolType)

    def test_logical(self):
        """AnyType supports logical."""
        a = AnyType(True)
        result = a.and_(False)
        assert isinstance(result, BoolType)

    def test_bitwise(self):
        """AnyType supports bitwise."""
        a = AnyType(0b1100)
        result = a.bitand(0b1010)
        assert isinstance(result, AnyType)


# =============================================================================
# LITERAL FUNCTION TESTS
# =============================================================================


class TestLiteralFunction:
    """literal() function comprehensive tests."""

    def test_int(self):
        """literal(int) returns IntType."""
        result = literal(42)
        assert isinstance(result, IntType)
        assert result.source == 42

    def test_float(self):
        """literal(float) returns FloatType."""
        result = literal(3.14)
        assert isinstance(result, FloatType)
        assert result.source == 3.14

    def test_bool_true(self):
        """literal(True) returns BoolType (not IntType)."""
        result = literal(True)
        assert isinstance(result, BoolType)
        assert result.source is True

    def test_bool_false(self):
        """literal(False) returns BoolType."""
        result = literal(False)
        assert isinstance(result, BoolType)
        assert result.source is False

    def test_str(self):
        """literal(str) returns StrType."""
        result = literal("hello")
        assert isinstance(result, StrType)
        assert result.source == "hello"

    def test_bytes(self):
        """literal(bytes) returns BytesType."""
        result = literal(b"hello")
        assert isinstance(result, BytesType)
        assert result.source == b"hello"

    def test_none(self):
        """literal(None) returns NoneType."""
        result = literal(None)
        assert isinstance(result, NoneType)

    def test_list(self):
        """literal(list) returns ListType."""
        result = literal([1, 2, 3])
        assert isinstance(result, ListType)
        assert result.source == [1, 2, 3]

    def test_tuple(self):
        """literal(tuple) returns TupleType."""
        result = literal((1, 2, 3))
        assert isinstance(result, TupleType)
        assert result.source == (1, 2, 3)

    def test_dict(self):
        """literal(dict) returns DictType."""
        result = literal({"a": 1})
        assert isinstance(result, DictType)
        assert result.source == {"a": 1}

    def test_set(self):
        """literal(set) returns SetType."""
        result = literal({1, 2, 3})
        assert isinstance(result, SetType)

    def test_frozenset(self):
        """literal(frozenset) returns FrozenSetType."""
        result = literal(frozenset({1, 2, 3}))
        assert isinstance(result, FrozenSetType)

    def test_passthrough_term(self):
        """literal(Term) returns Term unchanged."""
        original = IntType(42)
        result = literal(original)
        assert result is original

    def test_unsupported_type(self):
        """literal(unsupported) raises TypeError."""
        with pytest.raises(TypeError, match="Not supported type"):
            literal(object())


# =============================================================================
# TYPE PROPERTIES TESTS
# =============================================================================


class TestTypeProperties:
    """Test type properties like is_literal, is_pure, children."""

    def test_literal_is_literal(self):
        """Literal types have is_literal=True."""
        x = IntType(42)
        assert x.is_literal is True

    def test_computed_not_literal(self):
        """Computed types have is_literal=False."""
        x = IntType(42)
        y = x + 1
        assert y.is_literal is False

    def test_literal_is_pure(self):
        """Literal types are pure."""
        x = IntType(42)
        assert x.is_pure is True

    def test_operation_is_pure(self):
        """Operations are pure."""
        x = IntType(42)
        y = x + 1
        assert y.is_pure is True

    def test_literal_no_children(self):
        """Literal types have empty children."""
        x = IntType(42)
        assert x.children == ()

    def test_computed_has_children(self):
        """Computed types have source as child."""
        x = IntType(42)
        y = x + 1
        assert len(y.children) == 1
        assert y.children[0] is y.source
