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
interactions (built via ``ScalarQueryFactory`` / ``MethodFactory``), not
raw Python callable dispatch. If you have a callable value in a Nu tree,
wrap it in the appropriate interaction.
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
    """Any/dynamic interface. Supports all interactions, results stay Any.

    Absorbing under arithmetic + bitwise + subscript + attribute descent
    (result is another ``Any``); comparison and logical ops yield
    ``Bool`` (well-typed decision even in the dynamic world).

    Types as ``TypedNu[Any]`` (not ``TypedNu[object]``) so that Any
    can slot into any narrow ``Arg`` position (``IntArg``, ``StrArg``, ...) -
    ``Any``'s special variance rules let ``Nu[Any]`` substitute for
    ``Nu[int]`` / ``Nu[str]`` / etc. That is how ``intref + anyval``
    lands as ``Int`` instead of degrading through ``__radd__``.
    """

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: object) -> Any:
        from nu.core import Add

        return Any(Add(self, other))

    def __radd__(self, other: object) -> Any:
        from nu.core import Add

        return Any(Add(other, self))

    def __sub__(self, other: object) -> Any:
        from nu.core import Sub

        return Any(Sub(self, other))

    def __rsub__(self, other: object) -> Any:
        from nu.core import Sub

        return Any(Sub(other, self))

    def __mul__(self, other: object) -> Any:
        from nu.core import Mul

        return Any(Mul(self, other))

    def __rmul__(self, other: object) -> Any:
        from nu.core import Mul

        return Any(Mul(other, self))

    def __matmul__(self, other: object) -> Any:
        from nu.core import MatMul

        return Any(MatMul(self, other))

    def __rmatmul__(self, other: object) -> Any:
        from nu.core import MatMul

        return Any(MatMul(other, self))

    def __truediv__(self, other: object) -> Any:
        from nu.core import Div

        return Any(Div(self, other))

    def __rtruediv__(self, other: object) -> Any:
        from nu.core import Div

        return Any(Div(other, self))

    def __floordiv__(self, other: object) -> Any:
        from nu.core import FloorDiv

        return Any(FloorDiv(self, other))

    def __rfloordiv__(self, other: object) -> Any:
        from nu.core import FloorDiv

        return Any(FloorDiv(other, self))

    def __mod__(self, other: object) -> Any:
        from nu.core import Mod

        return Any(Mod(self, other))

    def __rmod__(self, other: object) -> Any:
        from nu.core import Mod

        return Any(Mod(other, self))

    def __pow__(self, other: object) -> Any:
        from nu.core import Pow

        return Any(Pow(self, other))

    def __rpow__(self, other: object) -> Any:
        from nu.core import Pow

        return Any(Pow(other, self))

    def __neg__(self) -> Any:
        from nu.core import Neg

        return Any(Neg(self))

    def __pos__(self) -> Any:
        from nu.core import Pos

        return Any(Pos(self))

    def __abs__(self) -> Any:
        from nu.core import Abs

        return Any(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: object) -> Bool:
        from nu.core import Gt

        from .bool_ import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: object) -> Bool:
        from nu.core import Lt

        from .bool_ import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: object) -> Bool:
        from nu.core import Ge

        from .bool_ import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: object) -> Bool:
        from nu.core import Le

        from .bool_ import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from .bool_ import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: object) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from .bool_ import Bool

        return Bool(Ne(self, other))

    def is_(self, other: object) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from .bool_ import Bool

        return Bool(Is(self, other))

    # =========================================================================
    # LOGICAL (named methods; ``&`` / ``|`` are reserved for flow)
    # =========================================================================

    def and_(self, other: object) -> Bool:
        """Logical AND: self AND other."""
        from nu.core import And

        from .bool_ import Bool

        return Bool(And(self, other))

    def or_(self, other: object) -> Bool:
        """Logical OR: self OR other."""
        from nu.core import Or

        from .bool_ import Bool

        return Bool(Or(self, other))

    def not_(self) -> Bool:
        """Logical NOT: NOT self."""
        from nu.core import Not

        from .bool_ import Bool

        return Bool(Not(self))

    def bool_(self) -> Bool:
        """Convert to boolean."""
        from nu.core import ToBool

        from .bool_ import Bool

        return Bool(ToBool(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: object) -> Any:
        """Bitwise AND: ``self & other`` (``&`` is reserved for ``Race``)."""
        from nu.core import BitAnd

        return Any(BitAnd(self, other))

    def bitor(self, other: object) -> Any:
        """Bitwise OR: ``self | other`` (``|`` is reserved for ``Parallel``)."""
        from nu.core import BitOr

        return Any(BitOr(self, other))

    def bitnot(self) -> Any:
        """Bitwise NOT: ``~self`` (named form)."""
        from nu.core import BitNot

        return Any(BitNot(self))

    def __invert__(self) -> Any:
        from nu.core import BitNot

        return Any(BitNot(self))

    def __xor__(self, other: object) -> Any:
        from nu.core import BitXor

        return Any(BitXor(self, other))

    def __rxor__(self, other: object) -> Any:
        from nu.core import BitXor

        return Any(BitXor(other, self))

    def __lshift__(self, other: object) -> Any:
        from nu.core import LShift

        return Any(LShift(self, other))

    def __rlshift__(self, other: object) -> Any:
        from nu.core import LShift

        return Any(LShift(other, self))

    def __rshift__(self, other: object) -> Any:
        from nu.core import RShift

        return Any(RShift(self, other))

    def __rrshift__(self, other: object) -> Any:
        from nu.core import RShift

        return Any(RShift(other, self))

    # =========================================================================
    # DYNAMIC DESCENT (subscript + attribute)
    # =========================================================================

    def __getitem__(self, key: object) -> Any:
        """Subscript access: ``self[key]``.

        For slice keys ``a:b:c``, the slice is threaded through ``Slice``
        so the whole thing stays symbolic.
        """
        from nu.core import GetItem, Slice

        if isinstance(key, slice):
            key = Slice(key.start, key.stop, key.step)
        return Any(GetItem(self, key))

    def __setitem__(self, key: object, value: object) -> object:
        """Subscript write: ``self[key] = value``.

        Ref-gated at build time: the wrapped source MUST be a ``Ref`` (a
        fabric-writable location), otherwise the produced ``Command`` would be
        silently discarded by Python's assignment syntax. Raises ``TypeError``
        clearly instead of building an invalid tree.
        """
        _require_ref_source(self, "__setitem__")
        from nu.core import SetItem

        return SetItem(self, key, value)

    def __delitem__(self, key: object) -> object:
        """Subscript delete: ``del self[key]``. Ref-gated (see ``__setitem__``)."""
        _require_ref_source(self, "__delitem__")
        from nu.core import DelItem

        return DelItem(self, key)

    def __getattr__(self, name: str) -> Any:
        """Attribute read: ``self.name`` -> ``GetAttr(self, name)``.

        Attributes starting with ``_`` are considered internal machinery and
        are NEVER intercepted - they fall through to Python's normal lookup
        (which raises ``AttributeError`` if genuinely missing). This keeps
        engine-private state (``_payload``, ``_children``, ``_source``, ...)
        safe from accidental capture as tree nodes.
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
        """Length: ``len(self)`` as an ``Int`` in the tree."""
        from nu.core import Len

        from .int_ import Int

        return Int(Len(self))

    def contains(self, item: object) -> Bool:
        """Membership: ``item in self`` as a ``Bool`` in the tree."""
        from nu.core import Contains

        from .bool_ import Bool

        return Bool(Contains(self, item))

    def iter_(self) -> Iterator:
        """Iteration: ``iter(self)`` as an ``Iterator``."""
        from nu.core import Iter

        from ..collections.iterator_ import Iterator

        return Iterator(Iter(self))

    def has_attr(self, name: object) -> Bool:
        """Attribute presence: ``hasattr(self, name)`` as a ``Bool``."""
        from nu.core import HasAttr

        from .bool_ import Bool

        return Bool(HasAttr(self, name))


def _require_ref_source(form: Any, op: str) -> None:
    """Guard: the wrapped source of ``form`` must be a ``Ref``.

    Python's ``x[k] = v`` / ``del x[k]`` syntax discards the return value of
    ``__setitem__`` / ``__delitem__``, so a value-node ``Any`` returning
    a ``Command`` would leave the mutation orphaned. Raise clearly instead.
    """
    source = form._source
    if not isinstance(source, Ref):
        msg = (
            f"Any.{op}: cannot mutate through a value-node - the "
            f"wrapped source must be a Ref (a fabric-writable location). "
            f"Got: {type(source).__name__ if source is not None else 'None'}."
        )
        raise TypeError(msg)
