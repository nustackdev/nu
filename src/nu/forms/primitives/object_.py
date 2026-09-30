"""Object - the interface every term has.

The honest terminal for value-Form descent: genuinely-unknown or dynamically
typed values live here. Every operation on an ``Object`` is absorbing -
arithmetic, bitwise, subscript, and attribute access all yield another
``Object``; comparison and logical ops yield ``Bool``.

``Object`` carries the arithmetic and comparison operators; the runtime type
is unknown, so Python decides at evaluation time what each does. ``&``, ``|``
and ``>>`` compose flows (Race, Parallel, Sequential) on an ``Object`` like on
every term. The value versions are named methods that pass through to the
value: ``bitand`` / ``bitor`` / ``bitxor`` / ``bitnot`` / ``lshift`` /
``rshift``, ``and_`` / ``or_`` / ``not_``, ``union`` / ``intersection`` /
``difference`` / ``symmetric_difference``, ``merge`` / ``merge_update``.

Protocol dunders (``__len__``, ``__contains__``, ``__bool__``, ``__iter__``) must return
Python-native values and cannot be part of a Nu tree; the ``Nu`` base blocks
them with a hint. They are exposed as named methods (``len()``,
``contains()``, ``iter()``, ``bool_()``) that return the matching Form so
the tree stays symbolic.

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
    "Object",
]


class Object(Form, TypedNu[Any]):
    """The interface every term has. Full operator surface, no promise about the runtime type.

    Arithmetic, bitwise, subscript, and attribute descent are all
    absorbing: the result of any of them is another Object, since the
    concrete type isn't known until evaluation. Comparison and logical
    operators are the exception - they still yield Bool, because "is
    this true" is a well-typed question even when the operand type
    isn't.

    Notes:
        - Typed as `TypedNu[Any]`, not `TypedNu[object]`. That lets an
          Object value slot into any narrow Arg position (IntArg, StrArg,
          ...), so `intref + objval` resolves through Int's `__add__`
          and lands as Int instead of falling through to Object's `__radd__`.
        - `&`, `|` and `>>` compose flows (Race, Parallel, Sequential)
          like on every term. Bit, set and merge operations are named
          methods (`bitand`, `union`, `merge`, ...).
        - There's no `__call__`. A callable value in a Nu tree goes
          through an interaction (built via `host` or hand-written),
          not raw Python call dispatch.

    Example:
        >>> nu.run(nu.Object(6) * nu.Object(7))[0]
        42
    """

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: object) -> Object:
        """Sum of self and other.

        Args:
            other: the value to add to self. Any type; the result stays
                Object regardless.

        Yields:
            The sum. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(2) + nu.Object(3))[0]
            5
        """
        from nu.core import Add

        return Object(Add(self, other))

    def __radd__(self, other: object) -> Object:
        """Sum of other and self, with self on the right.

        Args:
            other: the value on the left of the `+`.

        Notes:
            - Reached only when the left operand's own `__add__` declines,
              e.g. a plain Python value that doesn't know about Object.

        Yields:
            The sum. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(3 + nu.Object(2))[0]
            5
        """
        from nu.core import Add

        return Object(Add(other, self))

    def __sub__(self, other: object) -> Object:
        """Self minus other.

        Args:
            other: the value to subtract from self.

        Yields:
            The difference. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(10) - nu.Object(3))[0]
            7
        """
        from nu.core import Sub

        return Object(Sub(self, other))

    def __rsub__(self, other: object) -> Object:
        """Other minus self, with self on the right.

        Args:
            other: the value on the left of the `-`, the minuend.

        Notes:
            - Reached only when the left operand's own `__sub__` declines.

        Yields:
            The difference. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(10 - nu.Object(3))[0]
            7
        """
        from nu.core import Sub

        return Object(Sub(other, self))

    def __mul__(self, other: object) -> Object:
        """Product of self and other.

        Args:
            other: the value to multiply self by.

        Yields:
            The product. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(6) * nu.Object(7))[0]
            42
        """
        from nu.core import Mul

        return Object(Mul(self, other))

    def __rmul__(self, other: object) -> Object:
        """Product of other and self, with self on the right.

        Args:
            other: the value on the left of the `*`.

        Notes:
            - Reached only when the left operand's own `__mul__` declines.

        Yields:
            The product. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(3 * nu.Object(4))[0]
            12
        """
        from nu.core import Mul

        return Object(Mul(other, self))

    def __matmul__(self, other: object) -> Object:
        """Matrix multiplication: self @ other.

        Args:
            other: the right operand. Needs a type that supports Python's
                matmul protocol (e.g. a numpy array); plain numbers don't.

        Yields:
            The product. INVALID when either operand is a sentinel. Raises
            at evaluation time when neither operand supports `@`.
        """
        from nu.core import MatMul

        return Object(MatMul(self, other))

    def __rmatmul__(self, other: object) -> Object:
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

        return Object(MatMul(other, self))

    def __truediv__(self, other: object) -> Object:
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
            >>> nu.run(nu.Object(7) / nu.Object(2))[0]
            3.5
        """
        from nu.core import Div

        return Object(Div(self, other))

    def __rtruediv__(self, other: object) -> Object:
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
            >>> nu.run(10 / nu.Object(4))[0]
            2.5
        """
        from nu.core import Div

        return Object(Div(other, self))

    def __floordiv__(self, other: object) -> Object:
        """Self floor-divided by other.

        Args:
            other: the divisor.

        Notes:
            - Rounds toward negative infinity, as Python's `//` does.

        Yields:
            The floored quotient. INVALID when either operand is a
            sentinel. Raises at evaluation time when the divisor is zero.

        Example:
            >>> nu.run(nu.Object(7) // nu.Object(2))[0]
            3
        """
        from nu.core import FloorDiv

        return Object(FloorDiv(self, other))

    def __rfloordiv__(self, other: object) -> Object:
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
            >>> nu.run(-7 // nu.Object(2))[0]
            -4
        """
        from nu.core import FloorDiv

        return Object(FloorDiv(other, self))

    def __mod__(self, other: object) -> Object:
        """Self modulo other.

        Args:
            other: the divisor.

        Notes:
            - The result's sign follows the divisor, as Python's `%` does.

        Yields:
            The remainder. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(7) % nu.Object(3))[0]
            1
        """
        from nu.core import Mod

        return Object(Mod(self, other))

    def __rmod__(self, other: object) -> Object:
        """Other modulo self, with self as the divisor.

        Args:
            other: the value being divided, on the left of the `%`.

        Notes:
            - The result's sign follows the divisor, which here is self.
            - Reached only when the left operand's own `__mod__` declines.

        Yields:
            The remainder. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(-7 % nu.Object(3))[0]
            2
        """
        from nu.core import Mod

        return Object(Mod(other, self))

    def __pow__(self, other: object) -> Object:
        """Self raised to the other power.

        Args:
            other: the exponent.

        Yields:
            The power. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(2) ** nu.Object(10))[0]
            1024
        """
        from nu.core import Pow

        return Object(Pow(self, other))

    def __rpow__(self, other: object) -> Object:
        """Other raised to the self power, with self as the exponent.

        Args:
            other: the base, on the left of the `**`.

        Notes:
            - Reached only when the left operand's own `__pow__` declines.

        Yields:
            The power. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(2 ** nu.Object(10))[0]
            1024
        """
        from nu.core import Pow

        return Object(Pow(other, self))

    def __neg__(self) -> Object:
        """Negation of self.

        Yields:
            The negation. INVALID when self is a sentinel.

        Example:
            >>> nu.run(-nu.Object(4))[0]
            -4
        """
        from nu.core import Neg

        return Object(Neg(self))

    def __pos__(self) -> Object:
        """Self unchanged.

        Notes:
            - Identity for numbers. Kept for symmetry with `__neg__` and so
              `+x` inside an expression is still a Nu term.

        Yields:
            The value unchanged. INVALID when self is a sentinel.

        Example:
            >>> nu.run(+nu.Object(-4))[0]
            -4
        """
        from nu.core import Pos

        return Object(Pos(self))

    def __abs__(self) -> Object:
        """Absolute value of self.

        Yields:
            The magnitude. INVALID when self is a sentinel.

        Example:
            >>> nu.run(abs(nu.Object(-4)))[0]
            4
        """
        from nu.core import Abs

        return Object(Abs(self))

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
            >>> nu.run(nu.Object(5) > nu.Object(3))[0]
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
            >>> nu.run(nu.Object(5) < nu.Object(3))[0]
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
            >>> nu.run(nu.Object(5) >= nu.Object(5))[0]
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
            >>> nu.run(nu.Object(3) <= nu.Object(5))[0]
            True
        """
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

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
            >>> nu.run(nu.Object(5) == 5)[0]
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
            >>> nu.run(nu.Object(5) != 4)[0]
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
            >>> nu.run(nu.Object(1).is_(1))[0]
            True
        """
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL (named methods; ``&`` / ``|`` compose flows on every term)
    # =========================================================================

    def and_(self, other: object) -> Bool:
        """Logical AND of self and other.

        Args:
            other: the value to AND with self. Coerced to Bool by
                truthiness (falsy is False, everything else is True).

        Notes:
            - Short-circuits like Python: the right operand is only
              evaluated when the left does not already decide the result.
            - Bitwise AND is `bitand`, not this.

        Yields:
            True when both operands are truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(1).and_(nu.Object(0)))[0]
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
            - Short-circuits like Python: the right operand is only
              evaluated when the left does not already decide the result.
            - Bitwise OR is `bitor`, not this.

        Yields:
            True when either operand is truthy, False otherwise. INVALID
            when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(0).or_(nu.Object(5)))[0]
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
            >>> nu.run(nu.Object(0).not_())[0]
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
            >>> nu.run(nu.Object(5).bool_())[0]
            True
        """
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # BITWISE, SET AND MAPPING (named methods, passed through to the value)
    #
    # ``& | >>`` compose flows on every term, Object included, and ``^ ~ <<``
    # are not defined on forms. The runtime type is unknown, so each method
    # applies Python's own operation to whatever the value turns out to be.
    # =========================================================================

    def bitand(self, other: object) -> Object:
        """Python's `&` on the values: bits for ints, intersection for sets.

        Args:
            other: the value to AND with self.

        Notes:
            - A named method because `&` composes flows (Race) on every term.

        Yields:
            The AND. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(0b1100).bitand(0b1010))[0]
            8
        """
        from nu.core import BitAnd

        return Object(BitAnd(self, other))

    def bitor(self, other: object) -> Object:
        """Python's `|` on the values: bits for ints, union for sets, merge for dicts.

        Args:
            other: the value to OR with self.

        Notes:
            - A named method because `|` composes flows (Parallel) on every
              term.

        Yields:
            The OR. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(0b1100).bitor(0b1010))[0]
            14
        """
        from nu.core import BitOr

        return Object(BitOr(self, other))

    def bitxor(self, other: object) -> Object:
        """Python's `^` on the values: bits for ints, symmetric difference for sets.

        Args:
            other: the value to XOR with self.

        Yields:
            The XOR. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object(0b1100).bitxor(0b1010))[0]
            6
        """
        from nu.core import BitXor

        return Object(BitXor(self, other))

    def bitnot(self) -> Object:
        """Python's `~` on the value.

        Yields:
            The bitwise complement. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.Object(5).bitnot())[0]
            -6
        """
        from nu.core import BitNot

        return Object(BitNot(self))

    def lshift(self, other: object) -> Object:
        """Self shifted left by other bits: Python's `<<` on the values.

        Args:
            other: the shift amount. Must be non-negative at evaluation
                time.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.
            Raises at evaluation time when the shift amount is negative.

        Example:
            >>> nu.run(nu.Object(1).lshift(4))[0]
            16
        """
        from nu.core import LShift

        return Object(LShift(self, other))

    def rshift(self, other: object) -> Object:
        """Self shifted right by other bits: Python's `>>` on the values.

        Args:
            other: the shift amount. Must be non-negative at evaluation
                time.

        Notes:
            - A named method because `>>` composes flows (Sequential) on
              every term.

        Yields:
            The shifted value. INVALID when either operand is a sentinel.
            Raises at evaluation time when the shift amount is negative.

        Example:
            >>> nu.run(nu.Object(16).rshift(2))[0]
            4
        """
        from nu.core import RShift

        return Object(RShift(self, other))

    def union(self, other: object) -> Object:
        """Set union of self and other.

        Args:
            other: the iterable to union with self.

        Yields:
            A new set with every element of self and other. INVALID when
            self is not set-like or either operand is a sentinel.

        Example:
            >>> sorted(nu.run(nu.Object({1, 2}).union({2, 3}))[0])
            [1, 2, 3]
        """
        from ..collections.abc.set_interactions import Union

        return Object(Union(self, other))

    def intersection(self, other: object) -> Object:
        """Set intersection of self and other.

        Args:
            other: the iterable to intersect with self.

        Yields:
            A new set with only the elements found in both. INVALID when
            self is not set-like or either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object({1, 2, 3}).intersection({2, 4}))[0]
            {2}
        """
        from ..collections.abc.set_interactions import Intersection

        return Object(Intersection(self, other))

    def difference(self, other: object) -> Object:
        """Elements of self that are not in other.

        Args:
            other: the iterable of elements to leave out.

        Yields:
            A new set. INVALID when self is not set-like or either operand
            is a sentinel.

        Example:
            >>> nu.run(nu.Object({1, 2, 3}).difference({2}))[0]
            {1, 3}
        """
        from ..collections.abc.set_interactions import Difference

        return Object(Difference(self, other))

    def symmetric_difference(self, other: object) -> Object:
        """Elements in exactly one of self and other.

        Args:
            other: the iterable to compare self against.

        Yields:
            A new set. INVALID when self is not set-like or either operand
            is a sentinel.

        Example:
            >>> nu.run(nu.Object({1, 2}).symmetric_difference({2, 3}))[0]
            {1, 3}
        """
        from ..collections.abc.set_interactions import SymmetricDifference

        return Object(SymmetricDifference(self, other))

    def merge(self, other: object) -> Object:
        """Self and other merged into a new mapping: Python's dict `|`.

        Args:
            other: the mapping to merge in. Its keys win over self's on
                overlap.

        Yields:
            A new mapping. INVALID when either operand is a sentinel.

        Example:
            >>> nu.run(nu.Object({"a": 1}).merge({"b": 2}))[0]
            {'a': 1, 'b': 2}
        """
        from ..collections.abc.mapping_interactions import Merge

        return Object(Merge(self, other))

    def merge_update(self, other: object) -> Object:
        """Merge other into self in place, and yield self: Python's dict `|=`.

        Args:
            other: the mapping to merge in. Its values win over self's on
                shared keys.

        Notes:
            - Mutates slot 0 in place and yields the mutated mapping, an
              Action like `Dict.merge_update`.

        Yields:
            Self, updated with other's entries. INVALID when either operand
            is a sentinel.

        Example:
            >>> nu.run(nu.Object({"a": 1}).merge_update({"b": 2}))[0]
            {'a': 1, 'b': 2}
        """
        from ..collections.abc.mapping_interactions import MergeUpdate

        return Object(MergeUpdate(self, other))

    # =========================================================================
    # DYNAMIC DESCENT (subscript + attribute)
    # =========================================================================

    def __getitem__(self, key: object) -> Object:
        """Subscript access: self[key].

        Args:
            key: the index, key, or slice to read. A plain Python slice
                is threaded through `Slice` so the whole thing stays
                symbolic.

        Yields:
            The item at key. INVALID when self is a sentinel. Raises at
            evaluation time when key doesn't exist on the runtime value.

        Example:
            >>> nu.run(nu.Object([1, 2, 3])[1])[0]
            2

            >>> nu.run(nu.Object([1, 2, 3])[0:2])[0]
            [1, 2]
        """
        from nu.core import GetItem, Slice

        if isinstance(key, slice):
            key = Slice(key.start, key.stop, key.step)
        return Object(GetItem(self, key))

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
            >>> nu.Object([1, 2, 3])[0] = 5
            Traceback (most recent call last):
                ...
            TypeError: Object.__setitem__: cannot mutate through a value-node - the wrapped source must be a Ref (a fabric-writable location). Got: Literal.
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
            >>> del nu.Object([1, 2, 3])[0]
            Traceback (most recent call last):
                ...
            TypeError: Object.__delitem__: cannot mutate through a value-node - the wrapped source must be a Ref (a fabric-writable location). Got: Literal.
        """
        _require_ref_source(self, "__delitem__")
        from nu.core import DelItem

        return DelItem(self, key)

    def __getattr__(self, name: str) -> Object:
        """Attribute read: self.name.

        Args:
            name: the attribute name.

        Notes:
            - Names starting with `_` are never intercepted; they fall
              through to Python's normal lookup, raising `AttributeError`
              if genuinely missing. That keeps engine-private state
              (`_payload`, `_children`, `_source`, ...) from being
              accidentally captured as a tree node.
            - Only names Object does not define descend. These are Object's
              own methods and reach the method, never the value's attribute:
              `and_`, `bitand`, `bitnot`, `bitor`, `bitxor`, `bool_`,
              `contains`, `difference`, `has_attr`, `intersection`, `is_`,
              `is_empty`, `is_invalid`, `is_sentinel`, `iter`, `len`,
              `lshift`, `merge`, `merge_update`, `not_`, `not_empty`,
              `not_invalid`, `or_`, `rshift`, `symmetric_difference`,
              `union`. To read a value attribute with one of those names,
              build the read directly: `nu.Object(nu.GetAttr(o, "len"))`.

        Yields:
            The attribute's value. INVALID when self is a sentinel. Raises
            at evaluation time when the attribute doesn't exist on the
            runtime value.

        Example:
            >>> class Obj:
            ...     x = 5
            >>> nu.run(nu.Object(Obj()).x)[0]
            5
        """
        if name.startswith("_"):
            msg = f"{type(self).__name__!r} object has no attribute {name!r}"
            raise AttributeError(msg)
        from nu.core import GetAttr

        return Object(GetAttr(self, name))

    # =========================================================================
    # NAMED METHODS FOR PROTOCOL DUNDERS
    #
    # ``__len__`` / ``__contains__`` / ``__iter__`` / ``__bool__`` all require
    # Python-native return types at runtime, so they cannot participate in a
    # Nu tree. The ``Nu`` base blocks ``len()`` / ``in`` / ``bool()`` with a
    # hint pointing here; these named methods are the tree-shaped equivalents.
    # =========================================================================

    def len(self) -> Int:
        """Length of self.

        Notes:
            - Named `len` because Python's `__len__` must return a
              native int and can't carry a Nu tree node.

        Yields:
            The length as Int. INVALID when self is a sentinel. Raises at
            evaluation time when the runtime value has no length.

        Example:
            >>> nu.run(nu.Object([1, 2, 3]).len())[0]
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
            >>> nu.run(nu.Object([1, 2, 3]).contains(2))[0]
            True
        """
        from nu.core import Contains

        from .bool_ import Bool

        return Bool(Contains(self, item))

    def iter(self) -> Iterator:
        """Lazy iterator stream over self's elements.

        Notes:
            - Named because Python's `iter()` / `for` would loop over the
              term at build time; the ``Nu`` base blocks them.
            - The returned Iterator is a stream, not a scalar: loop it with
              `nu.ForEachDo`, drain it with `to_list()` / `to_set()` /
              `to_tuple()`, or pull one item with `next()`.

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
            >>> nu.run(nu.Object(Obj()).has_attr("x"))[0]
            True
        """
        from nu.core import HasAttr

        from .bool_ import Bool

        return Bool(HasAttr(self, name))


def _require_ref_source(form: Object, op: str) -> None:
    """Guard: the wrapped source of form must be a Ref.

    Args:
        form: the Object instance being mutated.
        op: the name of the calling dunder, used in the error message.

    Notes:
        - Python's `x[k] = v` / `del x[k]` syntax discards the return
          value of `__setitem__` / `__delitem__`, so a value-node Object
          returning a Command would leave the mutation orphaned. Raises
          `TypeError` up front instead.
    """
    source = form._source
    if not isinstance(source, Ref):
        msg = (
            f"Object.{op}: cannot mutate through a value-node - the "
            f"wrapped source must be a Ref (a fabric-writable location). "
            f"Got: {type(source).__name__ if source is not None else 'None'}."
        )
        raise TypeError(msg)
