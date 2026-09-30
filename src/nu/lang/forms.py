"""Form and TypedNu - the type-wrapping layer.

``Form`` is a mixin that contributes shared helpers (sentinel checks) to typed
interfaces. The collection ABCs (``MappingForm``, ``SequenceForm``, ...) and the
primitive leaves (``Int``, ``Str``, ...) inherit ``Form`` to get them.

``TypedNu[T]`` is a transparent ``ScalarQuery`` passthrough: it wraps a single
Nu child (any non-Term child is auto-wrapped as a ``Literal`` by ``Nu``) and
yields the child's value unchanged. Operand recursion lives in the child thunk;
``TypedNu`` just forwards. Leaf interfaces inherit both ``Form`` and ``TypedNu``
so they participate as Nu tree nodes::

    Int(Add(a, b)) + 1  ->  Add(Int(Add(a, b)), Literal(1))

``TypedNuStream[T]`` is its stream-shaped twin: a transparent ``StreamQuery``
passthrough over one stream child, so a stream form (``Iterator``) sits
wherever the validator expects a stream.

Hierarchy::

    Form                                    mixin (sentinel checks)
    TypedNu[T]                              ScalarQuery passthrough
    TypedNuStream[T]                        StreamQuery passthrough
    Int(Form, TypedNu[int])            primitive leaf
    Dict(MutableMappingForm, TypedNu[dict])   collection leaf

The sentinel-check helpers and ``Bool`` they return live in ``nu.forms``;
``Form`` reaches them with a lazy import so this module keeps no import-time
dependency on the forms package (it would be a cycle: forms imports ``Form``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from .kinds import ScalarQuery, StreamQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.forms import Bool
    from nu.lang.runtime import Runtime


__all__ = [
    "Form",
    "TypedNu",
    "TypedNuStream",
]


T_co = TypeVar("T_co", covariant=True)


class Form:
    """Mixin for typed interfaces. Contributes sentinel-check helpers and ``==``.

    ``==`` / ``!=`` on a Form build ``Eq`` / ``Ne`` over the values it yields
    (the bare ``Nu`` base raises instead). Concrete Forms narrow the operand
    type by overriding them; a Form with no value equality raises.
    """

    def __eq__(self, other: object) -> Bool:  # type: ignore[override]
        """Self equal to other by value: an ``Eq`` term, never a Python bool."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: object) -> Bool:  # type: ignore[override]
        """Self not equal to other by value: a ``Ne`` term, never a Python bool."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))

    def is_empty(self) -> Bool:
        """True if this Form yields the EMPTY sentinel."""
        from nu.core import IsEmpty
        from nu.forms import Bool

        return Bool(IsEmpty(self))

    def is_invalid(self) -> Bool:
        """True if this Form yields the INVALID sentinel."""
        from nu.core import IsInvalid
        from nu.forms import Bool

        return Bool(IsInvalid(self))

    def is_sentinel(self) -> Bool:
        """True if this Form yields either sentinel (EMPTY or INVALID)."""
        return self.is_empty().or_(self.is_invalid())

    def not_empty(self) -> Bool:
        """True if this Form does not yield EMPTY."""
        return self.is_empty().not_()

    def not_invalid(self) -> Bool:
        """True if this Form does not yield INVALID."""
        return self.is_invalid().not_()


class TypedNu(ScalarQuery[T_co], Generic[T_co]):  # PEP 695 has no variance markers
    """Transparent ScalarQuery passthrough carrying a python type tag ``T``.

    Wraps a single Nu child and yields its value unchanged - sentinels ride
    through untouched. The type tag is for the fluent surface only; it has no
    runtime effect.
    """

    def __init__(self, *children: object) -> None:
        super().__init__(*children)

    @property
    def _source(self) -> Any:  # noqa: ANN401
        """The wrapped child Term, or None when there is no child."""
        return self._children[0] if self._children else None

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            return only(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            return await only(rt)

        return athunk


class TypedNuStream(StreamQuery[T_co], Generic[T_co]):  # PEP 695 has no variance markers
    """Transparent StreamQuery passthrough carrying a python type tag ``T``.

    The stream twin of ``TypedNu``: wraps a single stream child and yields
    its items unchanged, so a stream form is stream-sorted and every stream
    consumer (``Collect``, ``Map``, ``ForEachDo``, ...) accepts it. The type
    tag is for the fluent surface only; it has no runtime effect.
    """

    def __init__(self, *children: object) -> None:
        super().__init__(*children)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            return only(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            return await only(rt)

        return athunk
