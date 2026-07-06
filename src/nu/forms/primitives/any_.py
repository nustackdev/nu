"""AnyForm - dynamic/unknown type interface.

The honest terminal for value-Form descent: genuinely-unknown or dynamically
typed values live here. Every operation on an ``AnyForm`` is absorbing -
arithmetic, bitwise, subscript, and attribute access all yield another
``AnyForm``; comparison and logical ops yield ``BoolForm``.

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

    from ..collections.iterator_ import IteratorForm
    from .bool_ import BoolForm
    from .int_ import IntForm


__all__ = [
    "AnyForm",
]


class AnyForm(Form, TypedNu[Any]):
    """Any/dynamic interface. Supports all interactions, results stay AnyForm.

    Absorbing under arithmetic + bitwise + subscript + attribute descent
    (result is another ``AnyForm``); comparison and logical ops yield
    ``BoolForm`` (well-typed decision even in the dynamic world).

    Types as ``TypedNu[Any]`` (not ``TypedNu[object]``) so that AnyForm
    can slot into any narrow ``Arg`` position (``IntArg``, ``StrArg``, ...) -
    ``Any``'s special variance rules let ``Nu[Any]`` substitute for
    ``Nu[int]`` / ``Nu[str]`` / etc. That is how ``intref + anyval``
    lands as ``IntForm`` instead of degrading through ``__radd__``.
    """

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: object) -> AnyForm:
        from nu.core import AddQuery

        return AnyForm(AddQuery(self, other))

    def __radd__(self, other: object) -> AnyForm:
        from nu.core import AddQuery

        return AnyForm(AddQuery(other, self))

    def __sub__(self, other: object) -> AnyForm:
        from nu.core import SubQuery

        return AnyForm(SubQuery(self, other))

    def __rsub__(self, other: object) -> AnyForm:
        from nu.core import SubQuery

        return AnyForm(SubQuery(other, self))

    def __mul__(self, other: object) -> AnyForm:
        from nu.core import MulQuery

        return AnyForm(MulQuery(self, other))

    def __rmul__(self, other: object) -> AnyForm:
        from nu.core import MulQuery

        return AnyForm(MulQuery(other, self))

    def __matmul__(self, other: object) -> AnyForm:
        from nu.core import MatMulQuery

        return AnyForm(MatMulQuery(self, other))

    def __rmatmul__(self, other: object) -> AnyForm:
        from nu.core import MatMulQuery

        return AnyForm(MatMulQuery(other, self))

    def __truediv__(self, other: object) -> AnyForm:
        from nu.core import DivQuery

        return AnyForm(DivQuery(self, other))

    def __rtruediv__(self, other: object) -> AnyForm:
        from nu.core import DivQuery

        return AnyForm(DivQuery(other, self))

    def __floordiv__(self, other: object) -> AnyForm:
        from nu.core import FloorDivQuery

        return AnyForm(FloorDivQuery(self, other))

    def __rfloordiv__(self, other: object) -> AnyForm:
        from nu.core import FloorDivQuery

        return AnyForm(FloorDivQuery(other, self))

    def __mod__(self, other: object) -> AnyForm:
        from nu.core import ModQuery

        return AnyForm(ModQuery(self, other))

    def __rmod__(self, other: object) -> AnyForm:
        from nu.core import ModQuery

        return AnyForm(ModQuery(other, self))

    def __pow__(self, other: object) -> AnyForm:
        from nu.core import PowQuery

        return AnyForm(PowQuery(self, other))

    def __rpow__(self, other: object) -> AnyForm:
        from nu.core import PowQuery

        return AnyForm(PowQuery(other, self))

    def __neg__(self) -> AnyForm:
        from nu.core import NegQuery

        return AnyForm(NegQuery(self))

    def __pos__(self) -> AnyForm:
        from nu.core import PosQuery

        return AnyForm(PosQuery(self))

    def __abs__(self) -> AnyForm:
        from nu.core import AbsQuery

        return AnyForm(AbsQuery(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: object) -> BoolForm:
        from nu.core import GtQuery

        from .bool_ import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: object) -> BoolForm:
        from nu.core import LtQuery

        from .bool_ import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: object) -> BoolForm:
        from nu.core import GeQuery

        from .bool_ import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: object) -> BoolForm:
        from nu.core import LeQuery

        from .bool_ import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from .bool_ import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: object) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from .bool_ import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: object) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from .bool_ import BoolForm

        return BoolForm(IsQuery(self, other))

    # =========================================================================
    # LOGICAL (named methods; ``&`` / ``|`` are reserved for flow)
    # =========================================================================

    def and_(self, other: object) -> BoolForm:
        """Logical AND: self AND other."""
        from nu.core import AndQuery

        from .bool_ import BoolForm

        return BoolForm(AndQuery(self, other))

    def or_(self, other: object) -> BoolForm:
        """Logical OR: self OR other."""
        from nu.core import OrQuery

        from .bool_ import BoolForm

        return BoolForm(OrQuery(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu.core import NotQuery

        from .bool_ import BoolForm

        return BoolForm(NotQuery(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu.core import BoolQuery

        from .bool_ import BoolForm

        return BoolForm(BoolQuery(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: object) -> AnyForm:
        """Bitwise AND: ``self & other`` (``&`` is reserved for ``Race``)."""
        from nu.core import BitAndQuery

        return AnyForm(BitAndQuery(self, other))

    def bitor(self, other: object) -> AnyForm:
        """Bitwise OR: ``self | other`` (``|`` is reserved for ``Parallel``)."""
        from nu.core import BitOrQuery

        return AnyForm(BitOrQuery(self, other))

    def bitnot(self) -> AnyForm:
        """Bitwise NOT: ``~self`` (named form)."""
        from nu.core import BitNotQuery

        return AnyForm(BitNotQuery(self))

    def __invert__(self) -> AnyForm:
        from nu.core import BitNotQuery

        return AnyForm(BitNotQuery(self))

    def __xor__(self, other: object) -> AnyForm:
        from nu.core import BitXorQuery

        return AnyForm(BitXorQuery(self, other))

    def __rxor__(self, other: object) -> AnyForm:
        from nu.core import BitXorQuery

        return AnyForm(BitXorQuery(other, self))

    def __lshift__(self, other: object) -> AnyForm:
        from nu.core import LShiftQuery

        return AnyForm(LShiftQuery(self, other))

    def __rlshift__(self, other: object) -> AnyForm:
        from nu.core import LShiftQuery

        return AnyForm(LShiftQuery(other, self))

    def __rshift__(self, other: object) -> AnyForm:
        from nu.core import RShiftQuery

        return AnyForm(RShiftQuery(self, other))

    def __rrshift__(self, other: object) -> AnyForm:
        from nu.core import RShiftQuery

        return AnyForm(RShiftQuery(other, self))

    # =========================================================================
    # DYNAMIC DESCENT (subscript + attribute)
    # =========================================================================

    def __getitem__(self, key: object) -> AnyForm:
        """Subscript access: ``self[key]``.

        For slice keys ``a:b:c``, the slice is threaded through ``SliceQuery``
        so the whole thing stays symbolic.
        """
        from nu.core import GetItemQuery, SliceQuery

        if isinstance(key, slice):
            key = SliceQuery(key.start, key.stop, key.step)
        return AnyForm(GetItemQuery(self, key))

    def __setitem__(self, key: object, value: object) -> object:
        """Subscript write: ``self[key] = value``.

        Ref-gated at build time: the wrapped source MUST be a ``Ref`` (a
        fabric-writable location), otherwise the produced ``Command`` would be
        silently discarded by Python's assignment syntax. Raises ``TypeError``
        clearly instead of building an invalid tree.
        """
        _require_ref_source(self, "__setitem__")
        from nu.core import SetItemCommand

        return SetItemCommand(self, key, value)

    def __delitem__(self, key: object) -> object:
        """Subscript delete: ``del self[key]``. Ref-gated (see ``__setitem__``)."""
        _require_ref_source(self, "__delitem__")
        from nu.core import DelItemCommand

        return DelItemCommand(self, key)

    def __getattr__(self, name: str) -> AnyForm:
        """Attribute read: ``self.name`` -> ``GetAttr(self, name)``.

        Attributes starting with ``_`` are considered internal machinery and
        are NEVER intercepted - they fall through to Python's normal lookup
        (which raises ``AttributeError`` if genuinely missing). This keeps
        engine-private state (``_payload``, ``_children``, ``_source``, ...)
        safe from accidental capture as tree nodes.
        """
        if name.startswith("_"):
            msg = (
                f"{type(self).__name__!r} object has no attribute {name!r}"
            )
            raise AttributeError(msg)
        from nu.core import GetAttrQuery

        return AnyForm(GetAttrQuery(self, name))

    # =========================================================================
    # NAMED METHODS FOR PROTOCOL DUNDERS
    #
    # ``__len__`` / ``__contains__`` / ``__iter__`` / ``__bool__`` all require
    # Python-native return types at runtime, so they cannot participate in a
    # Nu tree. Expose the tree-shaped equivalents as named methods instead.
    # =========================================================================

    def len_(self) -> IntForm:
        """Length: ``len(self)`` as an ``IntForm`` in the tree."""
        from nu.core import LenQuery

        from .int_ import IntForm

        return IntForm(LenQuery(self))

    def contains(self, item: object) -> BoolForm:
        """Membership: ``item in self`` as a ``BoolForm`` in the tree."""
        from nu.core import ContainsQuery

        from .bool_ import BoolForm

        return BoolForm(ContainsQuery(self, item))

    def iter_(self) -> IteratorForm:
        """Iteration: ``iter(self)`` as an ``IteratorForm``."""
        from nu.core import IterQuery

        from ..collections.iterator_ import IteratorForm

        return IteratorForm(IterQuery(self))

    def has_attr(self, name: object) -> BoolForm:
        """Attribute presence: ``hasattr(self, name)`` as a ``BoolForm``."""
        from nu.core import HasAttrQuery

        from .bool_ import BoolForm

        return BoolForm(HasAttrQuery(self, name))


def _require_ref_source(form: AnyForm, op: str) -> None:
    """Guard: the wrapped source of ``form`` must be a ``Ref``.

    Python's ``x[k] = v`` / ``del x[k]`` syntax discards the return value of
    ``__setitem__`` / ``__delitem__``, so a value-node ``AnyForm`` returning
    a ``Command`` would leave the mutation orphaned. Raise clearly instead.
    """
    source = form._source
    if not isinstance(source, Ref):
        msg = (
            f"AnyForm.{op}: cannot mutate through a value-node - the "
            f"wrapped source must be a Ref (a fabric-writable location). "
            f"Got: {type(source).__name__ if source is not None else 'None'}."
        )
        raise TypeError(msg)
