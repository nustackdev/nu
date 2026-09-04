"""Any - dynamic/unknown type interface.

The honest terminal for value-Form descent: genuinely-unknown or dynamically
typed values live here. Every operation on an ``Any`` is absorbing -
arithmetic, bitwise, subscript, and attribute access all yield another
``Any``; comparison and logical ops yield ``Bool``.

Reserved at the ``Nu`` base and deliberately NOT overridden here:

- ``__and__`` -> ``Race`` (flow), ``__or__`` -> ``Parallel`` (flow).
  Use ``bitand()`` / ``bitor()`` for bitwise instead.

Protocol dunders (``__len__``, ``__contains__``, ``__iter__``, ``__bool__``,
``__int__``, ``__float__``, ...) require Python-native return types and
cannot be part of a Nu tree. They are exposed as named methods
(``len_()``, ``contains()``, ``iter_()``, ``bool_()``) that return the
matching Form so the tree stays symbolic.

Mutation via ``__setitem__`` / ``__delitem__`` is Ref-gated: the underlying
source must be a ``Ref`` (fabric-writable), otherwise Python's assign-syntax
would silently discard the resulting ``Command`` node and produce an
invalid tree. A clear ``TypeError`` fires at build time in that case.

There is deliberately no ``__call__`` here - Nu programs run through
interactions (built via ``host`` or hand-written), not raw
Python callable dispatch. If you have a callable value in a Nu tree, wrap
it in the appropriate interaction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.lang import Form, Ref, TypedNu


if TYPE_CHECKING:
    from ..collections.iterator_ import Iterator
    from .bool_ import Bool
    from .int_ import Int


__all__ = [
    "Any",
]


class Any(Form, TypedNu[Any]):
    """Wildcard interface. Full operator surface, no promise about the runtime type.

    Arithmetic, bitwise, subscript, and attribute descent are all
    absorbing: the result of any of them is another Any, since the
    concrete type isn't known until evaluation. Comparison and logical
    operators are the exception - they still yield Bool, because "is
    this true" is a well-typed question even when the operand type
    isn't.

    Notes:
        - Typed as `TypedNu[Any]`, not `TypedNu[object]`. That lets an
          Any value slot into any narrow Arg position (IntArg, StrArg,
          ...), so `intref + anyval` resolves through Int's `__add__`
          and lands as Int instead of falling through to Any's `__radd__`.
        - `&` and `|` are reserved at the Nu base for flow (`Race`,
          `Parallel`) and are not overridden here. Use `bitand()` /
          `bitor()` for bitwise.
        - There's no `__call__`. A callable value in a Nu tree goes
          through an interaction (built via `host` or hand-written),
          not raw Python call dispatch.

    Example:
        >>> nu.run(nu.Any(6) * nu.Any(7))[0]
        42
    """

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: object) -> Any:
        """Sum of self and other.

        Args:
            other: the value to add to self. Any type; the result stays
                Any regardless.

        Yields:
            The sum. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(2) + nu.Any(3))[0]
            5
        """
        from nu.core import Add

        return Any(Add(self, other))

    def __radd__(self, other: object) -> Any:
        """Sum of other and self, with self on the right.

        Args:
            other: the value on the left of the `+`.

        Notes:
            - Reached only when the left operand's own `__add__` declines,
              e.g. a plain Python value that doesn't know about Any.

        Yields:
            The sum. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(3 + nu.Any(2))[0]
            5
        """
        from nu.core import Add

        return Any(Add(other, self))

    def __sub__(self, other: object) -> Any:
        """Self minus other.

        Args:
            other: the value to subtract from self.

        Yields:
            The difference. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(10) - nu.Any(3))[0]
            7
        """
        from nu.core import Sub

        return Any(Sub(self, other))

    def __rsub__(self, other: object) -> Any:
        """Other minus self, with self on the right.

        Args:
            other: the value on the left of the `-`, the minuend.

        Notes:
            - Reached only when the left operand's own `__sub__` declines.

        Yields:
            The difference. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(10 - nu.Any(3))[0]
            7
        """
        from nu.core import Sub

        return Any(Sub(other, self))

    def __mul__(self, other: object) -> Any:
        """Product of self and other.

        Args:
            other: the value to multiply self by.

        Yields:
            The product. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(6) * nu.Any(7))[0]
            42
        """
        from nu.core import Mul

        return Any(Mul(self, other))

    def __rmul__(self, other: object) -> Any:
        """Product of other and self, with self on the right.

        Args:
            other: the value on the left of the `*`.

        Notes:
            - Reached only when the left operand's own `__mul__` declines.

        Yields:
            The product. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(3 * nu.Any(4))[0]
            12
        """
        from nu.core import Mul

        return Any(Mul(other, self))

    def __matmul__(self, other: object) -> Any:
        """Matrix multiplication: self @ other.

        Args:
            other: the right operand. Needs a type that supports Python's
                matmul protocol (e.g. a numpy array); plain numbers don't.

        Yields:
            The product. INVALID when either operand is a sentinel. Raises
            at evaluation time when neither operand supports `@`.
        """
        from nu.core import MatMul

        return Any(MatMul(self, other))

    def __rmatmul__(self, other: object) -> Any:
        """Matrix multiplication: other @ self, with self on the right.

        Args:
            other: the left operand, on the left of the `@`.

        Notes:
            - Reached only when the left operand's own `__matmul__`
              declines.

        Yields:
            The product. INVALID when either operand is a sentinel. Raises
            at evaluation time when neither operand supports `@`.
        """
        from nu.core import MatMul

        return Any(MatMul(other, self))

    def __truediv__(self, other: object) -> Any:
        """Self divided by other.

        Args:
            other: the divisor.

        Notes:
            - A zero divisor is not caught here; the underlying Div raises
              at evaluation time.

        Yields:
            The quotient. INVALID when either operand is a sentinel.
            Raises at evaluation time when the divisor is zero.

        Example:
            >>> nu.run(nu.Any(7) / nu.Any(2))[0]
            3.5
        """
        from nu.core import Div

        return Any(Div(self, other))

    def __rtruediv__(self, other: object) -> Any:
        """Other divided by self, with self as the divisor.

        Args:
            other: the numerator, on the left of the `/`.

        Notes:
            - Reached only when the left operand's own `__truediv__`
              declines.

        Yields:
            The quotient. INVALID when either operand is a sentinel.
            Raises at evaluation time when self evaluates to zero.

        Example:
            >>> nu.run(10 / nu.Any(4))[0]
            2.5
        """
        from nu.core import Div

        return Any(Div(other, self))

    def __floordiv__(self, other: object) -> Any:
        """Self floor-divided by other.

        Args:
            other: the divisor.

        Notes:
            - Rounds toward negative infinity, as Python's `//` does.

        Yields:
            The floored quotient. INVALID when either operand is a
            sentinel. Raises at evaluation time when the divisor is zero.

        Example:
            >>> nu.run(nu.Any(7) // nu.Any(2))[0]
            3
        """
        from nu.core import FloorDiv

        return Any(FloorDiv(self, other))

    def __rfloordiv__(self, other: object) -> Any:
        """Other floor-divided by self, with self as the divisor.

        Args:
            other: the numerator, on the left of the `//`.

        Notes:
            - Reached only when the left operand's own `__floordiv__`
              declines.

        Yields:
            The floored quotient. INVALID when either operand is a
            sentinel.

        Example:
            >>> nu.run(-7 // nu.Any(2))[0]
            -4
        """
        from nu.core import FloorDiv

        return Any(FloorDiv(other, self))

    def __mod__(self, other: object) -> Any:
        """Self modulo other.

        Args:
            other: the divisor.

        Notes:
            - The result's sign follows the divisor, as Python's `%` does.

        Yields:
            The remainder. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(7) % nu.Any(3))[0]
            1
        """
        from nu.core import Mod

        return Any(Mod(self, other))

    def __rmod__(self, other: object) -> Any:
        """Other modulo self, with self as the divisor.

        Args:
            other: the value being divided, on the left of the `%`.

        Notes:
            - The result's sign follows the divisor, which here is self.
            - Reached only when the left operand's own `__mod__` declines.

        Yields:
            The remainder. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(-7 % nu.Any(3))[0]
            2
        """
        from nu.core import Mod

        return Any(Mod(other, self))

    def __pow__(self, other: object) -> Any:
        """Self raised to the other power.

        Args:
            other: the exponent.

        Yields:
            The power. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(2) ** nu.Any(10))[0]
            1024
        """
        from nu.core import Pow

        return Any(Pow(self, other))

    def __rpow__(self, other: object) -> Any:
        """Other raised to the self power, with self as the exponent.

        Args:
            other: the base, on the left of the `**`.

        Notes:
            - Reached only when the left operand's own `__pow__` declines.

        Yields:
            The power. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(2 ** nu.Any(10))[0]
            1024
        """
        from nu.core import Pow

        return Any(Pow(other, self))

    def __neg__(self) -> Any:
        """Negation of self.

        Yields:
            The negation. INVALID when self is a sentinel.

        Example:
            >>> nu.run(-nu.Any(4))[0]
            -4
        """
        from nu.core import Neg

        return Any(Neg(self))

    def __pos__(self) -> Any:
        """Self unchanged.

        Notes:
            - Identity for numbers. Kept for symmetry with `__neg__` and so
              `+x` inside an expression is still a Nu term.

        Yields:
            The value unchanged. INVALID when self is a sentinel.

        Example:
            >>> nu.run(+nu.Any(-4))[0]
            -4
        """
        from nu.core import Pos

        return Any(Pos(self))

    def __abs__(self) -> Any:
        """Absolute value of self.

        Yields:
            The magnitude. INVALID when self is a sentinel.

        Example:
            >>> nu.run(abs(nu.Any(-4)))[0]
            4
        """
        from nu.core import Abs

        return Any(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: object) -> Bool:
        """Self strictly greater than other.

        Args:
            other: the value to compare against. Any type; comparison
                still yields a well-typed Bool.

        Yields:
            True when self is greater, False otherwise. INVALID when
            either operand is a sentinel. Raises at evaluation time when
            the runtime types aren't comparable.

        Example:
            >>> nu.run(nu.Any(5) > nu.Any(3))[0]
            True
        """
        from nu.core import Gt

        from .bool_ import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: object) -> Bool:
        """Self strictly less than other.

        Args:
            other: the value to compare against.

        Yields:
            True when self is less, False otherwise. INVALID when either
            operand is a sentinel. Raises at evaluation time when the
            runtime types aren't comparable.

        Example:
            >>> nu.run(nu.Any(5) < nu.Any(3))[0]
            False
        """
        from nu.core import Lt

        from .bool_ import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: object) -> Bool:
        """Self greater than or equal to other.

        Args:
            other: the value to compare against.

        Yields:
            True when self is greater or equal, False otherwise. INVALID
            when either operand is a sentinel. Raises at evaluation time
            when the runtime types aren't comparable.

        Example:
            >>> nu.run(nu.Any(5) >= nu.Any(5))[0]
            True
        """
        from nu.core import Ge

        from .bool_ import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: object) -> Bool:
        """Self less than or equal to other.

        Args:
            other: the value to compare against.

        Yields:
            True when self is less or equal, False otherwise. INVALID when
            either operand is a sentinel. Raises at evaluation time when
            the runtime types aren't comparable.

        Example:
            >>> nu.run(nu.Any(3) <= nu.Any(5))[0]
            True
        """
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> Bool:  # type: ignore[override]
        """Self equal to other by value.

        Args:
            other: the value to compare against. Any type; unlike `>`/`<`,
                equality never raises for mismatched types, it's just False.

        Notes:
            - Value equality, not identity. Use `is_` for identity.

        Yields:
            True when the values compare equal, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(5) == 5)[0]
            True
        """
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: object) -> Bool:  # type: ignore[override]
        """Self not equal to other by value.

        Args:
            other: the value to compare against.

        Notes:
            - Value inequality, not identity. Use `is_` for identity.

        Yields:
            True when the values differ, False otherwise. INVALID when
            either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(5) != 4)[0]
            True
        """
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))

    def is_(self, other: object) -> Bool:
        """Identity comparison: self is other.

        Args:
            other: the value to compare identity against.

        Notes:
            - Object identity, not value equality. For scalar comparison
              use `==` instead.

        Yields:
            True when self and other evaluate to the same Python object,
            False otherwise.

        Example:
            >>> nu.run(nu.Any(1).is_(1))[0]
            True
        """
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL (named methods; ``&`` / ``|`` are reserved for flow)
    # =========================================================================

    def and_(self, other: object) -> Bool:
        """Logical AND of self and other.

        Args:
            other: the value to AND with self. Coerced to Bool by
                truthiness (falsy is False, everything else is True).

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.
            - Bitwise AND is `bitand`, not this; `&` is reserved for `Race`.

        Yields:
            True when both operands are truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(1).and_(nu.Any(0)))[0]
            False
        """
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: object) -> Bool:
        """Logical OR of self and other.

        Args:
            other: the value to OR with self. Coerced to Bool by
                truthiness.

        Notes:
            - Both operands are always evaluated; there is no Python-style
              short-circuit at the tree level.
            - Bitwise OR is `bitor`, not this; `|` is reserved for
              `Parallel`.

        Yields:
            True when either operand is truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(0).or_(nu.Any(5)))[0]
            True
        """
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT of self.

        Notes:
            - Falsy yields True, everything else yields False.
            - Bitwise NOT is `bitnot`, not this.

        Yields:
            True when self is falsy, False otherwise. INVALID when self is
            a sentinel.

        Example:
            >>> nu.run(nu.Any(0).not_())[0]
            True
        """
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Cast self to Bool.

        Notes:
            - Falsy becomes False, everything else becomes True, matching
              Python's truthiness rule.

        Yields:
            True when self is truthy, False when self is falsy. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.Any(5).bool_())[0]
            True
        """
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: object) -> Any:
        """Bitwise AND: self & other.

        Args:
            other: the value to AND with self, bit by bit.

        Notes:
            - Named form rather than `__and__`: `&` is reserved at the Nu
              base for `Race` (flow), so bitwise AND has to live elsewhere.

        Yields:
            The bitwise AND. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(0b1100).bitand(0b1010))[0]
            8
        """
        from nu.core import BitAnd

        return Any(BitAnd(self, other))

    def bitor(self, other: object) -> Any:
        """Bitwise OR: self | other.

        Args:
            other: the value to OR with self, bit by bit.

        Notes:
            - Named form rather than `__or__`: `|` is reserved at the Nu
              base for `Parallel` (flow).

        Yields:
            The bitwise OR. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(0b1100).bitor(0b1010))[0]
            14
        """
        from nu.core import BitOr

        return Any(BitOr(self, other))

    def bitnot(self) -> Any:
        """Bitwise NOT: ~self.

        Notes:
            - Named form, symmetric with `bitand` / `bitor`, though unlike
              those `~` isn't reserved for flow. `__invert__` is also
              wired to the same op, so both `~self` and `self.bitnot()`
              work.

        Yields:
            The bitwise complement. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Any(5).bitnot())[0]
            -6
        """
        from nu.core import BitNot

        return Any(BitNot(self))

    def __invert__(self) -> Any:
        """Bitwise NOT: ~self.

        Notes:
            - Same op as `bitnot()`, reached through Python's `~` operator.

        Yields:
            The bitwise complement. INVALID when self is a sentinel.

        Example:
            >>> nu.run(~nu.Any(5))[0]
            -6
        """
        from nu.core import BitNot

        return Any(BitNot(self))

    def __xor__(self, other: object) -> Any:
        """Bitwise XOR: self ^ other.

        Args:
            other: the value to XOR with self, bit by bit.

        Yields:
            The bitwise XOR. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any(0b1100) ^ nu.Any(0b1010))[0]
            6
        """
        from nu.core import BitXor

        return Any(BitXor(self, other))

    def __rxor__(self, other: object) -> Any:
        """Bitwise XOR: other ^ self, with self on the right.

        Args:
            other: the value on the left of the `^`.

        Notes:
            - Reached only when the left operand's own `__xor__` declines.

        Yields:
            The bitwise XOR. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(0b1100 ^ nu.Any(0b1010))[0]
            6
        """
        from nu.core import BitXor

        return Any(BitXor(other, self))

    def __lshift__(self, other: object) -> Any:
        """Left shift: self shifted left by other bits.

        Args:
            other: the shift amount. Must be non-negative at evaluation
                time.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.
            Raises at evaluation time when the shift amount is negative.

        Example:
            >>> nu.run(nu.Any(1) << nu.Any(4))[0]
            16
        """
        from nu.core import LShift

        return Any(LShift(self, other))

    def __rlshift__(self, other: object) -> Any:
        """Left shift: other shifted left by self bits.

        Args:
            other: the value on the left of the `<<`, the value being
                shifted.

        Notes:
            - Reached only when the left operand's own `__lshift__`
              declines.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(1 << nu.Any(4))[0]
            16
        """
        from nu.core import LShift

        return Any(LShift(other, self))

    def __rshift__(self, other: object) -> Any:
        """Right shift: self shifted right by other bits.

        Args:
            other: the shift amount. Must be non-negative at evaluation
                time.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.
            Raises at evaluation time when the shift amount is negative.

        Example:
            >>> nu.run(nu.Any(16) >> nu.Any(2))[0]
            4
        """
        from nu.core import RShift

        return Any(RShift(self, other))

    def __rrshift__(self, other: object) -> Any:
        """Right shift: other shifted right by self bits.

        Args:
            other: the value on the left of the `>>`, the value being
                shifted.

        Notes:
            - Reached only when the left operand's own `__rshift__`
              declines.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(16 >> nu.Any(2))[0]
            4
        """
        from nu.core import RShift

        return Any(RShift(other, self))

    # =========================================================================
    # DYNAMIC DESCENT (subscript + attribute)
    # =========================================================================

    def __getitem__(self, key: object) -> Any:
        """Subscript access: self[key].

        Args:
            key: the index, key, or slice to read. A plain Python slice
                is threaded through `Slice` so the whole thing stays
                symbolic.

        Yields:
            The item at key. INVALID when self is a sentinel. Raises at
            evaluation time when key doesn't exist on the runtime value.

        Example:
            >>> nu.run(nu.Any([1, 2, 3])[1])[0]
            2

            >>> nu.run(nu.Any([1, 2, 3])[0:2])[0]
            [1, 2]
        """
        from nu.core import GetItem, Slice

        if isinstance(key, slice):
            key = Slice(key.start, key.stop, key.step)
        return Any(GetItem(self, key))

    def __setitem__(self, key: object, value: object) -> object:
        """Subscript write: self[key] = value.

        Args:
            key: the index or key to write.
            value: the value to store there.

        Notes:
            - Ref-gated at build time: the wrapped source must be a Ref
              (a fabric-writable location). Python's assignment syntax
              discards the return value, so a value-node write would
              silently produce an orphaned, invalid tree; this raises
              `TypeError` instead.

        Example:
            >>> nu.Any([1, 2, 3])[0] = 5
            Traceback (most recent call last):
                ...
            TypeError: Any.__setitem__: cannot mutate through a value-node - the wrapped source must be a Ref (a fabric-writable location). Got: Literal.
        """
        _require_ref_source(self, "__setitem__")
        from nu.core import SetItem

        return SetItem(self, key, value)

    def __delitem__(self, key: object) -> object:
        """Subscript delete: del self[key].

        Args:
            key: the index or key to delete.

        Notes:
            - Ref-gated the same way as `__setitem__`; see there for why.

        Example:
            >>> del nu.Any([1, 2, 3])[0]
            Traceback (most recent call last):
                ...
            TypeError: Any.__delitem__: cannot mutate through a value-node - the wrapped source must be a Ref (a fabric-writable location). Got: Literal.
        """
        _require_ref_source(self, "__delitem__")
        from nu.core import DelItem

        return DelItem(self, key)

    def __getattr__(self, name: str) -> Any:
        """Attribute read: self.name.

        Args:
            name: the attribute name.

        Notes:
            - Names starting with `_` are never intercepted; they fall
              through to Python's normal lookup, raising `AttributeError`
              if genuinely missing. That keeps engine-private state
              (`_payload`, `_children`, `_source`, ...) from being
              accidentally captured as a tree node.

        Yields:
            The attribute's value. INVALID when self is a sentinel. Raises
            at evaluation time when the attribute doesn't exist on the
            runtime value.

        Example:
            >>> class Obj:
            ...     x = 5
            >>> nu.run(nu.Any(Obj()).x)[0]
            5
        """
        if name.startswith("_"):
            msg = f"{type(self).__name__!r} object has no attribute {name!r}"
            raise AttributeError(msg)
        from nu.core import GetAttr

        return Any(GetAttr(self, name))

    # =========================================================================
    # NAMED METHODS FOR PROTOCOL DUNDERS
    #
    # ``__len__`` / ``__contains__`` / ``__iter__`` / ``__bool__`` all require
    # Python-native return types at runtime, so they cannot participate in a
    # Nu tree. Expose the tree-shaped equivalents as named methods instead.
    # =========================================================================

    def len_(self) -> Int:
        """Length of self, as len(self).

        Notes:
            - Named `len_` because Python's `__len__` must return a
              native int and can't carry a Nu tree node.

        Yields:
            The length as Int. INVALID when self is a sentinel. Raises at
            evaluation time when the runtime value has no length.

        Example:
            >>> nu.run(nu.Any([1, 2, 3]).len_())[0]
            3
        """
        from nu.core import Len

        from .int_ import Int

        return Int(Len(self))

    def contains(self, item: object) -> Bool:
        """Membership test: item in self.

        Args:
            item: the value to look for.

        Notes:
            - Named `contains` because Python's `__contains__` must
              return a native bool and can't carry a Nu tree node.

        Yields:
            True when item is found in self, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Any([1, 2, 3]).contains(2))[0]
            True
        """
        from nu.core import Contains

        from .bool_ import Bool

        return Bool(Contains(self, item))

    def iter_(self) -> Iterator:
        """Iterator over self, as iter(self).

        Notes:
            - Named `iter_` because Python's `__iter__` must return a
              native iterator and can't carry a Nu tree node.
            - The returned Iterator is a stream, not a scalar: it needs to
              be consumed through a stream-shaped context (materialized
              with `to_list()` / `to_set()` / `to_tuple()`, or driven
              inside a flow), not evaluated directly with `nu.run`.

        Yields:
            An Iterator over self's elements. INVALID when self is a
            sentinel.
        """
        from nu.core import Iter

        from ..collections.iterator_ import Iterator

        return Iterator(Iter(self))

    def has_attr(self, name: object) -> Bool:
        """Attribute presence: hasattr(self, name).

        Args:
            name: the attribute name to check for.

        Notes:
            - Named `has_attr` because Python's `__getattr__` fallback
              here (`hasattr`) must return a native bool.

        Yields:
            True when self has the named attribute, False otherwise.
            INVALID when either operand is a sentinel.

        Example:
            >>> class Obj:
            ...     x = 5
            >>> nu.run(nu.Any(Obj()).has_attr("x"))[0]
            True
        """
        from nu.core import HasAttr

        from .bool_ import Bool

        return Bool(HasAttr(self, name))


def _require_ref_source(form: Any, op: str) -> None:
    """Guard: the wrapped source of form must be a Ref.

    Args:
        form: the Any instance being mutated.
        op: the name of the calling dunder, used in the error message.

    Notes:
        - Python's `x[k] = v` / `del x[k]` syntax discards the return
          value of `__setitem__` / `__delitem__`, so a value-node Any
          returning a Command would leave the mutation orphaned. Raises
          `TypeError` up front instead.
    """
    source = form._source
    if not isinstance(source, Ref):
        msg = (
            f"Any.{op}: cannot mutate through a value-node - the "
            f"wrapped source must be a Ref (a fabric-writable location). "
            f"Got: {type(source).__name__ if source is not None else 'None'}."
        )
        raise TypeError(msg)
