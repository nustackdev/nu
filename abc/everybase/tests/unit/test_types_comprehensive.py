"""Comprehensive unit tests for all Term types.

Tests type construction, operations, and method availability for:
- IntRef, FloatRef, BoolRef (numeric/boolean)
- StrRef, BytesRef (text/binary)
- ListRef, TupleRef, DictRef, SetRef, FrozenSetRef (collections)
- NoneRef, AnyRef (special types)
"""

import pytest

from everybase import (
    AnyRef,
    BoolRef,
    BytesRef,
    DictRef,
    FloatRef,
    FrozenSetRef,
    IntRef,
    ListRef,
    NoneRef,
    SetRef,
    StrRef,
    TupleRef,
    ensure_term,
)


# =============================================================================
# INT TYPE TESTS
# =============================================================================


class TestIntRefArithmetic:
    """IntRef arithmetic operations."""

    def test_addition_int_int(self):
        """int + int returns IntRef."""
        x = IntRef(10)
        result = x + 5
        assert isinstance(result, IntRef)

    def test_addition_int_inttype(self):
        """IntRef + IntRef returns IntRef."""
        x = IntRef(10)
        y = IntRef(5)
        result = x + y
        assert isinstance(result, IntRef)

    def test_addition_int_float(self):
        """int + float returns FloatRef."""
        x = IntRef(10)
        result = x + 2.5
        assert isinstance(result, FloatRef)

    def test_radd(self):
        """5 + IntRef works via __radd__."""
        x = IntRef(10)
        result = 5 + x
        assert isinstance(result, IntRef)

    def test_subtraction(self):
        """IntRef subtraction."""
        x = IntRef(10)
        result = x - 3
        assert isinstance(result, IntRef)

    def test_rsub(self):
        """20 - IntRef works."""
        x = IntRef(10)
        result = 20 - x
        assert isinstance(result, IntRef)

    def test_multiplication(self):
        """IntRef multiplication."""
        x = IntRef(6)
        result = x * 7
        assert isinstance(result, IntRef)

    def test_rmul(self):
        """7 * IntRef works."""
        x = IntRef(6)
        result = 7 * x
        assert isinstance(result, IntRef)

    def test_division(self):
        """IntRef division always returns FloatRef."""
        x = IntRef(10)
        result = x / 3
        assert isinstance(result, FloatRef)

    def test_rdiv(self):
        """30 / IntRef works."""
        x = IntRef(10)
        result = 30 / x
        assert isinstance(result, FloatRef)

    def test_floor_division(self):
        """IntRef floor division."""
        x = IntRef(10)
        result = x // 3
        assert isinstance(result, IntRef)

    def test_rfloordiv(self):
        """30 // IntRef works."""
        x = IntRef(10)
        result = 30 // x
        assert isinstance(result, IntRef)

    def test_modulo(self):
        """IntRef modulo."""
        x = IntRef(10)
        result = x % 3
        assert isinstance(result, IntRef)

    def test_rmod(self):
        """30 % IntRef works."""
        x = IntRef(7)
        result = 30 % x
        assert isinstance(result, IntRef)

    def test_power(self):
        """IntRef power."""
        x = IntRef(2)
        result = x**10
        assert isinstance(result, IntRef)

    def test_rpow(self):
        """2 ** IntRef works."""
        x = IntRef(10)
        result = 2**x
        assert isinstance(result, IntRef)

    def test_negation(self):
        """IntRef negation."""
        x = IntRef(42)
        result = -x
        assert isinstance(result, IntRef)

    def test_positive(self):
        """IntRef unary plus."""
        x = IntRef(42)
        result = +x
        assert isinstance(result, IntRef)

    def test_absolute(self):
        """IntRef absolute value."""
        x = IntRef(-42)
        result = abs(x)
        assert isinstance(result, IntRef)


class TestIntRefBitwise:
    """IntRef bitwise operations."""

    def test_bitwise_and(self):
        """IntRef bitand() method."""
        x = IntRef(0b1100)
        result = x.bitand(0b1010)
        assert isinstance(result, IntRef)

    def test_bitwise_or(self):
        """IntRef bitor() method."""
        x = IntRef(0b1100)
        result = x.bitor(0b1010)
        assert isinstance(result, IntRef)

    def test_bitwise_xor(self):
        """IntRef xor via ^."""
        x = IntRef(0b1100)
        result = x ^ 0b1010
        assert isinstance(result, IntRef)

    def test_bitwise_not(self):
        """IntRef bitnot() method."""
        x = IntRef(0b1100)
        result = x.bitnot()
        assert isinstance(result, IntRef)

    def test_left_shift(self):
        """IntRef left shift."""
        x = IntRef(1)
        result = x << 4
        assert isinstance(result, IntRef)

    def test_right_shift(self):
        """IntRef right shift."""
        x = IntRef(16)
        result = x >> 2
        assert isinstance(result, IntRef)


class TestIntRefComparison:
    """IntRef comparison operations."""

    def test_greater_than(self):
        """IntRef > comparison."""
        x = IntRef(10)
        result = x > 5
        assert isinstance(result, BoolRef)

    def test_less_than(self):
        """IntRef < comparison."""
        x = IntRef(10)
        result = x < 20
        assert isinstance(result, BoolRef)

    def test_greater_equal(self):
        """IntRef >= comparison."""
        x = IntRef(10)
        result = x >= 10
        assert isinstance(result, BoolRef)

    def test_less_equal(self):
        """IntRef <= comparison."""
        x = IntRef(10)
        result = x <= 10
        assert isinstance(result, BoolRef)

    def test_equality_method(self):
        """IntRef eq() method."""
        x = IntRef(10)
        result = x.eq(10)
        assert isinstance(result, BoolRef)

    def test_inequality_method(self):
        """IntRef ne() method."""
        x = IntRef(10)
        result = x.ne(5)
        assert isinstance(result, BoolRef)

    def test_identity_method(self):
        """IntRef is_() method."""
        x = IntRef(10)
        result = x.is_(10)
        assert isinstance(result, BoolRef)


class TestIntRefLogical:
    """IntRef logical operations."""

    def test_and(self):
        """IntRef and_() method."""
        x = IntRef(1)
        result = x.and_(IntRef(2))
        assert isinstance(result, BoolRef)

    def test_or(self):
        """IntRef or_() method."""
        x = IntRef(0)
        result = x.or_(IntRef(1))
        assert isinstance(result, BoolRef)

    def test_not(self):
        """IntRef not_() method."""
        x = IntRef(0)
        result = x.not_()
        assert isinstance(result, BoolRef)

    def test_bool_method(self):
        """IntRef bool_() method."""
        x = IntRef(42)
        result = x.bool_()
        assert isinstance(result, BoolRef)


class TestIntRefConversions:
    """IntRef type conversion methods."""

    def test_to_float(self):
        """IntRef.to_float() returns FloatRef."""
        x = IntRef(42)
        result = x.to_float()
        assert isinstance(result, FloatRef)

    def test_to_str(self):
        """IntRef.to_str() returns StrRef."""
        x = IntRef(42)
        result = x.to_str()
        assert isinstance(result, StrRef)

    def test_to_bool(self):
        """IntRef.to_bool() returns BoolRef."""
        x = IntRef(42)
        result = x.to_bool()
        assert isinstance(result, BoolRef)


class TestIntRefSpecialChecks:
    """IntRef special value checks."""

    def test_is_empty(self):
        """IntRef.is_empty() returns BoolRef."""
        x = IntRef(42)
        result = x.is_empty()
        assert isinstance(result, BoolRef)

    def test_is_invalid(self):
        """IntRef.is_invalid() returns BoolRef."""
        x = IntRef(42)
        result = x.is_invalid()
        assert isinstance(result, BoolRef)

    def test_is_sentinel(self):
        """IntRef.is_sentinel() returns BoolRef."""
        x = IntRef(42)
        result = x.is_sentinel()
        assert isinstance(result, BoolRef)

    def test_not_empty(self):
        """IntRef.not_empty() returns BoolRef."""
        x = IntRef(42)
        result = x.not_empty()
        assert isinstance(result, BoolRef)

    def test_not_invalid(self):
        """IntRef.not_invalid() returns BoolRef."""
        x = IntRef(42)
        result = x.not_invalid()
        assert isinstance(result, BoolRef)


class TestIntRefConditional:
    """IntRef conditional operations."""

    def test_ifelse(self):
        """IntRef.ifelse() returns AnyRef."""
        x = IntRef(100)
        result = x.ifelse(BoolRef(True), IntRef(0))
        assert isinstance(result, AnyRef)

    def test_or_default(self):
        """IntRef.or_default() returns AnyRef."""
        x = IntRef(42)
        result = x.or_default(0)
        assert isinstance(result, AnyRef)


# =============================================================================
# FLOAT TYPE TESTS
# =============================================================================


class TestFloatRef:
    """FloatRef operations."""

    def test_literal_creation(self):
        """FloatRef can wrap literal."""
        FloatRef(3.14)

    def test_addition(self):
        """FloatRef addition."""
        f = FloatRef(1.5)
        result = f + 2.5
        assert isinstance(result, FloatRef)

    def test_subtraction(self):
        """FloatRef subtraction."""
        f = FloatRef(5.0)
        result = f - 2.0
        assert isinstance(result, FloatRef)

    def test_multiplication(self):
        """FloatRef multiplication."""
        f = FloatRef(2.5)
        result = f * 4.0
        assert isinstance(result, FloatRef)

    def test_division(self):
        """FloatRef division."""
        f = FloatRef(10.0)
        result = f / 4.0
        assert isinstance(result, FloatRef)

    def test_floor_division(self):
        """FloatRef floor division."""
        f = FloatRef(10.0)
        result = f // 3.0
        assert isinstance(result, FloatRef)

    def test_modulo(self):
        """FloatRef modulo."""
        f = FloatRef(10.0)
        result = f % 3.0
        assert isinstance(result, FloatRef)

    def test_power(self):
        """FloatRef power."""
        f = FloatRef(2.0)
        result = f**3.0
        assert isinstance(result, FloatRef)

    def test_negation(self):
        """FloatRef negation."""
        f = FloatRef(3.14)
        result = -f
        assert isinstance(result, FloatRef)

    def test_comparison(self):
        """FloatRef comparison."""
        f = FloatRef(3.14)
        result = f > 3.0
        assert isinstance(result, BoolRef)

    def test_to_int(self):
        """FloatRef.to_int() returns IntRef."""
        f = FloatRef(3.14)
        result = f.to_int()
        assert isinstance(result, IntRef)


# =============================================================================
# BOOL TYPE TESTS
# =============================================================================


class TestBoolRef:
    """BoolRef operations."""

    def test_literal_creation_true(self):
        """BoolRef can wrap True."""
        BoolRef(True)

    def test_literal_creation_false(self):
        """BoolRef can wrap False."""
        BoolRef(False)

    def test_and_operation(self):
        """BoolRef and_() method."""
        a = BoolRef(True)
        b = BoolRef(False)
        result = a.and_(b)
        assert isinstance(result, BoolRef)

    def test_or_operation(self):
        """BoolRef or_() method."""
        a = BoolRef(True)
        b = BoolRef(False)
        result = a.or_(b)
        assert isinstance(result, BoolRef)

    def test_not_operation(self):
        """BoolRef not_() method."""
        a = BoolRef(True)
        result = a.not_()
        assert isinstance(result, BoolRef)

    def test_bool_method(self):
        """BoolRef bool_() method."""
        a = BoolRef(True)
        result = a.bool_()
        assert isinstance(result, BoolRef)

    def test_comparison(self):
        """BoolRef comparison."""
        a = BoolRef(True)
        result = a > BoolRef(False)
        assert isinstance(result, BoolRef)

    def test_equality(self):
        """BoolRef eq() method."""
        a = BoolRef(True)
        result = a.eq(True)
        assert isinstance(result, BoolRef)


# =============================================================================
# STR TYPE TESTS
# =============================================================================


class TestStrRefBasic:
    """StrRef basic operations."""

    def test_literal_creation(self):
        """StrRef can wrap literal."""
        StrRef("hello")

    def test_concatenation(self):
        """StrRef + str returns StrRef."""
        s = StrRef("hello")
        result = s + " world"
        assert isinstance(result, StrRef)

    def test_radd(self):
        """str + StrRef works."""
        s = StrRef("world")
        result = "hello " + s
        assert isinstance(result, StrRef)


class TestStrRefCaseMethods:
    """StrRef case transformation methods."""

    def test_upper(self):
        """StrRef.upper() returns StrRef."""
        s = StrRef("hello")
        result = s.upper()
        assert isinstance(result, StrRef)

    def test_lower(self):
        """StrRef.lower() returns StrRef."""
        s = StrRef("HELLO")
        result = s.lower()
        assert isinstance(result, StrRef)

    def test_title(self):
        """StrRef.title() returns StrRef."""
        s = StrRef("hello world")
        result = s.title()
        assert isinstance(result, StrRef)

    def test_capitalize(self):
        """StrRef.capitalize() returns StrRef."""
        s = StrRef("hello")
        result = s.capitalize()
        assert isinstance(result, StrRef)

    def test_swapcase(self):
        """StrRef.swapcase() returns StrRef."""
        s = StrRef("HeLLo")
        result = s.swapcase()
        assert isinstance(result, StrRef)


class TestStrRefStrippingMethods:
    """StrRef stripping methods."""

    def test_strip(self):
        """StrRef.strip() returns StrRef."""
        s = StrRef("  hello  ")
        result = s.strip()
        assert isinstance(result, StrRef)

    def test_strip_with_chars(self):
        """StrRef.strip(chars) returns StrRef."""
        s = StrRef("xxhelloxx")
        result = s.strip("x")
        assert isinstance(result, StrRef)

    def test_lstrip(self):
        """StrRef.lstrip() returns StrRef."""
        s = StrRef("  hello")
        result = s.lstrip()
        assert isinstance(result, StrRef)

    def test_rstrip(self):
        """StrRef.rstrip() returns StrRef."""
        s = StrRef("hello  ")
        result = s.rstrip()
        assert isinstance(result, StrRef)


class TestStrRefSplittingMethods:
    """StrRef splitting methods."""

    def test_split(self):
        """StrRef.split() returns ListRef."""
        s = StrRef("a,b,c")
        result = s.split(",")
        assert isinstance(result, ListRef)

    def test_split_no_sep(self):
        """StrRef.split() with no separator."""
        s = StrRef("a b c")
        result = s.split()
        assert isinstance(result, ListRef)

    def test_rsplit(self):
        """StrRef.rsplit() returns ListRef."""
        s = StrRef("a,b,c")
        result = s.rsplit(",")
        assert isinstance(result, ListRef)


class TestStrRefSearchMethods:
    """StrRef search methods."""

    def test_find(self):
        """StrRef.find() returns IntRef."""
        s = StrRef("hello world")
        result = s.find("world")
        assert isinstance(result, IntRef)

    def test_rfind(self):
        """StrRef.rfind() returns IntRef."""
        s = StrRef("hello world world")
        result = s.rfind("world")
        assert isinstance(result, IntRef)

    def test_count_substring(self):
        """StrRef.count_substring() returns IntRef."""
        s = StrRef("abcabc")
        result = s.count_substring("abc")
        assert isinstance(result, IntRef)


class TestStrRefTestMethods:
    """StrRef testing methods."""

    def test_startswith(self):
        """StrRef.startswith() returns BoolRef."""
        s = StrRef("hello")
        result = s.startswith("he")
        assert isinstance(result, BoolRef)

    def test_endswith(self):
        """StrRef.endswith() returns BoolRef."""
        s = StrRef("hello")
        result = s.endswith("lo")
        assert isinstance(result, BoolRef)

    def test_isdigit(self):
        """StrRef.isdigit() returns BoolRef."""
        s = StrRef("123")
        result = s.isdigit()
        assert isinstance(result, BoolRef)

    def test_isalpha(self):
        """StrRef.isalpha() returns BoolRef."""
        s = StrRef("abc")
        result = s.isalpha()
        assert isinstance(result, BoolRef)

    def test_isalnum(self):
        """StrRef.isalnum() returns BoolRef."""
        s = StrRef("abc123")
        result = s.isalnum()
        assert isinstance(result, BoolRef)

    def test_isspace(self):
        """StrRef.isspace() returns BoolRef."""
        s = StrRef("   ")
        result = s.isspace()
        assert isinstance(result, BoolRef)


class TestStrRefPaddingMethods:
    """StrRef padding methods."""

    def test_center(self):
        """StrRef.center() returns StrRef."""
        s = StrRef("hi")
        result = s.center(10)
        assert isinstance(result, StrRef)

    def test_ljust(self):
        """StrRef.ljust() returns StrRef."""
        s = StrRef("hi")
        result = s.ljust(10)
        assert isinstance(result, StrRef)

    def test_rjust(self):
        """StrRef.rjust() returns StrRef."""
        s = StrRef("hi")
        result = s.rjust(10)
        assert isinstance(result, StrRef)

    def test_zfill(self):
        """StrRef.zfill() returns StrRef."""
        s = StrRef("42")
        result = s.zfill(5)
        assert isinstance(result, StrRef)


class TestStrRefOtherMethods:
    """StrRef other methods."""

    def test_replace(self):
        """StrRef.replace() returns StrRef."""
        s = StrRef("hello")
        result = s.replace("l", "L")
        assert isinstance(result, StrRef)

    def test_encode(self):
        """StrRef.encode() returns BytesRef."""
        s = StrRef("hello")
        result = s.encode()
        assert isinstance(result, BytesRef)

    def test_len(self):
        """StrRef.len_() returns IntRef."""
        s = StrRef("hello")
        result = s.len_()
        assert isinstance(result, IntRef)

    def test_contains(self):
        """StrRef.contains() returns BoolRef."""
        s = StrRef("hello")
        result = s.contains("ell")
        assert isinstance(result, BoolRef)


class TestStrRefComparison:
    """StrRef comparison operations."""

    def test_greater_than(self):
        """StrRef > comparison."""
        s = StrRef("b")
        result = s > "a"
        assert isinstance(result, BoolRef)

    def test_less_than(self):
        """StrRef < comparison."""
        s = StrRef("a")
        result = s < "b"
        assert isinstance(result, BoolRef)

    def test_equality(self):
        """StrRef eq() method."""
        s = StrRef("hello")
        result = s.eq("hello")
        assert isinstance(result, BoolRef)


# =============================================================================
# BYTES TYPE TESTS
# =============================================================================


class TestBytesRef:
    """BytesRef operations."""

    def test_literal_creation(self):
        """BytesRef can wrap literal."""
        BytesRef(b"hello")

    def test_concatenation(self):
        """BytesRef + bytes returns BytesRef."""
        b = BytesRef(b"hello")
        result = b + b" world"
        assert isinstance(result, BytesRef)

    def test_decode(self):
        """BytesRef.decode() returns StrRef."""
        b = BytesRef(b"hello")
        result = b.decode()
        assert isinstance(result, StrRef)

    def test_hex(self):
        """BytesRef.hex_() returns StrRef."""
        b = BytesRef(b"hello")
        result = b.hex_()
        assert isinstance(result, StrRef)

    def test_upper(self):
        """BytesRef.upper() returns BytesRef."""
        b = BytesRef(b"hello")
        result = b.upper()
        assert isinstance(result, BytesRef)

    def test_lower(self):
        """BytesRef.lower() returns BytesRef."""
        b = BytesRef(b"HELLO")
        result = b.lower()
        assert isinstance(result, BytesRef)

    def test_strip(self):
        """BytesRef.strip() returns BytesRef."""
        b = BytesRef(b"  hello  ")
        result = b.strip()
        assert isinstance(result, BytesRef)

    def test_find_bytes(self):
        """BytesRef.find_bytes() returns IntRef."""
        b = BytesRef(b"hello world")
        result = b.find_bytes(b"world")
        assert isinstance(result, IntRef)

    def test_startswith(self):
        """BytesRef.startswith() returns BoolRef."""
        b = BytesRef(b"hello")
        result = b.startswith(b"he")
        assert isinstance(result, BoolRef)

    def test_len(self):
        """BytesRef.len_() returns IntRef."""
        b = BytesRef(b"hello")
        result = b.len_()
        assert isinstance(result, IntRef)


# =============================================================================
# LIST TYPE TESTS
# =============================================================================


class TestListRefBasic:
    """ListRef basic operations."""

    def test_literal_creation(self):
        """ListRef can wrap literal."""
        ListRef([1, 2, 3])

    def test_concatenation(self):
        """ListRef + list returns ListRef."""
        lst = ListRef([1, 2])
        result = lst + [3, 4]  # noqa: RUF005
        assert isinstance(result, ListRef)

    def test_indexing(self):
        """ListRef[int] returns AnyRef."""
        lst = ListRef([1, 2, 3])
        result = lst[0]
        assert isinstance(result, AnyRef)

    def test_slicing(self):
        """ListRef[slice] returns ListRef."""
        lst = ListRef([1, 2, 3, 4, 5])
        result = lst[1:4]
        assert isinstance(result, ListRef)


class TestListRefSequenceMethods:
    """ListRef sequence methods."""

    def test_len(self):
        """ListRef.len_() returns IntRef."""
        lst = ListRef([1, 2, 3])
        result = lst.len_()
        assert isinstance(result, IntRef)

    def test_contains(self):
        """ListRef.contains() returns BoolRef."""
        lst = ListRef([1, 2, 3])
        result = lst.contains(2)
        assert isinstance(result, BoolRef)

    def test_first(self):
        """ListRef.first() returns AnyRef."""
        lst = ListRef([1, 2, 3])
        result = lst.first()
        assert isinstance(result, AnyRef)

    def test_last(self):
        """ListRef.last() returns AnyRef."""
        lst = ListRef([1, 2, 3])
        result = lst.last()
        assert isinstance(result, AnyRef)

    def test_reversed(self):
        """ListRef.reversed_() returns ListRef."""
        lst = ListRef([1, 2, 3])
        result = lst.reversed_()
        assert isinstance(result, ListRef)

    def test_sorted(self):
        """ListRef.sorted_() returns ListRef."""
        lst = ListRef([3, 1, 2])
        result = lst.sorted_()
        assert isinstance(result, ListRef)

    def test_index(self):
        """ListRef.index() returns IntRef."""
        lst = ListRef([1, 2, 3])
        result = lst.index(2)
        assert isinstance(result, IntRef)

    def test_count(self):
        """ListRef.count() returns IntRef."""
        lst = ListRef([1, 2, 2, 3])
        result = lst.count(2)
        assert isinstance(result, IntRef)


class TestListRefIterableMethods:
    """ListRef iterable/functional methods."""

    def test_sum(self):
        """ListRef.sum_() returns AnyRef."""
        lst = ListRef([1, 2, 3])
        result = lst.sum_()
        assert isinstance(result, AnyRef)

    def test_min(self):
        """ListRef.min_() returns AnyRef."""
        lst = ListRef([3, 1, 2])
        result = lst.min_()
        assert isinstance(result, AnyRef)

    def test_max(self):
        """ListRef.max_() returns AnyRef."""
        lst = ListRef([3, 1, 2])
        result = lst.max_()
        assert isinstance(result, AnyRef)

    def test_any(self):
        """ListRef.any_() returns BoolRef."""
        lst = ListRef([False, True, False])
        result = lst.any_()
        assert isinstance(result, BoolRef)

    def test_all(self):
        """ListRef.all_() returns BoolRef."""
        lst = ListRef([True, True, True])
        result = lst.all_()
        assert isinstance(result, BoolRef)


# =============================================================================
# TUPLE TYPE TESTS
# =============================================================================


class TestTupleRef:
    """TupleRef operations."""

    def test_literal_creation(self):
        """TupleRef can wrap literal."""
        TupleRef((1, 2, 3))

    def test_indexing(self):
        """TupleRef[int] returns AnyRef."""
        t = TupleRef((1, 2, 3))
        result = t[0]
        assert isinstance(result, AnyRef)

    def test_slicing(self):
        """TupleRef[slice] returns TupleRef."""
        t = TupleRef((1, 2, 3, 4, 5))
        result = t[1:4]
        # TupleRef slicing returns TupleRef (not ListRef)
        assert isinstance(result, TupleRef)

    def test_len(self):
        """TupleRef.len_() returns IntRef."""
        t = TupleRef((1, 2, 3))
        result = t.len_()
        assert isinstance(result, IntRef)

    def test_contains(self):
        """TupleRef.contains() returns BoolRef."""
        t = TupleRef((1, 2, 3))
        result = t.contains(2)
        assert isinstance(result, BoolRef)


# =============================================================================
# DICT TYPE TESTS
# =============================================================================


class TestDictRef:
    """DictRef operations."""

    def test_literal_creation(self):
        """DictRef can wrap literal."""
        DictRef({"a": 1, "b": 2})

    def test_key_access(self):
        """DictRef[key] returns AnyRef."""
        d = DictRef({"a": 1, "b": 2})
        result = d["a"]
        assert isinstance(result, AnyRef)

    def test_len(self):
        """DictRef.len_() returns IntRef."""
        d = DictRef({"a": 1, "b": 2})
        result = d.len_()
        assert isinstance(result, IntRef)

    def test_contains(self):
        """DictRef.contains() returns BoolRef."""
        d = DictRef({"a": 1, "b": 2})
        result = d.contains("a")
        assert isinstance(result, BoolRef)

    def test_keys(self):
        """DictRef.keys_() returns ListRef."""
        d = DictRef({"a": 1, "b": 2})
        result = d.keys_()
        assert isinstance(result, ListRef)

    def test_values(self):
        """DictRef.values_() returns ListRef."""
        d = DictRef({"a": 1, "b": 2})
        result = d.values_()
        assert isinstance(result, ListRef)

    def test_items(self):
        """DictRef.items_() returns ListRef."""
        d = DictRef({"a": 1, "b": 2})
        result = d.items_()
        assert isinstance(result, ListRef)

    def test_get(self):
        """DictRef.get_() returns AnyRef."""
        d = DictRef({"a": 1, "b": 2})
        result = d.get_("a", 0)
        assert isinstance(result, AnyRef)


# =============================================================================
# SET TYPE TESTS
# =============================================================================


class TestSetRef:
    """SetRef operations."""

    def test_literal_creation(self):
        """SetRef can wrap literal."""
        SetRef({1, 2, 3})

    def test_len(self):
        """SetRef.len_() returns IntRef."""
        s = SetRef({1, 2, 3})
        result = s.len_()
        assert isinstance(result, IntRef)

    def test_contains(self):
        """SetRef.contains() returns BoolRef."""
        s = SetRef({1, 2, 3})
        result = s.contains(2)
        assert isinstance(result, BoolRef)

    def test_union(self):
        """SetRef.union() returns SetRef."""
        s = SetRef({1, 2})
        result = s.union({3, 4})
        assert isinstance(result, SetRef)

    def test_intersection(self):
        """SetRef.intersection() returns SetRef."""
        s = SetRef({1, 2, 3})
        result = s.intersection({2, 3, 4})
        assert isinstance(result, SetRef)

    def test_difference(self):
        """SetRef.difference() returns SetRef."""
        s = SetRef({1, 2, 3})
        result = s.difference({2, 3})
        assert isinstance(result, SetRef)

    def test_symmetric_difference(self):
        """SetRef.symmetric_difference() returns SetRef."""
        s = SetRef({1, 2, 3})
        result = s.symmetric_difference({2, 3, 4})
        assert isinstance(result, SetRef)

    def test_issubset(self):
        """SetRef.issubset() returns BoolRef."""
        s = SetRef({1, 2})
        result = s.issubset({1, 2, 3})
        assert isinstance(result, BoolRef)

    def test_issuperset(self):
        """SetRef.issuperset() returns BoolRef."""
        s = SetRef({1, 2, 3})
        result = s.issuperset({1, 2})
        assert isinstance(result, BoolRef)

    def test_isdisjoint(self):
        """SetRef.isdisjoint() returns BoolRef."""
        s = SetRef({1, 2})
        result = s.isdisjoint({3, 4})
        assert isinstance(result, BoolRef)


class TestFrozenSetRef:
    """FrozenSetRef operations."""

    def test_literal_creation(self):
        """FrozenSetRef can wrap literal."""
        FrozenSetRef(frozenset({1, 2, 3}))

    def test_union(self):
        """FrozenSetRef.union() returns FrozenSetRef."""
        s = FrozenSetRef(frozenset({1, 2}))
        result = s.union(frozenset({3, 4}))
        assert isinstance(result, FrozenSetRef)


# =============================================================================
# NONE TYPE TESTS
# =============================================================================


class TestNoneRef:
    """NoneRef operations."""

    def test_default_creation(self):
        """NoneRef() creates None literal."""
        _ = NoneRef()

    def test_is_empty(self):
        """NoneRef.is_empty() returns BoolRef."""
        n = NoneRef()
        result = n.is_empty()
        assert isinstance(result, BoolRef)

    def test_logical_and(self):
        """NoneRef.and_() works."""
        n = NoneRef()
        result = n.and_(BoolRef(True))
        assert isinstance(result, BoolRef)


# =============================================================================
# ANY TYPE TESTS
# =============================================================================


class TestAnyRef:
    """AnyRef operations."""

    def test_literal_creation(self):
        """AnyRef can wrap literal."""
        AnyRef(42)

    def test_arithmetic(self):
        """AnyRef supports arithmetic."""
        a = AnyRef(10)
        result = a + 5
        assert isinstance(result, AnyRef)

    def test_comparison(self):
        """AnyRef supports comparison."""
        a = AnyRef(10)
        result = a > 5
        assert isinstance(result, BoolRef)

    def test_logical(self):
        """AnyRef supports logical."""
        a = AnyRef(True)
        result = a.and_(False)
        assert isinstance(result, BoolRef)

    def test_bitwise(self):
        """AnyRef supports bitwise."""
        a = AnyRef(0b1100)
        result = a.bitand(0b1010)
        assert isinstance(result, AnyRef)


# =============================================================================
# ENSURE_TERM FUNCTION TESTS
# =============================================================================


class TestEnsureTermFunction:
    """ensure_term() function comprehensive tests."""

    def test_int(self):
        """ensure_term(int) returns IntRef."""
        result = ensure_term(42)
        assert isinstance(result, IntRef)

    def test_float(self):
        """ensure_term(float) returns FloatRef."""
        result = ensure_term(3.14)
        assert isinstance(result, FloatRef)

    def test_bool_true(self):
        """ensure_term(True) returns BoolRef (not IntRef)."""
        result = ensure_term(True)
        assert isinstance(result, BoolRef)

    def test_bool_false(self):
        """ensure_term(False) returns BoolRef."""
        result = ensure_term(False)
        assert isinstance(result, BoolRef)

    def test_str(self):
        """ensure_term(str) returns StrRef."""
        result = ensure_term("hello")
        assert isinstance(result, StrRef)

    def test_bytes(self):
        """ensure_term(bytes) returns BytesRef."""
        result = ensure_term(b"hello")
        assert isinstance(result, BytesRef)

    def test_none(self):
        """ensure_term(None) returns NoneRef."""
        result = ensure_term(None)
        assert isinstance(result, NoneRef)

    def test_list(self):
        """ensure_term(list) returns ListRef."""
        result = ensure_term([1, 2, 3])
        assert isinstance(result, ListRef)

    def test_tuple(self):
        """ensure_term(tuple) returns TupleRef."""
        result = ensure_term((1, 2, 3))
        assert isinstance(result, TupleRef)

    def test_dict(self):
        """ensure_term(dict) returns DictRef."""
        result = ensure_term({"a": 1})
        assert isinstance(result, DictRef)

    def test_set(self):
        """ensure_term(set) returns SetRef."""
        result = ensure_term({1, 2, 3})
        assert isinstance(result, SetRef)

    def test_frozenset(self):
        """ensure_term(frozenset) returns FrozenSetRef."""
        result = ensure_term(frozenset({1, 2, 3}))
        assert isinstance(result, FrozenSetRef)

    def test_passthrough_term(self):
        """ensure_term(Term) returns Term unchanged."""
        original = IntRef(42)
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
        x = IntRef(10)
        y = IntRef(10)
        with pytest.raises(TypeError, match="Cannot use =="):
            _ = x == y

    def test_ne_blocked(self):
        """Using != on Terms raises TypeError."""
        x = IntRef(10)
        y = IntRef(5)
        with pytest.raises(TypeError, match="Cannot use !="):
            _ = x != y

    def test_bool_conversion_blocked(self):
        """Using bool() on Terms raises TypeError."""
        x = IntRef(10)
        with pytest.raises(TypeError, match="Cannot convert Term to bool"):
            bool(x)

    def test_eq_method_works(self):
        """The eq() method works for equality checks."""
        x = IntRef(10)
        result = x.eq(10)
        assert isinstance(result, BoolRef)

    def test_ne_method_works(self):
        """The ne() method works for inequality checks."""
        x = IntRef(10)
        result = x.ne(5)
        assert isinstance(result, BoolRef)
