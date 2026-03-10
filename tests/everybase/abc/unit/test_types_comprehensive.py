"""Comprehensive unit tests for all Term types.

Tests type construction, operations, and method availability for:
- IntValue, FloatValue, BoolValue (numeric/boolean)
- StrValue, BytesValue (text/binary)
- ListValue, TupleValue, DictValue, SetValue, FrozenSetValue (collections)
- NoneValue, AnyValue (special types)
"""

import pytest

from everybase.abc import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictItemsValue,
    DictKeysValue,
    DictValue,
    DictValuesValue,
    FloatValue,
    FrozenSetValue,
    IntValue,
    IteratorValue,
    ListValue,
    NoneValue,
    SetValue,
    StrValue,
    ToBoolOp,
    ToFloatOp,
    ToIntOp,
    ToStrOp,
    TupleValue,
    ensure_term,
    fn,
)


# =============================================================================
# INT TYPE TESTS
# =============================================================================


class TestIntRefArithmetic:
    """IntValue arithmetic operations."""

    def test_addition_int_int(self):
        """int + int returns IntValue."""
        x = IntValue(10)
        result = x + 5
        assert isinstance(result, IntValue)

    def test_addition_int_inttype(self):
        """IntValue + IntValue returns IntValue."""
        x = IntValue(10)
        y = IntValue(5)
        result = x + y
        assert isinstance(result, IntValue)

    def test_addition_int_float(self):
        """int + float returns FloatValue."""
        x = IntValue(10)
        result = x + 2.5
        assert isinstance(result, FloatValue)

    def test_radd(self):
        """5 + IntValue works via __radd__."""
        x = IntValue(10)
        result = 5 + x
        assert isinstance(result, IntValue)

    def test_subtraction(self):
        """IntValue subtraction."""
        x = IntValue(10)
        result = x - 3
        assert isinstance(result, IntValue)

    def test_rsub(self):
        """20 - IntValue works."""
        x = IntValue(10)
        result = 20 - x
        assert isinstance(result, IntValue)

    def test_multiplication(self):
        """IntValue multiplication."""
        x = IntValue(6)
        result = x * 7
        assert isinstance(result, IntValue)

    def test_rmul(self):
        """7 * IntValue works."""
        x = IntValue(6)
        result = 7 * x
        assert isinstance(result, IntValue)

    def test_division(self):
        """IntValue division always returns FloatValue."""
        x = IntValue(10)
        result = x / 3
        assert isinstance(result, FloatValue)

    def test_rdiv(self):
        """30 / IntValue works."""
        x = IntValue(10)
        result = 30 / x
        assert isinstance(result, FloatValue)

    def test_floor_division(self):
        """IntValue floor division."""
        x = IntValue(10)
        result = x // 3
        assert isinstance(result, IntValue)

    def test_rfloordiv(self):
        """30 // IntValue works."""
        x = IntValue(10)
        result = 30 // x
        assert isinstance(result, IntValue)

    def test_modulo(self):
        """IntValue modulo."""
        x = IntValue(10)
        result = x % 3
        assert isinstance(result, IntValue)

    def test_rmod(self):
        """30 % IntValue works."""
        x = IntValue(7)
        result = 30 % x
        assert isinstance(result, IntValue)

    def test_power(self):
        """IntValue power."""
        x = IntValue(2)
        result = x**10
        assert isinstance(result, IntValue)

    def test_rpow(self):
        """2 ** IntValue works."""
        x = IntValue(10)
        result = 2**x
        assert isinstance(result, IntValue)

    def test_negation(self):
        """IntValue negation."""
        x = IntValue(42)
        result = -x
        assert isinstance(result, IntValue)

    def test_positive(self):
        """IntValue unary plus."""
        x = IntValue(42)
        result = +x
        assert isinstance(result, IntValue)

    def test_absolute(self):
        """IntValue absolute value."""
        x = IntValue(-42)
        result = abs(x)
        assert isinstance(result, IntValue)


class TestIntRefBitwise:
    """IntValue bitwise operations."""

    def test_bitwise_and(self):
        """IntValue bitand() method."""
        x = IntValue(0b1100)
        result = x.bitand(0b1010)
        assert isinstance(result, IntValue)

    def test_bitwise_or(self):
        """IntValue bitor() method."""
        x = IntValue(0b1100)
        result = x.bitor(0b1010)
        assert isinstance(result, IntValue)

    def test_bitwise_xor(self):
        """IntValue xor via ^."""
        x = IntValue(0b1100)
        result = x ^ 0b1010
        assert isinstance(result, IntValue)

    def test_bitwise_not(self):
        """IntValue bitnot() method."""
        x = IntValue(0b1100)
        result = x.bitnot()
        assert isinstance(result, IntValue)

    def test_left_shift(self):
        """IntValue left shift."""
        x = IntValue(1)
        result = x << 4
        assert isinstance(result, IntValue)

    def test_right_shift(self):
        """IntValue right shift."""
        x = IntValue(16)
        result = x >> 2
        assert isinstance(result, IntValue)


class TestIntRefComparison:
    """IntValue comparison operations."""

    def test_greater_than(self):
        """IntValue > comparison."""
        x = IntValue(10)
        result = x > 5
        assert isinstance(result, BoolValue)

    def test_less_than(self):
        """IntValue < comparison."""
        x = IntValue(10)
        result = x < 20
        assert isinstance(result, BoolValue)

    def test_greater_equal(self):
        """IntValue >= comparison."""
        x = IntValue(10)
        result = x >= 10
        assert isinstance(result, BoolValue)

    def test_less_equal(self):
        """IntValue <= comparison."""
        x = IntValue(10)
        result = x <= 10
        assert isinstance(result, BoolValue)

    def test_equality_method(self):
        """IntValue eq() method."""
        x = IntValue(10)
        result = x.eq(10)
        assert isinstance(result, BoolValue)

    def test_inequality_method(self):
        """IntValue ne() method."""
        x = IntValue(10)
        result = x.ne(5)
        assert isinstance(result, BoolValue)

    def test_identity_method(self):
        """IntValue is_() method."""
        x = IntValue(10)
        result = x.is_(10)
        assert isinstance(result, BoolValue)


class TestIntRefLogical:
    """IntValue logical operations."""

    def test_and(self):
        """IntValue and_() method."""
        x = IntValue(1)
        result = x.and_(IntValue(2))
        assert isinstance(result, BoolValue)

    def test_or(self):
        """IntValue or_() method."""
        x = IntValue(0)
        result = x.or_(IntValue(1))
        assert isinstance(result, BoolValue)

    def test_not(self):
        """IntValue not_() method."""
        x = IntValue(0)
        result = x.not_()
        assert isinstance(result, BoolValue)

    def test_bool_method(self):
        """IntValue bool_() method."""
        x = IntValue(42)
        result = x.bool_()
        assert isinstance(result, BoolValue)


class TestIntRefConversions:
    """IntValue type conversion via standalone morphisms."""

    def test_to_float(self):
        """ToFloatOp wrapping returns FloatValue."""
        x = IntValue(42)
        result = FloatValue(ToFloatOp(x))
        assert isinstance(result, FloatValue)

    def test_to_str(self):
        """ToStrOp wrapping returns StrValue."""
        x = IntValue(42)
        result = StrValue(ToStrOp(x))
        assert isinstance(result, StrValue)

    def test_to_bool(self):
        """ToBoolOp wrapping returns BoolValue."""
        x = IntValue(42)
        result = BoolValue(ToBoolOp(x))
        assert isinstance(result, BoolValue)


class TestIntRefSpecialChecks:
    """IntValue special value checks."""

    def test_is_empty(self):
        """IntValue.is_empty() returns BoolValue."""
        x = IntValue(42)
        result = x.is_empty()
        assert isinstance(result, BoolValue)

    def test_is_invalid(self):
        """IntValue.is_invalid() returns BoolValue."""
        x = IntValue(42)
        result = x.is_invalid()
        assert isinstance(result, BoolValue)

    def test_is_sentinel(self):
        """IntValue.is_sentinel() returns BoolValue."""
        x = IntValue(42)
        result = x.is_sentinel()
        assert isinstance(result, BoolValue)

    def test_not_empty(self):
        """IntValue.not_empty() returns BoolValue."""
        x = IntValue(42)
        result = x.not_empty()
        assert isinstance(result, BoolValue)

    def test_not_invalid(self):
        """IntValue.not_invalid() returns BoolValue."""
        x = IntValue(42)
        result = x.not_invalid()
        assert isinstance(result, BoolValue)


# =============================================================================
# FLOAT TYPE TESTS
# =============================================================================


class TestFloatRef:
    """FloatValue operations."""

    def test_literal_creation(self):
        """FloatValue can wrap literal."""
        FloatValue(3.14)

    def test_addition(self):
        """FloatValue addition."""
        f = FloatValue(1.5)
        result = f + 2.5
        assert isinstance(result, FloatValue)

    def test_subtraction(self):
        """FloatValue subtraction."""
        f = FloatValue(5.0)
        result = f - 2.0
        assert isinstance(result, FloatValue)

    def test_multiplication(self):
        """FloatValue multiplication."""
        f = FloatValue(2.5)
        result = f * 4.0
        assert isinstance(result, FloatValue)

    def test_division(self):
        """FloatValue division."""
        f = FloatValue(10.0)
        result = f / 4.0
        assert isinstance(result, FloatValue)

    def test_floor_division(self):
        """FloatValue floor division."""
        f = FloatValue(10.0)
        result = f // 3.0
        assert isinstance(result, FloatValue)

    def test_modulo(self):
        """FloatValue modulo."""
        f = FloatValue(10.0)
        result = f % 3.0
        assert isinstance(result, FloatValue)

    def test_power(self):
        """FloatValue power."""
        f = FloatValue(2.0)
        result = f**3.0
        assert isinstance(result, FloatValue)

    def test_negation(self):
        """FloatValue negation."""
        f = FloatValue(3.14)
        result = -f
        assert isinstance(result, FloatValue)

    def test_comparison(self):
        """FloatValue comparison."""
        f = FloatValue(3.14)
        result = f > 3.0
        assert isinstance(result, BoolValue)

    def test_to_int(self):
        """ToIntOp wrapping returns IntValue."""
        f = FloatValue(3.14)
        result = IntValue(ToIntOp(f))
        assert isinstance(result, IntValue)


# =============================================================================
# BOOL TYPE TESTS
# =============================================================================


class TestBoolRef:
    """BoolValue operations."""

    def test_literal_creation_true(self):
        """BoolValue can wrap True."""
        BoolValue(True)

    def test_literal_creation_false(self):
        """BoolValue can wrap False."""
        BoolValue(False)

    def test_and_operation(self):
        """BoolValue and_() method."""
        a = BoolValue(True)
        b = BoolValue(False)
        result = a.and_(b)
        assert isinstance(result, BoolValue)

    def test_or_operation(self):
        """BoolValue or_() method."""
        a = BoolValue(True)
        b = BoolValue(False)
        result = a.or_(b)
        assert isinstance(result, BoolValue)

    def test_not_operation(self):
        """BoolValue not_() method."""
        a = BoolValue(True)
        result = a.not_()
        assert isinstance(result, BoolValue)

    def test_bool_method(self):
        """BoolValue bool_() method."""
        a = BoolValue(True)
        result = a.bool_()
        assert isinstance(result, BoolValue)

    def test_comparison(self):
        """BoolValue comparison."""
        a = BoolValue(True)
        result = a > BoolValue(False)
        assert isinstance(result, BoolValue)

    def test_equality(self):
        """BoolValue eq() method."""
        a = BoolValue(True)
        result = a.eq(True)
        assert isinstance(result, BoolValue)


# =============================================================================
# STR TYPE TESTS
# =============================================================================


class TestStrRefBasic:
    """StrValue basic operations."""

    def test_literal_creation(self):
        """StrValue can wrap literal."""
        StrValue("hello")

    def test_concatenation(self):
        """StrValue + str returns StrValue."""
        s = StrValue("hello")
        result = s + " world"
        assert isinstance(result, StrValue)

    def test_radd(self):
        """str + StrValue works."""
        s = StrValue("world")
        result = "hello " + s
        assert isinstance(result, StrValue)


class TestStrRefCaseMethods:
    """StrValue case transformation methods."""

    def test_upper(self):
        """StrValue.upper() returns StrValue."""
        s = StrValue("hello")
        result = s.upper()
        assert isinstance(result, StrValue)

    def test_lower(self):
        """StrValue.lower() returns StrValue."""
        s = StrValue("HELLO")
        result = s.lower()
        assert isinstance(result, StrValue)

    def test_title(self):
        """StrValue.title() returns StrValue."""
        s = StrValue("hello world")
        result = s.title()
        assert isinstance(result, StrValue)

    def test_capitalize(self):
        """StrValue.capitalize() returns StrValue."""
        s = StrValue("hello")
        result = s.capitalize()
        assert isinstance(result, StrValue)

    def test_swapcase(self):
        """StrValue.swapcase() returns StrValue."""
        s = StrValue("HeLLo")
        result = s.swapcase()
        assert isinstance(result, StrValue)


class TestStrRefStrippingMethods:
    """StrValue stripping methods."""

    def test_strip(self):
        """StrValue.strip() returns StrValue."""
        s = StrValue("  hello  ")
        result = s.strip()
        assert isinstance(result, StrValue)

    def test_strip_with_chars(self):
        """StrValue.strip(chars) returns StrValue."""
        s = StrValue("xxhelloxx")
        result = s.strip("x")
        assert isinstance(result, StrValue)

    def test_lstrip(self):
        """StrValue.lstrip() returns StrValue."""
        s = StrValue("  hello")
        result = s.lstrip()
        assert isinstance(result, StrValue)

    def test_rstrip(self):
        """StrValue.rstrip() returns StrValue."""
        s = StrValue("hello  ")
        result = s.rstrip()
        assert isinstance(result, StrValue)


class TestStrRefSplittingMethods:
    """StrValue splitting methods."""

    def test_split(self):
        """StrValue.split() returns ListValue."""
        s = StrValue("a,b,c")
        result = s.split(",")
        assert isinstance(result, ListValue)

    def test_split_no_sep(self):
        """StrValue.split() with no separator."""
        s = StrValue("a b c")
        result = s.split()
        assert isinstance(result, ListValue)

    def test_rsplit(self):
        """StrValue.rsplit() returns ListValue."""
        s = StrValue("a,b,c")
        result = s.rsplit(",")
        assert isinstance(result, ListValue)


class TestStrRefSearchMethods:
    """StrValue search methods."""

    def test_find(self):
        """StrValue.find() returns IntValue."""
        s = StrValue("hello world")
        result = s.find("world")
        assert isinstance(result, IntValue)

    def test_rfind(self):
        """StrValue.rfind() returns IntValue."""
        s = StrValue("hello world world")
        result = s.rfind("world")
        assert isinstance(result, IntValue)

    def test_count_substring(self):
        """StrValue.count_substring() returns IntValue."""
        s = StrValue("abcabc")
        result = s.count_substring("abc")
        assert isinstance(result, IntValue)


class TestStrRefTestMethods:
    """StrValue testing methods."""

    def test_startswith(self):
        """StrValue.startswith() returns BoolValue."""
        s = StrValue("hello")
        result = s.startswith("he")
        assert isinstance(result, BoolValue)

    def test_endswith(self):
        """StrValue.endswith() returns BoolValue."""
        s = StrValue("hello")
        result = s.endswith("lo")
        assert isinstance(result, BoolValue)

    def test_isdigit(self):
        """StrValue.isdigit() returns BoolValue."""
        s = StrValue("123")
        result = s.isdigit()
        assert isinstance(result, BoolValue)

    def test_isalpha(self):
        """StrValue.isalpha() returns BoolValue."""
        s = StrValue("abc")
        result = s.isalpha()
        assert isinstance(result, BoolValue)

    def test_isalnum(self):
        """StrValue.isalnum() returns BoolValue."""
        s = StrValue("abc123")
        result = s.isalnum()
        assert isinstance(result, BoolValue)

    def test_isspace(self):
        """StrValue.isspace() returns BoolValue."""
        s = StrValue("   ")
        result = s.isspace()
        assert isinstance(result, BoolValue)


class TestStrRefPaddingMethods:
    """StrValue padding methods."""

    def test_center(self):
        """StrValue.center() returns StrValue."""
        s = StrValue("hi")
        result = s.center(10)
        assert isinstance(result, StrValue)

    def test_ljust(self):
        """StrValue.ljust() returns StrValue."""
        s = StrValue("hi")
        result = s.ljust(10)
        assert isinstance(result, StrValue)

    def test_rjust(self):
        """StrValue.rjust() returns StrValue."""
        s = StrValue("hi")
        result = s.rjust(10)
        assert isinstance(result, StrValue)

    def test_zfill(self):
        """StrValue.zfill() returns StrValue."""
        s = StrValue("42")
        result = s.zfill(5)
        assert isinstance(result, StrValue)


class TestStrRefOtherMethods:
    """StrValue other methods."""

    def test_replace(self):
        """StrValue.replace() returns StrValue."""
        s = StrValue("hello")
        result = s.replace("l", "L")
        assert isinstance(result, StrValue)

    def test_encode(self):
        """StrValue.encode() returns BytesValue."""
        s = StrValue("hello")
        result = s.encode()
        assert isinstance(result, BytesValue)

    def test_len(self):
        """fn.Len(StrValue) returns IntValue."""
        s = StrValue("hello")
        result = fn.Len(s)
        assert isinstance(result, IntValue)

    def test_contains(self):
        """fn.Contains(StrValue, ...) returns BoolValue."""
        s = StrValue("hello")
        result = fn.Contains(s, "ell")
        assert isinstance(result, BoolValue)


class TestStrRefComparison:
    """StrValue comparison operations."""

    def test_greater_than(self):
        """StrValue > comparison."""
        s = StrValue("b")
        result = s > "a"
        assert isinstance(result, BoolValue)

    def test_less_than(self):
        """StrValue < comparison."""
        s = StrValue("a")
        result = s < "b"
        assert isinstance(result, BoolValue)

    def test_equality(self):
        """StrValue eq() method."""
        s = StrValue("hello")
        result = s.eq("hello")
        assert isinstance(result, BoolValue)


# =============================================================================
# BYTES TYPE TESTS
# =============================================================================


class TestBytesRef:
    """BytesValue operations."""

    def test_literal_creation(self):
        """BytesValue can wrap literal."""
        BytesValue(b"hello")

    def test_concatenation(self):
        """BytesValue + bytes returns BytesValue."""
        b = BytesValue(b"hello")
        result = b + b" world"
        assert isinstance(result, BytesValue)

    def test_decode(self):
        """BytesValue.decode() returns StrValue."""
        b = BytesValue(b"hello")
        result = b.decode()
        assert isinstance(result, StrValue)

    def test_hex(self):
        """BytesValue.hex_() returns StrValue."""
        b = BytesValue(b"hello")
        result = b.hex_()
        assert isinstance(result, StrValue)

    def test_upper(self):
        """BytesValue.upper() returns BytesValue."""
        b = BytesValue(b"hello")
        result = b.upper()
        assert isinstance(result, BytesValue)

    def test_lower(self):
        """BytesValue.lower() returns BytesValue."""
        b = BytesValue(b"HELLO")
        result = b.lower()
        assert isinstance(result, BytesValue)

    def test_strip(self):
        """BytesValue.strip() returns BytesValue."""
        b = BytesValue(b"  hello  ")
        result = b.strip()
        assert isinstance(result, BytesValue)

    def test_find_bytes(self):
        """BytesValue.find_bytes() returns IntValue."""
        b = BytesValue(b"hello world")
        result = b.find_bytes(b"world")
        assert isinstance(result, IntValue)

    def test_startswith(self):
        """BytesValue.startswith() returns BoolValue."""
        b = BytesValue(b"hello")
        result = b.startswith(b"he")
        assert isinstance(result, BoolValue)

    def test_len(self):
        """fn.Len(BytesValue) returns IntValue."""
        b = BytesValue(b"hello")
        result = fn.Len(b)
        assert isinstance(result, IntValue)


# =============================================================================
# LIST TYPE TESTS
# =============================================================================


class TestListRefBasic:
    """ListValue basic operations."""

    def test_literal_creation(self):
        """ListValue can wrap literal."""
        ListValue([1, 2, 3])

    def test_concatenation(self):
        """ListValue + list returns ListValue."""
        lst = ListValue([1, 2])
        result = lst + [3, 4]  # noqa: RUF005
        assert isinstance(result, ListValue)

    def test_indexing(self):
        """ListValue[int] returns AnyValue."""
        lst = ListValue([1, 2, 3])
        result = lst[0]
        assert isinstance(result, AnyValue)

    def test_slicing(self):
        """ListValue[slice] returns ListValue."""
        lst = ListValue([1, 2, 3, 4, 5])
        result = lst[1:4]
        assert isinstance(result, ListValue)


class TestListRefSequenceMethods:
    """ListValue sequence methods."""

    def test_len(self):
        """fn.Len(ListValue) returns IntValue."""
        lst = ListValue([1, 2, 3])
        result = fn.Len(lst)
        assert isinstance(result, IntValue)

    def test_contains(self):
        """fn.Contains(ListValue, ...) returns BoolValue."""
        lst = ListValue([1, 2, 3])
        result = fn.Contains(lst, 2)
        assert isinstance(result, BoolValue)

    def test_first(self):
        """ListValue.first() returns AnyValue."""
        lst = ListValue([1, 2, 3])
        result = lst.first()
        assert isinstance(result, AnyValue)

    def test_last(self):
        """ListValue.last() returns AnyValue."""
        lst = ListValue([1, 2, 3])
        result = lst.last()
        assert isinstance(result, AnyValue)

    def test_reversed(self):
        """fn.Reversed() returns IteratorValue."""
        lst = ListValue([1, 2, 3])
        result = fn.Reversed(lst)
        assert isinstance(result, IteratorValue)

    def test_sorted(self):
        """fn.Sorted() returns ListValue."""
        lst = ListValue([3, 1, 2])
        result = fn.Sorted(lst)
        assert isinstance(result, ListValue)

    def test_index(self):
        """ListValue.index() returns IntValue."""
        lst = ListValue([1, 2, 3])
        result = lst.index(2)
        assert isinstance(result, IntValue)

    def test_count(self):
        """ListValue.count() returns IntValue."""
        lst = ListValue([1, 2, 2, 3])
        result = lst.count(2)
        assert isinstance(result, IntValue)


class TestStandaloneFnMethods:
    """Standalone fn module methods (previously on IterableBase)."""

    def test_sum(self):
        """fn.Sum() returns AnyValue."""
        lst = ListValue([1, 2, 3])
        result = fn.Sum(lst)
        assert isinstance(result, AnyValue)

    def test_min(self):
        """fn.Min() returns AnyValue."""
        lst = ListValue([3, 1, 2])
        result = fn.Min(lst)
        assert isinstance(result, AnyValue)

    def test_max(self):
        """fn.Max() returns AnyValue."""
        lst = ListValue([3, 1, 2])
        result = fn.Max(lst)
        assert isinstance(result, AnyValue)

    def test_any(self):
        """fn.Any() returns BoolValue."""
        lst = ListValue([False, True, False])
        result = fn.Any(lst)
        assert isinstance(result, BoolValue)

    def test_all(self):
        """fn.All() returns BoolValue."""
        lst = ListValue([True, True, True])
        result = fn.All(lst)
        assert isinstance(result, BoolValue)


# =============================================================================
# TUPLE TYPE TESTS
# =============================================================================


class TestTupleRef:
    """TupleValue operations."""

    def test_literal_creation(self):
        """TupleValue can wrap literal."""
        TupleValue((1, 2, 3))

    def test_indexing(self):
        """TupleValue[int] returns AnyValue."""
        t = TupleValue((1, 2, 3))
        result = t[0]
        assert isinstance(result, AnyValue)

    def test_slicing(self):
        """TupleValue[slice] returns TupleValue."""
        t = TupleValue((1, 2, 3, 4, 5))
        result = t[1:4]
        # TupleValue slicing returns TupleValue (not ListValue)
        assert isinstance(result, TupleValue)

    def test_len(self):
        """fn.Len(TupleValue) returns IntValue."""
        t = TupleValue((1, 2, 3))
        result = fn.Len(t)
        assert isinstance(result, IntValue)

    def test_contains(self):
        """fn.Contains(TupleValue, ...) returns BoolValue."""
        t = TupleValue((1, 2, 3))
        result = fn.Contains(t, 2)
        assert isinstance(result, BoolValue)


# =============================================================================
# DICT TYPE TESTS
# =============================================================================


class TestDictRef:
    """DictValue operations."""

    def test_literal_creation(self):
        """DictValue can wrap literal."""
        DictValue({"a": 1, "b": 2})

    def test_key_access(self):
        """DictValue[key] returns AnyValue."""
        d = DictValue({"a": 1, "b": 2})
        result = d["a"]
        assert isinstance(result, AnyValue)

    def test_len(self):
        """fn.Len(DictValue) returns IntValue."""
        d = DictValue({"a": 1, "b": 2})
        result = fn.Len(d)
        assert isinstance(result, IntValue)

    def test_contains(self):
        """fn.Contains(DictValue, ...) returns BoolValue."""
        d = DictValue({"a": 1, "b": 2})
        result = fn.Contains(d, "a")
        assert isinstance(result, BoolValue)

    def test_keys(self):
        """DictValue.keys() returns DictKeysValue."""
        d = DictValue({"a": 1, "b": 2})
        result = d.keys()
        assert isinstance(result, DictKeysValue)

    def test_values(self):
        """DictValue.values() returns DictValuesValue."""
        d = DictValue({"a": 1, "b": 2})
        result = d.values()
        assert isinstance(result, DictValuesValue)

    def test_items(self):
        """DictValue.items() returns DictItemsValue."""
        d = DictValue({"a": 1, "b": 2})
        result = d.items()
        assert isinstance(result, DictItemsValue)

    def test_get(self):
        """DictValue.get() returns AnyValue."""
        d = DictValue({"a": 1, "b": 2})
        result = d.get("a", 0)
        assert isinstance(result, AnyValue)


# =============================================================================
# SET TYPE TESTS
# =============================================================================


class TestSetRef:
    """SetValue operations."""

    def test_literal_creation(self):
        """SetValue can wrap literal."""
        SetValue({1, 2, 3})

    def test_len(self):
        """fn.Len(SetValue) returns IntValue."""
        s = SetValue({1, 2, 3})
        result = fn.Len(s)
        assert isinstance(result, IntValue)

    def test_contains(self):
        """fn.Contains(SetValue, ...) returns BoolValue."""
        s = SetValue({1, 2, 3})
        result = fn.Contains(s, 2)
        assert isinstance(result, BoolValue)

    def test_union(self):
        """SetValue.union() returns SetValue."""
        s = SetValue({1, 2})
        result = s.union({3, 4})
        assert isinstance(result, SetValue)

    def test_intersection(self):
        """SetValue.intersection() returns SetValue."""
        s = SetValue({1, 2, 3})
        result = s.intersection({2, 3, 4})
        assert isinstance(result, SetValue)

    def test_difference(self):
        """SetValue.difference() returns SetValue."""
        s = SetValue({1, 2, 3})
        result = s.difference({2, 3})
        assert isinstance(result, SetValue)

    def test_symmetric_difference(self):
        """SetValue.symmetric_difference() returns SetValue."""
        s = SetValue({1, 2, 3})
        result = s.symmetric_difference({2, 3, 4})
        assert isinstance(result, SetValue)

    def test_issubset(self):
        """SetValue.issubset() returns BoolValue."""
        s = SetValue({1, 2})
        result = s.issubset({1, 2, 3})
        assert isinstance(result, BoolValue)

    def test_issuperset(self):
        """SetValue.issuperset() returns BoolValue."""
        s = SetValue({1, 2, 3})
        result = s.issuperset({1, 2})
        assert isinstance(result, BoolValue)

    def test_isdisjoint(self):
        """SetValue.isdisjoint() returns BoolValue."""
        s = SetValue({1, 2})
        result = s.isdisjoint({3, 4})
        assert isinstance(result, BoolValue)


class TestFrozenSetRef:
    """FrozenSetValue operations."""

    def test_literal_creation(self):
        """FrozenSetValue can wrap literal."""
        FrozenSetValue(frozenset({1, 2, 3}))

    def test_union(self):
        """FrozenSetValue.union() returns FrozenSetValue."""
        s = FrozenSetValue(frozenset({1, 2}))
        result = s.union(frozenset({3, 4}))
        assert isinstance(result, FrozenSetValue)


# =============================================================================
# NONE TYPE TESTS
# =============================================================================


class TestNoneRef:
    """NoneValue operations."""

    def test_default_creation(self):
        """NoneValue() creates None literal."""
        _ = NoneValue()

    def test_is_empty(self):
        """NoneValue.is_empty() returns BoolValue."""
        n = NoneValue()
        result = n.is_empty()
        assert isinstance(result, BoolValue)

    def test_logical_and(self):
        """NoneValue.and_() works."""
        n = NoneValue()
        result = n.and_(BoolValue(True))
        assert isinstance(result, BoolValue)


# =============================================================================
# ANY TYPE TESTS
# =============================================================================


class TestAnyRef:
    """AnyValue operations."""

    def test_literal_creation(self):
        """AnyValue can wrap literal."""
        AnyValue(42)

    def test_arithmetic(self):
        """AnyValue supports arithmetic."""
        a = AnyValue(10)
        result = a + 5
        assert isinstance(result, AnyValue)

    def test_comparison(self):
        """AnyValue supports comparison."""
        a = AnyValue(10)
        result = a > 5
        assert isinstance(result, BoolValue)

    def test_logical(self):
        """AnyValue supports logical."""
        a = AnyValue(True)
        result = a.and_(False)
        assert isinstance(result, BoolValue)

    def test_bitwise(self):
        """AnyValue supports bitwise."""
        a = AnyValue(0b1100)
        result = a.bitand(0b1010)
        assert isinstance(result, AnyValue)


# =============================================================================
# ENSURE_TERM FUNCTION TESTS
# =============================================================================


class TestEnsureTermFunction:
    """ensure_term() function comprehensive tests."""

    def test_int(self):
        """ensure_term(int) returns IntValue."""
        result = ensure_term(42)
        assert isinstance(result, IntValue)

    def test_float(self):
        """ensure_term(float) returns FloatValue."""
        result = ensure_term(3.14)
        assert isinstance(result, FloatValue)

    def test_bool_true(self):
        """ensure_term(True) returns BoolValue (not IntValue)."""
        result = ensure_term(True)
        assert isinstance(result, BoolValue)

    def test_bool_false(self):
        """ensure_term(False) returns BoolValue."""
        result = ensure_term(False)
        assert isinstance(result, BoolValue)

    def test_str(self):
        """ensure_term(str) returns StrValue."""
        result = ensure_term("hello")
        assert isinstance(result, StrValue)

    def test_bytes(self):
        """ensure_term(bytes) returns BytesValue."""
        result = ensure_term(b"hello")
        assert isinstance(result, BytesValue)

    def test_none(self):
        """ensure_term(None) returns NoneValue."""
        result = ensure_term(None)
        assert isinstance(result, NoneValue)

    def test_list(self):
        """ensure_term(list) returns ListValue."""
        result = ensure_term([1, 2, 3])
        assert isinstance(result, ListValue)

    def test_tuple(self):
        """ensure_term(tuple) returns TupleValue."""
        result = ensure_term((1, 2, 3))
        assert isinstance(result, TupleValue)

    def test_dict(self):
        """ensure_term(dict) returns DictValue."""
        result = ensure_term({"a": 1})
        assert isinstance(result, DictValue)

    def test_set(self):
        """ensure_term(set) returns SetValue."""
        result = ensure_term({1, 2, 3})
        assert isinstance(result, SetValue)

    def test_frozenset(self):
        """ensure_term(frozenset) returns FrozenSetValue."""
        result = ensure_term(frozenset({1, 2, 3}))
        assert isinstance(result, FrozenSetValue)

    def test_passthrough_term(self):
        """ensure_term(Term) returns Term unchanged."""
        original = IntValue(42)
        result = ensure_term(original)
        assert result is original

    def test_unsupported_type(self):
        """ensure_term(unsupported) raises TypeError."""
        with pytest.raises(TypeError, match="Not supported type"):
            ensure_term(object())


# =============================================================================
# BLOCKED OPERATORS
# =============================================================================


class TestBlockedOperators:
    """Tests for operators that are intentionally blocked."""

    def test_eq_blocked(self):
        """Using == on Terms raises TypeError."""
        x = IntValue(10)
        y = IntValue(10)
        with pytest.raises(TypeError, match="Cannot use =="):
            _ = x == y

    def test_ne_blocked(self):
        """Using != on Terms raises TypeError."""
        x = IntValue(10)
        y = IntValue(5)
        with pytest.raises(TypeError, match="Cannot use !="):
            _ = x != y

    def test_eq_method_works(self):
        """The eq() method works for equality checks."""
        x = IntValue(10)
        result = x.eq(10)
        assert isinstance(result, BoolValue)

    def test_ne_method_works(self):
        """The ne() method works for inequality checks."""
        x = IntValue(10)
        result = x.ne(5)
        assert isinstance(result, BoolValue)
