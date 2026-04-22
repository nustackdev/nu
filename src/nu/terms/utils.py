"""Utilities for authoring Interfaces and analyzing trees.

Contains:
  - AutoInterface, method, prop  (declarative Interface construction)
  - tracked_effects, is_pure      (tree effect analysis)
"""

from __future__ import annotations

import typing
from typing import TYPE_CHECKING, overload

from .interface import Interface
from .ref import Ref
from .types import Direction, TrackedEffect


if TYPE_CHECKING:
    from .nu import Nu


__all__ = [
    "AutoInterface",
    "is_pure",
    "method",
    "prop",
    "tracked_effects",
]


# =============================================================================
# INTERFACE DESCRIPTORS
# =============================================================================


class _BoundMethod[V: Interface]:
    """Method descriptor bound to a specific instance.

    Calling this creates a MethodCallOp (pure) or MethodCallCmd (impure) op
    wrapping the call, then wraps it in value_type.
    """

    __slots__ = ("_method_name", "_owner", "_pure", "_value_type")

    def __init__(self, owner: object, value_type: type[V], method_name: str, *, pure: bool) -> None:
        self._owner = owner
        self._value_type = value_type
        self._method_name = method_name
        self._pure = pure

    def __call__(self, *args: object, **kwargs: object) -> V:
        from nu.ops import MethodCallCmd, MethodCallOp

        morph_cls = MethodCallOp if self._pure else MethodCallCmd
        return self._value_type(morph_cls(self._owner, self._method_name, *args, **kwargs))

    def __repr__(self) -> str:
        return f"{self._owner!r}.{self._method_name}"


class _ClassBoundMethod[V: Interface]:
    """Method descriptor bound to a Ref subclass.

    The Ref subclass itself acts as the factory - calling it creates a ref
    Nu that resolves the target object from context at execution time.
    """

    __slots__ = ("_method_name", "_pure", "_ref_cls", "_value_type")

    def __init__(
        self,
        ref_cls: type[Ref],
        value_type: type[V],
        method_name: str,
        *,
        pure: bool,
    ) -> None:
        self._ref_cls = ref_cls
        self._value_type = value_type
        self._method_name = method_name
        self._pure = pure

    def __call__(self, *args: object, **kwargs: object) -> V:
        from nu.ops import MethodCallCmd, MethodCallOp

        target = self._ref_cls()
        morph_cls = MethodCallOp if self._pure else MethodCallCmd
        return self._value_type(morph_cls(target, self._method_name, *args, **kwargs))

    def __repr__(self) -> str:
        return f"{self._ref_cls.__name__}.{self._method_name}"


class method[V: Interface]:  # noqa: N801
    """Descriptor that proxies method calls to a Type's underlying object.

    Generic in V (an Interface subclass). Pyright infers the return type.

    Two access modes:
    - Instance access (`my_str.upper()`): creates MethodCall with instance as target.
    - Class access on Ref subclass (`Solana.get_slot()`): creates MethodCall with a
      new Ref instance as target (resolved from context at execution time).

    Uses `__set_name__` to auto-infer the method name. An explicit name can
    be provided for APIs with different naming conventions.
    """

    def __init__(self, value_type: type[V], name: str | None = None, *, pure: bool = False) -> None:
        self._value_type = value_type
        self._explicit_name = name
        self._pure = pure
        self._attr_name: str = ""
        self._method_name: str = name or ""

    def __set_name__(self, owner: type, attr_name: str) -> None:
        self._attr_name = attr_name
        self._method_name = self._explicit_name or attr_name

    @overload
    def __get__(self, obj: None, objtype: type) -> _ClassBoundMethod[V]: ...
    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> _BoundMethod[V]: ...

    def __get__(
        self, obj: object | None, objtype: type | None = None
    ) -> method[V] | _BoundMethod[V] | _ClassBoundMethod[V]:
        if obj is None:
            if objtype is not None and issubclass(objtype, Ref):
                return _ClassBoundMethod(
                    objtype, self._value_type, self._method_name, pure=self._pure
                )
            return self
        return _BoundMethod(obj, self._value_type, self._method_name, pure=self._pure)

    def __repr__(self) -> str:
        name = self._method_name or self._explicit_name or "?"
        purity = "pure" if self._pure else "impure"
        return f"method({self._value_type.__name__}, {name!r}, {purity})"


class prop[V: Interface]:  # noqa: N801
    """Descriptor that proxies property/attribute access on a Type's underlying object."""

    def __init__(self, value_type: type[V], name: str | None = None) -> None:
        self._value_type = value_type
        self._explicit_name = name
        self._attr_name: str = ""
        self._prop_name: str = name or ""

    def __set_name__(self, owner: type, attr_name: str) -> None:
        self._attr_name = attr_name
        self._prop_name = self._explicit_name or attr_name

    @overload
    def __get__(self, obj: None, objtype: type) -> V: ...
    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> V: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> prop[V] | V:
        from nu.ops import GetAttrOp

        if obj is None:
            if objtype is not None and issubclass(objtype, Ref):
                return self._value_type(GetAttrOp(objtype(), self._prop_name))
            return self
        return self._value_type(GetAttrOp(obj, self._prop_name))

    def __repr__(self) -> str:
        name = self._prop_name or self._explicit_name or "?"
        return f"prop({self._value_type.__name__}, {name!r})"


class AutoInterface:
    """Base class that auto-creates method descriptors from annotations.

    Inherit alongside Interface. Annotations of Interface subclasses become
    `method()` descriptors automatically.
    """

    def __init_subclass__(cls, *, pure: bool = False, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        own_names = set(cls.__dict__.get("__annotations__", {}))
        if not own_names:
            return

        try:
            hints = typing.get_type_hints(cls)
        except Exception:
            return

        for name in own_names:
            if name.startswith("_"):
                continue
            if name in cls.__dict__ and name != "__annotations__":
                existing = cls.__dict__[name]
                if not isinstance(existing, type):
                    continue
            hint = hints.get(name)
            if hint is not None and isinstance(hint, type) and issubclass(hint, Interface):
                setattr(cls, name, method(hint, name, pure=pure))


# =============================================================================
# EFFECT ANALYSIS
# =============================================================================


def _as_positions(spec: int | tuple[int, ...]) -> frozenset[int]:
    """Normalize `int | tuple[int, ...]` to a frozenset."""
    if isinstance(spec, int):
        return frozenset({spec})
    return frozenset(spec)


def _position_map(op: object) -> dict[int, Direction]:
    """Build {position: Direction} from an Interaction's writes/reads attrs."""
    result: dict[int, Direction] = {}
    for i in _as_positions(op.reads):  # type: ignore[attr-defined]
        result[i] = Direction.READ
    for i in _as_positions(op.writes):  # type: ignore[attr-defined]
        result[i] = Direction.WRITE
    return result


def tracked_effects(nu: Nu) -> frozenset[TrackedEffect]:
    """Compute the set of tracked effects for a Nu tree.

    Rules:
        1. Literal -> no effects
        2. Ref (not at a declared position) -> {(type(ref), READ)} + children
        3. Interaction with reads/writes -> check declared positions, recurse
    """
    from .interaction import Interaction
    from .query import Literal

    if isinstance(nu, Literal):
        return frozenset()

    if isinstance(nu, Interaction):
        effects: set[TrackedEffect] = set()
        positions = _position_map(nu)
        for i, child in enumerate(nu.children):
            if i in positions and isinstance(child, Ref):
                effects.add(TrackedEffect(type(child), positions[i]))
                for grandchild in child.children:
                    effects |= tracked_effects(grandchild)
            else:
                effects |= tracked_effects(child)
        return frozenset(effects)

    if isinstance(nu, Ref):
        effects = {TrackedEffect(type(nu), Direction.READ)}
        for child in nu.children:
            effects |= tracked_effects(child)
        return frozenset(effects)

    # Bare Nu (plain composition, NuIndepComm): recurse, union
    result: set[TrackedEffect] = set()
    for child in nu.children:
        result |= tracked_effects(child)
    return frozenset(result)


def is_pure(nu: Nu) -> bool:
    """True if the Nu tree has no tracked effects."""
    return len(tracked_effects(nu)) == 0
