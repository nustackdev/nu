"""Comprehensive functional tests for all operations execution.

Tests that all operations execute correctly and produce expected results.
Organized by operation category:
- Arithmetic, Bitwise, Comparison, Logical
- Type Conversion, Special Value Checks
- Collection Access, Aggregation, Search, Transform
- Conditional, Callable
"""

import pytest

from everyabc import INVALID, Context
from everybase import (
    BoolRef,
    BytesRef,
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    SetRef,
    StrRef,
    TupleRef,
    all_,
    any_,
    ifelse,
    none_,
)


@pytest.fixture
def ctx():
    """Create a minimal mock context for term execution."""

    return Context()


# =============================================================================
# ARITHMETIC OPERATIONS
# =============================================================================


class TestArithmeticOps:
    """Test all arithmetic operations."""

    # Unary arithmetic
    def test_neg_int(self, ctx):
        """-42 = -42."""
        assert (-IntRef(42)).execute(ctx) == -42

    def test_neg_float(self, ctx):
        """-3.14 = -3.14."""
        assert (-FloatRef(3.14)).execute(ctx) == -3.14

    def test_pos_int(self, ctx):
        """+42 = 42."""
        assert (+IntRef(42)).execute(ctx) == 42

    def test_abs_positive(self, ctx):
        """abs(42) = 42."""
        assert abs(IntRef(42)).execute(ctx) == 42

    def test_abs_negative(self, ctx):
        """abs(-42) = 42."""
        assert abs(IntRef(-42)).execute(ctx) == 42

    # Binary arithmetic
    def test_add_int_int(self, ctx):
        """5 + 3 = 8."""
        assert (IntRef(5) + IntRef(3)).execute(ctx) == 8

    def test_add_int_ensure_term(self, ctx):
        """5 + 3 = 8 (with literal)."""
        assert (IntRef(5) + 3).execute(ctx) == 8

    def test_add_float_float(self, ctx):
        """1.5 + 2.5 = 4.0."""
        assert (FloatRef(1.5) + FloatRef(2.5)).execute(ctx) == 4.0

    def test_add_int_float(self, ctx):
        """5 + 2.5 = 7.5."""
        assert (IntRef(5) + 2.5).execute(ctx) == 7.5

    def test_add_str_str(self, ctx):
        """'hello' + ' world' = 'hello world'."""
        assert (StrRef("hello") + " world").execute(ctx) == "hello world"

    def test_add_list_list(self, ctx):
        """[1,2] + [3,4] = [1,2,3,4]."""
        assert (ListRef([1, 2]) + [3, 4]).execute(ctx) == [1, 2, 3, 4]  # noqa: RUF005

    def test_radd(self, ctx):
        """5 + IntRef(3) = 8."""
        assert (5 + IntRef(3)).execute(ctx) == 8

    def test_sub_int_int(self, ctx):
        """10 - 4 = 6."""
        assert (IntRef(10) - IntRef(4)).execute(ctx) == 6

    def test_rsub(self, ctx):
        """10 - IntRef(4) = 6."""
        assert (10 - IntRef(4)).execute(ctx) == 6

    def test_mul_int_int(self, ctx):
        """6 * 7 = 42."""
        assert (IntRef(6) * IntRef(7)).execute(ctx) == 42

    def test_mul_float_float(self, ctx):
        """2.5 * 4.0 = 10.0."""
        assert (FloatRef(2.5) * FloatRef(4.0)).execute(ctx) == 10.0

    def test_rmul(self, ctx):
        """6 * IntRef(7) = 42."""
        assert (6 * IntRef(7)).execute(ctx) == 42

    def test_div_int_int(self, ctx):
        """10 / 4 = 2.5."""
        assert (IntRef(10) / IntRef(4)).execute(ctx) == 2.5

    def test_div_by_zero(self, ctx):
        """10 / 0 = INVALID."""
        assert (IntRef(10) / 0).execute(ctx) is INVALID

    def test_rdiv(self, ctx):
        """20 / IntRef(4) = 5.0."""
        assert (20 / IntRef(4)).execute(ctx) == 5.0

    def test_floordiv_int_int(self, ctx):
        """10 // 3 = 3."""
        assert (IntRef(10) // IntRef(3)).execute(ctx) == 3

    def test_floordiv_by_zero(self, ctx):
        """10 // 0 = INVALID."""
        assert (IntRef(10) // 0).execute(ctx) is INVALID

    def test_rfloordiv(self, ctx):
        """10 // IntRef(3) = 3."""
        assert (10 // IntRef(3)).execute(ctx) == 3

    def test_mod_int_int(self, ctx):
        """10 % 3 = 1."""
        assert (IntRef(10) % IntRef(3)).execute(ctx) == 1

    def test_mod_by_zero(self, ctx):
        """10 % 0 = INVALID."""
        assert (IntRef(10) % 0).execute(ctx) is INVALID

    def test_rmod(self, ctx):
        """10 % IntRef(3) = 1."""
        assert (10 % IntRef(3)).execute(ctx) == 1

    def test_pow_int_int(self, ctx):
        """2 ** 10 = 1024."""
        assert (IntRef(2) ** IntRef(10)).execute(ctx) == 1024

    def test_pow_float(self, ctx):
        """2.0 ** 3 = 8.0."""
        assert (FloatRef(2.0) ** 3).execute(ctx) == 8.0

    def test_rpow(self, ctx):
        """2 ** IntRef(10) = 1024."""
        assert (2 ** IntRef(10)).execute(ctx) == 1024


# =============================================================================
# BITWISE OPERATIONS
# =============================================================================


class TestBitwiseOps:
    """Test all bitwise operations."""

    def test_bitwise_and(self, ctx):
        """0b1100 & 0b1010 = 0b1000."""
        assert IntRef(0b1100).bitand(0b1010).execute(ctx) == 0b1000

    def test_bitwise_or(self, ctx):
        """0b1100 | 0b1010 = 0b1110."""
        assert IntRef(0b1100).bitor(0b1010).execute(ctx) == 0b1110

    def test_bitwise_xor(self, ctx):
        """0b1100 ^ 0b1010 = 0b0110."""
        assert (IntRef(0b1100) ^ 0b1010).execute(ctx) == 0b0110

    def test_bitwise_not(self, ctx):
        """~1 = -2."""
        assert IntRef(1).bitnot().execute(ctx) == -2

    def test_left_shift(self, ctx):
        """1 << 4 = 16."""
        assert (IntRef(1) << 4).execute(ctx) == 16

    def test_right_shift(self, ctx):
        """16 >> 2 = 4."""
        assert (IntRef(16) >> 2).execute(ctx) == 4

    def test_rxor(self, ctx):
        """0b1010 ^ IntRef(0b1100) = 0b0110."""
        assert (0b1010 ^ IntRef(0b1100)).execute(ctx) == 0b0110


# =============================================================================
# COMPARISON OPERATIONS
# =============================================================================


class TestComparisonOps:
    """Test all comparison operations."""

    def test_gt_true(self, ctx):
        """10 > 5 = True."""
        assert (IntRef(10) > 5).execute(ctx) is True

    def test_gt_false(self, ctx):
        """5 > 10 = False."""
        assert (IntRef(5) > 10).execute(ctx) is False

    def test_gt_equal(self, ctx):
        """10 > 10 = False."""
        assert (IntRef(10) > 10).execute(ctx) is False

    def test_lt_true(self, ctx):
        """5 < 10 = True."""
        assert (IntRef(5) < 10).execute(ctx) is True

    def test_lt_false(self, ctx):
        """10 < 5 = False."""
        assert (IntRef(10) < 5).execute(ctx) is False

    def test_ge_true_greater(self, ctx):
        """10 >= 5 = True."""
        assert (IntRef(10) >= 5).execute(ctx) is True

    def test_ge_true_equal(self, ctx):
        """10 >= 10 = True."""
        assert (IntRef(10) >= 10).execute(ctx) is True

    def test_ge_false(self, ctx):
        """5 >= 10 = False."""
        assert (IntRef(5) >= 10).execute(ctx) is False

    def test_le_true_less(self, ctx):
        """5 <= 10 = True."""
        assert (IntRef(5) <= 10).execute(ctx) is True

    def test_le_true_equal(self, ctx):
        """10 <= 10 = True."""
        assert (IntRef(10) <= 10).execute(ctx) is True

    def test_le_false(self, ctx):
        """10 <= 5 = False."""
        assert (IntRef(10) <= 5).execute(ctx) is False

    def test_eq_true(self, ctx):
        """42 == 42 = True."""
        assert IntRef(42).eq(42).execute(ctx) is True

    def test_eq_false(self, ctx):
        """42 == 10 = False."""
        assert IntRef(42).eq(10).execute(ctx) is False

    def test_ne_true(self, ctx):
        """42 != 10 = True."""
        assert IntRef(42).ne(10).execute(ctx) is True

    def test_ne_false(self, ctx):
        """42 != 42 = False."""
        assert IntRef(42).ne(42).execute(ctx) is False

    def test_str_comparison(self, ctx):
        """'abc' < 'abd' = True."""
        assert (StrRef("abc") < "abd").execute(ctx) is True

    def test_float_comparison(self, ctx):
        """3.14 > 3.0 = True."""
        assert (FloatRef(3.14) > 3.0).execute(ctx) is True


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


class TestLogicalOps:
    """Test all logical operations."""

    def test_not_true(self, ctx):
        """not True = False."""
        assert BoolRef(True).not_().execute(ctx) is False

    def test_not_false(self, ctx):
        """not False = True."""
        assert BoolRef(False).not_().execute(ctx) is True

    def test_and_true_true(self, ctx):
        """True and True = True."""
        assert BoolRef(True).and_(True).execute(ctx) is True

    def test_and_true_false(self, ctx):
        """True and False = False."""
        assert BoolRef(True).and_(False).execute(ctx) is False

    def test_and_false_true(self, ctx):
        """False and True = False."""
        assert BoolRef(False).and_(True).execute(ctx) is False

    def test_and_false_false(self, ctx):
        """False and False = False."""
        assert BoolRef(False).and_(False).execute(ctx) is False

    def test_or_true_true(self, ctx):
        """True or True = True."""
        assert BoolRef(True).or_(True).execute(ctx) is True

    def test_or_true_false(self, ctx):
        """True or False = True."""
        assert BoolRef(True).or_(False).execute(ctx) is True

    def test_or_false_true(self, ctx):
        """False or True = True."""
        assert BoolRef(False).or_(True).execute(ctx) is True

    def test_or_false_false(self, ctx):
        """False or False = False."""
        assert BoolRef(False).or_(False).execute(ctx) is False

    def test_bool_truthy(self, ctx):
        """bool(42) = True."""
        assert IntRef(42).bool_().execute(ctx) is True

    def test_bool_falsy(self, ctx):
        """bool(0) = False."""
        assert IntRef(0).bool_().execute(ctx) is False

    def test_bool_empty_string(self, ctx):
        """bool('') = False."""
        assert StrRef("").bool_().execute(ctx) is False

    def test_bool_nonempty_string(self, ctx):
        """bool('x') = True."""
        assert StrRef("x").bool_().execute(ctx) is True


# =============================================================================
# TYPE CONVERSION OPERATIONS
# =============================================================================


class TestConversionOps:
    """Test all type conversion operations."""

    def test_to_int_from_float(self, ctx):
        """int(3.14) = 3."""
        assert FloatRef(3.14).to_int().execute(ctx) == 3

    def test_to_int_from_str(self, ctx):
        """int('42') = 42."""
        assert StrRef("42").to_int().execute(ctx) == 42

    def test_to_int_from_bool(self, ctx):
        """int(True) = 1."""
        assert BoolRef(True).to_int().execute(ctx) == 1

    def test_to_float_from_int(self, ctx):
        """float(42) = 42.0."""
        assert IntRef(42).to_float().execute(ctx) == 42.0

    def test_to_float_from_str(self, ctx):
        """float('3.14') = 3.14."""
        assert StrRef("3.14").to_float().execute(ctx) == 3.14

    def test_to_str_from_int(self, ctx):
        """str(42) = '42'."""
        assert IntRef(42).to_str().execute(ctx) == "42"

    def test_to_str_from_float(self, ctx):
        """str(3.14) = '3.14'."""
        assert FloatRef(3.14).to_str().execute(ctx) == "3.14"

    def test_to_str_from_bool(self, ctx):
        """str(True) = 'True'."""
        assert BoolRef(True).to_str().execute(ctx) == "True"

    def test_to_bool_from_int_truthy(self, ctx):
        """bool(42) = True."""
        assert IntRef(42).to_bool().execute(ctx) is True

    def test_to_bool_from_int_falsy(self, ctx):
        """bool(0) = False."""
        assert IntRef(0).to_bool().execute(ctx) is False

    def test_to_list_from_tuple(self, ctx):
        """list((1,2,3)) = [1,2,3]."""
        assert TupleRef((1, 2, 3)).to_list().execute(ctx) == [1, 2, 3]

    def test_to_bytes_from_str(self, ctx):
        """'hello'.encode() = b'hello'."""
        assert StrRef("hello").to_bytes().execute(ctx) == b"hello"


# =============================================================================
# STRING OPERATIONS
# =============================================================================


class TestStringOps:
    """Test string-specific operations."""

    def test_upper(self, ctx):
        """'hello'.upper() = 'HELLO'."""
        assert StrRef("hello").upper().execute(ctx) == "HELLO"

    def test_lower(self, ctx):
        """'HELLO'.lower() = 'hello'."""
        assert StrRef("HELLO").lower().execute(ctx) == "hello"

    def test_title(self, ctx):
        """'hello world'.title() = 'Hello World'."""
        assert StrRef("hello world").title().execute(ctx) == "Hello World"

    def test_capitalize(self, ctx):
        """'hello'.capitalize() = 'Hello'."""
        assert StrRef("hello").capitalize().execute(ctx) == "Hello"

    def test_swapcase(self, ctx):
        """'HeLLo'.swapcase() = 'hEllO'."""
        assert StrRef("HeLLo").swapcase().execute(ctx) == "hEllO"

    def test_strip(self, ctx):
        """'  hello  '.strip() = 'hello'."""
        assert StrRef("  hello  ").strip().execute(ctx) == "hello"

    def test_strip_chars(self, ctx):
        """'xxhelloxx'.strip('x') = 'hello'."""
        assert StrRef("xxhelloxx").strip("x").execute(ctx) == "hello"

    def test_lstrip(self, ctx):
        """'  hello'.lstrip() = 'hello'."""
        assert StrRef("  hello").lstrip().execute(ctx) == "hello"

    def test_rstrip(self, ctx):
        """'hello  '.rstrip() = 'hello'."""
        assert StrRef("hello  ").rstrip().execute(ctx) == "hello"

    def test_split(self, ctx):
        """'a,b,c'.split(',') = ['a', 'b', 'c']."""
        assert StrRef("a,b,c").split(",").execute(ctx) == ["a", "b", "c"]

    def test_split_whitespace(self, ctx):
        """'a b c'.split() = ['a', 'b', 'c']."""
        assert StrRef("a b c").split().execute(ctx) == ["a", "b", "c"]

    def test_find(self, ctx):
        """'hello'.find('l') = 2."""
        assert StrRef("hello").find("l").execute(ctx) == 2

    def test_find_not_found(self, ctx):
        """'hello'.find('x') = -1."""
        assert StrRef("hello").find("x").execute(ctx) == -1

    def test_rfind(self, ctx):
        """'hello'.rfind('l') = 3."""
        assert StrRef("hello").rfind("l").execute(ctx) == 3

    def test_count_substring(self, ctx):
        """'abcabc'.count_substring('abc') = 2."""
        assert StrRef("abcabc").count_substring("abc").execute(ctx) == 2

    def test_startswith_true(self, ctx):
        """'hello'.startswith('he') = True."""
        assert StrRef("hello").startswith("he").execute(ctx) is True

    def test_startswith_false(self, ctx):
        """'hello'.startswith('lo') = False."""
        assert StrRef("hello").startswith("lo").execute(ctx) is False

    def test_endswith_true(self, ctx):
        """'hello'.endswith('lo') = True."""
        assert StrRef("hello").endswith("lo").execute(ctx) is True

    def test_endswith_false(self, ctx):
        """'hello'.endswith('he') = False."""
        assert StrRef("hello").endswith("he").execute(ctx) is False

    def test_isdigit_true(self, ctx):
        """'123'.isdigit() = True."""
        assert StrRef("123").isdigit().execute(ctx) is True

    def test_isdigit_false(self, ctx):
        """'12a'.isdigit() = False."""
        assert StrRef("12a").isdigit().execute(ctx) is False

    def test_isalpha_true(self, ctx):
        """'abc'.isalpha() = True."""
        assert StrRef("abc").isalpha().execute(ctx) is True

    def test_isalpha_false(self, ctx):
        """'ab1'.isalpha() = False."""
        assert StrRef("ab1").isalpha().execute(ctx) is False

    def test_isalnum_true(self, ctx):
        """'abc123'.isalnum() = True."""
        assert StrRef("abc123").isalnum().execute(ctx) is True

    def test_isalnum_false(self, ctx):
        """'abc 123'.isalnum() = False (has space)."""
        assert StrRef("abc 123").isalnum().execute(ctx) is False

    def test_isspace_true(self, ctx):
        """'   '.isspace() = True."""
        assert StrRef("   ").isspace().execute(ctx) is True

    def test_isspace_false(self, ctx):
        """'  x  '.isspace() = False."""
        assert StrRef("  x  ").isspace().execute(ctx) is False

    def test_center(self, ctx):
        """'hi'.center(6) = '  hi  '."""
        assert StrRef("hi").center(6).execute(ctx) == "  hi  "

    def test_ljust(self, ctx):
        """'hi'.ljust(5) = 'hi   '."""
        assert StrRef("hi").ljust(5).execute(ctx) == "hi   "

    def test_rjust(self, ctx):
        """'hi'.rjust(5) = '   hi'."""
        assert StrRef("hi").rjust(5).execute(ctx) == "   hi"

    def test_zfill(self, ctx):
        """'42'.zfill(5) = '00042'."""
        assert StrRef("42").zfill(5).execute(ctx) == "00042"

    def test_replace(self, ctx):
        """'hello'.replace('l', 'L') = 'heLLo'."""
        assert StrRef("hello").replace("l", "L").execute(ctx) == "heLLo"

    def test_encode(self, ctx):
        """'hello'.encode() = b'hello'."""
        assert StrRef("hello").encode().execute(ctx) == b"hello"


# =============================================================================
# BYTES OPERATIONS
# =============================================================================


class TestBytesOps:
    """Test bytes-specific operations."""

    def test_decode(self, ctx):
        """b'hello'.decode() = 'hello'."""
        assert BytesRef(b"hello").decode().execute(ctx) == "hello"

    def test_hex(self, ctx):
        """b'AB'.hex_() = '4142'."""
        assert BytesRef(b"AB").hex_().execute(ctx) == "4142"

    def test_upper(self, ctx):
        """b'hello'.upper() = b'HELLO'."""
        assert BytesRef(b"hello").upper().execute(ctx) == b"HELLO"

    def test_lower(self, ctx):
        """b'HELLO'.lower() = b'hello'."""
        assert BytesRef(b"HELLO").lower().execute(ctx) == b"hello"


# =============================================================================
# COLLECTION ACCESS OPERATIONS
# =============================================================================


class TestCollectionAccessOps:
    """Test collection access operations."""

    def test_list_index(self, ctx):
        """[1,2,3][1] = 2."""
        assert ListRef([1, 2, 3])[1].execute(ctx) == 2

    def test_list_negative_index(self, ctx):
        """[1,2,3][-1] = 3."""
        assert ListRef([1, 2, 3])[-1].execute(ctx) == 3

    def test_list_slice(self, ctx):
        """[1,2,3,4,5][1:4] = [2,3,4]."""
        assert ListRef([1, 2, 3, 4, 5])[1:4].execute(ctx) == [2, 3, 4]

    def test_dict_key(self, ctx):
        """{'a': 1}['a'] = 1."""
        assert DictRef({"a": 1})["a"].execute(ctx) == 1

    def test_str_index(self, ctx):
        """'hello'[1] = 'e'."""
        assert StrRef("hello")[1].execute(ctx) == "e"

    def test_len_list(self, ctx):
        """len([1,2,3]) = 3."""
        assert ListRef([1, 2, 3]).len_().execute(ctx) == 3

    def test_len_str(self, ctx):
        """len('hello') = 5."""
        assert StrRef("hello").len_().execute(ctx) == 5

    def test_len_dict(self, ctx):
        """len({'a': 1, 'b': 2}) = 2."""
        assert DictRef({"a": 1, "b": 2}).len_().execute(ctx) == 2

    def test_contains_list_true(self, ctx):
        """2 in [1,2,3] = True."""
        assert ListRef([1, 2, 3]).contains(2).execute(ctx) is True

    def test_contains_list_false(self, ctx):
        """5 in [1,2,3] = False."""
        assert ListRef([1, 2, 3]).contains(5).execute(ctx) is False

    def test_contains_str_true(self, ctx):
        """'ell' in 'hello' = True."""
        assert StrRef("hello").contains("ell").execute(ctx) is True

    def test_contains_dict_true(self, ctx):
        """'a' in {'a': 1} = True."""
        assert DictRef({"a": 1}).contains("a").execute(ctx) is True


# =============================================================================
# COLLECTION AGGREGATION OPERATIONS
# =============================================================================


class TestCollectionAggregationOps:
    """Test collection aggregation operations."""

    def test_sum(self, ctx):
        """sum([1,2,3]) = 6."""
        assert ListRef([1, 2, 3]).sum_().execute(ctx) == 6

    def test_min(self, ctx):
        """min([3,1,2]) = 1."""
        assert ListRef([3, 1, 2]).min_().execute(ctx) == 1

    def test_max(self, ctx):
        """max([3,1,2]) = 3."""
        assert ListRef([3, 1, 2]).max_().execute(ctx) == 3

    def test_any_true(self, ctx):
        """any([False, True, False]) = True."""
        assert ListRef([False, True, False]).any_().execute(ctx) is True

    def test_any_false(self, ctx):
        """any([False, False]) = False."""
        assert ListRef([False, False]).any_().execute(ctx) is False

    def test_all_true(self, ctx):
        """all([True, True]) = True."""
        assert ListRef([True, True]).all_().execute(ctx) is True

    def test_all_false(self, ctx):
        """all([True, False]) = False."""
        assert ListRef([True, False]).all_().execute(ctx) is False


# =============================================================================
# COLLECTION SEARCH OPERATIONS
# =============================================================================


class TestCollectionSearchOps:
    """Test collection search operations."""

    def test_first(self, ctx):
        """[1,2,3].first() = 1."""
        assert ListRef([1, 2, 3]).first().execute(ctx) == 1

    def test_last(self, ctx):
        """[1,2,3].last() = 3."""
        assert ListRef([1, 2, 3]).last().execute(ctx) == 3

    def test_index(self, ctx):
        """[1,2,3].index(2) = 1."""
        assert ListRef([1, 2, 3]).index(2).execute(ctx) == 1

    def test_count(self, ctx):
        """[1,2,2,3].count(2) = 2."""
        assert ListRef([1, 2, 2, 3]).count(2).execute(ctx) == 2


# =============================================================================
# COLLECTION TRANSFORM OPERATIONS
# =============================================================================


class TestCollectionTransformOps:
    """Test collection transform operations."""

    def test_sorted(self, ctx):
        """sorted([3,1,2]) = [1,2,3]."""
        assert ListRef([3, 1, 2]).sorted_().execute(ctx) == [1, 2, 3]

    def test_sorted_reverse(self, ctx):
        """sorted([1,2,3], reverse=True) = [3,2,1]."""
        assert ListRef([1, 2, 3]).sorted_(reverse=True).execute(ctx) == [3, 2, 1]

    def test_reversed(self, ctx):
        """reversed([1,2,3]) = [3,2,1]."""
        assert ListRef([1, 2, 3]).reversed_().execute(ctx) == [3, 2, 1]

    def test_join(self, ctx):
        """['a','b','c'].join(',') = 'a,b,c'."""
        assert ListRef(["a", "b", "c"]).join(",").execute(ctx) == "a,b,c"


# =============================================================================
# DICT OPERATIONS
# =============================================================================


class TestDictOps:
    """Test dict-specific operations."""

    def test_keys(self, ctx):
        """{'a': 1, 'b': 2}.keys_() returns keys."""
        result = DictRef({"a": 1, "b": 2}).keys_().execute(ctx)
        assert set(result) == {"a", "b"}

    def test_values(self, ctx):
        """{'a': 1, 'b': 2}.values_() returns values."""
        result = DictRef({"a": 1, "b": 2}).values_().execute(ctx)
        assert set(result) == {1, 2}

    def test_items(self, ctx):
        """{'a': 1}.items_() returns items."""
        result = DictRef({"a": 1}).items_().execute(ctx)
        assert result == [("a", 1)]

    def test_get_existing(self, ctx):
        """{'a': 1}.get_('a', 0) = 1."""
        assert DictRef({"a": 1}).get_("a", 0).execute(ctx) == 1

    def test_get_default(self, ctx):
        """{'a': 1}.get_('b', 0) = 0."""
        assert DictRef({"a": 1}).get_("b", 0).execute(ctx) == 0


# =============================================================================
# SET OPERATIONS
# =============================================================================


class TestSetOps:
    """Test set-specific operations."""

    def test_union(self, ctx):
        """{1,2} | {2,3} = {1,2,3}."""
        assert SetRef({1, 2}).union({2, 3}).execute(ctx) == {1, 2, 3}

    def test_intersection(self, ctx):
        """{1,2,3} & {2,3,4} = {2,3}."""
        assert SetRef({1, 2, 3}).intersection({2, 3, 4}).execute(ctx) == {2, 3}

    def test_difference(self, ctx):
        """{1,2,3} - {2,3} = {1}."""
        assert SetRef({1, 2, 3}).difference({2, 3}).execute(ctx) == {1}

    def test_symmetric_difference(self, ctx):
        """{1,2,3} ^ {2,3,4} = {1,4}."""
        assert SetRef({1, 2, 3}).symmetric_difference({2, 3, 4}).execute(ctx) == {1, 4}

    def test_issubset_true(self, ctx):
        """{1,2} <= {1,2,3} = True."""
        assert SetRef({1, 2}).issubset({1, 2, 3}).execute(ctx) is True

    def test_issubset_false(self, ctx):
        """{1,4} <= {1,2,3} = False."""
        assert SetRef({1, 4}).issubset({1, 2, 3}).execute(ctx) is False

    def test_issuperset_true(self, ctx):
        """{1,2,3} >= {1,2} = True."""
        assert SetRef({1, 2, 3}).issuperset({1, 2}).execute(ctx) is True

    def test_isdisjoint_true(self, ctx):
        """{1,2}.isdisjoint({3,4}) = True."""
        assert SetRef({1, 2}).isdisjoint({3, 4}).execute(ctx) is True

    def test_isdisjoint_false(self, ctx):
        """{1,2}.isdisjoint({2,3}) = False."""
        assert SetRef({1, 2}).isdisjoint({2, 3}).execute(ctx) is False


# =============================================================================
# CONDITIONAL OPERATIONS
# =============================================================================


class TestConditionalOps:
    """Test conditional operations."""

    def test_ifelse_true(self, ctx):
        """ifelse(True, 100, 0) = 100."""
        result = ifelse(BoolRef(True), IntRef(100), IntRef(0)).execute(ctx)
        assert result == 100

    def test_ifelse_false(self, ctx):
        """ifelse(False, 100, 0) = 0."""
        result = ifelse(BoolRef(False), IntRef(100), IntRef(0)).execute(ctx)
        assert result == 0

    def test_ifelse_with_comparison(self, ctx):
        """ifelse(10 > 5, 'yes', 'no') = 'yes'."""
        result = ifelse(IntRef(10) > 5, StrRef("yes"), StrRef("no")).execute(ctx)
        assert result == "yes"

    def test_or_default(self, ctx):
        """Value.or_default() returns value if not sentinel."""
        result = IntRef(42).or_default(0).execute(ctx)
        assert result == 42


# =============================================================================
# COMBINER OPERATIONS
# =============================================================================


class TestCombinerOps:
    """Test combiner functions."""

    def test_all_true(self, ctx):
        """all_(True, True, True) = True."""
        result = all_(BoolRef(True), BoolRef(True), BoolRef(True)).execute(ctx)
        assert result is True

    def test_all_false(self, ctx):
        """all_(True, False, True) = False."""
        result = all_(BoolRef(True), BoolRef(False), BoolRef(True)).execute(ctx)
        assert result is False

    def test_all_with_comparisons(self, ctx):
        """all_(5 > 3, 10 < 20) = True."""
        result = all_(IntRef(5) > 3, IntRef(10) < 20).execute(ctx)
        assert result is True

    def test_any_true(self, ctx):
        """any_(False, True, False) = True."""
        result = any_(BoolRef(False), BoolRef(True), BoolRef(False)).execute(ctx)
        assert result is True

    def test_any_false(self, ctx):
        """any_(False, False) = False."""
        result = any_(BoolRef(False), BoolRef(False)).execute(ctx)
        assert result is False

    def test_none_true(self, ctx):
        """none_(False, False) = True."""
        result = none_(BoolRef(False), BoolRef(False)).execute(ctx)
        assert result is True

    def test_none_false(self, ctx):
        """none_(False, True) = False."""
        result = none_(BoolRef(False), BoolRef(True)).execute(ctx)
        assert result is False


# =============================================================================
# SPECIAL VALUE OPERATIONS
# =============================================================================


class TestSpecialValueOps:
    """Test special value check operations."""

    def test_is_empty_false(self, ctx):
        """42.is_empty() = False."""
        assert IntRef(42).is_empty().execute(ctx) is False

    def test_is_invalid_false(self, ctx):
        """42.is_invalid() = False."""
        assert IntRef(42).is_invalid().execute(ctx) is False

    def test_is_sentinel_false(self, ctx):
        """42.is_sentinel() = False."""
        assert IntRef(42).is_sentinel().execute(ctx) is False

    def test_not_empty_true(self, ctx):
        """42.not_empty() = True."""
        assert IntRef(42).not_empty().execute(ctx) is True

    def test_not_invalid_true(self, ctx):
        """42.not_invalid() = True."""
        assert IntRef(42).not_invalid().execute(ctx) is True
