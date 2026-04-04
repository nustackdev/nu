"""Comprehensive functional tests for all operations execution.

Tests that all operations execute correctly and produce expected results.
Organized by operation category:
- Arithmetic, Bitwise, Comparison, Logical
- Type Conversion, Special Value Checks
- Collection Access, Aggregation, Search, Transform
- Conditional, Callable
"""

import pytest

from nu import INVALID, Context
from nu import (
    BoolI,
    BytesI,
    DictI,
    FloatI,
    IntI,
    ListI,
    SetI,
    StrI,
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToStrOp,
    TupleI,
    all_,
    any_,
    fn,
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
    async def test_neg_int(self, ctx):
        """-42 = -42."""
        assert await (-IntI(42)).execute(ctx) == -42

    async def test_neg_float(self, ctx):
        """-3.14 = -3.14."""
        assert await (-FloatI(3.14)).execute(ctx) == -3.14

    async def test_pos_int(self, ctx):
        """+42 = 42."""
        assert await (+IntI(42)).execute(ctx) == 42

    async def test_abs_positive(self, ctx):
        """abs(42) = 42."""
        assert await abs(IntI(42)).execute(ctx) == 42

    async def test_abs_negative(self, ctx):
        """abs(-42) = 42."""
        assert await abs(IntI(-42)).execute(ctx) == 42

    # Binary arithmetic
    async def test_add_int_int(self, ctx):
        """5 + 3 = 8."""
        assert await (IntI(5) + IntI(3)).execute(ctx) == 8

    async def test_add_int_ensure_term(self, ctx):
        """5 + 3 = 8 (with literal)."""
        assert await (IntI(5) + 3).execute(ctx) == 8

    async def test_add_float_float(self, ctx):
        """1.5 + 2.5 = 4.0."""
        assert await (FloatI(1.5) + FloatI(2.5)).execute(ctx) == 4.0

    async def test_add_int_float(self, ctx):
        """5 + 2.5 = 7.5."""
        assert await (IntI(5) + 2.5).execute(ctx) == 7.5

    async def test_add_str_str(self, ctx):
        """'hello' + ' world' = 'hello world'."""
        assert await (StrI("hello") + " world").execute(ctx) == "hello world"

    async def test_add_list_list(self, ctx):
        """[1,2] + [3,4] = [1,2,3,4]."""
        assert await (ListI([1, 2]) + [3, 4]).execute(ctx) == [1, 2, 3, 4]  # noqa: RUF005

    async def test_radd(self, ctx):
        """5 + IntI(3) = 8."""
        assert await (5 + IntI(3)).execute(ctx) == 8

    async def test_sub_int_int(self, ctx):
        """10 - 4 = 6."""
        assert await (IntI(10) - IntI(4)).execute(ctx) == 6

    async def test_rsub(self, ctx):
        """10 - IntI(4) = 6."""
        assert await (10 - IntI(4)).execute(ctx) == 6

    async def test_mul_int_int(self, ctx):
        """6 * 7 = 42."""
        assert await (IntI(6) * IntI(7)).execute(ctx) == 42

    async def test_mul_float_float(self, ctx):
        """2.5 * 4.0 = 10.0."""
        assert await (FloatI(2.5) * FloatI(4.0)).execute(ctx) == 10.0

    async def test_rmul(self, ctx):
        """6 * IntI(7) = 42."""
        assert await (6 * IntI(7)).execute(ctx) == 42

    async def test_div_int_int(self, ctx):
        """10 / 4 = 2.5."""
        assert await (IntI(10) / IntI(4)).execute(ctx) == 2.5

    async def test_div_by_zero(self, ctx):
        """10 / 0 = INVALID."""
        assert await (IntI(10) / 0).execute(ctx) is INVALID

    async def test_rdiv(self, ctx):
        """20 / IntI(4) = 5.0."""
        assert await (20 / IntI(4)).execute(ctx) == 5.0

    async def test_floordiv_int_int(self, ctx):
        """10 // 3 = 3."""
        assert await (IntI(10) // IntI(3)).execute(ctx) == 3

    async def test_floordiv_by_zero(self, ctx):
        """10 // 0 = INVALID."""
        assert await (IntI(10) // 0).execute(ctx) is INVALID

    async def test_rfloordiv(self, ctx):
        """10 // IntI(3) = 3."""
        assert await (10 // IntI(3)).execute(ctx) == 3

    async def test_mod_int_int(self, ctx):
        """10 % 3 = 1."""
        assert await (IntI(10) % IntI(3)).execute(ctx) == 1

    async def test_mod_by_zero(self, ctx):
        """10 % 0 = INVALID."""
        assert await (IntI(10) % 0).execute(ctx) is INVALID

    async def test_rmod(self, ctx):
        """10 % IntI(3) = 1."""
        assert await (10 % IntI(3)).execute(ctx) == 1

    async def test_pow_int_int(self, ctx):
        """2 ** 10 = 1024."""
        assert await (IntI(2) ** IntI(10)).execute(ctx) == 1024

    async def test_pow_float(self, ctx):
        """2.0 ** 3 = 8.0."""
        assert await (FloatI(2.0) ** 3).execute(ctx) == 8.0

    async def test_rpow(self, ctx):
        """2 ** IntI(10) = 1024."""
        assert await (2 ** IntI(10)).execute(ctx) == 1024


# =============================================================================
# BITWISE OPERATIONS
# =============================================================================


class TestBitwiseOps:
    """Test all bitwise operations."""

    async def test_bitwise_and(self, ctx):
        """0b1100 & 0b1010 = 0b1000."""
        assert await IntI(0b1100).bitand(0b1010).execute(ctx) == 0b1000

    async def test_bitwise_or(self, ctx):
        """0b1100 | 0b1010 = 0b1110."""
        assert await IntI(0b1100).bitor(0b1010).execute(ctx) == 0b1110

    async def test_bitwise_xor(self, ctx):
        """0b1100 ^ 0b1010 = 0b0110."""
        assert await (IntI(0b1100) ^ 0b1010).execute(ctx) == 0b0110

    async def test_bitwise_not(self, ctx):
        """~1 = -2."""
        assert await IntI(1).bitnot().execute(ctx) == -2

    async def test_left_shift(self, ctx):
        """1 << 4 = 16."""
        assert await (IntI(1) << 4).execute(ctx) == 16

    async def test_right_shift(self, ctx):
        """16 >> 2 = 4."""
        assert await (IntI(16) >> 2).execute(ctx) == 4

    async def test_rxor(self, ctx):
        """0b1010 ^ IntI(0b1100) = 0b0110."""
        assert await (0b1010 ^ IntI(0b1100)).execute(ctx) == 0b0110


# =============================================================================
# COMPARISON OPERATIONS
# =============================================================================


class TestComparisonOps:
    """Test all comparison operations."""

    async def test_gt_true(self, ctx):
        """10 > 5 = True."""
        assert await (IntI(10) > 5).execute(ctx) is True

    async def test_gt_false(self, ctx):
        """5 > 10 = False."""
        assert await (IntI(5) > 10).execute(ctx) is False

    async def test_gt_equal(self, ctx):
        """10 > 10 = False."""
        assert await (IntI(10) > 10).execute(ctx) is False

    async def test_lt_true(self, ctx):
        """5 < 10 = True."""
        assert await (IntI(5) < 10).execute(ctx) is True

    async def test_lt_false(self, ctx):
        """10 < 5 = False."""
        assert await (IntI(10) < 5).execute(ctx) is False

    async def test_ge_true_greater(self, ctx):
        """10 >= 5 = True."""
        assert await (IntI(10) >= 5).execute(ctx) is True

    async def test_ge_true_equal(self, ctx):
        """10 >= 10 = True."""
        assert await (IntI(10) >= 10).execute(ctx) is True

    async def test_ge_false(self, ctx):
        """5 >= 10 = False."""
        assert await (IntI(5) >= 10).execute(ctx) is False

    async def test_le_true_less(self, ctx):
        """5 <= 10 = True."""
        assert await (IntI(5) <= 10).execute(ctx) is True

    async def test_le_true_equal(self, ctx):
        """10 <= 10 = True."""
        assert await (IntI(10) <= 10).execute(ctx) is True

    async def test_le_false(self, ctx):
        """10 <= 5 = False."""
        assert await (IntI(10) <= 5).execute(ctx) is False

    async def test_eq_true(self, ctx):
        """42 == 42 = True."""
        assert await IntI(42).eq(42).execute(ctx) is True

    async def test_eq_false(self, ctx):
        """42 == 10 = False."""
        assert await IntI(42).eq(10).execute(ctx) is False

    async def test_ne_true(self, ctx):
        """42 != 10 = True."""
        assert await IntI(42).ne(10).execute(ctx) is True

    async def test_ne_false(self, ctx):
        """42 != 42 = False."""
        assert await IntI(42).ne(42).execute(ctx) is False

    async def test_str_comparison(self, ctx):
        """'abc' < 'abd' = True."""
        assert await (StrI("abc") < "abd").execute(ctx) is True

    async def test_float_comparison(self, ctx):
        """3.14 > 3.0 = True."""
        assert await (FloatI(3.14) > 3.0).execute(ctx) is True


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


class TestLogicalOps:
    """Test all logical operations."""

    async def test_not_true(self, ctx):
        """not True = False."""
        assert await BoolI(True).not_().execute(ctx) is False

    async def test_not_false(self, ctx):
        """not False = True."""
        assert await BoolI(False).not_().execute(ctx) is True

    async def test_and_true_true(self, ctx):
        """True and True = True."""
        assert await BoolI(True).and_(True).execute(ctx) is True

    async def test_and_true_false(self, ctx):
        """True and False = False."""
        assert await BoolI(True).and_(False).execute(ctx) is False

    async def test_and_false_true(self, ctx):
        """False and True = False."""
        assert await BoolI(False).and_(True).execute(ctx) is False

    async def test_and_false_false(self, ctx):
        """False and False = False."""
        assert await BoolI(False).and_(False).execute(ctx) is False

    async def test_or_true_true(self, ctx):
        """True or True = True."""
        assert await BoolI(True).or_(True).execute(ctx) is True

    async def test_or_true_false(self, ctx):
        """True or False = True."""
        assert await BoolI(True).or_(False).execute(ctx) is True

    async def test_or_false_true(self, ctx):
        """False or True = True."""
        assert await BoolI(False).or_(True).execute(ctx) is True

    async def test_or_false_false(self, ctx):
        """False or False = False."""
        assert await BoolI(False).or_(False).execute(ctx) is False

    async def test_bool_truthy(self, ctx):
        """bool(42) = True."""
        assert await IntI(42).bool_().execute(ctx) is True

    async def test_bool_falsy(self, ctx):
        """bool(0) = False."""
        assert await IntI(0).bool_().execute(ctx) is False

    async def test_bool_empty_string(self, ctx):
        """bool('') = False."""
        assert await StrI("").bool_().execute(ctx) is False

    async def test_bool_nonempty_string(self, ctx):
        """bool('x') = True."""
        assert await StrI("x").bool_().execute(ctx) is True


# =============================================================================
# TYPE CONVERSION OPERATIONS
# =============================================================================


class TestConversionOps:
    """Test all type conversion operations via standalone morphisms."""

    async def test_to_int_from_float(self, ctx):
        """int(3.14) = 3."""
        assert await IntI(ToIntOp(FloatI(3.14))).execute(ctx) == 3

    async def test_to_int_from_str(self, ctx):
        """int('42') = 42."""
        assert await IntI(ToIntOp(StrI("42"))).execute(ctx) == 42

    async def test_to_int_from_bool(self, ctx):
        """int(True) = 1."""
        assert await IntI(ToIntOp(BoolI(True))).execute(ctx) == 1

    async def test_to_float_from_int(self, ctx):
        """float(42) = 42.0."""
        assert await FloatI(ToFloatOp(IntI(42))).execute(ctx) == 42.0

    async def test_to_float_from_str(self, ctx):
        """float('3.14') = 3.14."""
        assert await FloatI(ToFloatOp(StrI("3.14"))).execute(ctx) == 3.14

    async def test_to_str_from_int(self, ctx):
        """str(42) = '42'."""
        assert await StrI(ToStrOp(IntI(42))).execute(ctx) == "42"

    async def test_to_str_from_float(self, ctx):
        """str(3.14) = '3.14'."""
        assert await StrI(ToStrOp(FloatI(3.14))).execute(ctx) == "3.14"

    async def test_to_str_from_bool(self, ctx):
        """str(True) = 'True'."""
        assert await StrI(ToStrOp(BoolI(True))).execute(ctx) == "True"

    async def test_to_bool_from_int_truthy(self, ctx):
        """bool(42) = True."""
        assert await BoolI(ToBoolOp(IntI(42))).execute(ctx) is True

    async def test_to_bool_from_int_falsy(self, ctx):
        """bool(0) = False."""
        assert await BoolI(ToBoolOp(IntI(0))).execute(ctx) is False

    async def test_to_list_from_tuple(self, ctx):
        """list((1,2,3)) = [1,2,3]."""
        assert await ListI(ToListOp(TupleI((1, 2, 3)))).execute(ctx) == [1, 2, 3]

    async def test_to_bytes_from_str(self, ctx):
        """'hello'.encode() = b'hello'."""
        assert await BytesI(ToBytesOp(StrI("hello"))).execute(ctx) == b"hello"


# =============================================================================
# STRING OPERATIONS
# =============================================================================


class TestStringOps:
    """Test string-specific operations."""

    async def test_upper(self, ctx):
        """'hello'.upper() = 'HELLO'."""
        assert await StrI("hello").upper().execute(ctx) == "HELLO"

    async def test_lower(self, ctx):
        """'HELLO'.lower() = 'hello'."""
        assert await StrI("HELLO").lower().execute(ctx) == "hello"

    async def test_title(self, ctx):
        """'hello world'.title() = 'Hello World'."""
        assert await StrI("hello world").title().execute(ctx) == "Hello World"

    async def test_capitalize(self, ctx):
        """'hello'.capitalize() = 'Hello'."""
        assert await StrI("hello").capitalize().execute(ctx) == "Hello"

    async def test_swapcase(self, ctx):
        """'HeLLo'.swapcase() = 'hEllO'."""
        assert await StrI("HeLLo").swapcase().execute(ctx) == "hEllO"

    async def test_strip(self, ctx):
        """'  hello  '.strip() = 'hello'."""
        assert await StrI("  hello  ").strip().execute(ctx) == "hello"

    async def test_strip_chars(self, ctx):
        """'xxhelloxx'.strip('x') = 'hello'."""
        assert await StrI("xxhelloxx").strip("x").execute(ctx) == "hello"

    async def test_lstrip(self, ctx):
        """'  hello'.lstrip() = 'hello'."""
        assert await StrI("  hello").lstrip().execute(ctx) == "hello"

    async def test_rstrip(self, ctx):
        """'hello  '.rstrip() = 'hello'."""
        assert await StrI("hello  ").rstrip().execute(ctx) == "hello"

    async def test_split(self, ctx):
        """'a,b,c'.split(',') = ['a', 'b', 'c']."""
        assert await StrI("a,b,c").split(",").execute(ctx) == ["a", "b", "c"]

    async def test_split_whitespace(self, ctx):
        """'a b c'.split() = ['a', 'b', 'c']."""
        assert await StrI("a b c").split().execute(ctx) == ["a", "b", "c"]

    async def test_find(self, ctx):
        """'hello'.find('l') = 2."""
        assert await StrI("hello").find("l").execute(ctx) == 2

    async def test_find_not_found(self, ctx):
        """'hello'.find('x') = -1."""
        assert await StrI("hello").find("x").execute(ctx) == -1

    async def test_rfind(self, ctx):
        """'hello'.rfind('l') = 3."""
        assert await StrI("hello").rfind("l").execute(ctx) == 3

    async def test_count_substring(self, ctx):
        """'abcabc'.count_substring('abc') = 2."""
        assert await StrI("abcabc").count_substring("abc").execute(ctx) == 2

    async def test_startswith_true(self, ctx):
        """'hello'.startswith('he') = True."""
        assert await StrI("hello").startswith("he").execute(ctx) is True

    async def test_startswith_false(self, ctx):
        """'hello'.startswith('lo') = False."""
        assert await StrI("hello").startswith("lo").execute(ctx) is False

    async def test_endswith_true(self, ctx):
        """'hello'.endswith('lo') = True."""
        assert await StrI("hello").endswith("lo").execute(ctx) is True

    async def test_endswith_false(self, ctx):
        """'hello'.endswith('he') = False."""
        assert await StrI("hello").endswith("he").execute(ctx) is False

    async def test_isdigit_true(self, ctx):
        """'123'.isdigit() = True."""
        assert await StrI("123").isdigit().execute(ctx) is True

    async def test_isdigit_false(self, ctx):
        """'12a'.isdigit() = False."""
        assert await StrI("12a").isdigit().execute(ctx) is False

    async def test_isalpha_true(self, ctx):
        """'abc'.isalpha() = True."""
        assert await StrI("abc").isalpha().execute(ctx) is True

    async def test_isalpha_false(self, ctx):
        """'ab1'.isalpha() = False."""
        assert await StrI("ab1").isalpha().execute(ctx) is False

    async def test_isalnum_true(self, ctx):
        """'abc123'.isalnum() = True."""
        assert await StrI("abc123").isalnum().execute(ctx) is True

    async def test_isalnum_false(self, ctx):
        """'abc 123'.isalnum() = False (has space)."""
        assert await StrI("abc 123").isalnum().execute(ctx) is False

    async def test_isspace_true(self, ctx):
        """'   '.isspace() = True."""
        assert await StrI("   ").isspace().execute(ctx) is True

    async def test_isspace_false(self, ctx):
        """'  x  '.isspace() = False."""
        assert await StrI("  x  ").isspace().execute(ctx) is False

    async def test_center(self, ctx):
        """'hi'.center(6) = '  hi  '."""
        assert await StrI("hi").center(6).execute(ctx) == "  hi  "

    async def test_ljust(self, ctx):
        """'hi'.ljust(5) = 'hi   '."""
        assert await StrI("hi").ljust(5).execute(ctx) == "hi   "

    async def test_rjust(self, ctx):
        """'hi'.rjust(5) = '   hi'."""
        assert await StrI("hi").rjust(5).execute(ctx) == "   hi"

    async def test_zfill(self, ctx):
        """'42'.zfill(5) = '00042'."""
        assert await StrI("42").zfill(5).execute(ctx) == "00042"

    async def test_replace(self, ctx):
        """'hello'.replace('l', 'L') = 'heLLo'."""
        assert await StrI("hello").replace("l", "L").execute(ctx) == "heLLo"

    async def test_encode(self, ctx):
        """'hello'.encode() = b'hello'."""
        assert await StrI("hello").encode().execute(ctx) == b"hello"


# =============================================================================
# BYTES OPERATIONS
# =============================================================================


class TestBytesOps:
    """Test bytes-specific operations."""

    async def test_decode(self, ctx):
        """b'hello'.decode() = 'hello'."""
        assert await BytesI(b"hello").decode().execute(ctx) == "hello"

    async def test_hex(self, ctx):
        """b'AB'.hex_() = '4142'."""
        assert await BytesI(b"AB").hex_().execute(ctx) == "4142"

    async def test_upper(self, ctx):
        """b'hello'.upper() = b'HELLO'."""
        assert await BytesI(b"hello").upper().execute(ctx) == b"HELLO"

    async def test_lower(self, ctx):
        """b'HELLO'.lower() = b'hello'."""
        assert await BytesI(b"HELLO").lower().execute(ctx) == b"hello"


# =============================================================================
# COLLECTION ACCESS OPERATIONS
# =============================================================================


class TestCollectionAccessOps:
    """Test collection access operations."""

    async def test_list_index(self, ctx):
        """[1,2,3][1] = 2."""
        assert await ListI([1, 2, 3])[1].execute(ctx) == 2

    async def test_list_negative_index(self, ctx):
        """[1,2,3][-1] = 3."""
        assert await ListI([1, 2, 3])[-1].execute(ctx) == 3

    async def test_list_slice(self, ctx):
        """[1,2,3,4,5][1:4] = [2,3,4]."""
        assert await ListI([1, 2, 3, 4, 5])[1:4].execute(ctx) == [2, 3, 4]

    async def test_dict_key(self, ctx):
        """{'a': 1}['a'] = 1."""
        assert await DictI({"a": 1})["a"].execute(ctx) == 1

    async def test_str_index(self, ctx):
        """'hello'[1] = 'e'."""
        assert await StrI("hello")[1].execute(ctx) == "e"

    async def test_len_list(self, ctx):
        """len([1,2,3]) = 3."""
        assert await fn.Len(ListI([1, 2, 3])).execute(ctx) == 3

    async def test_len_str(self, ctx):
        """len('hello') = 5."""
        assert await fn.Len(StrI("hello")).execute(ctx) == 5

    async def test_len_dict(self, ctx):
        """len({'a': 1, 'b': 2}) = 2."""
        assert await fn.Len(DictI({"a": 1, "b": 2})).execute(ctx) == 2

    async def test_contains_list_true(self, ctx):
        """2 in [1,2,3] = True."""
        assert await fn.Contains(ListI([1, 2, 3]), 2).execute(ctx) is True

    async def test_contains_list_false(self, ctx):
        """5 in [1,2,3] = False."""
        assert await fn.Contains(ListI([1, 2, 3]), 5).execute(ctx) is False

    async def test_contains_str_true(self, ctx):
        """'ell' in 'hello' = True."""
        assert await fn.Contains(StrI("hello"), "ell").execute(ctx) is True

    async def test_contains_dict_true(self, ctx):
        """'a' in {'a': 1} = True."""
        assert await fn.Contains(DictI({"a": 1}), "a").execute(ctx) is True


# =============================================================================
# COLLECTION AGGREGATION OPERATIONS
# =============================================================================


class TestCollectionAggregationOps:
    """Test collection aggregation operations."""

    async def test_sum(self, ctx):
        """Sum([1,2,3]) = 6."""
        assert await fn.Sum(ListI([1, 2, 3])).execute(ctx) == 6

    async def test_min(self, ctx):
        """Min([3,1,2]) = 1."""
        assert await fn.Min(ListI([3, 1, 2])).execute(ctx) == 1

    async def test_max(self, ctx):
        """Max([3,1,2]) = 3."""
        assert await fn.Max(ListI([3, 1, 2])).execute(ctx) == 3

    async def test_any_true(self, ctx):
        """Any([False, True, False]) = True."""
        assert await fn.Any(ListI([False, True, False])).execute(ctx) is True

    async def test_any_false(self, ctx):
        """Any([False, False]) = False."""
        assert await fn.Any(ListI([False, False])).execute(ctx) is False

    async def test_all_true(self, ctx):
        """All([True, True]) = True."""
        assert await fn.All(ListI([True, True])).execute(ctx) is True

    async def test_all_false(self, ctx):
        """All([True, False]) = False."""
        assert await fn.All(ListI([True, False])).execute(ctx) is False


# =============================================================================
# COLLECTION SEARCH OPERATIONS
# =============================================================================


class TestCollectionSearchOps:
    """Test collection search operations."""

    async def test_first(self, ctx):
        """[1,2,3].first() = 1."""
        assert await ListI([1, 2, 3]).first().execute(ctx) == 1

    async def test_last(self, ctx):
        """[1,2,3].last() = 3."""
        assert await ListI([1, 2, 3]).last().execute(ctx) == 3

    async def test_index(self, ctx):
        """[1,2,3].index(2) = 1."""
        assert await ListI([1, 2, 3]).index(2).execute(ctx) == 1

    async def test_count(self, ctx):
        """[1,2,2,3].count(2) = 2."""
        assert await ListI([1, 2, 2, 3]).count(2).execute(ctx) == 2


# =============================================================================
# COLLECTION TRANSFORM OPERATIONS
# =============================================================================


class TestCollectionTransformOps:
    """Test collection transform operations."""

    async def test_sorted(self, ctx):
        """Sorted([3,1,2]) = [1,2,3]."""
        assert await fn.Sorted(ListI([3, 1, 2])).execute(ctx) == [1, 2, 3]

    async def test_sorted_reverse(self, ctx):
        """Sorted([1,2,3], reverse=True) = [3,2,1]."""
        assert await fn.Sorted(ListI([1, 2, 3]), reverse=True).execute(ctx) == [3, 2, 1]

    async def test_reversed(self, ctx):
        """Reversed([1,2,3]).to_list() = [3,2,1]."""
        assert await fn.Reversed(ListI([1, 2, 3])).to_list().execute(ctx) == [3, 2, 1]

    async def test_join(self, ctx):
        """StrI(',').join(['a','b','c']) = 'a,b,c'."""
        from nu.interfaces.primitives import StrI

        assert await StrI(",").join(ListI(["a", "b", "c"])).execute(ctx) == "a,b,c"


# =============================================================================
# DICT OPERATIONS
# =============================================================================


class TestDictOps:
    """Test dict-specific operations."""

    async def test_keys(self, ctx):
        """{'a': 1, 'b': 2}.keys() returns keys."""
        result = await DictI({"a": 1, "b": 2}).keys().execute(ctx)
        assert set(result) == {"a", "b"}

    async def test_values(self, ctx):
        """{'a': 1, 'b': 2}.values() returns values."""
        result = await DictI({"a": 1, "b": 2}).values().execute(ctx)
        assert set(result) == {1, 2}

    async def test_items(self, ctx):
        """{'a': 1}.items() returns items."""
        result = await DictI({"a": 1}).items().execute(ctx)
        assert set(result) == {("a", 1)}

    async def test_get_existing(self, ctx):
        """{'a': 1}.get('a', 0) = 1."""
        assert await DictI({"a": 1}).get("a", 0).execute(ctx) == 1

    async def test_get_default(self, ctx):
        """{'a': 1}.get('b', 0) = 0."""
        assert await DictI({"a": 1}).get("b", 0).execute(ctx) == 0


# =============================================================================
# SET OPERATIONS
# =============================================================================


class TestSetOps:
    """Test set-specific operations."""

    async def test_union(self, ctx):
        """{1,2} | {2,3} = {1,2,3}."""
        assert await SetI({1, 2}).union({2, 3}).execute(ctx) == {1, 2, 3}

    async def test_intersection(self, ctx):
        """{1,2,3} & {2,3,4} = {2,3}."""
        assert await SetI({1, 2, 3}).intersection({2, 3, 4}).execute(ctx) == {2, 3}

    async def test_difference(self, ctx):
        """{1,2,3} - {2,3} = {1}."""
        assert await SetI({1, 2, 3}).difference({2, 3}).execute(ctx) == {1}

    async def test_symmetric_difference(self, ctx):
        """{1,2,3} ^ {2,3,4} = {1,4}."""
        assert await SetI({1, 2, 3}).symmetric_difference({2, 3, 4}).execute(ctx) == {1, 4}

    async def test_issubset_true(self, ctx):
        """{1,2} <= {1,2,3} = True."""
        assert await SetI({1, 2}).issubset({1, 2, 3}).execute(ctx) is True

    async def test_issubset_false(self, ctx):
        """{1,4} <= {1,2,3} = False."""
        assert await SetI({1, 4}).issubset({1, 2, 3}).execute(ctx) is False

    async def test_issuperset_true(self, ctx):
        """{1,2,3} >= {1,2} = True."""
        assert await SetI({1, 2, 3}).issuperset({1, 2}).execute(ctx) is True

    async def test_isdisjoint_true(self, ctx):
        """{1,2}.isdisjoint({3,4}) = True."""
        assert await SetI({1, 2}).isdisjoint({3, 4}).execute(ctx) is True

    async def test_isdisjoint_false(self, ctx):
        """{1,2}.isdisjoint({2,3}) = False."""
        assert await SetI({1, 2}).isdisjoint({2, 3}).execute(ctx) is False


# =============================================================================
# COMBINER OPERATIONS
# =============================================================================


class TestCombinerOps:
    """Test combiner functions."""

    async def test_all_true(self, ctx):
        """all_(True, True, True) = True."""
        result = await all_(BoolI(True), BoolI(True), BoolI(True)).execute(ctx)
        assert result is True

    async def test_all_false(self, ctx):
        """all_(True, False, True) = False."""
        result = await all_(BoolI(True), BoolI(False), BoolI(True)).execute(ctx)
        assert result is False

    async def test_all_with_comparisons(self, ctx):
        """all_(5 > 3, 10 < 20) = True."""
        result = await all_(IntI(5) > 3, IntI(10) < 20).execute(ctx)
        assert result is True

    async def test_any_true(self, ctx):
        """any_(False, True, False) = True."""
        result = await any_(BoolI(False), BoolI(True), BoolI(False)).execute(ctx)
        assert result is True

    async def test_any_false(self, ctx):
        """any_(False, False) = False."""
        result = await any_(BoolI(False), BoolI(False)).execute(ctx)
        assert result is False

    async def test_none_true(self, ctx):
        """none_(False, False) = True."""
        result = await none_(BoolI(False), BoolI(False)).execute(ctx)
        assert result is True

    async def test_none_false(self, ctx):
        """none_(False, True) = False."""
        result = await none_(BoolI(False), BoolI(True)).execute(ctx)
        assert result is False


# =============================================================================
# SPECIAL VALUE OPERATIONS
# =============================================================================


class TestSpecialValueOps:
    """Test special value check operations."""

    async def test_is_empty_false(self, ctx):
        """42.is_empty() = False."""
        assert await IntI(42).is_empty().execute(ctx) is False

    async def test_is_invalid_false(self, ctx):
        """42.is_invalid() = False."""
        assert await IntI(42).is_invalid().execute(ctx) is False

    async def test_is_sentinel_false(self, ctx):
        """42.is_sentinel() = False."""
        assert await IntI(42).is_sentinel().execute(ctx) is False

    async def test_not_empty_true(self, ctx):
        """42.not_empty() = True."""
        assert await IntI(42).not_empty().execute(ctx) is True

    async def test_not_invalid_true(self, ctx):
        """42.not_invalid() = True."""
        assert await IntI(42).not_invalid().execute(ctx) is True
