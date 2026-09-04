"""Recursive type info for shape slots.

``TypeInfo`` is the runtime carrier for an annotation-derived type. Refs stash
it on their payload; wrappers read it to pick the child ref/form on subscript
or attribute descent.

A Shape slot annotation is one of:

- **Bare ref class** (``nm.StrRef``, ``nd.HeadingRef``): a ``Ref`` subclass
  with no generic parameters. Represented as ``TypeInfo(<ref_cls>)``.
- **Parametric ref class** (``nv.PrimitiveListRef[str]``,
  ``nm.ShapesDictRef[int, Order]``): a ``Ref`` subclass with generic params.
  Represented as ``TypeInfo(<ref_origin>, key=..., elem=...)`` where key/elem
  recurse.
- **Bare Shape subclass** (``Order``): a shorthand for a ``ShapeRef``
  navigating that shape. Represented as ``TypeInfo(<shape_cls>)``.
- **Python primitive** (``str``, ``int``, ...): only appears as an inner
  type arg of a ``Primitive*Ref`` (blob-stored collection). Represented as
  ``TypeInfo(<primitive_cls>)``.
- **``Any``**: the fallback (non-trivial union, unresolvable forward ref,
  unknown type).

The primitive is:

- ``TypeInfo.from_annotation(ann, hints)`` normalizes any annotation into a
  recursive ``TypeInfo``: resolves ``T | None`` to ``T``, folds non-trivial
  unions to ``Any``, recognises Ref subclasses (bare + parametric), Shape
  subclasses, primitives, native container generics, and
  ``ForwardRef`` / string annotations via ``hints``.
- ``TypeInfo.to_form(tier=None)`` dispatches ``py_type`` to a concrete
  ``Form`` class, meaningful at primitive-leaf yield positions. Ref-typed
  or Shape-typed levels are handled by the wrapper directly (it descends
  into the ref/shape instead of yielding a value-Form). ``Any`` is the
  fallback.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from types import UnionType
from typing import TYPE_CHECKING, Any, ForwardRef, Union

from nu.lang.kinds import Ref


if TYPE_CHECKING:
    from nu.lang.forms import Form


__all__ = ["TypeInfo", "value_type_for"]


_NoneType = type(None)

_PRIMITIVE_TYPES: frozenset[type] = frozenset(
    {int, str, float, bool, bytes, list, dict, set, tuple, frozenset}
)


@dataclass(frozen=True)
class TypeInfo:
    """Recursive carrier of an annotation-derived type.

    ``py_type`` is the resolved outer type (a ``Ref`` subclass, a ``Shape``
    subclass, a Python primitive, or ``Any``). ``key`` and ``elem`` are
    optional child ``TypeInfo`` s: populated for mapping-like containers
    (``key`` + ``elem``) and sequence/set-like containers (``elem`` only),
    otherwise ``None``.
    """

    py_type: Any
    key: TypeInfo | None = None
    elem: TypeInfo | None = None

    @classmethod
    def any(cls) -> TypeInfo:
        """The honest-terminal ``TypeInfo``: genuinely unknown."""
        return cls(Any)

    @classmethod
    def from_annotation(cls, ann: object, hints: dict[str, object] | None = None) -> TypeInfo:
        """Normalize an annotation into a recursive ``TypeInfo``."""
        return _normalize(ann, hints or {})

    @property
    def is_ref(self) -> bool:
        """True when ``py_type`` is a ``Ref`` subclass."""
        return isinstance(self.py_type, type) and issubclass(self.py_type, Ref)

    @property
    def is_shape(self) -> bool:
        """True when ``py_type`` is a ``Shape`` subclass.

        Duck-typed on the ``_slots`` marker set by ``ShapeMeta`` so this
        module does not import ``nu.domains.shape.dsl`` (which imports us).
        """
        py = self.py_type
        return (
            isinstance(py, type)
            and hasattr(py, "_slots")
            and not (isinstance(py, type) and issubclass(py, Ref))
        )

    @property
    def is_primitive(self) -> bool:
        """True when ``py_type`` is a native Python primitive."""
        return self.py_type in _PRIMITIVE_TYPES

    @property
    def is_any(self) -> bool:
        """True when this is the ``Any`` fallback."""
        return self.py_type is Any

    def to_form(self, tier: object | None = None) -> type[Form]:
        """Dispatch ``py_type`` to its ``Form`` class (``Any`` fallback).

        Meaningful only at primitive-leaf positions (inside
        ``Primitive*Ref`` type args). Ref-typed or Shape-typed levels are
        handled by the wrapper directly: it descends into the ref/shape
        instead of yielding a value-Form.

        ``tier`` is reserved for the structured-ref tier ladder.
        """
        del tier
        return _form_for(self.py_type)


def _normalize(ann: object, hints: dict[str, object]) -> TypeInfo:
    if isinstance(ann, str):
        if ann in hints:
            return _normalize(hints[ann], hints)
        return TypeInfo(Any)
    if isinstance(ann, ForwardRef):
        name = ann.__forward_arg__
        if name in hints:
            return _normalize(hints[name], hints)
        return TypeInfo(Any)

    if ann is Any:
        return TypeInfo(Any)

    origin = typing.get_origin(ann)
    args = typing.get_args(ann)

    if origin in (Union, UnionType):
        non_none = [a for a in args if a is not _NoneType]
        if len(non_none) == 1:
            return _normalize(non_none[0], hints)
        return TypeInfo(Any)

    if origin is not None and isinstance(origin, type) and issubclass(origin, Ref):
        return _parametric_ref(origin, args, hints)

    if origin is dict:
        k, v = (*args, Any, Any)[:2]
        return TypeInfo(dict, key=_normalize(k, hints), elem=_normalize(v, hints))
    if origin is list:
        elem = args[0] if args else Any
        return TypeInfo(list, elem=_normalize(elem, hints))
    if origin is tuple:
        elem = args[0] if args else Any
        return TypeInfo(tuple, elem=_normalize(elem, hints))
    if origin is set:
        elem = args[0] if args else Any
        return TypeInfo(set, elem=_normalize(elem, hints))
    if origin is frozenset:
        elem = args[0] if args else Any
        return TypeInfo(frozenset, elem=_normalize(elem, hints))

    if ann is dict:
        return TypeInfo(dict, key=TypeInfo(Any), elem=TypeInfo(Any))
    if ann is list:
        return TypeInfo(list, elem=TypeInfo(Any))
    if ann is tuple:
        return TypeInfo(tuple, elem=TypeInfo(Any))
    if ann is set:
        return TypeInfo(set, elem=TypeInfo(Any))
    if ann is frozenset:
        return TypeInfo(frozenset, elem=TypeInfo(Any))

    if isinstance(ann, type):
        return TypeInfo(ann)

    return TypeInfo(Any)


def _parametric_ref(ref_cls: type, args: tuple, hints: dict[str, object]) -> TypeInfo:
    """Build a ``TypeInfo`` for a parametric Ref like ``PrimitiveListRef[str]``.

    Arity-based placement: two args -> ``(key, elem)``; one arg -> ``elem``.
    Zero args -> the ref itself with no children.
    """
    if len(args) == 2:
        return TypeInfo(
            ref_cls,
            key=_normalize(args[0], hints),
            elem=_normalize(args[1], hints),
        )
    if len(args) == 1:
        return TypeInfo(ref_cls, elem=_normalize(args[0], hints))
    return TypeInfo(ref_cls)


def _form_for(py_type: object) -> type[Form]:
    from nu.forms import (
        Any as AnyForm,
    )
    from nu.forms import (
        Bool,
        Bytes,
        Dict,
        Float,
        FrozenSet,
        Int,
        List,
        Set,
        Str,
        Tuple,
    )

    mapping: dict[Any, type[Form]] = {
        bool: Bool,
        int: Int,
        float: Float,
        str: Str,
        bytes: Bytes,
        list: List,
        dict: Dict,
        set: Set,
        frozenset: FrozenSet,
        tuple: Tuple,
    }
    return mapping.get(py_type, AnyForm)  # type: ignore[arg-type]


def value_type_for(python_type: object) -> type[Form]:
    """Map a Python primitive type to its ``Form`` class (``Any`` fallback).

    Convenience wrapper over ``_form_for``: the sole dispatch source of truth.
    """
    return _form_for(python_type)
