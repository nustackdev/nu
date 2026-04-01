"""Comprehensive unit tests for all Nu types.

Tests type construction, operations, and method availability for:
- IntI, FloatI, BoolI (numeric/boolean)
- StrI, BytesI (text/binary)
- ListI, TupleI, DictI, SetI, FrozenSetI (collections)
- NoneI, AnyI (special types)
"""

import pytest

from nu import (
    AnyI,
    BoolI,
    BytesI,
    DictItemsI,
    DictKeysI,
    DictI,
    DictValuesI,
    FloatI,
    FrozenSetI,
    IntI,
    IteratorI,
    ListI,
    NoneI,
    SetI,
    StrI,
    ToBoolOp,
    ToFloatOp,
    ToIntOp,
    ToStrOp,
    TupleI,
    ensure_nu,
    fn,
)


# =============================================================================
# INT TYPE TESTS
# =============================================================================


class TestIntRefArithmetic:
    """IntI arithmetic operations."""

    def test_addition_int_int(self):
        """int + int returns IntI."""
        x = IntI(10)
        result = x + 5
        assert isinstance(result, IntI)

    def test_addition_int_inttype(self):
        """IntI + IntI returns IntI."""
        x = IntI(10)
        y = IntI(5)
        result = x + y
        assert isinstance(result, IntI)

    def test_addition_int_float(self):
        """int + float returns FloatI."""
        x = IntI(10)
        result = x + 2.5
        assert isinstance(result, FloatI)

    def test_radd(self):
        """5 + IntI works via __radd__."""
        x = IntI(10)
        result = 5 + x
        assert isinstance(result, IntI)

    def test_subtraction(self):
        """IntI subtraction."""
        x = IntI(10)
        result = x - 3
        assert isinstance(result, IntI)

    def test_rsub(self):
        """20 - IntI works."""
        x = IntI(10)
        result = 20 - x
        assert isinstance(result, IntI)

    def test_multiplication(self):
        """IntI multiplication."""
        x = IntI(6)
        result = x * 7
        assert isinstance(result, IntI)

    def test_rmul(self):
        """7 * IntI works."""
        x = IntI(6)
        result = 7 * x
        assert isinstance(result, IntI)

    def test_division(self):
        """IntI division always returns FloatI."""
        x = IntI(10)
        result = x / 3
        assert isinstance(result, FloatI)

    def test_rdiv(self):
        """30 / IntI works."""
        x = IntI(10)
        result = 30 / x
        assert isinstance(result, FloatI)

    def test_floor_division(self):
        """IntI floor division."""
        x = IntI(10)
        result = x // 3
        assert isinstance(result, IntI)

    def test_rfloordiv(self):
        """30 // IntI works."""
        x = IntI(10)
        result = 30 // x
        assert isinstance(result, IntI)

    def test_modulo(self):
        """IntI modulo."""
        x = IntI(10)
        result = x % 3
        assert isinstance(result, IntI)

    def test_rmod(self):
        """30 % IntI works."""
        x = IntI(7)
        result = 30 % x
        assert isinstance(result, IntI)

    def test_power(self):
        """IntI power."""
        x = IntI(2)
        result = x**10
        assert isinstance(result, IntI)

    def test_rpow(self):
        """2 ** IntI works."""
        x = IntI(10)
        result = 2**x
        assert isinstance(result, IntI)

    def test_negation(self):
        """IntI negation."""
        x = IntI(42)
        result = -x
        assert isinstance(result, IntI)

    def test_positive(self):
        """IntI unary plus."""
        x = IntI(42)
        result = +x
        assert isinstance(result, IntI)

    def test_absolute(self):
        """IntI absolute value."""
        x = IntI(-42)
        result = abs(x)
        assert isinstance(result, IntI)


class TestIntRefBitwise:
    """IntI bitwise operations."""

    def test_bitwise_and(self):
        """IntI bitand() method."""
        x = IntI(0b1100)
        result = x.bitand(0b1010)
        assert isinstance(result, IntI)

    def test_bitwise_or(self):
        """IntI bitor() method."""
        x = IntI(0b1100)
        result = x.bitor(0b1010)
        assert isinstance(result, IntI)

    def test_bitwise_xor(self):
        """IntI xor via ^."""
        x = IntI(0b1100)
        result = x ^ 0b1010
        assert isinstance(result, IntI)

    def test_bitwise_not(self):
        """IntI bitnot() method."""
        x = IntI(0b1100)
        result = x.bitnot()
        assert isinstance(result, IntI)

    def test_left_shift(self):
        """IntI left shift."""
        x = IntI(1)
        result = x << 4
        assert isinstance(result, IntI)

    def test_right_shift(self):
        """IntI right shift."""
        x = IntI(16)
        result = x >> 2
        assert isinstance(result, IntI)


class TestIntRefComparison:
    """IntI comparison operations."""

    def test_greater_than(self):
        """IntI > comparison."""
        x = IntI(10)
        result = x > 5
        assert isinstance(result, BoolI)

    def test_less_than(self):
        """IntI < comparison."""
        x = IntI(10)
        result = x < 20
        assert isinstance(result, BoolI)

    def test_greater_equal(self):
        """IntI >= comparison."""
        x = IntI(10)
        result = x >= 10
        assert isinstance(result, BoolI)

    def test_less_equal(self):
        """IntI <= comparison."""
        x = IntI(10)
        result = x <= 10
        assert isinstance(result, BoolI)

    def test_equality_method(self):
        """IntI eq() method."""
        x = IntI(10)
        result = x.eq(10)
        assert isinstance(result, BoolI)

    def test_inequality_method(self):
        """IntI ne() method."""
        x = IntI(10)
        result = x.ne(5)
        assert isinstance(result, BoolI)

    def test_identity_method(self):
        """IntI is_() method."""
        x = IntI(10)
        result = x.is_(10)
        assert isinstance(result, BoolI)


class TestIntRefLogical:
    """IntI logical operations."""

    def test_and(self):
        """IntI and_() method."""
        x = IntI(1)
        result = x.and_(IntI(2))
        assert isinstance(result, BoolI)

    def test_or(self):
        """IntI or_() method."""
        x = IntI(0)
        result = x.or_(IntI(1))
        assert isinstance(result, BoolI)

    def test_not(self):
        """IntI not_() method."""
        x = IntI(0)
        result = x.not_()
        assert isinstance(result, BoolI)

    def test_bool_method(self):
        """IntI bool_() method."""
        x = IntI(42)
        result = x.bool_()
        assert isinstance(result, BoolI)


class TestIntRefConversions:
    """IntI type conversion via standalone morphisms."""

    def test_to_float(self):
        """ToFloatOp wrapping returns FloatI."""
        x = IntI(42)
        result = FloatI(ToFloatOp(x))
        assert isinstance(result, FloatI)

    def test_to_str(self):
        """ToStrOp wrapping returns StrI."""
        x = IntI(42)
        result = StrI(ToStrOp(x))
        assert isinstance(result, StrI)

    def test_to_bool(self):
        """ToBoolOp wrapping returns BoolI."""
        x = IntI(42)
        result = BoolI(ToBoolOp(x))
        assert isinstance(result, BoolI)


class TestIntRefSpecialChecks:
    """IntI special value checks."""

    def test_is_empty(self):
        """IntI.is_empty() returns BoolI."""
        x = IntI(42)
        result = x.is_empty()
        assert isinstance(result, BoolI)

    def test_is_invalid(self):
        """IntI.is_invalid() returns BoolI."""
        x = IntI(42)
        result = x.is_invalid()
        assert isinstance(result, BoolI)

    def test_is_sentinel(self):
        """IntI.is_sentinel() returns BoolI."""
        x = IntI(42)
        result = x.is_sentinel()
        assert isinstance(result, BoolI)

    def test_not_empty(self):
        """IntI.not_empty() returns BoolI."""
        x = IntI(42)
        result = x.not_empty()
        assert isinstance(result, BoolI)

    def test_not_invalid(self):
        """IntI.not_invalid() returns BoolI."""
        x = IntI(42)
        result = x.not_invalid()
        assert isinstance(result, BoolI)


# =============================================================================
# FLOAT TYPE TESTS
# =============================================================================


class TestFloatRef:
    """FloatI operations."""

    def test_literal_creation(self):
        """FloatI can wrap literal."""
        FloatI(3.14)

    def test_addition(self):
        """FloatI addition."""
        f = FloatI(1.5)
        result = f + 2.5
        assert isinstance(result, FloatI)

    def test_subtraction(self):
        """FloatI subtraction."""
        f = FloatI(5.0)
        result = f - 2.0
        assert isinstance(result, FloatI)

    def test_multiplication(self):
        """FloatI multiplication."""
        f = FloatI(2.5)
        result = f * 4.0
        assert isinstance(result, FloatI)

    def test_division(self):
        """FloatI division."""
        f = FloatI(10.0)
        result = f / 4.0
        assert isinstance(result, FloatI)

    def test_floor_division(self):
        """FloatI floor division."""
        f = FloatI(10.0)
        result = f // 3.0
        assert isinstance(result, FloatI)

    def test_modulo(self):
        """FloatI modulo."""
        f = FloatI(10.0)
        result = f % 3.0
        assert isinstance(result, FloatI)

    def test_power(self):
        """FloatI power."""
        f = FloatI(2.0)
        result = f**3.0
        assert isinstance(result, FloatI)

    def test_negation(self):
        """FloatI negation."""
        f = FloatI(3.14)
        result = -f
        assert isinstance(result, FloatI)

    def test_comparison(self):
        """FloatI comparison."""
        f = FloatI(3.14)
        result = f > 3.0
        assert isinstance(result, BoolI)

    def test_to_int(self):
        """ToIntOp wrapping returns IntI."""
        f = FloatI(3.14)
        result = IntI(ToIntOp(f))
        assert isinstance(result, IntI)


# =============================================================================
# BOOL TYPE TESTS
# =============================================================================


class TestBoolRef:
    """BoolI operations."""

    def test_literal_creation_true(self):
        """BoolI can wrap True."""
        BoolI(True)

    def test_literal_creation_false(self):
        """BoolI can wrap False."""
        BoolI(False)

    def test_and_operation(self):
        """BoolI and_() method."""
        a = BoolI(True)
        b = BoolI(False)
        result = a.and_(b)
        assert isinstance(result, BoolI)

    def test_or_operation(self):
        """BoolI or_() method."""
        a = BoolI(True)
        b = BoolI(False)
        result = a.or_(b)
        assert isinstance(result, BoolI)

    def test_not_operation(self):
        """BoolI not_() method."""
        a = BoolI(True)
        result = a.not_()
        assert isinstance(result, BoolI)

    def test_bool_method(self):
        """BoolI bool_() method."""
        a = BoolI(True)
        result = a.bool_()
        assert isinstance(result, BoolI)

    def test_comparison(self):
        """BoolI comparison."""
        a = BoolI(True)
        result = a > BoolI(False)
        assert isinstance(result, BoolI)

    def test_equality(self):
        """BoolI eq() method."""
        a = BoolI(True)
        result = a.eq(True)
        assert isinstance(result, BoolI)


# =============================================================================
# STR TYPE TESTS
# =============================================================================


class TestStrRefBasic:
    """StrI basic operations."""

    def test_literal_creation(self):
        """StrI can wrap literal."""
        StrI("hello")

    def test_concatenation(self):
        """StrI + str returns StrI."""
        s = StrI("hello")
        result = s + " world"
        assert isinstance(result, StrI)

    def test_radd(self):
        """str + StrI works."""
        s = StrI("world")
        result = "hello " + s
        assert isinstance(result, StrI)


class TestStrRefCaseMethods:
    """StrI case transformation methods."""

    def test_upper(self):
        """StrI.upper() returns StrI."""
        s = StrI("hello")
        result = s.upper()
        assert isinstance(result, StrI)

    def test_lower(self):
        """StrI.lower() returns StrI."""
        s = StrI("HELLO")
        result = s.lower()
        assert isinstance(result, StrI)

    def test_title(self):
        """StrI.title() returns StrI."""
        s = StrI("hello world")
        result = s.title()
        assert isinstance(result, StrI)

    def test_capitalize(self):
        """StrI.capitalize() returns StrI."""
        s = StrI("hello")
        result = s.capitalize()
        assert isinstance(result, StrI)

    def test_swapcase(self):
        """StrI.swapcase() returns StrI."""
        s = StrI("HeLLo")
        result = s.swapcase()
        assert isinstance(result, StrI)


class TestStrRefStrippingMethods:
    """StrI stripping methods."""

    def test_strip(self):
        """StrI.strip() returns StrI."""
        s = StrI("  hello  ")
        result = s.strip()
        assert isinstance(result, StrI)

    def test_strip_with_chars(self):
        """StrI.strip(chars) returns StrI."""
        s = StrI("xxhelloxx")
        result = s.strip("x")
        assert isinstance(result, StrI)

    def test_lstrip(self):
        """StrI.lstrip() returns StrI."""
        s = StrI("  hello")
        result = s.lstrip()
        assert isinstance(result, StrI)

    def test_rstrip(self):
        """StrI.rstrip() returns StrI."""
        s = StrI("hello  ")
        result = s.rstrip()
        assert isinstance(result, StrI)


class TestStrRefSplittingMethods:
    """StrI splitting methods."""

    def test_split(self):
        """StrI.split() returns ListI."""
        s = StrI("a,b,c")
        result = s.split(",")
        assert isinstance(result, ListI)

    def test_split_no_sep(self):
        """StrI.split() with no separator."""
        s = StrI("a b c")
        result = s.split()
        assert isinstance(result, ListI)

    def test_rsplit(self):
        """StrI.rsplit() returns ListI."""
        s = StrI("a,b,c")
        result = s.rsplit(",")
        assert isinstance(result, ListI)


class TestStrRefSearchMethods:
    """StrI search methods."""

    def test_find(self):
        """StrI.find() returns IntI."""
        s = StrI("hello world")
        result = s.find("world")
        assert isinstance(result, IntI)

    def test_rfind(self):
        """StrI.rfind() returns IntI."""
        s = StrI("hello world world")
        result = s.rfind("world")
        assert isinstance(result, IntI)

    def test_count_substring(self):
        """StrI.count_substring() returns IntI."""
        s = StrI("abcabc")
        result = s.count_substring("abc")
        assert isinstance(result, IntI)


class TestStrRefTestMethods:
    """StrI testing methods."""

    def test_startswith(self):
        """StrI.startswith() returns BoolI."""
        s = StrI("hello")
        result = s.startswith("he")
        assert isinstance(result, BoolI)

    def test_endswith(self):
        """StrI.endswith() returns BoolI."""
        s = StrI("hello")
        result = s.endswith("lo")
        assert isinstance(result, BoolI)

    def test_isdigit(self):
        """StrI.isdigit() returns BoolI."""
        s = StrI("123")
        result = s.isdigit()
        assert isinstance(result, BoolI)

    def test_isalpha(self):
        """StrI.isalpha() returns BoolI."""
        s = StrI("abc")
        result = s.isalpha()
        assert isinstance(result, BoolI)

    def test_isalnum(self):
        """StrI.isalnum() returns BoolI."""
        s = StrI("abc123")
        result = s.isalnum()
        assert isinstance(result, BoolI)

    def test_isspace(self):
        """StrI.isspace() returns BoolI."""
        s = StrI("   ")
        result = s.isspace()
        assert isinstance(result, BoolI)


class TestStrRefPaddingMethods:
    """StrI padding methods."""

    def test_center(self):
        """StrI.center() returns StrI."""
        s = StrI("hi")
        result = s.center(10)
        assert isinstance(result, StrI)

    def test_ljust(self):
        """StrI.ljust() returns StrI."""
        s = StrI("hi")
        result = s.ljust(10)
        assert isinstance(result, StrI)

    def test_rjust(self):
        """StrI.rjust() returns StrI."""
        s = StrI("hi")
        result = s.rjust(10)
        assert isinstance(result, StrI)

    def test_zfill(self):
        """StrI.zfill() returns StrI."""
        s = StrI("42")
        result = s.zfill(5)
        assert isinstance(result, StrI)


class TestStrRefOtherMethods:
    """StrI other methods."""

    def test_replace(self):
        """StrI.replace() returns StrI."""
        s = StrI("hello")
        result = s.replace("l", "L")
        assert isinstance(result, StrI)

    def test_encode(self):
        """StrI.encode() returns BytesI."""
        s = StrI("hello")
        result = s.encode()
        assert isinstance(result, BytesI)

    def test_len(self):
        """fn.Len(StrI) returns IntI."""
        s = StrI("hello")
        result = fn.Len(s)
        assert isinstance(result, IntI)

    def test_contains(self):
        """fn.Contains(StrI, ...) returns BoolI."""
        s = StrI("hello")
        result = fn.Contains(s, "ell")
        assert isinstance(result, BoolI)


class TestStrRefComparison:
    """StrI comparison operations."""

    def test_greater_than(self):
        """StrI > comparison."""
        s = StrI("b")
        result = s > "a"
        assert isinstance(result, BoolI)

    def test_less_than(self):
        """StrI < comparison."""
        s = StrI("a")
        result = s < "b"
        assert isinstance(result, BoolI)

    def test_equality(self):
        """StrI eq() method."""
        s = StrI("hello")
        result = s.eq("hello")
        assert isinstance(result, BoolI)


# =============================================================================
# BYTES TYPE TESTS
# =============================================================================


class TestBytesRef:
    """BytesI operations."""

    def test_literal_creation(self):
        """BytesI can wrap literal."""
        BytesI(b"hello")

    def test_concatenation(self):
        """BytesI + bytes returns BytesI."""
        b = BytesI(b"hello")
        result = b + b" world"
        assert isinstance(result, BytesI)

    def test_decode(self):
        """BytesI.decode() returns StrI."""
        b = BytesI(b"hello")
        result = b.decode()
        assert isinstance(result, StrI)

    def test_hex(self):
        """BytesI.hex_() returns StrI."""
        b = BytesI(b"hello")
        result = b.hex_()
        assert isinstance(result, StrI)

    def test_upper(self):
        """BytesI.upper() returns BytesI."""
        b = BytesI(b"hello")
        result = b.upper()
        assert isinstance(result, BytesI)

    def test_lower(self):
        """BytesI.lower() returns BytesI."""
        b = BytesI(b"HELLO")
        result = b.lower()
        assert isinstance(result, BytesI)

    def test_strip(self):
        """BytesI.strip() returns BytesI."""
        b = BytesI(b"  hello  ")
        result = b.strip()
        assert isinstance(result, BytesI)

    def test_find_bytes(self):
        """BytesI.find_bytes() returns IntI."""
        b = BytesI(b"hello world")
        result = b.find_bytes(b"world")
        assert isinstance(result, IntI)

    def test_startswith(self):
        """BytesI.startswith() returns BoolI."""
        b = BytesI(b"hello")
        result = b.startswith(b"he")
        assert isinstance(result, BoolI)

    def test_len(self):
        """fn.Len(BytesI) returns IntI."""
        b = BytesI(b"hello")
        result = fn.Len(b)
        assert isinstance(result, IntI)


# =============================================================================
# LIST TYPE TESTS
# =============================================================================


class TestListRefBasic:
    """ListI basic operations."""

    def test_literal_creation(self):
        """ListI can wrap literal."""
        ListI([1, 2, 3])

    def test_concatenation(self):
        """ListI + list returns ListI."""
        lst = ListI([1, 2])
        result = lst + [3, 4]  # noqa: RUF005
        assert isinstance(result, ListI)

    def test_indexing(self):
        """ListI[int] returns AnyI."""
        lst = ListI([1, 2, 3])
        result = lst[0]
        assert isinstance(result, AnyI)

    def test_slicing(self):
        """ListI[slice] returns ListI."""
        lst = ListI([1, 2, 3, 4, 5])
        result = lst[1:4]
        assert isinstance(result, ListI)


class TestListRefSequenceMethods:
    """ListI sequence methods."""

    def test_len(self):
        """fn.Len(ListI) returns IntI."""
        lst = ListI([1, 2, 3])
        result = fn.Len(lst)
        assert isinstance(result, IntI)

    def test_contains(self):
        """fn.Contains(ListI, ...) returns BoolI."""
        lst = ListI([1, 2, 3])
        result = fn.Contains(lst, 2)
        assert isinstance(result, BoolI)

    def test_first(self):
        """ListI.first() returns AnyI."""
        lst = ListI([1, 2, 3])
        result = lst.first()
        assert isinstance(result, AnyI)

    def test_last(self):
        """ListI.last() returns AnyI."""
        lst = ListI([1, 2, 3])
        result = lst.last()
        assert isinstance(result, AnyI)

    def test_reversed(self):
        """fn.Reversed() returns IteratorI."""
        lst = ListI([1, 2, 3])
        result = fn.Reversed(lst)
        assert isinstance(result, IteratorI)

    def test_sorted(self):
        """fn.Sorted() returns ListI."""
        lst = ListI([3, 1, 2])
        result = fn.Sorted(lst)
        assert isinstance(result, ListI)

    def test_index(self):
        """ListI.index() returns IntI."""
        lst = ListI([1, 2, 3])
        result = lst.index(2)
        assert isinstance(result, IntI)

    def test_count(self):
        """ListI.count() returns IntI."""
        lst = ListI([1, 2, 2, 3])
        result = lst.count(2)
        assert isinstance(result, IntI)


class TestStandaloneFnMethods:
    """Standalone fn module methods (previously on IterableBase)."""

    def test_sum(self):
        """fn.Sum() returns AnyI."""
        lst = ListI([1, 2, 3])
        result = fn.Sum(lst)
        assert isinstance(result, AnyI)

    def test_min(self):
        """fn.Min() returns AnyI."""
        lst = ListI([3, 1, 2])
        result = fn.Min(lst)
        assert isinstance(result, AnyI)

    def test_max(self):
        """fn.Max() returns AnyI."""
        lst = ListI([3, 1, 2])
        result = fn.Max(lst)
        assert isinstance(result, AnyI)

    def test_any(self):
        """fn.Any() returns BoolI."""
        lst = ListI([False, True, False])
        result = fn.Any(lst)
        assert isinstance(result, BoolI)

    def test_all(self):
        """fn.All() returns BoolI."""
        lst = ListI([True, True, True])
        result = fn.All(lst)
        assert isinstance(result, BoolI)


# =============================================================================
# TUPLE TYPE TESTS
# =============================================================================


class TestTupleRef:
    """TupleI operations."""

    def test_literal_creation(self):
        """TupleI can wrap literal."""
        TupleI((1, 2, 3))

    def test_indexing(self):
        """TupleI[int] returns AnyI."""
        t = TupleI((1, 2, 3))
        result = t[0]
        assert isinstance(result, AnyI)

    def test_slicing(self):
        """TupleI[slice] returns TupleI."""
        t = TupleI((1, 2, 3, 4, 5))
        result = t[1:4]
        # TupleI slicing returns TupleI (not ListI)
        assert isinstance(result, TupleI)

    def test_len(self):
        """fn.Len(TupleI) returns IntI."""
        t = TupleI((1, 2, 3))
        result = fn.Len(t)
        assert isinstance(result, IntI)

    def test_contains(self):
        """fn.Contains(TupleI, ...) returns BoolI."""
        t = TupleI((1, 2, 3))
        result = fn.Contains(t, 2)
        assert isinstance(result, BoolI)


# =============================================================================
# DICT TYPE TESTS
# =============================================================================


class TestDictRef:
    """DictI operations."""

    def test_literal_creation(self):
        """DictI can wrap literal."""
        DictI({"a": 1, "b": 2})

    def test_key_access(self):
        """DictI[key] returns AnyI."""
        d = DictI({"a": 1, "b": 2})
        result = d["a"]
        assert isinstance(result, AnyI)

    def test_len(self):
        """fn.Len(DictI) returns IntI."""
        d = DictI({"a": 1, "b": 2})
        result = fn.Len(d)
        assert isinstance(result, IntI)

    def test_contains(self):
        """fn.Contains(DictI, ...) returns BoolI."""
        d = DictI({"a": 1, "b": 2})
        result = fn.Contains(d, "a")
        assert isinstance(result, BoolI)

    def test_keys(self):
        """DictI.keys() returns DictKeysI."""
        d = DictI({"a": 1, "b": 2})
        result = d.keys()
        assert isinstance(result, DictKeysI)

    def test_values(self):
        """DictI.values() returns DictValuesI."""
        d = DictI({"a": 1, "b": 2})
        result = d.values()
        assert isinstance(result, DictValuesI)

    def test_items(self):
        """DictI.items() returns DictItemsI."""
        d = DictI({"a": 1, "b": 2})
        result = d.items()
        assert isinstance(result, DictItemsI)

    def test_get(self):
        """DictI.get() returns AnyI."""
        d = DictI({"a": 1, "b": 2})
        result = d.get("a", 0)
        assert isinstance(result, AnyI)


# =============================================================================
# SET TYPE TESTS
# =============================================================================


class TestSetRef:
    """SetI operations."""

    def test_literal_creation(self):
        """SetI can wrap literal."""
        SetI({1, 2, 3})

    def test_len(self):
        """fn.Len(SetI) returns IntI."""
        s = SetI({1, 2, 3})
        result = fn.Len(s)
        assert isinstance(result, IntI)

    def test_contains(self):
        """fn.Contains(SetI, ...) returns BoolI."""
        s = SetI({1, 2, 3})
        result = fn.Contains(s, 2)
        assert isinstance(result, BoolI)

    def test_union(self):
        """SetI.union() returns SetI."""
        s = SetI({1, 2})
        result = s.union({3, 4})
        assert isinstance(result, SetI)

    def test_intersection(self):
        """SetI.intersection() returns SetI."""
        s = SetI({1, 2, 3})
        result = s.intersection({2, 3, 4})
        assert isinstance(result, SetI)

    def test_difference(self):
        """SetI.difference() returns SetI."""
        s = SetI({1, 2, 3})
        result = s.difference({2, 3})
        assert isinstance(result, SetI)

    def test_symmetric_difference(self):
        """SetI.symmetric_difference() returns SetI."""
        s = SetI({1, 2, 3})
        result = s.symmetric_difference({2, 3, 4})
        assert isinstance(result, SetI)

    def test_issubset(self):
        """SetI.issubset() returns BoolI."""
        s = SetI({1, 2})
        result = s.issubset({1, 2, 3})
        assert isinstance(result, BoolI)

    def test_issuperset(self):
        """SetI.issuperset() returns BoolI."""
        s = SetI({1, 2, 3})
        result = s.issuperset({1, 2})
        assert isinstance(result, BoolI)

    def test_isdisjoint(self):
        """SetI.isdisjoint() returns BoolI."""
        s = SetI({1, 2})
        result = s.isdisjoint({3, 4})
        assert isinstance(result, BoolI)


class TestFrozenSetRef:
    """FrozenSetI operations."""

    def test_literal_creation(self):
        """FrozenSetI can wrap literal."""
        FrozenSetI(frozenset({1, 2, 3}))

    def test_union(self):
        """FrozenSetI.union() returns FrozenSetI."""
        s = FrozenSetI(frozenset({1, 2}))
        result = s.union(frozenset({3, 4}))
        assert isinstance(result, FrozenSetI)


# =============================================================================
# NONE TYPE TESTS
# =============================================================================


class TestNoneRef:
    """NoneI operations."""

    def test_default_creation(self):
        """NoneI() creates None literal."""
        _ = NoneI()

    def test_is_empty(self):
        """NoneI.is_empty() returns BoolI."""
        n = NoneI()
        result = n.is_empty()
        assert isinstance(result, BoolI)

    def test_logical_and(self):
        """NoneI.and_() works."""
        n = NoneI()
        result = n.and_(BoolI(True))
        assert isinstance(result, BoolI)


# =============================================================================
# ANY TYPE TESTS
# =============================================================================


class TestAnyRef:
    """AnyI operations."""

    def test_literal_creation(self):
        """AnyI can wrap literal."""
        AnyI(42)

    def test_arithmetic(self):
        """AnyI supports arithmetic."""
        a = AnyI(10)
        result = a + 5
        assert isinstance(result, AnyI)

    def test_comparison(self):
        """AnyI supports comparison."""
        a = AnyI(10)
        result = a > 5
        assert isinstance(result, BoolI)

    def test_logical(self):
        """AnyI supports logical."""
        a = AnyI(True)
        result = a.and_(False)
        assert isinstance(result, BoolI)

    def test_bitwise(self):
        """AnyI supports bitwise."""
        a = AnyI(0b1100)
        result = a.bitand(0b1010)
        assert isinstance(result, AnyI)


# =============================================================================
# ENSURE_TERM FUNCTION TESTS
# =============================================================================


class TestEnsureTermFunction:
    """ensure_nu() function comprehensive tests."""

    def test_int(self):
        """ensure_nu(int) returns IntI."""
        result = ensure_nu(42)
        assert isinstance(result, IntI)

    def test_float(self):
        """ensure_nu(float) returns FloatI."""
        result = ensure_nu(3.14)
        assert isinstance(result, FloatI)

    def test_bool_true(self):
        """ensure_nu(True) returns BoolI (not IntI)."""
        result = ensure_nu(True)
        assert isinstance(result, BoolI)

    def test_bool_false(self):
        """ensure_nu(False) returns BoolI."""
        result = ensure_nu(False)
        assert isinstance(result, BoolI)

    def test_str(self):
        """ensure_nu(str) returns StrI."""
        result = ensure_nu("hello")
        assert isinstance(result, StrI)

    def test_bytes(self):
        """ensure_nu(bytes) returns BytesI."""
        result = ensure_nu(b"hello")
        assert isinstance(result, BytesI)

    def test_none(self):
        """ensure_nu(None) returns NoneI."""
        result = ensure_nu(None)
        assert isinstance(result, NoneI)

    def test_list(self):
        """ensure_nu(list) returns ListI."""
        result = ensure_nu([1, 2, 3])
        assert isinstance(result, ListI)

    def test_tuple(self):
        """ensure_nu(tuple) returns TupleI."""
        result = ensure_nu((1, 2, 3))
        assert isinstance(result, TupleI)

    def test_dict(self):
        """ensure_nu(dict) returns DictI."""
        result = ensure_nu({"a": 1})
        assert isinstance(result, DictI)

    def test_set(self):
        """ensure_nu(set) returns SetI."""
        result = ensure_nu({1, 2, 3})
        assert isinstance(result, SetI)

    def test_frozenset(self):
        """ensure_nu(frozenset) returns FrozenSetI."""
        result = ensure_nu(frozenset({1, 2, 3}))
        assert isinstance(result, FrozenSetI)

    def test_passthrough_term(self):
        """ensure_nu(Nu) returns Nu unchanged."""
        original = IntI(42)
        result = ensure_nu(original)
        assert result is original

    def test_unsupported_type(self):
        """ensure_nu(unsupported) raises TypeError."""
        with pytest.raises(TypeError, match="Not supported type"):
            ensure_nu(object())


# =============================================================================
# BLOCKED OPERATORS
# =============================================================================


class TestBlockedOperators:
    """Tests for operators that are intentionally blocked."""

    def test_eq_is_identity(self):
        """Python == on Interfaces uses identity, not DSL equality."""
        x = IntI(10)
        y = IntI(10)
        # Different objects, so identity comparison returns False
        assert not (x == y)
        assert x == x

    def test_ne_is_identity(self):
        """Python != on Interfaces uses identity, not DSL equality."""
        x = IntI(10)
        y = IntI(5)
        assert x != y

    def test_eq_method_works(self):
        """The eq() method works for equality checks."""
        x = IntI(10)
        result = x.eq(10)
        assert isinstance(result, BoolI)

    def test_ne_method_works(self):
        """The ne() method works for inequality checks."""
        x = IntI(10)
        result = x.ne(5)
        assert isinstance(result, BoolI)
